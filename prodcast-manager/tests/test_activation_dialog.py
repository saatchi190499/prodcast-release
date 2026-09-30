import json
import tkinter as tk
import uuid
from pathlib import Path
import pytest
from cryptography.exceptions import InvalidSignature
from prodcast_manager.activation_dialog import ActivationDialog
from test_activation import signed


def test_offline_import_uses_issued_tenant_and_preserves_signed_bytes():
    root=tk.Tk();root.withdraw();identity=str(uuid.uuid4());issued=signed(identity)
    try:
        dialog=ActivationDialog(root,identity,issued,'unrelated-site-company',lambda value:None)
        dialog.withdraw()
        dialog.values['tenant_id'].set('online-company')
        value=dialog.value()
        assert value['tenant_id']=='customer'
        assert value['document']==issued['document']
        assert value['public_key']==issued['public_key']
        assert dialog.save_button.cget('text')=='Импортировать готовый файл'
        changed=json.loads(issued['document']);changed['payload']['tenant_id']='changed'
        dialog.files['document']=json.dumps(changed)
        with pytest.raises(InvalidSignature):dialog.value()
        dialog.destroy()
    finally:root.destroy()


def test_modes_keep_connection_and_import_separate():
    root=tk.Tk();root.withdraw();identity=str(uuid.uuid4())
    saved={'mode':'online','tenant_id':'company','url':'https://activation.test','token':'a'*64}
    try:
        dialog=ActivationDialog(root,identity,saved,'company',lambda value:None);dialog.withdraw()
        assert dialog.value()['url']=='https://activation.test/v1/decision'
        dialog.tabs.select(1)
        with pytest.raises(ValueError,match='готовый'):dialog.value()
        dialog.tabs.select(0)
        assert dialog.value()['token']==saved['token']
        dialog.destroy()
    finally:root.destroy()


def test_private_key_is_not_imported(tmp_path,monkeypatch):
    root=tk.Tk();root.withdraw();path=tmp_path/'private.pem'
    path.write_text('-----BEGIN PRIVATE KEY-----\nprivate\n-----END PRIVATE KEY-----')
    messages=[]
    monkeypatch.setattr('prodcast_manager.activation_dialog.filedialog.askopenfilename',lambda **kw:str(path))
    monkeypatch.setattr('prodcast_manager.activation_dialog.messagebox.showerror',lambda *a,**kw:messages.append(a))
    try:
        dialog=ActivationDialog(root,str(uuid.uuid4()),{},'company',lambda value:None);dialog.withdraw()
        dialog.pick('public_key')
        assert dialog.files['public_key']=='' and 'Приватный ключ' in messages[0][1]
        assert path.read_text().startswith('-----BEGIN PRIVATE KEY-----')
        dialog.destroy()
    finally:root.destroy()
