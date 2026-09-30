import hashlib,io,json,tarfile,zipfile
from pathlib import Path
import pytest
from prodcast_manager.offline import assemble_parts
from test_remote_configuration import agent

def archive(path,files):
    with tarfile.open(path,'w') as tar:
        for name,body in files.items():
            item=tarfile.TarInfo(name);item.size=len(body);tar.addfile(item,io.BytesIO(body))

def test_parts_assembled_and_corrupt_cached_copy_rebuilt(tmp_path):
    a=tmp_path/'release.zip.001';b=tmp_path/'release.zip.002'
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:z.writestr('test','offline')
    content=data.getvalue();a.write_bytes(content[:30]);b.write_bytes(content[30:])
    result=assemble_parts(a,tmp_path/'cache');assert result.read_bytes()==content
    result.write_bytes(b'broken')
    assert assemble_parts(a,tmp_path/'cache').read_bytes()==content

def test_missing_last_part_has_clear_error(tmp_path):
    a=tmp_path/'release.zip.001';a.write_bytes(b'PK incomplete')
    with pytest.raises(ValueError,match='incomplete or corrupt'):assemble_parts(a,tmp_path/'cache')

def test_missing_middle_part_refused(tmp_path):
    a=tmp_path/'release.zip.001';a.write_bytes(b'first')
    (tmp_path/'release.zip.003').write_bytes(b'last')
    with pytest.raises(ValueError,match='missing'):assemble_parts(a,tmp_path/'cache')

def test_offline_repository_never_uses_system_sources_or_downloads(agent,monkeypatch,tmp_path):
    tar=tmp_path/'repo.tar';archive(tar,{'Packages':b'','Packages.gz':b'fake'})
    agent.P['offline']={'linux_packages':{'ubuntu:22.04':'repo.tar'}}
    monkeypatch.setattr(agent,'offline_asset',lambda name:tar)
    monkeypatch.setattr(agent.platform,'freedesktop_os_release',lambda:{'ID':'ubuntu','VERSION_ID':'22.04'})
    calls=[]
    def run(args,**kw):calls.append(list(map(str,args)));return '2.35.0' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run)
    result=agent.bootstrap();assert result['offline']
    apt=[c for c in calls if c[0]=='apt-get'];assert len(apt)==2
    assert all('Dir::Etc::sourceparts=-' in c for c in apt)
    assert '--no-download' in apt[1]
    source=next((agent.STATE/'offline-packages').rglob('sources.list'))
    assert source.read_text().startswith('deb [trusted=yes] file:')
    assert not any('http:' in ' '.join(c) or 'https:' in ' '.join(c) for c in calls)

@pytest.mark.parametrize('name',['../escaped','/absolute'])
def test_offline_archive_cannot_escape_destination(agent,tmp_path,name):
    tar=tmp_path/'repo.tar';archive(tar,{name:b'x'})
    with pytest.raises(RuntimeError,match='Unsafe'):agent.extract_offline(tar,tmp_path/'dest')
    assert not (tmp_path/'escaped').exists()

def test_offline_model_import_checks_manifest_and_every_blob(agent,monkeypatch,tmp_path):
    blob=b'public test model';digest='sha256:'+hashlib.sha256(blob).hexdigest()
    manifest=json.dumps({'config':{'digest':digest,'size':len(blob)},'layers':[]}).encode()
    tar=tmp_path/'model.tar'
    archive(tar,{'manifests/registry.ollama.ai/library/qwen3/4b-instruct':manifest,'blobs/'+digest.replace(':','-'):blob})
    agent.P['offline']={'model_archive':tar.name,'model_digest':'sha256:'+hashlib.sha256(manifest).hexdigest()}
    monkeypatch.setattr(agent,'offline_asset',lambda name:tar)
    agent.install_offline_model(1000,1000)
    assert (agent.OLLAMA_HOME/'models/blobs'/digest.replace(':','-')).read_bytes()==blob
    archive(tar,{'manifests/registry.ollama.ai/library/qwen3/4b-instruct':manifest,'blobs/'+digest.replace(':','-'):b'corrupted'})
    with pytest.raises(RuntimeError,match='checksum mismatch'):agent.install_offline_model(1000,1000)

