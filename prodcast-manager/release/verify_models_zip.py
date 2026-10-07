"""Local release verification: import the real model ZIP through both adapters."""
import importlib.util
import json
import shutil
import sys
import types
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prodcast_manager.ai_models import prepare_bundle
from prodcast_manager.release import sha


def main():
    release,models,metadata,cache=map(Path,sys.argv[1:])
    cache.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(release) as archive:
        name=next(n for n in archive.namelist() if n.endswith('release-manifest.json'))
        document=json.loads(archive.read(name));offline=document['management']['offline']
    expected=next(a['sha256'] for a in document['artifacts'] if a['name']==offline['model_archive'])
    assert sha(metadata)==expected
    bundle=prepare_bundle(models,cache,offline['external_model'],offline['model_digest'])
    print('PASS: real ZIP validated by Manager',flush=True)
    shutil.copyfile(metadata,cache/metadata.name)
    if sys.platform=='win32':sys.modules['fcntl']=types.SimpleNamespace()
    spec=importlib.util.spec_from_file_location('verify_linux_agent',Path(__file__).parents[1]/'prodcast_manager/resources/linux.py')
    agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
    agent.OLLAMA_HOME=cache/'remote-import';agent.os.chown=lambda *a:None
    agent.P={'offline':offline,'stage':str(cache),'files':{
        'offline-model_archive':{'name':metadata.name,'sha256':sha(metadata)},
        'offline-model_bundle':{'name':bundle.name,'sha256':sha(bundle)}}}
    agent.install_offline_model(1000,1000)
    agent.verify_embedding_cache()
    print('PASS: real ZIP imported and every chat/embedding blob reverified by Linux adapter',flush=True)


if __name__=='__main__':main()
