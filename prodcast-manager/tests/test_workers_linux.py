import importlib.util
import json
import types
from pathlib import Path
import pytest
from prodcast_manager.engine import RESOURCES

spec=importlib.util.spec_from_file_location('workers_linux',RESOURCES/'workers_linux.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


@pytest.fixture
def agent(tmp_path,monkeypatch):
    monkeypatch.setattr(module.os,'chown',lambda *args:None,raising=False)
    a=types.SimpleNamespace(ROOT=tmp_path/'root',STATE=tmp_path/'state')
    a.STATE.mkdir();folder=a.ROOT/'db/config';folder.mkdir(parents=True)
    (folder/'pg_hba.conf').write_text('local all postgres peer\nhost all all 0.0.0.0/0 reject\n')
    (folder/'users.acl').write_text('user default off\nuser prodcast_worker_01_scheduler on #'+('a'*64)+' ~worker01.* &* -@all +ping\n')
    (a.STATE/'firewall.sh').write_text('#!/bin/sh\niptables -A PCMAN-DB -j DROP\n')
    a.P={'role':'db','mode':'add-workers','action':'workers-prepare','operation':'a'*32,'version':'v0.5','manifest':'digest','stage':str(RESOURCES),
         'worker_expansion':{'id':'a'*32,'target':'bound','new_workers':['worker3'],'previous_workers':{'worker1':'10.0.0.1','worker2':'10.0.0.2'}}}
    a.ST={'version':'v0.5','manifest':'digest'}
    a.C={'hosts':{f'worker{n}':{'address':f'10.0.0.{n}'} for n in range(1,4)}}
    a.S={'PW_W03':'b'*64,'REDIS_W03':'c'*64,'REDIS_ADMIN':'private'}
    a.calls=[];a.accounts=set();a.acl_result='OK';a.saved=[]
    def psql(sql,db='postgres'):
        a.calls.append(('psql',sql))
        if sql.startswith('SELECT 1 FROM pg_roles'):return '1' if 'prodcast_worker_03' in a.accounts else ''
        if sql.startswith('CREATE ROLE'):a.accounts.add(sql.split()[2])
        if 'pg_hba_file_rules' in sql:return '0'
        if 'pg_reload_conf' in sql:return 't'
        return ''
    def write(path,text,mode=0o600):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    def dc(*args,**kwargs):a.calls.append(('dc',args));return a.acl_result
    a.psql=psql;a.write=write;a.dc=dc
    a.save=lambda:a.saved.append(dict(a.ST))
    a.require_database_data=lambda:None;a.database_ready=lambda:None
    a.selinux_enabled=lambda:False;a.firewalld_active=lambda:False
    a.worker_roles=lambda:list(a.C['hosts'])
    def run(args):
        a.calls.append(('run',args))
        if args[:2]==['iptables','-C']:raise RuntimeError('missing rule')
        return ''
    a.run=run
    return a


def test_db_hot_add_is_idempotent_and_never_recreates_containers(agent):
    a=agent;folder=a.ROOT/'db/config';before=(folder/'users.acl').read_text()
    assert module.dispatch(a)['prepared']
    assert a.ST['maintenance']==a.P['operation']
    assert module.dispatch(a)['prepared']
    assert (folder/'users.acl').read_text().startswith(before)
    assert (folder/'users.acl').read_text().count('user prodcast_worker_03_scheduler ')==1
    assert (folder/'pg_hba.conf').read_text().count('hostssl prodcast2 prodcast_worker_03 10.0.0.3/32')==1
    assert sum(sql.startswith('CREATE ROLE') for kind,sql in a.calls if kind=='psql')==1
    assert all(args[:4]==('db','exec','-T','redis') for kind,args in a.calls if kind=='dc')
    assert not any('-F' in args for kind,args in a.calls if kind=='run')
    a.P['action']='workers-commit';assert module.dispatch(a)['complete']
    assert a.ST['maintenance']=='' and a.ST['worker_hosts']['worker3']=='10.0.0.3'


def test_redis_reload_failure_keeps_transaction_for_retry(agent):
    a=agent;a.acl_result='ERR invalid ACL'
    with pytest.raises(RuntimeError,match='ACL reload'):module.dispatch(a)
    assert a.ST['maintenance']==a.P['operation']
    receipt=json.loads((a.STATE/'workers-transaction.json').read_text())
    assert not receipt.get('prepared') and not receipt['complete']
    a.acl_result='OK';assert module.dispatch(a)['prepared']


def test_existing_account_is_not_adopted(agent):
    agent.accounts.add('prodcast_worker_03')
    with pytest.raises(RuntimeError,match='already exists'):module.dispatch(agent)
    assert not (agent.STATE/'workers-transaction.json').exists()
    assert not any(sql.startswith('GRANT') for kind,sql in agent.calls if kind=='psql')


def test_db_rejects_other_transaction(agent):
    module.dispatch(agent);agent.P['operation']='b'*32;agent.P['worker_expansion']['id']='b'*32
    with pytest.raises(RuntimeError,match='owns'):module.dispatch(agent)
