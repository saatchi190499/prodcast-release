"""Validate a component build and contribute it to the common draft release."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile

from release_common import COMPONENTS, REPO, draft, download, gh, pack, record, sha256, upload, verify, version, write_json


def prepare(component, tag, source_commit, folder, output):
    if component not in COMPONENTS or not re.fullmatch(r'v\d+\.\d+\.\d+-rc\.\d+', tag):
        raise ValueError('Only supported component RC tags can contribute builds')
    if not re.fullmatch(r'[a-f0-9]{40}', source_commit):
        raise ValueError('Expected full source commit')
    folder, output = Path(folder), Path(output)
    manifest = json.loads((folder / 'release-manifest.json').read_text())
    expected_repo = f'saatchi190499/prodcast-{component}'
    if (manifest['repository'], manifest['version'], manifest['source_commit']) != (expected_repo, tag, source_commit):
        raise ValueError('Build manifest does not match source repository, tag and commit')
    artifacts = manifest['artifacts']
    names = [item['name'] for item in artifacts]
    if not names or len(set(names)) != len(names) or {'release-manifest.json', 'SHA256SUMS'} & set(names):
        raise ValueError('Invalid build manifest artifact list')
    for item in artifacts:
        verify(folder, item)
    names += ['release-manifest.json', 'SHA256SUMS']
    if {p.name for p in folder.iterdir()} != set(names):
        raise ValueError('Unexpected files in build output')
    checksums = {}
    for line in (folder / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if name in checksums:
            raise ValueError('Duplicate checksum entry')
        checksums[name] = digest
    if set(checksums) != set(names) - {'SHA256SUMS'}:
        raise ValueError('Incomplete checksum list')
    if any(sha256(folder / name) != digest for name, digest in checksums.items()):
        raise ValueError('Build checksum mismatch')
    output.mkdir(parents=True, exist_ok=True)
    stem = f'prodcast-{component}-{tag}-component'
    archive = output / (stem + '.zip')
    pack(folder, archive, names)
    descriptor = output / (stem + '.json')
    write_json(descriptor, {'schema_version': 1, 'component': component, 'version': tag,
        'repository': expected_repo, 'source_commit': source_commit, 'archive': record(archive),
        'build_manifest_sha256': sha256(folder / 'release-manifest.json')})
    return archive, descriptor


def publish(tag, paths):
    version(tag)
    # Create the shared draft once, before starting concurrent component builds.
    # GitHub allows multiple drafts with the same tag, so publishers must not create it.
    existing = {a['name'] for a in draft(tag)['assets']}
    # Once assembly starts, component uploads cannot change the input set.
    if 'assembly-lock.json' in existing:
        raise ValueError('This draft is frozen for assembly; use a new release version')
    with tempfile.TemporaryDirectory() as temp:
        for path in paths:
            if path.name in existing:
                prior = download(tag, path.name, temp)
                if sha256(prior) != sha256(path):
                    raise ValueError('An asset with different content already exists; use a new component tag')
            else:
                upload(tag, [path])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--component', required=True, choices=sorted(COMPONENTS))
    parser.add_argument('--tag', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--output', default='dist/contribution')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if os.environ.get('GITHUB_REPOSITORY', f'saatchi190499/prodcast-{args.component}') != f'saatchi190499/prodcast-{args.component}':
        raise ValueError('Component does not match caller repository')
    paths = prepare(args.component, args.tag, args.source_commit, args.directory, args.output)
    target = args.tag.split('-rc.')[0]
    if not args.prepare_only:
        publish(target, paths)
    print(f'Component prepared for https://github.com/{REPO}/releases/tag/{target}')
    print('Descriptor:', paths[1].name, 'SHA256:', sha256(paths[1]))


if __name__ == '__main__':
    main()