def test_offline_db_loads_pinned_images_without_pull(agent,monkeypatch,tmp_path):
    image=tmp_path/'images.tar';image.write_bytes(b'validated archive')
    agent.P['offline']={'db_images':image.name,'database_images':{r:{'tag':'offline-'+r+':v0.4','image_id':'sha256:'+r} for r in ('postgres','redis')}}
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)))
        assert args[:2]!=['docker','pull']
        if args[:3]==['docker','image','inspect']:
            role='postgres' if 'postgres' in args[3] else 'redis'
            return json.dumps([{'Id':'sha256:'+role}])
        return '999' if 'id' in args else ''
    monkeypatch.setattr(agent,'offline_asset',lambda name:image)
    monkeypatch.setattr(agent,'run',run);monkeypatch.setattr(agent,'firewall',lambda role:None)
    monkeypatch.setattr(agent,'psql',lambda *a:'');monkeypatch.setattr(agent,'dc',lambda *a,**kw:'PONG')
    agent.install_db()
    compose=json.loads((agent.ROOT/'db/compose.json').read_text())
    assert compose['services']['postgres']['image']=='offline-postgres:v0.4'
    assert ['docker','load','-i',str(image)] in calls

def test_corrupt_offline_asset_rejected_before_execution(agent,tmp_path):
    (tmp_path/'dep.tar').write_bytes(b'corrupt')
    agent.P.update(stage=str(tmp_path),files={'offline-linux':{'name':'dep.tar','sha256':'0'*64}})
    with pytest.raises(RuntimeError,match='checksum'):agent.offline_asset('dep.tar')

def test_offline_bootstrap_retains_existing_working_docker(agent,monkeypatch,tmp_path):
    tar=tmp_path/'repo.tar';archive(tar,{'Packages':b''})
    agent.P['offline']={'linux_packages':{'ubuntu:22.04':'repo.tar'}}
    monkeypatch.setattr(agent,'offline_asset',lambda name:tar)
    monkeypatch.setattr(agent.platform,'freedesktop_os_release',lambda:{'ID':'ubuntu','VERSION_ID':'22.04'})
    monkeypatch.setattr(agent.shutil,'which',lambda name:'/usr/bin/'+name)
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)));return '2.40.3' if args[:3]==['docker','compose','version'] else '29.1.3'
    monkeypatch.setattr(agent,'run',run)
    agent.bootstrap()
    install=next(c for c in calls if c[0]=='apt-get' and 'install' in c)
    assert '--no-download' in install
    assert not any(n in install for n in ('docker-ce','containerd.io','docker-compose-plugin','docker-compose-v2-'))

def test_offline_bootstrap_resolves_ubuntu_compose_conflict_after_partial_install(agent,monkeypatch,tmp_path):
    tar=tmp_path/'repo.tar';archive(tar,{'Packages':b''})
    agent.P['offline']={'linux_packages':{'ubuntu:22.04':'repo.tar'}}
    monkeypatch.setattr(agent,'offline_asset',lambda name:tar)
    monkeypatch.setattr(agent.platform,'freedesktop_os_release',lambda:{'ID':'ubuntu','VERSION_ID':'22.04'})
    monkeypatch.setattr(agent.shutil,'which',lambda name:'/usr/bin/'+name)
    calls=[]
    def run(args,**kw):
        calls.append(list(map(str,args)))
        if args[:2]==['docker','info']:raise RuntimeError('Docker daemon unavailable after interrupted APT transaction')
        if args[0]=='dpkg-query':return 'docker-compose-v2\tinstall ok installed\ndocker-compose\tdeinstall ok config-files\n'
        return '2.40.3' if args[:3]==['docker','compose','version'] else ''
    monkeypatch.setattr(agent,'run',run)
    agent.bootstrap()
    install=next(c for c in calls if c[0]=='apt-get' and 'install' in c)
    assert 'docker-compose-plugin' in install and 'docker-compose-v2-' in install
    assert 'docker-compose-' not in install and '--no-download' in install

def test_linux_staging_uses_disk_temporary_directory():
    from prodcast_manager.ssh import Remote
    remote=object.__new__(Remote);remote.windows=False;commands=[];remote.command=commands.append
    remote.prepare_stage()
    assert remote.stage.startswith('/var/tmp/prodcast-manager-')
    assert 'umask 077' in commands[0]

def test_staging_capacity_checked_before_opening_sftp(tmp_path):
    from prodcast_manager.ssh import Remote
    remote=object.__new__(Remote);remote.windows=False;remote.stage='/var/tmp/prodcast-manager-test';remote.role='ai'
    remote.command=lambda command:'Server banner\nMANAGER_SPACE:128\n'
    payload=tmp_path/'model.tar';payload.write_bytes(b'model')
    with pytest.raises(RuntimeError,match='insufficient staging disk space'):remote.put(payload)

def test_external_model_must_match_release_pin(tmp_path):
    from prodcast_manager.release import Release,sha
    model=tmp_path/'model.gguf';model.write_bytes(b'official model')
    r=object.__new__(Release);r.model_path=model
    r.offline_spec={'external_model':{'sha256':sha(model),'bytes':model.stat().st_size}}
    assert r.model_file()==model
    model.write_bytes(b'corrupt! model')
    with pytest.raises(ValueError,match='checksum mismatch'):r.model_file()
    r.model_path=None
    with pytest.raises(ValueError,match='Select the separately'):r.model_file()

