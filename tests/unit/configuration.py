import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from conf import Conf


class ConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.saved = copy.deepcopy(Conf.__dict__.get('_snapshots', {}))
        self.original = {key: getattr(Conf, key, None)
                         for key in ('file', 'popeye_file', 'chest_file',
                                     'values', 'popeye', 'chest')}
        self.addCleanup(self.restore)
        for name, attr, filename in [('values', 'file', 'main.yaml'),
                                     ('popeye', 'popeye_file', 'popeye.yaml'),
                                     ('chest', 'chest_file', 'chest.yaml')]:
            path = Path(self.directory.name) / filename
            data = yaml.safe_load((Path('conf/dist') / filename).read_text(encoding='utf8'))
            path.write_bytes(Conf.dump(data))
            setattr(Conf, attr, str(path))
            setattr(Conf, name, copy.deepcopy(data))
        Conf._snapshots = {name: copy.deepcopy(getattr(Conf, name))
                           for name in Conf.editable_files()}

    def restore(self):
        for key, value in self.original.items():
            setattr(Conf, key, value)
        Conf._snapshots = self.saved

    def edit(self, name, **updates):
        path = Path(Conf.editable_files()[name])
        data = yaml.safe_load(path.read_bytes())
        data.update(updates)
        path.write_bytes(Conf.dump(data))

    def test_external_conflict_wins_and_unrelated_gui_edit_survives(self):
        Conf.popeye['memory'] = 2048
        Conf.popeye['path'] = 'gui.exe'
        self.edit('popeye', path='external.exe')
        changed, _ = Conf.reload('popeye')
        self.assertTrue(changed)
        self.assertEqual(2048, Conf.popeye['memory'])
        self.assertEqual('external.exe', Conf.popeye['path'])
        self.assertEqual([], Conf.write())
        disk = yaml.safe_load(Path(Conf.popeye_file).read_bytes())
        self.assertEqual(Conf.popeye, disk)

    def test_close_merges_edit_before_watcher_runs(self):
        Conf.chest['options'] = '-gui'
        self.edit('chest', path='external.exe')
        self.assertEqual([], Conf.write())
        self.assertEqual({'path': 'external.exe', 'options': '-gui'},
                         yaml.safe_load(Path(Conf.chest_file).read_bytes()))

    def test_unchanged_file_preserves_comments_and_mtime(self):
        path = Path(Conf.file)
        path.write_bytes(b'# keep my comment\n' + path.read_bytes())
        raw, mtime = path.read_bytes(), path.stat().st_mtime_ns
        self.assertEqual([], Conf.write())
        self.assertEqual(raw, path.read_bytes())
        self.assertEqual(mtime, path.stat().st_mtime_ns)

    def test_invalid_files_are_not_applied_or_overwritten(self):
        for content in (b'path: [', b'', b'[]', b'path: x\noptions: 123'):
            with self.subTest(content=content):
                path = Path(Conf.chest_file)
                path.write_bytes(content)
                previous = copy.deepcopy(Conf.chest)
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    Conf.reload('chest')
                self.assertEqual(previous, Conf.chest)
                self.assertEqual(1, len(Conf.write()))
                self.assertEqual(content, path.read_bytes())

    def test_invalid_shape_retains_snapshot_until_fixed(self):
        before = copy.deepcopy(Conf._snapshots['values'])
        self.edit('values', **{'fairy-zoo': [['bad']]})
        with self.assertRaises(ValueError):
            Conf.reload('values')
        self.assertEqual(before, Conf._snapshots['values'])
        Path(Conf.file).write_bytes(Conf.dump(before))
        self.edit('values', **{'font-size': 30})
        self.assertTrue(Conf.reload('values')[0])
        self.assertEqual(30, Conf.values['font-size'])

    def test_nested_merge_and_deletions(self):
        self.assertEqual({'nested': {'a': 3, 'b': 4}}, Conf.merge(
            {'nested': {'a': 1, 'b': 2}, 'removed': 1},
            {'nested': {'a': 3, 'b': 2}, 'removed': 2},
            {'nested': {'a': 1, 'b': 4}}))

    def test_missing_file_is_not_recreated_at_shutdown(self):
        path = Path(Conf.chest_file)
        path.unlink()
        Conf.chest['path'] = 'gui.exe'
        self.assertEqual(1, len(Conf.write()))
        self.assertFalse(path.exists())

    def test_ui_validation_failure_preserves_file_and_running_state(self):
        previous = copy.deepcopy(Conf.values)
        self.edit('values', **{'default-lang': 'missing', 'languages': {'missing': 'Missing'}})
        raw = Path(Conf.file).read_bytes()

        def validate(name, values):
            if name == 'values':
                raise ValueError('Translation unavailable')

        self.assertEqual(1, len(Conf.write(validate)))
        self.assertEqual(previous, Conf.values)
        self.assertEqual(raw, Path(Conf.file).read_bytes())

    def test_invalid_scalar_settings(self):
        for name, key, value in [('popeye', 'memory', True),
                                 ('popeye', 'memory', -1),
                                 ('popeye', 'sticky-options', [42]),
                                 ('values', 'font-size', 'large'),
                                 ('values', 'notations', {'en': []}),
                                 ('values', 'popeye-toolbar-options', [None])]:
            with self.subTest(name=name, key=key):
                data = copy.deepcopy(getattr(Conf, name))
                data[key] = value
                with self.assertRaises(ValueError):
                    Conf.validate(name, data)

    def test_failed_replace_preserves_original_and_cleans_temporary(self):
        Conf.chest['options'] = '-gui'
        raw = Path(Conf.chest_file).read_bytes()
        with patch('conf.os.replace', side_effect=PermissionError('locked')):
            self.assertEqual(1, len(Conf.write()))
        self.assertEqual(raw, Path(Conf.chest_file).read_bytes())
        self.assertEqual(3, len(os.listdir(self.directory.name)))


if __name__ == '__main__':
    unittest.main()
