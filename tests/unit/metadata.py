import sqlite3
import unittest
from pathlib import Path

from yacpdb.indexer import ql
from yacpdb.indexer.metadata import Author, PredicateStorage


class TestPersonPredicates(unittest.TestCase):

    def setUp(self):
        self.directory = str(Path(__file__).resolve().parents[2]) + '/'
        self.storage = PredicateStorage(self.directory)
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript('''
            CREATE TABLE problems2 (id INTEGER PRIMARY KEY);
            CREATE TABLE entities (entity_id INTEGER PRIMARY KEY, type TEXT, name TEXT);
            CREATE TABLE entities_to_problems (problem_id INTEGER, entity_id INTEGER, link_type TEXT);
            INSERT INTO problems2 VALUES (1), (2), (3), (4), (5), (6);
            INSERT INTO entities VALUES (1, 'person', 'Name'), (2, 'source', 'Name');
            INSERT INTO entities_to_problems VALUES
                (1, 1, 'author'), (2, 1, 'judge'), (3, 1, 'versionist'),
                (4, 1, 'corrector'), (5, 1, 'author'), (5, 1, 'judge'),
                (5, 1, 'versionist'), (5, 1, 'corrector'), (6, 2, 'source'),
                (6, 2, 'author');
        ''')

    def query(self, text):
        expr = ql.parser.parse(text, lexer=ql.lexer)
        expr.validate(self.storage)
        return expr.sql(self.storage)

    def matches(self, text):
        query = self.query(text)
        # SQLite exercises the generated membership expression and bound values;
        # only the DB-API placeholder spelling differs from MySQL.
        where = query.q.replace('%s', '?')
        rows = self.db.execute('SELECT p2.id FROM problems2 p2 WHERE ' + where,
                               query.ps).fetchall()
        count = self.db.execute('SELECT COUNT(*) FROM problems2 p2 WHERE ' + where,
                                query.ps).fetchone()[0]
        self.assertEqual(count, len(rows))
        return sorted(row[0] for row in rows)

    def test_roles_parse_and_validate(self):
        for role in ('author', 'judge', 'versionist', 'corrector',
                     'source', 'reprint', 'tourney', 'keyword'):
            with self.subTest(role=role):
                query = self.query("Entity('%s', 'Name')" % role)
                self.assertEqual(query.ps, ['Name', role])
        with self.assertRaises(ValueError):
            self.query("Entity('unknown', 'Name')")

    def test_author_matches_included_roles_once(self):
        for name in ('Name', 'Na%', 'N_me'):
            with self.subTest(name=name):
                self.assertEqual(self.matches("Author('%s')" % name), [1, 3, 4, 5])
        self.assertEqual(self.matches("Author('Missing')"), [])

    def test_judge_only_excluded_and_mixed_judge_author_included(self):
        matches = self.matches("Author('Name')")
        self.assertNotIn(2, matches)
        self.assertIn(5, matches)
        self.assertEqual(self.matches("Entity('judge', 'Name')"), [2, 5])

    def test_names_remain_bound_parameters(self):
        query = self.query('Author("Name\' OR 1=1 --%")')
        self.assertEqual(query.ps, ["Name' OR 1=1 --%"])
        self.assertNotIn(query.ps[0], query.q)
        self.assertEqual(query.q.count('%s'), 1)
        self.assertEqual(query.ts, [])
        self.assertEqual(query.preExecute, [])

    def test_entity_remains_role_specific(self):
        expected = {'author': [1, 5, 6], 'judge': [2, 5], 'versionist': [3, 5],
                    'corrector': [4, 5], 'source': [6]}
        for role, ids in expected.items():
            with self.subTest(role=role):
                self.assertEqual(self.matches("Entity('%s', 'Na%%')" % role), ids)

    def test_legacy_data_needs_no_new_roles(self):
        self.db.execute("DELETE FROM entities_to_problems WHERE link_type IN ('versionist', 'corrector')")
        self.assertEqual(self.matches("Author('Name')"), [1, 5])
        for role in ('versionist', 'corrector'):
            self.assertEqual(self.matches("Entity('%s', 'Name')" % role), [])

    def test_documentation_and_multiple_storage_instances(self):
        other = PredicateStorage(self.directory)
        for storage in (self.storage, other):
            docs = storage.getDocumentation()
            self.assertEqual(docs['Author']['declaration'], 'Author(STRING name)')
            self.assertEqual(docs['Entity']['declaration'], 'Entity(REFTYPE type, STRING name)')
            for role in ('author', 'versionist', 'corrector'):
                self.assertIn(role, docs['Author']['doc'])
                self.assertTrue(storage.ds['REFTYPE'].test(role))
            self.assertTrue(storage.ds['REFTYPE'].test('judge'))
            self.assertIn('Judge-only links do not match', docs['Author']['doc'])
            self.assertNotIn('any role', docs['Author']['doc'])
            self.assertIn('role-specific', docs['Entity']['doc'])
            self.assertNotIn('Same as', docs['Author']['doc'])
            self.assertIs(storage.get(1, 'Author').sql.__func__, Author.sql)
            self.assertIn('Author()', storage.getEditorTypeAheads())
        self.assertEqual(self.storage.getDocumentation(), other.getDocumentation())


if __name__ == '__main__':
    unittest.main()
