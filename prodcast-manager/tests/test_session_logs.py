import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from prodcast_manager.session_logs import SessionLog,application_directory
from prodcast_manager.ssh import Remote

def test_logs_follow_executable_not_extraction_dir(tmp_path,monkeypatch):
    monkeypatch.setattr(sys,'frozen',True,raising=False)
    monkeypatch.setattr(sys,'executable',str(tmp_path/'Manager.exe'))
    monkeypatch.setattr(sys,'_MEIPASS',str(tmp_path/'unpack'),raising=False)
    log=SessionLog();log.append('Ошибка AI')
    assert log.directory==tmp_path/'prodcast-data'/'logs'
    assert 'Ошибка AI' in log.path.read_text('utf-8')

def test_secrets_redacted_in_both_local_logs(tmp_path):
    log=SessionLog(tmp_path)
    log.protect({'secrets':{'PW_AI':'db-password-123'},'ssh':{'ai':{'password':'ssh-secret-123'}}})
    raw='Ошибка db-password-123 ssh-secret-123 postgresql://u:unknown@db/x https://host/x?sig=abc\nAPI_TOKEN=foo\nAuthorization: Bearer xyz\n-----BEGIN PRIVATE KEY-----\nprivate-material\n-----END PRIVATE KEY-----'
    clean=log.append(raw);path=log.remote('ai','install',raw)
    for secret in ('db-password-123','ssh-secret-123','unknown','sig=abc','foo','xyz','private-material'):
        assert secret not in clean and secret not in path.read_text('utf-8')
    assert 'Ошибка' in clean and 'postgresql://' in clean

def test_remote_error_downloads_redacted_diagnostics_and_preserves_failure(tmp_path):
    r=object.__new__(Remote);r.role='ai';r.diagnostics=SessionLog(tmp_path);messages=[];r.log=messages.append
    def fail(*a):raise RuntimeError('Ollama not ready')
    r._action=fail;r.collect_diagnostics=lambda:'secret-value Permission denied'
    with pytest.raises(RuntimeError,match='Ollama not ready'):
        r.action({'secrets':{'PW_AI':'secret-value'}},'install',None)
    path=next(tmp_path.glob('*-ai-install.log'))
    assert 'Permission denied' in path.read_text() and 'secret-value' not in path.read_text()
    assert str(path) in messages[0]
    def unavailable():raise OSError('SSH unavailable')
    r.collect_diagnostics=unavailable
    with pytest.raises(RuntimeError,match='Ollama not ready'):r.action({},'install',None)
    assert 'не удалось' in messages[-1]

def test_gui_copy_selection_all_and_cyrillic_shortcuts(tmp_path):
    import tkinter as tk
    from prodcast_manager.gui import App
    root=tk.Tk();root.withdraw();app=App(root,log_dir=tmp_path)
    try:
        app.session_log.protect({'secrets':{'test':'hidden-password'}})
        app.log('AI: ошибка hidden-password');app.poll();root.update()
        app.copy_log(all_text=True)
        assert 'AI: ошибка [REDACTED]' in root.clipboard_get()
        assert 'hidden-password' not in root.clipboard_get()
        app.output.tag_add('sel','1.0','1.6');app.copy_log()
        assert root.clipboard_get()==app.output.get('1.0','1.6')
        app.log_shortcut(SimpleNamespace(keycode=65,keysym='Cyrillic_ef'))
        app.log_shortcut(SimpleNamespace(keycode=67,keysym='Cyrillic_es'))
        assert 'AI: ошибка' in root.clipboard_get()
        assert app.output.cget('state')=='disabled'
    finally:root.destroy()

def test_gui_loads_saved_vm_and_site_addresses(tmp_path):
    import tkinter as tk
    import os
    from prodcast_manager.gui import App
    from prodcast_manager.config import atomic_json,example
    c=example();c['hosts']['app']['address']='192.168.31.23'
    c['public_url']='https://192.168.31.23';c['admin_ip']='192.168.31.225'
    from prodcast_manager.portable import profile_directory,remember
    home=tmp_path/'portable';directory=profile_directory(home,c)
    atomic_json(directory/'site.json',c);remember(home,directory)
    root=tk.Tk();root.withdraw();app=App(root,log_dir=tmp_path/'logs')
    try:
        assert app.hostvars['app']['address'].get()=='192.168.31.23'
        assert app.vars['public_url'].get()==c['public_url']
        assert app.vars['admin_ip'].get()==c['admin_ip']
    finally:root.destroy()
