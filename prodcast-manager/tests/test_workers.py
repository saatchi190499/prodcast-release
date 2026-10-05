import copy
import json
import pytest
from test_manager import engine, FakeRelease, FakeRemote
from prodcast_manager.config import topology_hash,validate_membership
from prodcast_manager.portable import save_config,runtime_config,open_credentials,profile_directory
from prodcast_manager.workers import add_workers,candidate,JOURNAL,require_no_expansion


class Release(FakeRelease):
    def validate_worker_count(self,n):assert 1<=n<=16


@pytest.fixture
def expansion(tmp_path):
    c=engine(tmp_path).c
    c=save_config(tmp_path,c)
    v=open_credentials(tmp_path);v.initialize(c)
    proposed=copy.deepcopy(c)
    proposed['hosts']['worker3']={**c['hosts']['worker2'],'address':'192.168.31.86'}
    class Remote(FakeRemote):
        states={r:dict(managed=True,version=Release.version,manifest=Release.digest,operation='') for r in c['hosts']}
        calls=[];failure=None
        def action(self,p,action,resources):
            self.calls.append((self.role,action))
            if self.failure==(self.role,action):raise RuntimeError('simulated disconnect')
            state=self.states.setdefault(self.role,{'managed':False})
            if action=='preflight':return dict(state)
            if action=='claim':state.update(managed=True,operation=p['operation'],worker_expansion=p['operation'])
            if action=='commit':state.update(operation='',version=p['version'],manifest=p['manifest'])
            if action=='workers-prepare':state['maintenance']=p['operation']
            if action=='workers-commit':state['maintenance']=''
            return {'healthy':True}
    return c,proposed,v,Release(),Remote


def test_append_preserves_identity_and_existing_secrets(tmp_path,expansion):
    c,target,v,release,remote=expansion;old=copy.deepcopy(v.data)
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert topology_hash(result)==topology_hash(c)
    assert profile_directory(tmp_path,result)==profile_directory(tmp_path,c)
    assert v.data['installation_id']==old['installation_id'] and v.data['tls']==old['tls']
    assert all(v.data['secrets'][k]==value for k,value in old['secrets'].items())
    assert all(k in v.data['secrets'] for k in ('PW_W03','REDIS_W03','SVC_W03'))
    validate_membership(result,v.data)
    assert all(action=='preflight' for role,action in remote.calls if role in ('app','worker1','worker2'))
    assert not any(role=='ai' for role,action in remote.calls)
    assert [action for role,action in remote.calls if role=='db']==['preflight','workers-prepare','workers-commit']
    assert json.loads((tmp_path/JOURNAL).read_text())['status']=='complete'


@pytest.mark.parametrize('failure',[('worker3','install'),('worker3','verify'),('worker3','commit'),('db','workers-commit')])
def test_resume_same_transaction_and_secrets(tmp_path,expansion,failure):
    c,target,v,release,remote=expansion;remote.failure=failure
    with pytest.raises(RuntimeError):add_workers(tmp_path,target,v,release,remote_factory=remote)
    journal=json.loads((tmp_path/JOURNAL).read_text());secrets=dict(v.data['secrets'])
    with pytest.raises(ValueError,match='Resume'):require_no_expansion(tmp_path)
    remote.failure=None
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert v.data['secrets']==secrets
    assert json.loads((tmp_path/JOURNAL).read_text())['operation']==journal['operation']
    validate_membership(result,v.data)


def test_refuses_nonempty_vm_before_any_server_mutation(tmp_path,expansion):
    c,target,v,release,remote=expansion
    remote.states['worker3']={'managed':True,'version':release.version,'manifest':release.digest}
    with pytest.raises(ValueError,match='already belongs'):add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert all(action=='preflight' for role,action in remote.calls)


def test_changed_roster_or_release_cannot_resume(tmp_path,expansion):
    c,target,v,release,remote=expansion;remote.failure=('worker3','install')
    with pytest.raises(RuntimeError):add_workers(tmp_path,target,v,release,remote_factory=remote)
    changed=copy.deepcopy(target);changed['hosts']['worker3']['address']='192.168.31.87'
    with pytest.raises(ValueError,match='same new Worker'):add_workers(tmp_path,changed,v,release,remote_factory=remote)
    release.digest='other'
    with pytest.raises(ValueError,match='original vault'):add_workers(tmp_path,target,v,release,remote_factory=remote)


