import hashlib
import json
import sys
import tarfile
import types
import zipfile
from pathlib import Path
import pytest
from prodcast_manager import ai_models
from prodcast_manager.engine import RESOURCES
from prodcast_manager.release import Release, sha
from test_remote_configuration import agent


def bundle_fixture(tmp_path,monkeypatch):
    chat=b'GGUF verified chat';blob=b'embedding';value=hashlib.sha256(blob).hexdigest()
    manifest=json.dumps({'config':{'digest':'sha256:'+value,'size':len(blob)},'layers':[]}).encode()
    monkeypatch.setattr(ai_models,'EMBEDDING_DIGEST',hashlib.sha256(manifest).hexdigest())
    files={'Qwen3-4B-Instruct-Q4_K_M.gguf':chat,
           'models/'+ai_models.EMBEDDING_MANIFEST:manifest,
           'models/blobs/sha256-'+value:blob}
    external={'sha256':hashlib.sha256(chat).hexdigest(),'bytes':len(chat)}
    return files,external


def zip_files(path,files):
    with zipfile.ZipFile(path,'w') as archive:
        for name,body in files.items():archive.writestr(name,body)
    return path


def test_models_zip_imports_release_verified_chat_and_pinned_embedding(tmp_path,monkeypatch):
    files,external=bundle_fixture(tmp_path,monkeypatch)
    result=ai_models.prepare_bundle(zip_files(tmp_path/'models.zip',files),tmp_path/'cache',external,'sha256:'+'a'*64)
    with tarfile.open(result) as tar:
        names=tar.getnames()
        assert ai_models.EMBEDDING_MANIFEST in names
        assert 'blobs/sha256-'+external['sha256'] in names
        assert all(not n.endswith('.gguf') for n in names)


def simple_fixture(monkeypatch):
    chat=b'GGUF verified chat';embedding=b'GGUF verified embedding';config=b'known embedding configuration'
    blob_digest=hashlib.sha256(embedding).hexdigest();config_digest=hashlib.sha256(config).hexdigest()
    manifest=json.dumps({'config':{'digest':'sha256:'+config_digest,'size':len(config)},
                         'layers':[{'digest':'sha256:'+blob_digest,'size':len(embedding)}]}).encode()
    monkeypatch.setattr(ai_models,'EMBEDDING_DIGEST',hashlib.sha256(manifest).hexdigest())
    monkeypatch.setattr(ai_models,'EMBEDDING_MANIFEST_BYTES',manifest)
    monkeypatch.setattr(ai_models,'EMBEDDING_CONFIG_BYTES',config)
    return {'Qwen3-4B-Instruct-Q4_K_M.gguf':chat,'Qwen3-Embedding-0.6B-Q8_0.gguf':embedding}, {'sha256':hashlib.sha256(chat).hexdigest(),'bytes':len(chat)},blob_digest,config_digest


@pytest.mark.parametrize('rename',[False,True])
def test_two_plain_ggufs_get_internal_metadata_without_downloads(tmp_path,monkeypatch,rename):
    files,external,embedding,config=simple_fixture(monkeypatch)
    if rename:files={'a.gguf':files['Qwen3-Embedding-0.6B-Q8_0.gguf'],'b.gguf':files['Qwen3-4B-Instruct-Q4_K_M.gguf']}
    source=zip_files(tmp_path/'models.zip',files)
    with zipfile.ZipFile(source) as zip:assert len(zip.namelist())==2
    result=ai_models.prepare_bundle(source,tmp_path/'cache',external,'sha256:'+'a'*64)
    with tarfile.open(result) as archive:
        assert set(archive.getnames())=={ai_models.EMBEDDING_MANIFEST,'blobs/sha256-'+embedding,'blobs/sha256-'+config,'blobs/sha256-'+external['sha256']}
        assert archive.extractfile(ai_models.EMBEDDING_MANIFEST).read()==ai_models.EMBEDDING_MANIFEST_BYTES


