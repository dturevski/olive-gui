"""Run with the installed wheel, from any directory, without the desktop tree."""
import copy
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CommonPackageTest(unittest.TestCase):
    def test_imports_are_independent_of_desktop_and_process_state(self):
        script = '''
import logging, os, sys
cwd, path, handlers = os.getcwd(), list(sys.path), list(logging.getLogger().handlers)
import yacpdb.board, yacpdb.model, yacpdb.validation
import yacpdb.indexer.metadata, yacpdb.indexer.ql, yacpdb.indexer.cruncher
assert os.getcwd() == cwd
assert sys.path == path
assert logging.getLogger().handlers == handlers
assert not ({'base', 'gui', 'model', 'board', 'PyQt5'} & sys.modules.keys())
assert not os.listdir(cwd), os.listdir(cwd)
'''
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, '-I', '-c', script], cwd=directory, check=True)

    def test_validation_and_cli_from_unrelated_directory(self):
        from yacpdb.validation import validate, validateEntity, load_schema
        entry = {'stipulation': '#1', 'solution': '1.Ka1-a2',
                 'algebraic': {'white': ['Ka1'], 'black': ['Kh8']},
                 'version-of': 4, 'after': 5, 'versionists': ['Versionist'],
                 'correctors': ['Corrector'], 'non-standard-stipulation': 'Last move?'}
        self.assertTrue(validate(entry)['success'])
        bad = copy.deepcopy(entry)
        del bad['version-of']
        self.assertFalse(validate(bad, propagate_exceptions=False)['success'])
        self.assertTrue(validateEntity('person', {'familyname': 'Person'})['success'])
        with self.assertRaises(ValueError):
            load_schema('../entry')
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / 'request.json'
            request.write_text(json.dumps(entry))
            result = subprocess.run([sys.executable, '-I', '-m', 'yacpdb.validation',
                                     '--validate', str(request)], cwd=directory,
                                    check=True, capture_output=True, text=True)
            self.assertTrue(json.loads(result.stdout)['success'])
            self.assertEqual('', result.stderr)
            self.assertEqual(['request.json'], os.listdir(directory))

    def test_query_resources_and_sql(self):
        from yacpdb.indexer.metadata import PredicateStorage
        from yacpdb.indexer import ql
        storage = PredicateStorage()
        self.assertTrue({'ContributorId', 'PublishedInId', 'EntityId'} <= storage.getDocumentation().keys())
        expr = ql.parser.parse('ContributorId(7) AND PublishedInId(8)', lexer=ql.lexer)
        expr.validate(storage)
        query = expr.sql(storage)
        self.assertIn("'corrector'", query.q)
        self.assertIn("'reprint'", query.q)

    def test_board_resources_and_legacy_input(self):
        from yacpdb.board import Board, FairyHelper
        from yacpdb.legacy.popeye import create_input
        board = Board()
        board.fromAlgebraic({'white': ['Ka1'], 'black': ['Kh8']})
        result = create_input({'stipulation': '#1'}, False, ['NoBoard'],
                              board.toPopeyePiecesClause(), FairyHelper.instance)
        self.assertIn('Stipulation #1', result)
        self.assertTrue(FairyHelper.instance.fontinfo)


if __name__ == '__main__':
    unittest.main()