def test_manual_roster_change_after_expansion_rejected(tmp_path,expansion):
    c,target,v,release,remote=expansion
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    result['hosts']['worker3']['address']='192.168.31.87'
    with pytest.raises(ValueError,match='membership'):validate_membership(result,v.data)
    with pytest.raises(ValueError,match='membership'):validate_membership(c,v.data)


def test_second_expansion_preserves_original_identity(tmp_path,expansion):
    c,target,v,release,remote=expansion
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    result['hosts']['worker4']={**result['hosts']['worker3'],'address':'192.168.31.88'}
    result=add_workers(tmp_path,result,v,release,remote_factory=remote)
    assert topology_hash(result)==topology_hash(c)
    validate_membership(result,v.data)


@pytest.mark.parametrize('change',[lambda c:c['hosts']['worker1'].update(address='192.168.31.90'),lambda c:c.update(company_name='other'),lambda c:c['hosts'].pop('worker2')])
def test_candidate_rejects_unrelated_changes(expansion,change):
    c,target,v,release,remote=expansion;change(target)
    with pytest.raises(ValueError):candidate(c,target)


def test_preflight_failure_allows_correcting_new_address(tmp_path,expansion):
    c,target,v,release,remote=expansion;remote.failure=('worker3','preflight')
    with pytest.raises(RuntimeError):add_workers(tmp_path,target,v,release,remote_factory=remote)
    target['hosts']['worker3']['address']='192.168.31.87';remote.failure=None
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert result['hosts']['worker3']['address']=='192.168.31.87'


def test_interrupted_local_commit_recovers_both_files(tmp_path,expansion,monkeypatch):
    import prodcast_manager.workers as workers
    c,target,v,release,remote=expansion
    def fail(*args):raise OSError('simulated profile write failure')
    monkeypatch.setattr(workers,'save_config',fail)
    with pytest.raises(OSError):add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert json.loads((tmp_path/JOURNAL).read_text())['phase']=='committing'
    assert 'worker3' not in runtime_config(tmp_path/'site.json')['hosts']
    monkeypatch.setattr(workers,'save_config',save_config)
    result=add_workers(tmp_path,target,v,release,remote_factory=remote)
    validate_membership(result,open_credentials(tmp_path).data)


def test_installed_core_manifest_mismatch_is_read_only(tmp_path,expansion):
    c,target,v,release,remote=expansion;remote.states['app']['manifest']='different'
    with pytest.raises(ValueError,match='exact installed release'):add_workers(tmp_path,target,v,release,remote_factory=remote)
    assert all(action=='preflight' for role,action in remote.calls)


def test_gui_expansion_bypasses_save_and_handles_result(tmp_path,expansion,monkeypatch):
    import tkinter as tk
    import prodcast_manager.gui as gui
    import prodcast_manager.workers as workers
    c,target,v,release,remote=expansion
    root=tk.Tk();root.withdraw()
    try:
        app=gui.App(root,log_dir=tmp_path/'logs',app_home=tmp_path/'manager')
        app.directory=tmp_path;app.populate(target);app.release.set('test-release')
        before=(tmp_path/'site.json').read_bytes();calls=[]
        monkeypatch.setattr(gui.messagebox,'askyesno',lambda *a:True)
        monkeypatch.setattr(gui.messagebox,'showerror',lambda *a:pytest.fail(str(a)))
        monkeypatch.setattr(gui,'Release',lambda *a,**kw:release)
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        monkeypatch.setattr(gui.threading,'Thread',Immediate)
        def run(directory,proposed,vault,selected,*args,**kwargs):
            assert (directory/'site.json').read_bytes()==before
            calls.append(proposed)
            return proposed
        monkeypatch.setattr(workers,'add_workers',run)
        app.add_workers();app.poll()
        assert len(calls)==1 and 'worker3' in calls[0]['hosts']
        assert not app.busy and app.worker_count.get()=='3'
    finally:root.destroy()
