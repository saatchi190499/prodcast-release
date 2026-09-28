"""Release integrity and GitHub helpers; only built artifacts cross repositories."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import zipfile

REPO = 'saatchi190499/prodcast-release'
COMPONENTS = {'app', 'agent', 'ai', 'worker'}


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def filename(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value):
        raise ValueError('Invalid artifact filename')
    return value


def version(value):
    if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?(?:-rc\.\d+)?', value):
        raise ValueError('Expected vX.Y.Z or vX.Y.Z-rc.N')
    return value


def record(path, **extra):
    path = Path(path)
    return {'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path), **extra}


def verify(folder, item):
    path = Path(folder) / filename(item['name'])
    if path.is_symlink() or not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
        raise ValueError('Artifact integrity failed: ' + item['name'])
    return path


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def unpack(archive, destination):
    """Our component and Complete ZIPs contain flat, regular files only."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as source:
        names = set()
        for item in source.infolist():
            name = filename(item.filename)
            mode = item.external_attr >> 16
            if name in names or item.is_dir() or stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError('Duplicate or non-regular ZIP entry')
            names.add(name)
        for item in source.infolist():
            with source.open(item) as src, (destination / item.filename).open('wb') as dst:
                shutil.copyfileobj(src, dst)


def pack(folder, output, names):
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in sorted(names):
            path = Path(folder) / filename(name)
            if path.is_symlink() or not path.is_file():
                raise ValueError('Only regular artifact files can be packaged')
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            with path.open('rb') as src, archive.open(info, 'w', force_zip64=True) as dst:
                shutil.copyfileobj(src, dst)


def gh(*args, json_input=None):
    command = ['gh', *args]
    if json_input is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=None if json_input is None else json.dumps(json_input),
                            text=True, capture_output=True, check=False)
    if result.returncode:
        # GitHub CLI redacts credentials; do not print request headers or environment.
        raise RuntimeError(result.stderr.strip() or 'GitHub request failed')
    return result.stdout


def release(tag):
    # The tag endpoint excludes drafts, even for authenticated owners.
    tag = version(tag)
    pages = json.loads(gh('api', f'repos/{REPO}/releases?per_page=100', '--paginate', '--slurp'))
    matches = [item for page in pages for item in page if item['tag_name'] == tag]
    if len(matches) > 1:
        raise ValueError('Multiple releases have this tag; resolve duplicate drafts first')
    if not matches:
        raise RuntimeError('Release not found (HTTP 404): ' + tag)
    return matches[0]


def draft(tag):
    value = release(tag)
    if not value['draft']:
        raise ValueError('Published releases are immutable; choose a new version')
    return value


def download(tag, name, folder):
    filename(name)
    Path(folder).mkdir(parents=True, exist_ok=True)
    gh('release', 'download', version(tag), '--repo', REPO, '--pattern', name, '--dir', str(folder))
    path = Path(folder) / name
    if not path.is_file():
        raise ValueError('Missing downloaded asset: ' + name)
    return path


def upload(tag, paths):
    draft(tag)
    gh('release', 'upload', version(tag), *map(str, paths), '--repo', REPO)
