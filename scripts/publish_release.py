"""Publish an already assembled, hash-pinned Complete package after manual approval."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

from release_common import REPO, download, draft, gh, sha256, upload, version, write_json


def verify_complete(manifest_path, complete, checksum_path, expected):
    if not re.fullmatch(r'[a-f0-9]{64}', expected) or sha256(manifest_path) != expected:
        raise ValueError('Manifest differs from the compatibility-approved package')
    digest, name = Path(checksum_path).read_text().strip().split('  ', 1)
    if name != Path(complete).name or sha256(complete) != digest:
        raise ValueError('Complete archive integrity failed')
    with zipfile.ZipFile(complete) as archive:
        if archive.namelist().count('release-manifest.json') != 1 or archive.read('release-manifest.json') != Path(manifest_path).read_bytes():
            raise ValueError('Complete archive contains a different manifest')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--validation-note', required=True)
    parser.add_argument('--approved', action='store_true')
    args = parser.parse_args()
    tag = version(args.version)
    if not args.approved or len(args.validation_note.strip()) < 20:
        raise ValueError('Explicit compatibility approval and a validation record/link are required')
    current = draft(tag)
    complete_name = f'ProdCast-{tag}-complete.zip'
    required = {'release-manifest.json', 'assembly-lock.json', 'RELEASE-NOTES.md', complete_name, complete_name + '.sha256'}
    if not required <= {a['name'] for a in current['assets']}:
        raise ValueError('Assembly is incomplete')
    with tempfile.TemporaryDirectory() as temp:
        manifest = download(tag, 'release-manifest.json', temp)
        complete = download(tag, complete_name, temp)
        checksum = download(tag, complete_name + '.sha256', temp)
        verify_complete(manifest, complete, checksum, args.manifest_sha256)
        if json.loads(manifest.read_text())['version'] != tag:
            raise ValueError('Manifest version mismatch')
        receipt = Path(temp) / 'publication-approval.json'
        write_json(receipt, {'version': tag, 'manifest_sha256': args.manifest_sha256,
            'approved_by': os.environ.get('GITHUB_ACTOR', 'operator'),
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'validation_note': args.validation_note, 'binaries_rebuilt': False})
        if 'publication-approval.json' in {a['name'] for a in current['assets']}:
            previous = download(tag, 'publication-approval.json', Path(temp) / 'prior')
            old = json.loads(previous.read_text())
            if old['manifest_sha256'] != args.manifest_sha256 or old['validation_note'] != args.validation_note:
                raise ValueError('A different approval receipt already exists')
        else:
            upload(tag, [receipt])
        notes = download(tag, 'RELEASE-NOTES.md', temp)
        notes.write_text(notes.read_text().replace(
            'Integrity verified. Installation/upgrade compatibility must be approved before publication.',
            'Integrity verified. Compatibility approval is recorded in publication-approval.json; see its validation scope.'))
        gh('release', 'edit', tag, '--repo', REPO, '--notes-file', str(notes),
           '--draft=false', '--prerelease=' + ('true' if '-rc.' in tag else 'false'),
           '--latest=' + ('false' if '-rc.' in tag else 'true'))
        print(f'Published https://github.com/{REPO}/releases/tag/{tag}')


if __name__ == '__main__':
    main()
