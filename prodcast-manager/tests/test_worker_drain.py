import sys
from types import SimpleNamespace
import pytest
from test_remote_configuration import agent


def run_drain(agent,monkeypatch,count,responses):
    host=agent.C['hosts']['worker1']
    agent.C['hosts']={r:h for r,h in agent.C['hosts'].items() if not r.startswith('worker')}
    agent.C['hosts'].update({'worker'+str(n):dict(host) for n in range(1,count+1)})
    inspector=SimpleNamespace(**{name:lambda:responses for name in ('active','reserved','scheduled')})
    inspector.active_queues=lambda:{'celery@app':[{'name':'default'}]}
    monkeypatch.setitem(sys.modules,'mainapp.celery',SimpleNamespace(app=SimpleNamespace(control=SimpleNamespace(inspect=lambda **kw:inspector))))
    monkeypatch.setitem(sys.modules,'redis',SimpleNamespace(Redis=SimpleNamespace(from_url=lambda _:SimpleNamespace(scan_iter=lambda **kw:[]))))
    monkeypatch.setenv('CELERY_BROKER_URL','redis://synthetic')
    monkeypatch.setattr(agent,'app_python',lambda code,current=False:exec(code,{}))
    return agent.drain()


def test_one_worker_update_can_drain(agent,monkeypatch):
    assert run_drain(agent,monkeypatch,1,{'prodcast-worker-01@vm1':[],'celery@app':[]})=={'queues':'drained'}


def test_update_requires_response_from_each_configured_worker(agent,monkeypatch):
    # Three responses are not enough when a configured Worker is missing.
    with pytest.raises(AssertionError,match='configured Worker'):
        run_drain(agent,monkeypatch,3,{'prodcast-worker-01@vm1':[],'prodcast-worker-02@vm2':[],'celery@app':[]})


def test_unrelated_consumers_cannot_replace_configured_worker(agent,monkeypatch):
    with pytest.raises(AssertionError,match='configured Worker'):
        run_drain(agent,monkeypatch,2,{'prodcast-worker-01@vm1':[],'other@vm':[],'celery@app':[]})
