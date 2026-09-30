import os
from pathlib import Path
import subprocess
import sys


def test_redirected_cli_handles_unicode_path_under_ansi_locale(tmp_path):
    site=tmp_path/'площадка клиента'/'site.json'
    env=dict(os.environ,PYTHONIOENCODING='cp1252')
    result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'manager.py'),
                           'init','--site',str(site)],env=env,capture_output=True)
    assert result.returncode==0,result.stderr.decode('utf-8','replace')
    assert site.exists()
    assert str(site) in result.stdout.decode('utf-8')
