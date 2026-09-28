"""Archive component inputs in Actions before removing their duplicate release assets."""
import argparse
import json
import os
from pathlib import Path
import re

from publish_release import verify_complete
from release_common import REPO, draft, download, gh, record, sha256, verify, version, write_json

INPUT = re.compile(r'prodcast-(app|agent|ai|worker)-(v\d+\.\d+\.\d+-rc\.\d+)-component\.(zip|json)')


def input_name(name, tag):
    match = INPUT.fullmatch(name)
    return bool(match and match[2].split('-rc.')[0] == tag)


def matched_asset(path, assets):
    item = record(path)
    asset = assets.get(item['name'])
    if not asset or asset['state'] != 'uploaded' or asset['size'] != item['bytes'] or asset.get('digest') != 'sha256:' + item['sha256']:
        raise ValueError('Uploaded release asset does not match verified local file: ' + item['name'])
    return {**item, 'id': asset['id']}


def stage(assembled, directory):
    assembled, directory = Path(assembled), Path(directory)
    manifest = assembled / 'release-manifest.json'
    data = json.loads(manifest.read_text())
    tag = version(data['version'])
    complete = assembled / f'ProdCast-{tag}-complete.zip'
    verify_complete(manifest, complete, assembled / (complete.name + '.sha256'), sha256(manifest))
    current = draft(tag)
    assets = {a['name']: a for a in current['assets']}
    protected = [matched_asset(p, assets) for p in (manifest, complete)]
    directory.mkdir(parents=True, exist_ok=False)
    names = {name for name in assets if input_name(name, tag)}
    if not names:
        raise ValueError('No component inputs to archive')
    inputs = []
    for name in sorted(names):
        path = download(tag, name, directory)
        inputs.append(matched_asset(path, assets))
    for name in sorted(names):
        if not name.endswith('.json'):
            if name[:-4] + '.json' not in names:
                raise ValueError('Component archive has no descriptor')
            continue
        descriptor = json.loads((directory / name).read_text())
        match = INPUT.fullmatch(name)
        if descriptor['component'] != match[1] or descriptor['version'] != match[2]:
            raise ValueError('Component descriptor does not match its filename')
        expected_zip = name[:-5] + '.zip'
        if descriptor['archive']['name'] != expected_zip or expected_zip not in names:
            raise ValueError('Component descriptor has no matching archive')
        verify(directory, descriptor['archive'])
    # Preserve the exact plan and all candidates, including RCs not selected for Complete.
    lock = download(tag, 'assembly-lock.json', directory)
    if json.loads(lock.read_text()) != data['assembly_source']:
        raise ValueError('Assembly lock differs from the completed manifest')
    plan = {'version': tag, 'release_id': current['id'], 'run_id': os.environ['GITHUB_RUN_ID'],
            'artifact_name': 'release-inputs-' + tag, 'protected': protected, 'inputs': inputs}
    write_json(directory / 'cleanup-plan.json', plan)
    return plan


def cleanup(directory, artifact_id):
    directory = Path(directory)
    plan = json.loads((directory / 'cleanup-plan.json').read_text())
    tag = version(plan['version'])
    if plan['run_id'] != os.environ['GITHUB_RUN_ID']:
        raise ValueError('Cleanup belongs to a different workflow run')
    artifact = json.loads(gh('api', f'repos/{REPO}/actions/artifacts/{int(artifact_id)}'))
    if artifact['expired'] or artifact['name'] != plan['artifact_name'] or str(artifact['workflow_run']['id']) != plan['run_id'] or artifact['size_in_bytes'] <= 0:
        raise ValueError('A successful retained Actions artifact is required before cleanup')
    current = draft(tag)
    if current['id'] != plan['release_id']:
        raise ValueError('Release changed after archiving')
    assets = {a['name']: a for a in current['assets']}
    # Validate every target before deleting anything. A failed archive/upload never reaches this step.
    for item in plan['protected'] + plan['inputs']:
        asset = assets.get(item['name'])
        if not asset or asset['id'] != item['id'] or asset.get('digest') != 'sha256:' + item['sha256'] or asset['size'] != item['bytes']:
            raise ValueError('Release assets changed after archiving')
    for item in plan['inputs']:
        if not input_name(item['name'], tag):
            raise ValueError('Refusing to delete a non-component asset')
        verify(directory, item)
    for item in plan['inputs']:
        # Exact archived asset IDs only; Complete, manifests, locks and reports are never targets.
        draft(tag)
        gh('api', '--method', 'DELETE', f"repos/{REPO}/releases/assets/{item['id']}")
    print(f'Removed {len(plan["inputs"])} archived component assets from draft {tag}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['stage', 'cleanup'])
    parser.add_argument('--assembled', default='dist/assembled')
    parser.add_argument('--directory', default='dist/retained-inputs')
    parser.add_argument('--artifact-id', type=int)
    args = parser.parse_args()
    if args.operation == 'stage':
        stage(args.assembled, args.directory)
    elif args.artifact_id:
        cleanup(args.directory, args.artifact_id)
    else:
        parser.error('--artifact-id is required for cleanup')
