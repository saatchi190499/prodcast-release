"""Portable profiles and automatic local credentials; no machine-bound encryption."""
from .i18n import tr
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import uuid
from .config import atomic_json, file_lock, validate
from .vault import Vault


class LegacyPasswordRequired(ValueError):
    pass


def _copy_missing(source, destination):
    """Copy legacy entries without replacing anything already in the new folder."""
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_symlink():
            continue
        if target.exists():
            # A profile directory is a consistency boundary: never merge two
            # same-named profiles, since that could mix site.json and vault state.
            if (item.is_dir() and target.is_dir() and item.parent.name.casefold() != 'sites'
                    and not target.is_symlink()):
                _copy_missing(item, target)
            continue
        if item.is_dir():
            shutil.copytree(item, target, symlinks=True)
        else:
            shutil.copy2(item, target)


def data_directory(home):
    """Return the Manager data root, migrating the previous `data` and `logs` paths."""
    home = Path(home)
    current = home / 'prodcast-data'
    legacy = home / 'data'
    if legacy.is_dir() and not current.exists():
        try:
            legacy.replace(current)
        except OSError:
            _copy_missing(legacy, current)
    elif legacy.is_dir():
        _copy_missing(legacy, current)

    old_logs = home / 'logs'
    new_logs = current / 'logs'
    if old_logs.is_dir() and not new_logs.exists():
        try:
            current.mkdir(parents=True, exist_ok=True)
            old_logs.replace(new_logs)
        except OSError:
            _copy_missing(old_logs, new_logs)
    elif old_logs.is_dir():
        _copy_missing(old_logs, new_logs)
    return current


def profile_directory(home, config):
    validate(config)
    endpoints = {r: h['address'] for r, h in config['hosts'].items() if r!='ai'}
    if '_worker_topology_hosts' in config:
        endpoints={r:a for r,a in endpoints.items() if not r.startswith('worker')}
        endpoints.update(config['_worker_topology_hosts'])
    key = hashlib.sha256(json.dumps(endpoints, sort_keys=True).encode()).hexdigest()[:12]
    return data_directory(home) / 'sites' / (config['site_id'] + '-' + key)


def runtime_config(path):
    path = Path(path)
    config = validate(json.loads(path.read_text('utf-8-sig')))
    config.setdefault('_ai_topology_address',config['hosts']['ai']['address'])
    for host in config['hosts'].values():
        if host.get('key_path') and not Path(host['key_path']).is_absolute():
            host['key_path'] = str((path.parent / host['key_path']).resolve())
    return config


def save_config(directory, config):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stored = copy.deepcopy(config)
    for role, host in stored['hosts'].items():
        if host['auth'] != 'key' or not host.get('key_path'):
            continue
        source = Path(host['key_path'])
        if not source.is_absolute():
            source = directory / source
        try: data = source.read_bytes()
        except OSError:
            if role != 'ai': raise
            # Missing optional AI credentials must not prevent saving/deploying core.
            continue
        name = 'ssh/' + role + '-' + hashlib.sha256(data).hexdigest()[:16] + '.key'
        target = directory / name
        target.parent.mkdir(exist_ok=True)
        if not target.exists():
            with target.open('xb') as f:
                os.chmod(target, 0o600)
                f.write(data)
        host['key_path'] = name
    atomic_json(directory / 'site.json', stored)
    return runtime_config(directory / 'site.json')


def import_site(path, home):
    path = Path(path).resolve()
    config = runtime_config(path)
    home = Path(home).resolve()
    root = data_directory(home)
    if path.is_relative_to(root / 'sites'):
        return path.parent, config
    destination = profile_directory(home, config)
    if destination.exists():
        raise ValueError(tr('Эта площадка уже есть в prodcast-data/sites. Откройте её site.json из папки Manager.'))
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + '.import-' + uuid.uuid4().hex)
    staging.mkdir()
    # Copy state as a snapshot. Never transfer locks or caches, or change the source.
    names = ('vault.json', 'secrets.json', 'secrets.key', 'journal.json',
             'app-tls-journal.json', 'ai-journal.json', 'workers-journal.json', 'worker-action-journal.json', 'maintenance-journal.json', 'prodcast-ca.crt', 'history')
    for name in names:
        source = path.parent / name
        if source.is_symlink():
            raise ValueError(tr('Импорт состояния через символические ссылки запрещён'))
        if source.is_dir():
            if any(p.is_symlink() for p in source.rglob('*')):
                raise ValueError(tr('В истории найдена символическая ссылка'))
            shutil.copytree(source, staging / name)
        elif source.exists():
            shutil.copy2(source, staging / name)
    save_config(staging, config)
    staging.rename(destination)
    return destination, runtime_config(destination / 'site.json')


def open_credentials(directory, legacy_password=''):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    secret_file = directory / 'secrets.json'
    key_file = directory / 'secrets.key'
    with file_lock(directory / 'credentials.lock'):
        if secret_file.exists():
            if not key_file.exists():
                raise ValueError(tr('Не найден secrets.key. Восстановите его из копии этой площадки; новый ключ создавать нельзя.'))
            return Vault(secret_file, key_file.read_text('ascii').strip())
        data = {}
        legacy = directory / 'vault.json'
        if legacy.exists():
            if not legacy_password:
                raise LegacyPasswordRequired(tr('Введите прежний пароль vault один раз для импорта площадки.'))
            data = Vault(legacy, legacy_password).data
        if not key_file.exists():
            with key_file.open('x', encoding='ascii') as f:
                os.chmod(key_file, 0o600)
                f.write(secrets.token_urlsafe(48))
        vault = Vault(secret_file, key_file.read_text('ascii').strip())
        vault.data = data
        vault.save()
        return vault


def remember(home, directory):
    root = data_directory(Path(home).resolve())
    atomic_json(root / 'manager.json', {'site': str(Path(directory).resolve().relative_to(root))})


def last_directory(home):
    root = data_directory(Path(home).resolve())
    path = root / 'manager.json'
    if path.exists():
        stored = Path(json.loads(path.read_text('utf-8'))['site'])
        parts = stored.parts
        if parts and parts[0].casefold() in ('data', 'prodcast-data'):
            stored = Path(*parts[1:])
        directory = (root / stored).resolve()
        if not directory.is_relative_to(root / 'sites'):
            raise ValueError(tr('Путь площадки выходит за пределы portable-папки'))
        return directory
    return root / 'sites' / 'new'
