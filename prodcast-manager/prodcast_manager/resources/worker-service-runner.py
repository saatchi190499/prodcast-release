"""Windows workflow service entry point; all submitted Python uses AppContainer."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlencode, quote

ROOT = Path(os.environ['PRODCAST_WORKER_HOME']).resolve()
config = json.loads((ROOT / 'site.json').read_text(encoding='utf-8-sig'))
for key in ('postgres_host', 'postgres_db', 'postgres_user', 'redis_host', 'redis_user', 'main_server_url'):
    if not config.get(key) or 'example.invalid' in config[key]:
        raise RuntimeError('Missing site setting: ' + key)
if not config['main_server_url'].startswith('https://'):
    raise RuntimeError('HTTPS main server required')
worker_number = config['worker_number']
if worker_number not in {f'{n:02}' for n in range(1,17)}:
    raise RuntimeError('Unknown worker identity')
postgres_user = config['postgres_user']
sys.path.insert(0, str(Path(__file__).resolve().parent))
import win32crypt
from worker.log_redaction import install_log_redaction
from worker.structured_logging import configure_worker_logging

install_log_redaction()
_, payload = win32crypt.CryptUnprotectData((ROOT / 'scheduler.machine.dpapi').read_bytes(), None, None, None, 0)
secret = json.loads(payload)
del payload
ca = str(ROOT / 'prodcast-db-ca.crt')
query = urlencode({'ssl_cert_reqs': 'required', 'ssl_ca_certs': ca})
redis_base = 'rediss://' + quote(config['redis_user'], safe='') + ':' + quote(secret['redis_password'], safe='') + '@' + config['redis_host'] + ':' + str(config.get('redis_port', 6380)) + '/'
os.environ.update(
    SERVICE_NAME=f'prodcast-worker-{worker_number}', WORKER_LOG_DIR=str(ROOT / 'logs'),
    WORKER_JSON_LOGS='true', WORKER_FILE_LOGS='true',
    POSTGRES_HOST=config['postgres_host'], POSTGRES_PORT=str(config.get('postgres_port', 5432)), POSTGRES_DB=config['postgres_db'],
    POSTGRES_USER=postgres_user, POSTGRES_PASSWORD=secret['postgres_password'],
    PGSSLMODE='verify-full', PGSSLROOTCERT=ca, PGCONNECT_TIMEOUT='5',
    PGOPTIONS='-c statement_timeout=10000',
    CELERY_BROKER_URL=redis_base+'0?'+query, CELERY_RESULT_BACKEND=redis_base+'1?'+query,
    WORKER_MAIN_SERVER_BASE_URL=config['main_server_url'],
    WORKER_MAIN_SERVER_API_KEY=secret['media_key'],
    WORKER_MAIN_SERVER_CA_BUNDLE=str(ROOT / 'prodcast-app-ca.crt'),
    WORKER_WORKFLOW_ARTIFACT_SIGNING_KEY=secret['signing_key'],
    WORKER_WORKFLOW_ARTIFACT_SIGNING_REQUIRED='true',
    WORKER_WORKFLOW_SANDBOX_MODE='windows-appcontainer',
    WORKER_WINDOWS_JOBS_ROOT=str(ROOT / 'jobs'),
    WORKER_SCENARIO_RECOVERY_ROOT=str(ROOT / 'recovery'),
    WORKER_DISABLE_REMOTE_IMPORTS='true', WORKER_MAX_WORKFLOW_ARTIFACT_BYTES='1000000',
    CELERY_DEAD_LETTER_LOG_PATH=str(ROOT / 'logs/dead-letter.jsonl'),
    MEDIA_ROOT=str(ROOT / 'jobs'), TEMP=str(ROOT / 'logs'), TMP=str(ROOT / 'logs'),
)
del secret
configure_worker_logging()
from worker.windows_sandbox import run_windows_python
from worker.db import setup_django
from worker.scenario_recovery import initialize_recovery
setup_django()
initialize_recovery()
rc, out, err = run_windows_python('print("WINDOWS_SANDBOX_READY")', timeout=20)
if rc != 0 or 'WINDOWS_SANDBOX_READY' not in out:
    raise RuntimeError('AppContainer startup check failed: ' + err[-1000:])
from worker.celery import app
from worker import tasks
from worker.health import install_consumer_lease
install_consumer_lease(app, f'worker{worker_number}.health')
app.finalize()
# Scenario task is Python-only on Windows; built-in helpers remain unavailable.
for name in list(app.tasks):
    if name not in {'worker.run_workflow', 'worker.run_scenario'}:
        app.tasks.pop(name, None)
for name in ('worker.run_workflow', 'worker.run_scenario'):
    app.tasks[name].acks_late = False
    app.tasks[name].reject_on_worker_lost = False
app.conf.update(
    broker_transport_options={'visibility_timeout': 900, 'unacked_key': f'worker{worker_number}.unacked',
                              'unacked_index_key': f'worker{worker_number}.unacked_index',
                              'unacked_mutex_key': f'worker{worker_number}.unacked_mutex'},
    result_expires=3600, worker_concurrency=1, worker_prefetch_multiplier=1,
    worker_send_task_events=False, task_acks_late=False,
)
# Never re-execute a partially completed script after a lost service process.
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT current_user, ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
    assert cursor.fetchone() == (postgres_user, True)
(ROOT / 'logs/scheduler-service-ready.json').write_text(json.dumps({'mode': 'windows-appcontainer', 'postgres_tls': True, 'queues': ['workflows', 'workflows_data', 'scenarios']}))
app.worker_main(['worker', '--pool=solo', '--concurrency=1', '-Q', 'workflows,workflows_data,scenarios',
                 '-n', f'prodcast-worker-{worker_number}@%h', '--without-gossip', '--without-mingle',
                 '--without-heartbeat', '--loglevel=WARNING'])
