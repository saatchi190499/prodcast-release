"""Scoped access retirement; database objects and historical records are retained."""
import json
import re


def dispatch(a):
    p = a.P
    spec = p['worker_action']
    role = spec['role']
    if (p['role'] != 'db' or p['mode'] != 'worker-remove'
            or not re.fullmatch(r'worker([1-9]|1[0-6])', role)
            or role not in spec['previous_workers']
            or role in spec['target']['hosts']):
        raise RuntimeError('Invalid Worker retirement request')
    target = {r: h['address'] for r, h in spec['target']['hosts'].items() if r.startswith('worker')}
    previous = spec['previous_workers']
    if not target or target != {r: ip for r, ip in previous.items() if r != role}:
        raise RuntimeError('Worker retirement must remove exactly one member')
    if a.ST.get('maintenance') != p['operation']:
        raise RuntimeError('Claim the DB for this Worker action first')
    receipt_path = a.STATE / 'worker-retirement.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    if receipt and not receipt.get('complete') and receipt.get('operation') != p['operation']:
        raise RuntimeError('Resume the previous Worker retirement')
    if receipt.get('operation') == p['operation'] and receipt.get('target') != target:
        raise RuntimeError('Worker retirement target changed')
    if p['action'] == 'worker-retire-membership':
        if receipt.get('operation') != p['operation'] or not receipt.get('revoked'):
            raise RuntimeError('Revoke Worker access before membership commit')
        a.ST['worker_hosts'] = target
        a.ST.setdefault('retired_workers',{})[role]={'operation':p['operation'],'address':previous[role]}
        a.save()
        receipt['complete'] = True
        a.write(receipt_path, json.dumps(receipt))
        return {'removed': role}
    if p['action'] != 'worker-retire-access':
        raise RuntimeError('Unknown Worker retirement action')
    folder = a.ROOT / 'db/config'
    hba = folder / 'pg_hba.conf'
    acl = folder / 'users.acl'
    if receipt.get('operation') != p['operation']:
        backup = a.STATE / 'worker-backups' / p['operation']
        a.write(backup / 'pg_hba.conf', hba.read_text())
        a.write(backup / 'users.acl', acl.read_text())
        receipt = {'operation': p['operation'], 'target': target, 'complete': False}
        a.write(receipt_path, json.dumps(receipt))
    name = 'prodcast_worker_' + f'{int(role[6:]):02}'
    # Retain SQL roles and object ownership, but prevent all new logins.
    a.psql("ALTER ROLE " + name + " NOLOGIN;")
    a.psql("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='" + name + "';")
    from workers_linux import replace
    replace(a, hba, ''.join(line for line in hba.read_text().splitlines(True)
                           if name not in line.split()))
    if a.psql('SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL;').strip() != '0':
        raise RuntimeError('PostgreSQL access configuration validation failed')
    if a.psql('SELECT pg_reload_conf();').strip() != 't':
        raise RuntimeError('PostgreSQL reload failed')
    scheduler = name + '_scheduler'
    replace(a, acl, ''.join(line for line in acl.read_text().splitlines(True)
                           if not line.startswith('user ' + scheduler + ' ')))
    def redis(*args):
        return a.dc('db', 'exec', '-T', 'redis', 'sh', '-c',
                    'read -r REDISCLI_AUTH; export REDISCLI_AUTH; exec redis-cli --tls --cacert /etc/prodcast-certs/ca.crt -h 127.0.0.1 -p 6380 --user db_admin "$@"',
                    'redis-admin', *args, input=a.S['REDIS_ADMIN'] + '\n')
    if redis('ACL', 'LOAD').strip() != 'OK':
        raise RuntimeError('Redis ACL reload failed')
    redis('CLIENT', 'KILL', 'USER', scheduler, 'SKIPME', 'yes')
    receipt['revoked'] = True
    a.write(receipt_path, json.dumps(receipt))
    return {'revoked': role, 'database_objects_preserved': True}