def test_optional_ai_files_do_not_block_core_release(tmp_path):
    from prodcast_manager.release import Release,sha
    from prodcast_manager.offline import PROFILE
    names=['app-deployment','backend-linux-amd64','frontend-linux-amd64','gateway-linux-amd64','ai-deployment','ai-linux-amd64','worker-windows-amd64']
    artifacts=[]
    for key in names:
        comp,suffix=key.split('-',1);name=f'prodcast-{comp}-v0.4-{suffix}'+('.zip' if comp=='worker' else '.tar.gz')
        path=tmp_path/name;path.write_bytes(b'test artifact');artifacts.append({'name':name,'sha256':sha(path)})
    for name in ('deps.tar','db.tar','runtime.tar','metadata.tar'):
        path=tmp_path/name;path.write_bytes(b'public payload');artifacts.append({'name':name,'sha256':sha(path)})
    offline={'schema':1,'linux_packages':{'ubuntu:22.04':'deps.tar'},'db_images':'db.tar','ollama_runtime':'runtime.tar','model_archive':'metadata.tar','model_name':'qwen3:4b-instruct','model_digest':'sha256:'+'a'*64,'external_model':{'sha256':'b'*64,'bytes':100}}
    management={'schema':3,'profile':PROFILE,'minimum_manager':'0.3.0','python':'3.14.7','database_major':18,'migration_policy':'forward-only','upgrade_from':['v0.3'],'offline':offline}
    components=[{'name':'prodcast-'+name,'images':[{'name':'prodcast-'+name,'transport_tag':'ghcr.io/saatchi190499/prodcast-'+name+':test'}]} for name in ('backend','frontend','gateway','ai')]
    manifest=tmp_path/'release-manifest.json';manifest.write_text(json.dumps({'version':'v0.4','management':management,'components':components,'artifacts':artifacts}))
    (tmp_path/'runtime.tar').unlink()
    r=Release(tmp_path,tmp_path/'cache',sha(manifest),validate_ai=False)
    assert r.for_role('app') and r.for_role('db') and r.for_role('worker1')
    with pytest.raises(ValueError,match='AI offline payload'):r.for_role('ai')
    (tmp_path/'runtime.tar').write_bytes(b'public payload')
    with pytest.raises(ValueError,match='Select the separately'):r.for_role('ai')

def test_external_model_import_uses_verified_selected_file(agent,monkeypatch,tmp_path):
    blob=b'model weights';sha=hashlib.sha256(blob).hexdigest()
    model=tmp_path/'model.gguf';model.write_bytes(blob)
    manifest=json.dumps({'config':{'digest':'sha256:'+sha,'size':len(blob)},'layers':[]}).encode()
    metadata=tmp_path/'metadata.tar'
    archive(metadata,{'manifests/registry.ollama.ai/library/qwen3/4b-instruct':manifest})
    agent.P.update(offline={'model_archive':metadata.name,'model_digest':'sha256:'+hashlib.sha256(manifest).hexdigest(),'external_model':{'sha256':sha,'bytes':len(blob)}},files={'offline-model_blob':{'name':model.name}})
    monkeypatch.setattr(agent,'offline_asset',lambda name:tmp_path/name)
    agent.install_offline_model(1000,1000)
    assert (agent.OLLAMA_HOME/'models/blobs'/('sha256-'+sha)).read_bytes()==blob
    model.write_bytes(b'bad')
    with pytest.raises(RuntimeError,match='External AI model checksum'):agent.install_offline_model(1000,1000)

def test_ollama_api_digest_prefix_is_normalized(agent):
    assert agent.same_model_digest('a'*64,'sha256:'+'a'*64)
    assert not agent.same_model_digest('b'*64,'sha256:'+'a'*64)

@pytest.mark.parametrize('failed',[False,True])
def test_xz_runtime_extraction_cleans_temporary_tar(agent,monkeypatch,tmp_path,failed):
    import lzma
    compressed=tmp_path/'runtime.tar.xz';compressed.write_bytes(lzma.compress(b'test tar'))
    agent.P['stage']=str(tmp_path)
    def run(args):
        assert Path(args[2]).read_bytes()==b'test tar'
        if failed:raise RuntimeError('extraction failed')
    monkeypatch.setattr(agent,'run',run)
    if failed:
        with pytest.raises(RuntimeError):agent.unpack_ollama(compressed,tmp_path/'out')
    else:agent.unpack_ollama(compressed,tmp_path/'out')
    assert not (tmp_path/'ollama-runtime-unpacked.tar').exists()
