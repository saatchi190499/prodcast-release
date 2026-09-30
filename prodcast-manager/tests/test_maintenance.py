import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
from types import SimpleNamespace
import zipfile
import pytest
from prodcast_manager import backup_archive as archive
from prodcast_manager.directory import app_directory
from prodcast_manager.engine import Engine,RESOURCES
from prodcast_manager.config import example,topology_hash
from prodcast_manager.maintenance import Maintenance


@pytest.fixture
def backup(tmp_path):
    data=tmp_path/'source';data.mkdir()
    for name in archive.FILES-{'manifest.json'}:
        p=data/name;p.parent.mkdir(exist_ok=True);p.write_bytes((name*200).encode())
    record={'schema':1,'database_major':18,'version':'v0.5.0-rc.2','manifest':'a'*64,'site':{},'vault':{'installation_id':'test','secrets':{'FERNET_KEY':'private-test-value'}}}
    (data/'recovery.json').write_text(json.dumps(record))
    z=tmp_path/'backup.zip';archive.pack(data,z)
    encrypted=tmp_path/'backup.pcbackup';archive.encrypt(z,encrypted,'password-for-test')
    return data,z,encrypted,record


def test_backup_roundtrip_excludes_heavy_files_and_hides_secrets(backup,tmp_path):
    data,z,encrypted,record=backup
    assert b'private-test-value' not in encrypted.read_bytes()
    plain=tmp_path/'decrypted.zip';archive.decrypt(encrypted,plain,'password-for-test')
    result=archive.unpack(plain,tmp_path/'restored');assert result==record
    for name in archive.FILES-{'manifest.json'}:assert (data/name).read_bytes()==(tmp_path/'restored'/name).read_bytes()
    assert not any('ollama' in name or 'docker' in name for name in zipfile.ZipFile(plain).namelist())


