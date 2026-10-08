"""Offline delivery helpers. No network operations are permitted here."""
import hashlib, zipfile
from pathlib import Path

PROFILE='prodcast-five-vm-v3-offline'

def assemble_parts(path,cache):
    path=Path(path)
    if not path.name.endswith('.zip.001'):return path
    prefix=path.name[:-3]
    parts=sorted(path.parent.glob(prefix+'[0-9][0-9][0-9]'))
    if not parts or len(parts)>32:raise ValueError('Missing or excessive offline archive parts')
    if [p.name for p in parts]!=[prefix+f'{n:03}' for n in range(1,len(parts)+1)]:
        raise ValueError('Offline archive parts are missing. Place every part in the same folder.')
    total=sum(p.stat().st_size for p in parts)
    if total>20*1024**3:raise ValueError('Offline archive exceeds 20 GiB')
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    # Content-derived cache name, never trust a sidecar or partial file.
    signature=hashlib.sha256()
    for part in parts:
        with part.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):signature.update(chunk)
    dest=cache/('offline-'+signature.hexdigest()[:24]+'.zip')
    if dest.exists():
        h=hashlib.sha256()
        with dest.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
        if h.digest()==signature.digest():return dest
    temporary=dest.with_suffix('.partial')
    try:
        with temporary.open('wb') as out:
            for part in parts:
                with part.open('rb') as src:
                    for chunk in iter(lambda:src.read(1024*1024),b''):out.write(chunk)
        if not zipfile.is_zipfile(temporary):
            raise ValueError('Offline archive is incomplete or corrupt. Place every numbered part in the same folder and select .zip.001.')
        temporary.replace(dest)
    except Exception:
        temporary.unlink(missing_ok=True);raise
    return dest
