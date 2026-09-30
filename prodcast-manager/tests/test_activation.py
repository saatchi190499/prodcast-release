import base64,json,uuid
from datetime import datetime,timedelta,timezone
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from prodcast_manager.activation import validate_activation
from prodcast_manager.session_logs import SessionLog
from test_remote_configuration import agent
from test_manager import engine,FakeRemote

def signed(identity):
    key=Ed25519PrivateKey.generate();now=datetime.now(timezone.utc)
    doc={'format_version':1,'key_id':'test-key','payload':{'installation_id':identity,'tenant_id':'customer','environment':'PROD','product':'ProdCast','valid_from':(now-timedelta(minutes=1)).isoformat(),'expires_at':(now+timedelta(days=1)).isoformat()}}
    doc['signature']=base64.b64encode(key.sign(json.dumps(doc,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii'))).decode()
    return {'mode':'offline','tenant_id':'customer','document':json.dumps(doc),'public_key':key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()}

def test_offline_signature_and_binding():
    identity=str(uuid.uuid4());v=signed(identity)
    assert validate_activation(v,identity)['key_id']=='test-key'
    with pytest.raises(ValueError,match='другой'):validate_activation(v,str(uuid.uuid4()))
    doc=json.loads(v['document']);doc['payload']['tenant_id']='tampered';v['document']=json.dumps(doc)
    with pytest.raises(Exception):validate_activation(v,identity)

@pytest.mark.parametrize('url',['http://server','https://a:b@server','https://server/?token=123','https://server/other'])
def test_online_rejects_unsafe_url(url):
    with pytest.raises(ValueError):validate_activation({'mode':'online','tenant_id':'customer','url':url,'token':'x'*40},str(uuid.uuid4()))

def test_online_normalizes_endpoint_and_drops_offline_inputs():
    v=validate_activation({'mode':'online','tenant_id':'customer','url':'https://192.168.31.150','token':'x'*40,'document':'old'},str(uuid.uuid4()))
    assert v['url']=='https://192.168.31.150/v1/decision' and 'document' not in v

def test_online_token_redacted(tmp_path):
    log=SessionLog(tmp_path);log.protect({'activation':{'token':'unique-client-bearer-token-value'}})
    assert 'unique-client' not in log.redact('error unique-client-bearer-token-value')

def test_external_activation_required_before_connecting(tmp_path):
    e=engine(tmp_path);e.release.external_activation=True;e.vault.data['installation_id']=uuid.uuid4().hex
    with pytest.raises(ValueError,match='активацию'):e.run('update')
    assert FakeRemote.history==[]

def test_external_configuration_does_not_create_authority(agent):
    m=agent;identity=uuid.uuid4().hex
    m.P.update(installation_id=identity,activation={'mode':'online','tenant_id':'customer','url':'https://192.168.31.150/v1/decision','token':'x'*40})
    b=m.ROOT/'app/runtime';(b/'certs').mkdir(parents=True)
    override={};m.configure_activation(b,'LICENSE_SERVICE_URL=https://old\nLICENSE_ENFORCEMENT_ENABLED=true\n',override)
    env=(b/'runtime.env').read_text()
    assert 'https://old' not in env and 'LICENSE_SERVICE_FAIL_OPEN=false' in env
    assert (m.STATE/'app-activation/installation-id').read_text().strip()==str(uuid.UUID(identity))
    assert set(override['services'])==set(m.APIS+['migrate','celery-worker','celery-beat'])
    assert not (m.ROOT/'license').exists()
    m.P['installation_id']=uuid.uuid4().hex
    with pytest.raises(RuntimeError,match='identity differs'):m.configure_activation(b,env,override)

def test_fresh_external_database_does_not_create_license_db(agent,monkeypatch):
    m=agent;m.P['external_activation']=True;sql=[]
    monkeypatch.setattr(m,'run',lambda args,**kw:'999\n' if 'id' in args else '')
    monkeypatch.setattr(m,'firewall',lambda role:None)
    monkeypatch.setattr(m,'psql',lambda text,db='postgres':sql.append(text) or '')
    monkeypatch.setattr(m,'dc',lambda *a,**kw:'PONG')
    m.install_db()
    assert not any('license' in q for q in sql)
    assert 'license' not in (m.ROOT/'db/config/pg_hba.conf').read_text()