@pytest.mark.parametrize('damage',['password','bit','truncate','append','header'])
def test_backup_rejects_tampering_and_removes_partial_plaintext(backup,tmp_path,damage):
    _,_,encrypted,_=backup;data=bytearray(encrypted.read_bytes());password='password-for-test'
    if damage=='password':password='another-password'
    if damage=='bit':data[len(data)//2]^=1
    if damage=='truncate':data=data[:-1]
    if damage=='append':data+=b'x'
    if damage=='header':data[0]^=1
    encrypted.write_bytes(data);dest=tmp_path/'plain'
    with pytest.raises(ValueError):archive.decrypt(encrypted,dest,password)
    assert not dest.exists()


def test_decrypt_does_not_delete_existing_destination(backup,tmp_path):
    dest=tmp_path/'keep';dest.write_text('keep')
    with pytest.raises(ValueError):archive.decrypt(backup[2],dest,'password-for-test')
    assert dest.read_text()=='keep'


def test_multiframe_backup_and_atomic_output(tmp_path):
    source=tmp_path/'source';source.write_bytes(os.urandom(archive.CHUNK*2+11));dest=tmp_path/'encrypted'
    archive.encrypt(source,dest,'password-for-test');plain=tmp_path/'plain';archive.decrypt(dest,plain,'password-for-test')
    assert archive.sha(source)==archive.sha(plain)
    with pytest.raises(ValueError):archive.encrypt(source,dest,'password-for-test')


@pytest.mark.parametrize('entry',['../escape','model.gguf','db/prodcast2.dump'])
def test_backup_rejects_extra_and_duplicate_entries(backup,tmp_path,entry):
    with zipfile.ZipFile(backup[1],'a') as z:z.writestr(entry,b'bad')
    with pytest.raises(ValueError):archive.unpack(backup[1],tmp_path/'bad')


def test_ldap_mapping_enables_group_tls_and_omits_bind_password():
    value={'enabled':True,'url':'ldaps://dc.example.com','domain':'example.com','base_dn':'DC=example,DC=com',
           'group_dn':'CN=ProdCast,DC=example,DC=com','bind_dn':'svc@example.com','bind_password':'private-bind-password','ca_pem':''}
    mapped=app_directory(value)
    assert mapped['mode']=='ldaps' and mapped['include_nested_groups'] and mapped['group_filter_enabled']
    assert mapped['user_dn_template']=='%(user)s@example.com'
    assert 'private-bind-password' not in json.dumps(mapped)
    assert app_directory(None) is None and app_directory({'enabled':False})=={'mode':'disabled'}


spec=importlib.util.spec_from_file_location('maintenance_linux_test',RESOURCES/'maintenance_linux.py')
linux=importlib.util.module_from_spec(spec);spec.loader.exec_module(linux)


@pytest.mark.parametrize('kind',['symlink','hardlink','parent','absolute'])
def test_restore_rejects_unsafe_media_before_modifying_data(tmp_path,kind):
    path=tmp_path/'media.tar.gz'
    with tarfile.open(path,'w:gz') as tar:
        i=tarfile.TarInfo({'parent':'../escape','absolute':'/escape'}.get(kind,'file'))
        if kind in ('symlink','hardlink'):i.type=tarfile.SYMTYPE if kind=='symlink' else tarfile.LNKTYPE;i.linkname='/etc/shadow'
        tar.addfile(i)
    with pytest.raises(RuntimeError):linux.validate_media(path)


def test_reset_keep_never_removes_storage(monkeypatch,tmp_path):
    monkeypatch.setattr(linux.shutil,'which',lambda n:'/bin/docker')
    called=[]
    def run(args):
        called.append(args)
        return 'a'*12 if args[:3]==['docker','ps','-aq'] else ''
    m=SimpleNamespace(P={'role':'db','mode':'reset-keep','operation':'test'},ST={'version':'v1','operation':'stale','steps':{'old':1}},STATE=tmp_path,run=run,save=lambda:None)
    r=linux.reset(m)
    assert r['data_preserved'] and m.ST['steps']=={} and m.ST['operation']==''
    assert called[-2]==['docker','stop','--time','90','a'*12] and called[-1]==['docker','rm','a'*12]
    assert not any('volume' in c or 'prune' in c for c in called)


def test_media_normal_files_accepted(tmp_path):
    path=tmp_path/'media.tar.gz'
    with tarfile.open(path,'w:gz') as tar:
        i=tarfile.TarInfo('./uploads/test.txt');i.size=4;tar.addfile(i,io.BytesIO(b'test'))
    linux.validate_media(path)


class FakeRemote:
    instances=[];fail=None
    def __init__(self,role,*args):self.role=role;self.actions=[];self.stage='/stage';self.instances.append(self)
    def probe(self):return {}
    def prepare_stage(self):pass
    def put_bytes(self,*a):pass
    def put(self,*a):pass
    def cleanup(self):pass
    def close(self):pass
    def action(self,payload,action,*a):
        self.actions.append(action)
        if self.fail==(self.role,action):raise RuntimeError('simulated failure')
        if action=='preflight':return {'managed':True,'version':'v0.5.0-rc.2','manifest':'a'*64}
        return {}


def fake_engine(tmp_path):
    c=example();c['install_ai']=False
    for n,(role,h) in enumerate(c['hosts'].items(),11):h.update(address='192.168.99.'+str(n),auth='password',fingerprint='SHA256:'+'A'*43)
    c.update(public_url='https://prodcast.example.test',admin_ip='192.168.99.1')
    vault=SimpleNamespace(data={'topology':topology_hash(c),'installation_id':'test'},save=lambda:None)
    return Engine(c,vault,None,tmp_path,lambda s:None,remote_factory=FakeRemote)


def test_reset_preflights_every_host_before_removal_and_preserves_profile(tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=None;e=fake_engine(tmp_path)
    before=copy.deepcopy(e.vault.data);Maintenance(e).run('reset-full')
    assert e.vault.data==before
    assert all(r.actions[:2]==['preflight','maintenance-claim'] for r in FakeRemote.instances)
    assert all('reset' in r.actions for r in FakeRemote.instances)
    assert json.loads((tmp_path/'maintenance-journal.json').read_text())['status']=='complete'


def test_reset_failure_preserves_journal_and_resumes_same_operation(tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=('db','reset');e=fake_engine(tmp_path)
    with pytest.raises(RuntimeError):Maintenance(e).run('reset-full')
    journal=json.loads((tmp_path/'maintenance-journal.json').read_text());assert journal['status']=='failed'
    with pytest.raises(ValueError,match='previous maintenance'):Maintenance(e).run('reset-keep')
    FakeRemote.fail=None;Maintenance(e).run('reset-full')
    done=json.loads((tmp_path/'maintenance-journal.json').read_text())
    assert done['operation']==journal['operation'] and done['status']=='complete'


def test_failed_preflight_never_resets_any_host(tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=('db','preflight')
    with pytest.raises(RuntimeError):Maintenance(fake_engine(tmp_path)).run('reset-full')
    assert not any('reset' in r.actions for r in FakeRemote.instances)
    FakeRemote.fail=None


def test_release_failure_does_not_repeat_completed_reset(tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=('app','maintenance-release');e=fake_engine(tmp_path)
    with pytest.raises(RuntimeError):Maintenance(e).run('reset-full')
    journal=json.loads((tmp_path/'maintenance-journal.json').read_text())
    assert journal['work_complete'] and journal['status']=='failed'
    FakeRemote.instances=[];FakeRemote.fail=None;Maintenance(e).run('reset-full')
    assert not any('reset' in r.actions for r in FakeRemote.instances)


def test_partial_restore_stays_stopped_and_can_resume(backup,tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=('app','data-restore');e=fake_engine(tmp_path/'site')
    e.vault.data['secrets']=backup[3]['vault']['secrets']
    with pytest.raises(RuntimeError):Maintenance(e).run('restore',backup[2],'password-for-test')
    assert not any('maintenance-resume' in r.actions for r in FakeRemote.instances)
    journal=json.loads((e.dir/'maintenance-journal.json').read_text())
    assert journal['quiesced'] and journal['steps']==['safety-db','safety-app']
    FakeRemote.instances=[];FakeRemote.fail=None;Maintenance(e).run('restore',backup[2],'password-for-test')
    app=next(r for r in FakeRemote.instances if r.role=='app')
    assert 'drain' not in app.actions and 'data-export' not in app.actions
    assert app.actions.index('maintenance-stop')<app.actions.index('data-restore')<app.actions.index('maintenance-resume')


def test_restore_wrong_identity_never_stops_services(backup,tmp_path):
    FakeRemote.instances=[];FakeRemote.fail=None;e=fake_engine(tmp_path/'site');e.vault.data['installation_id']='different'
    with pytest.raises(ValueError,match='another installation'):Maintenance(e).run('restore',backup[2],'password-for-test')
    assert not any('pause' in r.actions or 'data-restore' in r.actions for r in FakeRemote.instances)
