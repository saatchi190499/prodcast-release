"""RHEL adapter regression cases; execution deferred with the RHEL acceptance run."""
import json
from pathlib import Path
import pytest
from test_remote_configuration import agent

def test_offline_rhel_installs_only_from_local_signed_rpm_repository(agent,monkeypatch,tmp_path):
    repo=tmp_path/'repo';(repo/'repodata').mkdir(parents=True);(repo/'repodata/repomd.xml').write_text('metadata')
    (repo/'rpms').mkdir();(repo/'rpms/test.rpm').write_bytes(b'signed rpm')
    monkeypatch.setattr(agent,'docker_ready',lambda:False)
    monkeypatch.setattr(agent,'rpm_installed',lambda name:False)
    monkeypatch.setattr(agent,'selinux_enabled',lambda:False)
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)))
        return '5.5.1' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run)
    assert agent.bootstrap_rhel(repo)['offline']
    dnf=next(c for c in calls if c[0]=='dnf')
    assert '--disablerepo=*' in dnf and '--noplugins' in dnf
    assert '--setopt=prodcast-offline.gpgcheck=1' in dnf
    assert any(x.startswith('--repofrompath=prodcast-offline,file://') for x in dnf)
    assert not any('https://' in x or '--allowerasing' in x or 'setenforce' in x for c in calls for x in c)
    assert any(c[:2]==['rpmkeys','--checksig'] for c in calls)

def test_rhel_preserves_working_docker_and_full_curl(agent,monkeypatch,tmp_path):
    repo=tmp_path/'repo';(repo/'repodata').mkdir(parents=True);(repo/'repodata/repomd.xml').write_text('metadata')
    (repo/'rpms').mkdir();(repo/'rpms/test.rpm').write_bytes(b'rpm')
    monkeypatch.setattr(agent,'docker_ready',lambda:True)
    monkeypatch.setattr(agent,'rpm_installed',lambda name:name=='curl')
    monkeypatch.setattr(agent,'selinux_enabled',lambda:False)
    calls=[]
    def run(args,**kw):calls.append(list(map(str,args)));return '5.5.1' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run);agent.bootstrap_rhel(repo)
    install=next(c for c in calls if c[0]=='dnf')
    assert 'curl' not in install and 'curl-minimal' not in install and 'docker-ce' not in install

def test_rhel_minor_versions_select_same_payload():
    from prodcast_manager.release import Release
    r=object.__new__(Release);r.offline=True;r.offline_platforms={};r.offline_spec={'linux_packages':{'rhel:9':'rpm.tar.gz'}}
    r.select_platform('app',{'ID':'rhel','VERSION_ID':'9.8'})
    assert r.offline_platforms['app']=='rhel:9'
    with pytest.raises(ValueError):r.select_platform('app',{'ID':'rhel','VERSION_ID':'10.0'})

def test_shared_container_mounts_use_selinux_shared_label(agent,monkeypatch):
    monkeypatch.setattr(agent,'selinux_enabled',lambda:True)
    services={'api':{'volumes':['./certs:/certs:ro','./data:/data','named:/media']}}
    agent.selinux_json_mounts(services)
    assert services['api']['volumes']==['./certs:/certs:ro,z','./data:/data:z','named:/media']

def test_firewalld_uses_scoped_rules_without_reload_or_ssh_changes(agent,monkeypatch):
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)))
        if args[:2]==['ip','-j']:return json.dumps([{'ifname':'eth0','addr_info':[{'local':agent.C['hosts']['db']['address']}]}])
        if '--get-zone-of-interface=eth0' in args:return 'public\n'
        return ''
    monkeypatch.setattr(agent,'run',run);agent.firewalld_rules('db')
    assert any('--permanent' in c for c in calls)
    assert not any('--reload' in c or '--complete-reload' in c for c in calls)
    rules=json.loads((agent.STATE/'firewalld-rules.json').read_text())['rules']
    assert any('port="5432"' in rule and ' accept' in rule for rule in rules)
    assert any('port="6380"' in rule and ' drop' in rule for rule in rules)
    assert not any('port="22"' in rule for rule in rules)

def test_worker_grants_include_server_column_for_all_selected_workers(agent):
    agent.C['hosts']['worker3']=dict(agent.C['hosts']['worker1'])
    sql=agent.worker_grants()
    grant=next(line for line in sql.splitlines() if 'GRANT UPDATE (server)' in line)
    assert 'prodcast_worker_03' in grant and 'information_schema.columns' in sql

@pytest.mark.parametrize('damaged',[False,True])
def test_rhel90_keeps_audit_libraries_and_checks_dvd_binding(agent,monkeypatch,tmp_path,damaged):
    import shutil
    from prodcast_manager.engine import RESOURCES
    repo=tmp_path/'repo';(repo/'repodata').mkdir(parents=True);(repo/'repodata/repomd.xml').write_text('metadata')
    (repo/'rpms').mkdir();(repo/'rpms/test.rpm').write_bytes(b'signed rpm')
    stage=tmp_path/'stage';stage.mkdir();agent.P['stage']=str(stage)
    binding=next((RESOURCES/'rhel9').glob('*.rpm'));shutil.copy2(binding,stage/binding.name)
    if damaged:(stage/binding.name).write_bytes(b'bad package')
    installed={'ca-certificates','curl','gnupg2','zstd','iptables-nft','tar','shadow-utils','util-linux','python3','iproute','selinux-policy-targeted','audit-libs','audit'}
    monkeypatch.setattr(agent,'rpm_installed',lambda name:name in installed)
    monkeypatch.setattr(agent,'docker_ready',lambda:False)
    monkeypatch.setattr(agent,'selinux_enabled',lambda:False)
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)))
        if args[-1]=='audit-libs':return '3.0.7-101.el9_0.2.x86_64'
        return '5.5.1' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run)
    if damaged:
        with pytest.raises(RuntimeError,match='missing or damaged'):agent.bootstrap_rhel(repo)
        assert not any(c[0]=='dnf' for c in calls)
    else:
        agent.bootstrap_rhel(repo)
        install=next(c for c in calls if c[0]=='dnf')
        assert not installed.intersection(install)
        assert str(stage/binding.name) in install
        assert '--setopt=localpkg_gpgcheck=1' in install
        assert ['rpmkeys','--checksig',str(stage/binding.name)] in calls


def test_rhel_bootstrap_repeated_with_ready_dependencies_does_not_upgrade_os(agent,monkeypatch,tmp_path):
    repo=tmp_path/'repo';(repo/'repodata').mkdir(parents=True);(repo/'repodata/repomd.xml').write_text('metadata')
    (repo/'rpms').mkdir();(repo/'rpms/test.rpm').write_bytes(b'rpm')
    monkeypatch.setattr(agent,'rpm_installed',lambda name:True)
    monkeypatch.setattr(agent,'docker_ready',lambda:True)
    monkeypatch.setattr(agent,'selinux_enabled',lambda:False)
    calls=[]
    def run(args,**kw):calls.append(list(map(str,args)));return '5.5.1' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run);agent.bootstrap_rhel(repo)
    assert not any(c[0]=='dnf' for c in calls)
