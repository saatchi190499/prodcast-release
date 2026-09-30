from types import SimpleNamespace
import tkinter as tk

from prodcast_manager.gui import AdminAccessDialog


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
