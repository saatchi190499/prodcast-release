import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from release_common import record, sha256, write_json
from retain_inputs import cleanup, stage


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, {'GITHUB_RUN_ID': '42'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.assembled = self.root / 'assembled'
        self.remote = self.root / 'remote'
        self.retained = self.root / 'retained'
        self.assembled.mkdir()
        self.remote.mkdir()
        plan = {'version': 'v0.6.0', 'components': {}}
        manifest = self.assembled / 'release-manifest.json'
        write_json(manifest, {'version': 'v0.6.0', 'assembly_source': plan})
        complete = self.assembled / 'ProdCast-v0.6.0-complete.zip'
        with zipfile.ZipFile(complete, 'w') as archive:
            archive.write(manifest, manifest.name)
        (self.assembled / (complete.name + '.sha256')).write_text(sha256(complete) + '  ' + complete.name + '\n')
        write_json(self.remote / 'assembly-lock.json', plan)
        for rc in (1, 2):
            stem = f'prodcast-app-v0.6.0-rc.{rc}-component'
            package = self.remote / (stem + '.zip')
            package.write_bytes(b'component-' + str(rc).encode())
            write_json(self.remote / (stem + '.json'), {'component': 'app', 'version': f'v0.6.0-rc.{rc}', 'archive': record(package)})
        # Unrelated packages and final files must never be cleanup candidates.
        (self.remote / 'ProdCast-Manager-0.3.3.zip').write_bytes(b'manager')
        self.assets = []
        for index, path in enumerate([manifest, complete, *self.remote.iterdir()]):
            self.assets.append({'id': index + 100, 'name': path.name, 'size': path.stat().st_size,
                                'state': 'uploaded', 'digest': 'sha256:' + sha256(path)})
        self.release = {'id': 7, 'draft': True, 'assets': self.assets}
        self.artifact = {'expired': False, 'name': 'release-inputs-v0.6.0',
                         'workflow_run': {'id': 42}, 'size_in_bytes': 500}
        self.draft = patch('retain_inputs.draft', return_value=self.release)
        self.draft.start()
        self.addCleanup(self.draft.stop)

    def download(self, tag, name, directory):
        path = Path(directory) / name
        path.write_bytes((self.remote / name).read_bytes())
        return path

    def prepare(self):
        with patch('retain_inputs.download', side_effect=self.download):
            return stage(self.assembled, self.retained)

    def test_all_rc_inputs_retained_then_only_archived_components_removed(self):
        plan = self.prepare()
        self.assertEqual(len(plan['inputs']), 4)
        self.assertTrue((self.retained / 'assembly-lock.json').exists())
        with patch('retain_inputs.gh', return_value=json.dumps(self.artifact)) as gh:
            cleanup(self.retained, 9)
            deleted = [c.args[-1] for c in gh.call_args_list if 'DELETE' in c.args]
        self.assertEqual(set(deleted), {f"repos/saatchi190499/prodcast-release/releases/assets/{i['id']}" for i in plan['inputs']})

    def test_missing_or_expired_or_unrelated_backup_blocks_all_deletes(self):
        self.prepare()
        variants = [{**self.artifact, 'expired': True}, {**self.artifact, 'workflow_run': {'id': 99}},
                    {**self.artifact, 'name': 'other'}, {**self.artifact, 'size_in_bytes': 0}]
        for artifact in variants:
            with patch('retain_inputs.gh', return_value=json.dumps(artifact)) as gh:
                with self.assertRaises(ValueError):
                    cleanup(self.retained, 9)
                self.assertFalse(any('DELETE' in c.args for c in gh.call_args_list))
        with patch('retain_inputs.gh', side_effect=RuntimeError('artifact not found')) as gh:
            with self.assertRaises(RuntimeError):
                cleanup(self.retained, 9)
            self.assertEqual(gh.call_count, 1)

    def test_changed_complete_blocks_all_deletes(self):
        self.prepare()
        self.assets[1]['digest'] = 'sha256:' + '0' * 64
        with patch('retain_inputs.gh', return_value=json.dumps(self.artifact)) as gh:
            with self.assertRaises(ValueError):
                cleanup(self.retained, 9)
            self.assertEqual(gh.call_count, 1)

    def test_local_input_tampering_blocks_all_deletes(self):
        plan = self.prepare()
        (self.retained / plan['inputs'][0]['name']).write_bytes(b'tampered')
        with patch('retain_inputs.gh', return_value=json.dumps(self.artifact)) as gh:
            with self.assertRaises(ValueError):
                cleanup(self.retained, 9)
            self.assertEqual(gh.call_count, 1)

    def test_missing_complete_prevents_staging(self):
        self.release['assets'] = [a for a in self.assets if 'complete.zip' not in a['name']]
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.retained.exists())

    def test_foreign_final_file_cannot_be_added_to_cleanup_targets(self):
        plan = self.prepare()
        plan['inputs'].append(plan['protected'][0])
        write_json(self.retained / 'cleanup-plan.json', plan)
        with patch('retain_inputs.gh', return_value=json.dumps(self.artifact)) as gh:
            with self.assertRaisesRegex(ValueError, 'non-component'):
                cleanup(self.retained, 9)
            self.assertEqual(gh.call_count, 1)


if __name__ == '__main__':
    unittest.main()