@pytest.mark.parametrize('bad',['missing','chat','embedding','extra','metadata'])
def test_plain_gguf_zip_refuses_wrong_or_missing_models(tmp_path,monkeypatch,bad):
    files,external,_,_=simple_fixture(monkeypatch)
    if bad=='missing':files.pop('Qwen3-Embedding-0.6B-Q8_0.gguf')
    if bad=='chat':files['Qwen3-4B-Instruct-Q4_K_M.gguf']=b'incorrect chat'
    if bad=='embedding':files['Qwen3-Embedding-0.6B-Q8_0.gguf']=b'incorrect embedding'
    if bad=='extra':files['third.gguf']=b'extra'
    if bad=='metadata':monkeypatch.setattr(ai_models,'EMBEDDING_CONFIG_BYTES',b'corrupt configuration')
    with pytest.raises(ValueError):ai_models.prepare_bundle(zip_files(tmp_path/'models.zip',files),tmp_path/'cache',external,'sha256:'+'a'*64)


def test_bundled_official_embedding_configuration_matches_manifest():
    manifest=json.loads(ai_models.EMBEDDING_MANIFEST_BYTES)
    assert hashlib.sha256(ai_models.EMBEDDING_MANIFEST_BYTES).hexdigest()==ai_models.EMBEDDING_DIGEST
    assert hashlib.sha256(ai_models.EMBEDDING_CONFIG_BYTES).hexdigest()==manifest['config']['digest'][7:]


@pytest.mark.parametrize('bad',['missing','tampered','private-key','traversal','duplicate'])
def test_bad_models_zip_refused(tmp_path,monkeypatch,bad):
    files,external=bundle_fixture(tmp_path,monkeypatch)
    if bad=='missing':files={k:v for k,v in files.items() if 'manifests' not in k}
    if bad=='tampered':files['Qwen3-4B-Instruct-Q4_K_M.gguf']=b'wrong'
    if bad=='private-key':files['id_ed25519']=b'private account key'
    if bad=='traversal':files['../outside']=b'bad'
    source=zip_files(tmp_path/'models.zip',files)
    if bad=='duplicate':
        with zipfile.ZipFile(source,'a') as archive:archive.writestr('models/'+ai_models.EMBEDDING_MANIFEST,b'duplicate')
    with pytest.raises(ValueError):ai_models.prepare_bundle(source,tmp_path/'cache',external,'sha256:'+'a'*64)
    assert not (tmp_path/'outside').exists()


def test_complete_schema_is_transactional_and_owned_by_ai_role(agent,monkeypatch):
    agent.P.update(role='db',operation='test',stage=str(RESOURCES));agent.ST.update(version='v0.6.3',operation='')
    calls=[];monkeypatch.setattr(agent,'psql',lambda sql,db:calls.append((sql,db)))
    assert agent.configure_ai_documents()['documents_schema']
    sql,db=calls[0];assert db=='prodcast_ai'
    assert sql.startswith('BEGIN;') and sql.endswith(' COMMIT;')
    assert 'SET LOCAL ROLE prodcast_ai' in sql and 'NOSUPERUSER' not in sql
    for name in ('allowed_principals','managed_file','display_name','byte_size','status','job_version','modules','page','section','vector(1024)','document_text_idx'):
        assert name in sql
    assert 'Unexpected AI document table owner' in sql
    assert 'DROP TABLE' not in sql and 'DELETE FROM' not in sql


def test_schema_migration_refuses_a_different_operation(agent):
    agent.P.update(role='db',operation='new');agent.ST.update(version='v0.6.3',operation='other')
    with pytest.raises(RuntimeError,match='idle DB'):agent.configure_ai_documents()


def test_documents_environment_and_cache_revision(agent):
    agent.S['AI_HASH']='hash';env=agent.ai_environment('qwen3:4b-instruct')
    assert env['RAG_ENABLED']=='true' and env['EMBEDDING_MODEL']=='qwen3-embedding:0.6b'
    assert env['EMBEDDING_DIMENSION']=='1024' and env['DOCUMENT_STORAGE_ROOT']=='/app/data/documents'
    agent.P.update(role='ai',action='install',operation='existing')
    agent.ST['step_tls']={'existing:install':'old-manager-revision'}
    assert not agent.cached_runtime_present()


