import json
from pathlib import Path
import pytest
from test_manager import engine, FakeRemote
from test_optional_ai import report


def configure(e):
    e.release.offline_spec={'external_ollama':{'name':'components.zip'},'external_model':{'name':'models.gguf'}}
    e.release.model_path=None;e.release.ollama_path=None


def test_no_packages_skips_ai_without_contact_or_journal(tmp_path):
    e=engine(tmp_path);configure(e);e.run('update')
    assert report(tmp_path)['ai']['status']=='skipped'
    assert not (tmp_path/'ai-journal.json').exists()
    assert not any(r=='ai' for r,_,_ in FakeRemote.history)


@pytest.mark.parametrize('started',[False,True])
def test_skip_archives_unstarted_failure_but_keeps_real_recovery(tmp_path,started):
    e=engine(tmp_path);configure(e)
    prior={'status':'failed','operation':'old-operation','steps':[{'action':'claim'}] if started else []}
    p=tmp_path/'ai-journal.json';p.write_text(json.dumps(prior))
    e.run('update')
    assert report(tmp_path)['ai']['status']=='skipped'
    assert json.loads(p.read_text())==(prior if started else dict(prior,status='skipped',skip_reason='packages_not_selected',skipped_at=json.loads(p.read_text())['skipped_at']))
    if not started:assert json.loads((tmp_path/'history/ai-journal-skipped-old-operation.json').read_text())==prior


@pytest.mark.parametrize('field',['model_path','ollama_path'])
def test_partial_selection_is_not_silently_skipped(tmp_path,field):
    e=engine(tmp_path);configure(e);setattr(e.release,field,Path('selected.zip'))
    e.run('update')
    assert report(tmp_path)['ai']['status']!='skipped'


def test_explicit_retry_does_not_silently_skip(tmp_path):
    e=engine(tmp_path);configure(e)
    assert e._optional_ai('update','explicit-retry')['status']!='skipped'
