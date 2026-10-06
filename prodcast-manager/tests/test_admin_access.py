from types import SimpleNamespace
import tkinter as tk

from prodcast_manager.gui import AdminAccessDialog


def test_admin_access_during_worker_operation_is_read_only(tmp_path,monkeypatch):
    from prodcast_manager.gui import App
    from prodcast_manager.portable import save_config,open_credentials
    from prodcast_manager.config import example,atomic_json
    from unittest.mock import Mock
    directory=tmp_path/'site';c=save_config(directory,example())
    vault=open_credentials(directory);vault.data={'secrets':{'ADMIN_PASSWORD':'synthetic-admin-password'}};vault.save()
    atomic_json(directory/'worker-action-journal.json',{'status':'running'})
    files={p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()}
    app=App.__new__(App);app.root=Mock();app.directory=directory;app.busy=True
    app.vault=Mock(side_effect=AssertionError('Must not prepare/save profile'))
    app.config=Mock(side_effect=AssertionError('Must not use edited form'))
    app.credentials_error=Mock();dialog=Mock()
    monkeypatch.setattr('prodcast_manager.gui.AdminAccessDialog',dialog)
    app.show_admin()
    dialog.assert_called_once_with(app.root,c['public_url'],c['admin_username'],'synthetic-admin-password')
    app.credentials_error.assert_not_called()
    assert {p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()}==files


def test_admin_access_copy_and_russian_shortcuts():
    root = tk.Tk()
    root.withdraw()
    previous = None
    try:
        try:
            previous = root.clipboard_get()
        except tk.TclError:
            pass
        password = 'Synthetic-Password-123!'
        dialog = AdminAccessDialog(root, 'https://app.example.test', 'admin', password)
        dialog.withdraw()
        entry = dialog.entries['password']
        assert entry.cget('show') == '*'
        entry.delete(0, 'end')
        entry.insert(0, 'changed')
        assert entry.get() == password
        for name, value in [('password', password), ('username', 'admin'),
                            ('url', 'https://app.example.test')]:
            dialog.copy_buttons[name].invoke()
            assert root.clipboard_get() == value
        dialog.shortcut(SimpleNamespace(keycode=65, keysym='Cyrillic_ef'), entry)
        dialog.shortcut(SimpleNamespace(keycode=67, keysym='Cyrillic_es'), entry)
        assert root.clipboard_get() == password
        entry.selection_range(0, 9)
        dialog.copy(entry, selection=True)
        assert root.clipboard_get() == 'Synthetic'
        dialog.copy_buttons['password'].invoke()
        dialog.destroy()
        root.update()
        assert root.clipboard_get() == password
    finally:
        root.clipboard_clear()
        if previous is not None:
            root.clipboard_append(previous)
        root.update()
        root.destroy()
