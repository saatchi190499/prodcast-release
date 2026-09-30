import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

@pytest.fixture(autouse=True)
def isolate_local_appdata(tmp_path,monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local-appdata'))
    import prodcast_manager.gui as gui
    monkeypatch.setattr(gui,'application_directory',lambda:tmp_path/'portable')
