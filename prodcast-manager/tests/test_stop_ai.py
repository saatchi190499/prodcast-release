import json
import pytest
from test_manager import engine, FakeRemote


@pytest.mark.parametrize('owner',[None,'ai-operation'])
@pytest.mark.parametrize('status',['running','failed'])
def test_stop_optional_ai_after_completed_core(tmp_path,owner,status):
    e=engine(tmp_path);e.release=None;e.c['install_ai']=False
    core={'operation':'core-operation','status':'complete'}
    ai={'operation':'ai-operation','status':status,'ai_address':e.c['hosts']['ai']['address'],'inflight':'install','steps':[{'action':'claim'}]}
    (tmp_path/'journal.json').write_text(json.dumps(core))
    (tmp_path/'ai-journal.json').write_text(json.dumps(ai))
    class Remote(FakeRemote):
        def action(self,payload,action,resources):
            assert self.role=='ai'
            if action=='preflight':return {'operation':owner}
            assert action=='release-operation' and payload['operation']=='ai-operation'
            return {'released':True}
    e.factory=Remote
    assert e.stop_previous_operation()['status']=='stopped'
    assert json.loads((tmp_path/'journal.json').read_text())==core
    assert json.loads((tmp_path/'ai-journal.json').read_text())['status']=='stopped'
    assert json.loads((tmp_path/'history/ai-journal-ai-operation.json').read_text())==ai
    assert e.stop_previous_operation()['status']=='idle'


@pytest.mark.parametrize('failure',['connection','foreign-owner','wrong-address'])
def test_failed_stop_keeps_ai_journal_pending(tmp_path,failure):
    e=engine(tmp_path);e.release=None
    ai={'operation':'ai-operation','status':'failed','ai_address':'wrong' if failure=='wrong-address' else e.c['hosts']['ai']['address']}
    path=tmp_path/'ai-journal.json';path.write_text(json.dumps(ai))
    class Remote(FakeRemote):
        def probe(self):
            if failure=='connection':raise RuntimeError('offline')
            return super().probe()
        def action(self,*args):return {'operation':'foreign-owner'}
    e.factory=Remote
    with pytest.raises((RuntimeError,ValueError)):e.stop_previous_operation()
    assert json.loads(path.read_text())==ai
