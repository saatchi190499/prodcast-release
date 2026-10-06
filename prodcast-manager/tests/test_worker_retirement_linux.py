import importlib.util
import sys
import pytest
from test_workers_linux import agent, module as workers_module
from prodcast_manager.engine import RESOURCES

spec=importlib.util.spec_from_file_location('worker_lifecycle_linux',RESOURCES/'worker_lifecycle_linux.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def prepare(a,monkeypatch):
    monkeypatch.setitem(sys.modules,'workers_linux',workers_module)
    a.P.update(mode='worker-remove',action='worker-retire-access',worker_action={
        'role':'worker2','previous_workers':{'worker1':'10.0.0.1','worker2':'10.0.0.2','worker3':'10.0.0.3'},
        'target':{'hosts':{'worker1':{'address':'10.0.0.1'},'worker3':{'address':'10.0.0.3'}}}})
    a.ST['maintenance']=a.P['operation']
    folder=a.ROOT/'db/config'
    with (folder/'pg_hba.conf').open('a') as f:
        f.write('hostssl prodcast2 prodcast_worker_02 10.0.0.2/32 scram-sha-256\n')
        f.write('hostssl prodcast2 prodcast_worker_03 10.0.0.3/32 scram-sha-256\n')
    with (folder/'users.acl').open('a') as f:
        f.write('user prodcast_worker_02_scheduler on #'+('b'*64)+' ~worker02.* &* -@all +ping\n')


def test_revocation_only_affects_selected_worker_and_is_resumable(agent,monkeypatch):
    a=agent;prepare(a,monkeypatch)
    module.dispatch(a);module.dispatch(a)
    folder=a.ROOT/'db/config'
    assert 'prodcast_worker_02 ' not in (folder/'pg_hba.conf').read_text()
    assert 'prodcast_worker_03 ' in (folder/'pg_hba.conf').read_text()
    assert 'prodcast_worker_02_scheduler ' not in (folder/'users.acl').read_text()
    assert 'prodcast_worker_01_scheduler ' in (folder/'users.acl').read_text()
    statements=[sql for kind,sql in a.calls if kind=='psql']
    assert 'ALTER ROLE prodcast_worker_02 NOLOGIN;' in statements
    assert not any('DROP' in sql for sql in statements)
    a.P['action']='worker-retire-membership'
    assert module.dispatch(a)['removed']=='worker2'
    assert a.ST['worker_hosts']=={'worker1':'10.0.0.1','worker3':'10.0.0.3'}


def test_membership_cannot_commit_before_access_revocation(agent,monkeypatch):
    a=agent;prepare(a,monkeypatch);a.P['action']='worker-retire-membership'
    with pytest.raises(RuntimeError,match='Revoke'):
        module.dispatch(a)


def test_acl_reload_failure_does_not_commit_membership(agent,monkeypatch):
    a=agent;prepare(a,monkeypatch);a.acl_result='ERR'
    with pytest.raises(RuntimeError,match='ACL reload'):
        module.dispatch(a)
    assert 'worker_hosts' not in a.ST