def test_embedding_manifest_is_pinned_and_all_blobs_verified(agent,tmp_path,monkeypatch):
    files,external=bundle_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(agent,'EMBEDDING_DIGEST',ai_models.EMBEDDING_DIGEST)
    for name,body in files.items():
        if not name.startswith('models/'):continue
        target=agent.OLLAMA_HOME/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    agent.verify_embedding_cache()
    blob=next((agent.OLLAMA_HOME/'models/blobs').iterdir());blob.write_bytes(b'corrupted')
    with pytest.raises(RuntimeError,match='checksum'):agent.verify_embedding_cache()


def test_verify_from_app_checks_documents_with_tls_and_api_key(agent,monkeypatch):
    scripts=[];monkeypatch.setattr(agent,'app_python',lambda code,**kw:scripts.append(code))
    assert agent.verify_ai()['ai_documents']
    assert '/v1/documents' in scripts[0] and 'PRODCAST_AI_CA_BUNDLE' in scripts[0] and 'X-API-Key' in scripts[0]


def test_install_ai_mounts_persistent_storage_and_checks_embedding_and_documents(agent,monkeypatch,tmp_path):
    runtime=tmp_path/'runtime';(runtime/'bin').mkdir(parents=True);(runtime/'bin/ollama').write_bytes(b'test binary')
    original_path=agent.Path;original_write=agent.write
    monkeypatch.setattr(agent,'Path',lambda p:runtime if str(p)=='/opt/prodcast-ollama/0.34.0' else original_path(p))
    monkeypatch.setattr(agent,'write',lambda p,text,mode=0o600:original_write(tmp_path/'unit' if str(p).startswith('/etc/') else p,text,mode))
    monkeypatch.setitem(sys.modules,'pwd',types.SimpleNamespace(getpwnam=lambda _:types.SimpleNamespace(pw_uid=1000,pw_gid=1000)))
    monkeypatch.setitem(sys.modules,'grp',types.SimpleNamespace(getgrnam=lambda _:None))
    monkeypatch.setattr(agent,'prepare_ollama_runtime',lambda _:None)
    monkeypatch.setattr(agent,'load_packages',lambda:None)
    monkeypatch.setattr(agent,'run',lambda *a,**kw:'')
    monkeypatch.setattr(agent,'selinux_enabled',lambda:False)
    monkeypatch.setattr(agent,'firewall',lambda _:None)
    monkeypatch.setattr(agent,'wait_http',lambda *a,**kw:{'status':'ready'})
    monkeypatch.setattr(agent,'verify_embedding_cache',lambda:None)
    calls=[];commands=[]
    monkeypatch.setattr(agent,'dc',lambda *a,**kw:commands.append(a) or '')
    def request(url,data=None,**kw):
        calls.append((url,data,kw))
        if url.endswith('/api/tags'):return {'models':[{'name':'qwen3:4b-instruct','digest':'a'*64},{'name':agent.EMBEDDING_MODEL}]}
        if url.endswith('/api/embed'):return {'embeddings':[[0.1]*1024]}
        if url.endswith('/api/generate'):return {'response':'OK'}
        if url.endswith('/api/ps'):return {'models':[]}
        if url.endswith('/v1/documents'):return {'documents':[]}
        raise AssertionError(url)
    monkeypatch.setattr(agent,'request',request)
    agent.S['AI_HASH']='hash';agent.P['images']={'prodcast-ai':{'transport_tag':'offline-ai'}}
    agent.P['tls'].update({'ai.crt':'CERT','ai.key':'KEY'})
    (agent.ROOT/'releases'/agent.P['version']).mkdir(parents=True)
    assert agent.install_ai()['documents']
    service=json.loads((agent.target()/'ai/compose.json').read_text())['services']['api']
    assert str(agent.ROOT/'ai-data/documents')+':/app/data/documents' in service['volumes']
    assert service['user']=='1000:1000'
    assert any(url.endswith('/api/embed') and data['keep_alive']==0 for url,data,kw in calls)
    assert any(url.endswith('/v1/documents') and kw['headers']['X-API-Key']==agent.S['AI_KEY'] for url,data,kw in calls)
    assert any('TemporaryDirectory' in ' '.join(map(str,args)) for args in commands)
