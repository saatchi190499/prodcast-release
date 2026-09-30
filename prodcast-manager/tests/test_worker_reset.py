"""Execute the reset stop helper with mocked SCM/process APIs; no real services."""
import json
import os
import subprocess
from pathlib import Path
import pytest


@pytest.mark.skipif(os.name!='nt',reason='Windows PowerShell behavior')
@pytest.mark.parametrize('case',['graceful','owned-hung','foreign-pid','foreign-service'])
def test_reset_stops_only_the_owned_worker_process(tmp_path,case):
    source=(Path(__file__).parents[1]/'prodcast_manager/resources/worker.ps1').read_text('utf-8')
    helper=source.split('function Stop-OwnedWorker {',1)[1].split('function Dispatch {',1)[0]
    script=r'''
$ErrorActionPreference='Stop'
$case='CASE'
$service='ProdCastWorker01'
$script:state=[pscustomobject]@{install_root='C:\ProdCast\Managed\test';pending_root=''}
$script:events=New-Object Collections.Generic.List[string]
$script:stopped=$false
function Set-Service {param($Name,$StartupType);$script:events.Add('disable:'+ $StartupType)}
function Stop-Service {param($Name,$ErrorAction);$script:events.Add('stop');if($case -eq 'graceful'){$script:stopped=$true}else{throw 'Simulated wrapper failure'}}
function Start-Sleep {param($Seconds)}
function Get-CimInstance {param($ClassName,$Filter)
 if($ClassName -eq 'Win32_Service'){return [pscustomobject]@{State=$(if($script:stopped){'Stopped'}else{'Running'});ProcessId=1234;PathName=$(if($case -eq 'foreign-service'){'"C:\unrelated\service.exe"'}else{'"C:\ProdCast\Managed\test\ProdCastWorker01.exe"'})}}
 return [pscustomobject]@{ExecutablePath=$(if($case -eq 'foreign-pid'){'C:\Windows\System32\unrelated.exe'}else{'C:\ProdCast\Managed\test\ProdCastWorker01.exe'})}
}
function taskkill.exe {param($PID,$T,$F);$script:events.Add('kill');$script:stopped=$true;$script:LASTEXITCODE=0}
function Check-Native {param($Name);if($LASTEXITCODE){throw 'Native failure'}}
function Get-Service {param($Name);$v=New-Object PSObject;Add-Member -InputObject $v -MemberType ScriptMethod -Name WaitForStatus -Value {param($status,$timeout)};return $v}
HELPER
$errorText='';try{Stop-OwnedWorker}catch{$errorText=$_.Exception.Message}
@{events=@($script:events);error=$errorText;stopped=$script:stopped}|ConvertTo-Json -Compress
'''.replace('CASE',case).replace('HELPER','function Stop-OwnedWorker {'+helper)
    # Avoid PowerShell's built-in, read-only $PID in the mock parameter list.
    script=script.replace('param($PID,$T,$F)','param([Alias("PID")]$processId,$T,$F)')
    path=tmp_path/'reset-stop-test.ps1';path.write_text(script,encoding='utf-8-sig')
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(path)],capture_output=True,text=True,check=True)
    value=json.loads(result.stdout.strip().splitlines()[-1])
    if case=='foreign-service':
        assert not value['events'] and 'unowned' in value['error']
        return
    assert value['events'][:2]==['disable:Disabled','stop']
    if case=='foreign-pid':
        assert 'unowned' in value['error'] and 'kill' not in value['events'] and not value['stopped']
    else:
        assert not value['error'] and value['stopped']
        assert ('kill' in value['events'])==(case=='owned-hung')
