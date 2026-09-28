import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from assemble_release import build
from publish_component import prepare, publish
from publish_release import verify_complete
from release_common import pack, record, release, sha256, unpack, write_json

COMMIT = 'a' * 40
TAG = 'v0.5.0-rc.1'


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def payload(self, component='app'):
        folder = self.root / ('payload-' + component)
        folder.mkdir()
        names = {'app': [f'prodcast-backend-{TAG}-linux-amd64.tar.gz', f'prodcast-app-{TAG}-deployment.tar.gz'],
                 'ai': [f'prodcast-ai-{TAG}-linux-amd64.tar.gz', f'prodcast-ai-{TAG}-deployment.tar.gz'],
                 'agent': [f'ProdCastAgent-Setup-{TAG}.exe', 'INSTALL-RU.md'],
                 'worker': [f'prodcast-worker-{TAG}-windows-amd64.zip']}[component]
        for name in names:
            (folder / name).write_bytes(b'new-' + name.encode())
        if component in ('app', 'ai'):
            write_json(folder / 'images.json', [{'name': 'prodcast-' + component, 'image_id': 'sha256:new', 'transport_tag': TAG}])
            (folder / 'packages.env').write_text('IMAGE=sha256:new\n')
        write_json(folder / 'release-manifest.json', {'schema_version': 1, 'repository': f'saatchi190499/prodcast-{component}',
            'version': TAG, 'source_commit': COMMIT, 'artifacts': [record(p) for p in sorted(folder.iterdir())]})
        (folder / 'SHA256SUMS').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in sorted(folder.iterdir())))
        return folder

    def base(self):
        folder = self.root / 'base'
        folder.mkdir()
        for name in ['prodcast-backend-v0.4-linux-amd64.tar.gz', 'prodcast-app-v0.4-deployment.tar.gz',
                     'ProdCastAgent-Setup-v0.3.exe', 'prodcast-ai-v0.4-linux-amd64.tar.gz',
                     'prodcast-worker-v0.4-windows-amd64.zip', 'offline-database-images.tar',
                     'ProdCast-Manager-0.3.3.zip', 'prodcast-license-unchanged.tar.gz', 'INSTALL-RU.md']:
            (folder / name).write_bytes(b'old-' + name.encode())
        manifest = {'schema_version': 1, 'version': 'v0.4',
            'management': {'schema': 3, 'recommended_manager': '0.3.3', 'upgrade_from': ['v0.3'],
                'offline': {'external_ollama': {'name': 'ProdCast-v0.4-ollama-components.zip', 'sha256': 'b' * 64}}},
            'components': [{'component': c, 'repository': 'saatchi190499/prodcast-' + c,
                            'source_commit': 'b' * 40, 'binary_version': 'v0.4'} for c in ('app','agent','ai','worker','license')],
            'artifacts': [record(p, location='complete') for p in sorted(folder.iterdir())] + [
                {'name': 'offline-ollama.tar.xz', 'bytes': 1, 'sha256': 'c' * 64, 'location': 'ollama-components'}]}
        write_json(folder / 'release-manifest.json', manifest)
        archive = self.root / 'base.zip'
        pack(folder, archive, [p.name for p in folder.iterdir()])
        plan = {'version': 'v0.5.0', 'base': {'version': 'v0.4', 'manifest_sha256': sha256(folder / 'release-manifest.json')}, 'components': {}}
        return archive, plan

    def test_all_component_packages_are_deterministic_and_namespaced(self):
        for component in ('app','agent','ai','worker'):
            with self.subTest(component=component):
                folder = self.payload(component)
                paths = prepare(component, TAG, COMMIT, folder, self.root / component)
                first = [sha256(p) for p in paths]
                paths2 = prepare(component, TAG, COMMIT, folder, self.root / (component + '-again'))
                self.assertEqual(first, [sha256(p) for p in paths2])
                data = json.loads(paths[1].read_text())
                self.assertEqual(data['component'], component)
                self.assertEqual(data['archive']['sha256'], sha256(paths[0]))

    def test_changed_source_or_tampered_bytes_are_rejected(self):
        folder = self.payload()
        with self.assertRaisesRegex(ValueError, 'manifest does not match'):
            prepare('app', TAG, 'b' * 40, folder, self.root / 'out')
        (folder / f'prodcast-backend-{TAG}-linux-amd64.tar.gz').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            prepare('app', TAG, COMMIT, folder, self.root / 'out')

    def test_unlisted_files_and_incomplete_checksums_are_rejected(self):
        folder = self.payload()
        extra = folder / 'site.env'
        extra.write_text('not for distribution')
        with self.assertRaisesRegex(ValueError, 'Unexpected files'):
            prepare('app', TAG, COMMIT, folder, self.root / 'out')
        extra.unlink()
        (folder / 'SHA256SUMS').write_text('')
        with self.assertRaisesRegex(ValueError, 'Incomplete checksum'):
            prepare('app', TAG, COMMIT, folder, self.root / 'out')

    def test_unsafe_zip_paths_and_duplicate_entries_are_rejected(self):
        for index, names in enumerate([['../secret'], ['/tmp/secret'], ['a/b'], ['same', 'same']]):
            archive = self.root / f'unsafe-{index}.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for name in names:
                    z.writestr(name, b'bad')
            with self.assertRaises(ValueError):
                unpack(archive, self.root / f'unsafe-{index}')

    def test_assembly_updates_app_and_preserves_other_components_and_manager(self):
        archive, plan = self.base()
        payload = self.payload()
        zip_path, descriptor = prepare('app', TAG, COMMIT, payload, self.root / 'contributions')
        plan['components']['app'] = {'descriptor': descriptor.name, 'sha256': sha256(descriptor)}
        out = self.root / 'assembled'
        complete = build(plan, archive, {'app': (descriptor, zip_path)}, out)
        result = json.loads((out / 'release-manifest.json').read_text())
        components = {c['component']: c for c in result['components']}
        self.assertEqual(components['app']['source_commit'], COMMIT)
        self.assertEqual(components['license']['reused_from'], 'v0.4')
        self.assertEqual(result['management']['schema'], 3)
        self.assertIn('v0.4', result['management']['upgrade_from'])
        self.assertFalse(result['production_accepted'])
        with zipfile.ZipFile(complete) as z:
            self.assertNotIn('prodcast-backend-v0.4-linux-amd64.tar.gz', z.namelist())
            self.assertIn('prodcast-backend-v0.5.0-linux-amd64.tar.gz', z.namelist())
            self.assertEqual(z.read('ProdCast-Manager-0.3.3.zip'), b'old-ProdCast-Manager-0.3.3.zip')
            self.assertEqual(z.read('prodcast-license-unchanged.tar.gz'), b'old-prodcast-license-unchanged.tar.gz')
            for item in result['artifacts']:
                if item.get('location') == 'complete':
                    data = z.read(item['name'])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
        verify_complete(out / 'release-manifest.json', complete, out / (complete.name + '.sha256'), sha256(out / 'release-manifest.json'))
        with self.assertRaisesRegex(ValueError, 'compatibility-approved'):
            verify_complete(out / 'release-manifest.json', complete, out / (complete.name + '.sha256'), 'f' * 64)

    def test_base_checksum_and_license_rebuild_are_rejected(self):
        archive, plan = self.base()
        bad = copy.deepcopy(plan)
        bad['base']['manifest_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Base manifest'):
            build(bad, archive, {}, self.root / 'bad')
        plan['components']['license'] = {}
        with self.assertRaisesRegex(ValueError, 'License is unchanged'):
            build(plan, archive, {}, self.root / 'license')

    def test_published_release_or_assembly_lock_blocks_contributions(self):
        with patch('publish_component.draft', side_effect=ValueError('Published releases are immutable')):
            with self.assertRaisesRegex(ValueError, 'immutable'):
                publish('v0.5.0', [])
        with patch('publish_component.draft', return_value={'assets': [{'name': 'assembly-lock.json'}]}):
            with self.assertRaisesRegex(ValueError, 'frozen'):
                publish('v0.5.0', [])

    def test_release_lookup_finds_drafts_on_later_pages(self):
        value = {'tag_name': 'v0.5.0', 'draft': True, 'assets': [], 'id': 12}
        with patch('release_common.gh', return_value=json.dumps([[{'tag_name': 'v0.4'}], [value]])):
            self.assertEqual(release('v0.5.0'), value)

    def test_release_lookup_rejects_duplicate_drafts(self):
        with patch('release_common.gh', return_value=json.dumps([[{'tag_name': 'v0.5.0'}], [{'tag_name': 'v0.5.0'}]])):
            with self.assertRaisesRegex(ValueError, 'Multiple releases'):
                release('v0.5.0')

    def test_missing_draft_is_not_created_by_component_builds(self):
        with patch('publish_component.draft', side_effect=RuntimeError('HTTP 404')), patch('publish_component.gh') as gh:
            with self.assertRaises(RuntimeError):
                publish('v0.5.0', [])
            gh.assert_not_called()

    def test_auth_errors_do_not_create_release(self):
        with patch('publish_component.draft', side_effect=RuntimeError('HTTP 403')), patch('publish_component.gh') as gh:
            with self.assertRaises(RuntimeError):
                publish('v0.5.0', [])
            gh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
