"""Package only public binary release artifacts and write verification hashes."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prodcast_manager import __version__
from prodcast_manager.release import sha


def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--models',required=True)
    args=parser.parse_args();directory=Path(args.directory);models=Path(args.models)
    names=['ProdCast-Manager.exe',f'RELEASE-NOTES-{__version__}-EN.md',f'RELEASE-NOTES-{__version__}-RU.md',
           'ProdCast-Manager-Manual-EN-v0.6-Offline.pdf','ProdCast-Manager-Manual-RU-v0.6-Offline.pdf']
    hashes={name:sha(directory/name) for name in names}
    (directory/'SHA256SUMS.txt').write_text(''.join(f'{value}  {name}\n' for name,value in hashes.items()),encoding='ascii')
    archive=directory.with_name(directory.name+'.zip')
    if archive.exists():raise ValueError('Release ZIP already exists; do not overwrite a published artifact')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for name in names+['SHA256SUMS.txt']:output.write(directory/name,directory.name+'/'+name)
    archive_hash=sha(archive);model_hash=sha(models)
    Path(str(archive)+'.sha256').write_text(archive_hash+'  '+archive.name+'\n',encoding='ascii')
    Path(str(models)+'.sha256').write_text(model_hash+'  '+models.name+'\n',encoding='ascii')
    with zipfile.ZipFile(archive) as packaged:
        assert packaged.testzip() is None
        assert all(not n.endswith(('.py','.key','.json')) for n in packaged.namelist())
        assert len(packaged.namelist())==len(names)+1
        assert directory.name.endswith(__version__)
    print(json.dumps({'version':__version__,'manager_zip':str(archive),'manager_zip_sha256':archive_hash,
        'exe_sha256':hashes['ProdCast-Manager.exe'],'models_zip':str(models),'models_zip_sha256':model_hash,
        'models_zip_bytes':models.stat().st_size,'zip_contents':names+['SHA256SUMS.txt']},indent=2))


if __name__=='__main__':main()
