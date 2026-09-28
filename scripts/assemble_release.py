"""Assemble a Manager-compatible Complete ZIP from a pinned base and contributions."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import tempfile

from release_common import COMPONENTS, REPO, download, draft, filename, pack, record, sha256, unpack, upload, verify, version, write_json


def component_file(component, name):
    prefixes = {
        'app': ('prodcast-app-', 'prodcast-backend-', 'prodcast-frontend-', 'prodcast-gateway-'),
        'agent': ('prodcast-agent-', 'ProdCastAgent-', 'workflow-agent-'),
        'ai': ('prodcast-ai-',),
        'worker': ('prodcast-worker-',),
    }
    return name.startswith(prefixes[component])


def output_name(component, name, source_tag, target):
    filename(name)
    if name == 'release-manifest.json':
        return f'prodcast-{component}-source-manifest.json'
    if name in {'images.json', 'packages.env', 'INSTALL-RU.md', 'INSTALL-EN.md'}:
        return f'prodcast-{component}-{name}'
    if not component_file(component, name):
        raise ValueError('Unexpected component artifact: ' + name)
    return name.replace(source_tag, target)


def build(plan, base_archive, contributions, output):
    """Offline assembly entry point; every downloaded byte is checked before reuse."""
    target = version(plan['version'])
    base_version = version(plan['base']['version'])
    if target == base_version or set(plan['components']) - COMPONENTS:
        raise ValueError('Invalid release plan or unsupported component (License is unchanged)')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    contents = output / 'contents'
    unpack(base_archive, contents)
    manifest_path = contents / 'release-manifest.json'
    if sha256(manifest_path) != plan['base']['manifest_sha256']:
        raise ValueError('Base manifest checksum differs from the approved release')
    manifest = json.loads(manifest_path.read_text())
    if manifest['version'] != base_version or manifest.get('management', {}).get('schema') != 3:
        raise ValueError('Expected a matching Manager schema 3 base release')
    known = {'release-manifest.json', 'release-manifest.json.sha256', 'SHA256SUMS'}
    external = []
    for item in manifest['artifacts']:
        if item.get('location', 'complete') == 'complete':
            verify(contents, item)
            known.add(item['name'])
        else:
            external.append(copy.deepcopy(item))
    if {p.name for p in contents.iterdir()} - known:
        raise ValueError('Base archive has unlisted files')
    components = {c['component']: copy.deepcopy(c) for c in manifest['components']}
    if not COMPONENTS <= components.keys():
        raise ValueError('Base is missing required applications')
    for component, choice in plan['components'].items():
        descriptor_path, archive_path = map(Path, contributions[component])
        if sha256(descriptor_path) != choice['sha256']:
            raise ValueError('Component descriptor checksum mismatch')
        descriptor = json.loads(descriptor_path.read_text())
        if descriptor['component'] != component or descriptor['repository'] != f'saatchi190499/prodcast-{component}':
            raise ValueError('Wrong component descriptor')
        verify(archive_path.parent, descriptor['archive'])
        if archive_path.name != descriptor['archive']['name']:
            raise ValueError('Wrong component archive')
        payload = output / ('input-' + component)
        unpack(archive_path, payload)
        source = payload / 'release-manifest.json'
        if sha256(source) != descriptor['build_manifest_sha256']:
            raise ValueError('Source manifest checksum mismatch')
        build_manifest = json.loads(source.read_text())
        if any(build_manifest[k] != descriptor[k] for k in ('repository', 'version', 'source_commit')):
            raise ValueError('Component provenance mismatch')
        artifact_names = [i['name'] for i in build_manifest['artifacts']]
        if len(artifact_names) != len(set(artifact_names)) or set(artifact_names) & {'release-manifest.json', 'SHA256SUMS'}:
            raise ValueError('Invalid component artifact list')
        if {p.name for p in payload.iterdir()} != set(artifact_names) | {'release-manifest.json', 'SHA256SUMS'}:
            raise ValueError('Unexpected component payload files')
        for item in build_manifest['artifacts']:
            verify(payload, item)
        for old in list(contents.iterdir()):
            if component_file(component, old.name):
                old.unlink()
        mapping = {}
        for name in artifact_names + ['release-manifest.json']:
            destination = output_name(component, name, descriptor['version'], target)
            if (contents / destination).exists():
                raise ValueError('Artifact name collision: ' + destination)
            shutil.copyfile(payload / name, contents / destination)
            mapping[name] = destination
        images = json.loads((payload / 'images.json').read_text()) if (payload / 'images.json').exists() else []
        components[component] = {'component': component, 'repository': descriptor['repository'],
            'source_commit': descriptor['source_commit'], 'binary_version': descriptor['version'],
            'images': images, 'source_release': f'https://github.com/{REPO}/releases/tag/{target}',
            'contribution': {'descriptor': descriptor_path.name, 'sha256': choice['sha256']},
            'artifact_mapping': mapping}
    for component, info in components.items():
        if component not in plan['components']:
            info['reused_from'] = base_version
    manifest['version'] = target
    manifest['status'] = 'complete'
    manifest['publication_status'] = 'draft'
    manifest['production_accepted'] = False
    manifest['created_utc'] = datetime.now(timezone.utc).isoformat()
    manifest['components'] = list(components.values())
    manifest['assembly_source'] = copy.deepcopy(plan)
    manifest.pop('promotion_source', None)
    manifest['management']['upgrade_from'] = sorted(set(manifest['management'].get('upgrade_from', [])) | {base_version})
    external_ollama = manifest['management'].get('offline', {}).get('external_ollama')
    if external_ollama:
        external_ollama.setdefault('url', f'https://github.com/{REPO}/releases/download/{base_version}/{filename(external_ollama["name"])}')
    write_json(contents / 'compatibility-validation.json', {
        'version': target, 'artifact_integrity_checked': True,
        'manager_manifest_schema': 3, 'full_install_upgrade_tested': False,
        'requires_compatibility_approval_before_publication': True,
        'base_release': base_version,
        'changed_components': sorted(plan['components']),
    })
    for lang in ('EN', 'RU'):
        old = contents / f'INSTALL-{lang}.md'
        if old.exists():
            # Preserve the base guide but make its provenance unambiguous.
            inherited = old.read_text(encoding='utf-8')
            old.write_text(f'# ProdCast {target}\n\n'
                f'This package reuses infrastructure and Manager from {base_version}. '
                'The exact application versions and filenames are in release-manifest.json. '
                'Use its SHA256 in Manager. Component installation notes, when present, '
                'are named prodcast-<component>-INSTALL-*.md.\n\n'
                f'## Inherited infrastructure guide ({base_version})\n\n' + inherited, encoding='utf-8')
    controls = {'release-manifest.json', 'release-manifest.json.sha256', 'SHA256SUMS'}
    manifest['artifacts'] = external + [record(p, location='complete') for p in sorted(contents.iterdir()) if p.name not in controls]
    write_json(manifest_path, manifest)
    (contents / 'release-manifest.json.sha256').write_text(sha256(manifest_path) + '  release-manifest.json\n')
    (contents / 'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in sorted(contents.iterdir()) if p.name != 'SHA256SUMS'))
    complete = output / f'ProdCast-{target}-complete.zip'
    pack(contents, complete, [p.name for p in contents.iterdir()])
    for name in ('release-manifest.json', 'release-manifest.json.sha256', 'compatibility-validation.json'):
        shutil.copyfile(contents / name, output / name)
    (output / (complete.name + '.sha256')).write_text(sha256(complete) + '  ' + complete.name + '\n')
    notes = [f'# ProdCast {target}', '', 'Complete package assembled from pinned builds.', '',
             '| Component | Binary version | Source commit |', '|---|---|---|']
    notes += [f"| {c['component']} | {c.get('binary_version', c.get('upstream_tag', 'inherited'))} | {c['source_commit']} |" for c in components.values()]
    notes += ['', f"Manager: {manifest['management']['recommended_manager']} (included in Complete).",
              '', '**SHA256 of release-manifest.json for Manager:**', '', '```text', sha256(manifest_path), '```', '',
              'Integrity verified. Installation/upgrade compatibility must be approved before publication.']
    if external_ollama:
        notes += ['', f"Optional AI runtime: [Ollama components]({external_ollama['url']}) (reused with the base checksum)."]
    (output / 'RELEASE-NOTES.md').write_text('\n'.join(notes) + '\n', encoding='utf-8')
    return complete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output', default='dist/assembled')
    args = parser.parse_args()
    path = Path(args.plan).resolve()
    root = Path(__file__).resolve().parents[1] / 'plans'
    if not path.is_relative_to(root) or path.suffix != '.json':
        raise ValueError('Use a reviewed JSON plan inside plans/')
    plan = json.loads(path.read_text())
    tag = version(plan['version'])
    assets = {a['name'] for a in draft(tag)['assets']}
    if any(n.startswith('ProdCast-') and n.endswith('-complete.zip') for n in assets):
        raise ValueError('A Complete package already exists; publish it or choose a new version')
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        lock = temp / 'assembly-lock.json'
        write_json(lock, plan)
        if lock.name in assets:
            previous = download(tag, lock.name, temp / 'prior')
            if sha256(previous) != sha256(lock):
                raise ValueError('Draft is frozen with a different assembly plan')
        else:
            upload(tag, [lock])
        # A lock is append-only. Existing selected contributions cannot be replaced.
        base_version = version(plan['base']['version'])
        base = download(base_version, f'ProdCast-{base_version}-complete.zip', temp)
        contributions = {}
        for component, choice in plan['components'].items():
            if component not in COMPONENTS:
                raise ValueError('Unsupported component')
            descriptor = download(tag, filename(choice['descriptor']), temp)
            if sha256(descriptor) != choice['sha256']:
                raise ValueError('Descriptor does not match the reviewed plan')
            data = json.loads(descriptor.read_text())
            archive = download(tag, filename(data['archive']['name']), temp)
            contributions[component] = (descriptor, archive)
        complete = build(plan, base, contributions, args.output)
        out = complete.parent
        # Complete is uploaded last and is the completion marker for publication.
        paths = [out / n for n in ('release-manifest.json', 'release-manifest.json.sha256', 'compatibility-validation.json', 'RELEASE-NOTES.md', complete.name + '.sha256')]
        existing = {a['name'] for a in draft(tag)['assets']}
        if existing & {p.name for p in paths}:
            raise ValueError('Interrupted assembly has output assets; inspect them before starting a new version')
        upload(tag, paths)
        upload(tag, [complete])
        from release_common import gh
        gh('release', 'edit', tag, '--repo', REPO, '--title', f'ProdCast {tag}', '--notes-file', str(out / 'RELEASE-NOTES.md'))
        print('Draft Complete package ready. Manager manifest SHA256:', sha256(out / 'release-manifest.json'))


if __name__ == '__main__':
    main()
