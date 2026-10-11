import sqlite3
import unittest
from pathlib import Path

from yacpdb.indexer import ql
from yacpdb.indexer.metadata import Author, PredicateStorage


class MetadataQueryTestCase(unittest.TestCase):

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


class TestPersonPredicates(MetadataQueryTestCase):

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


class TestEntityIdPredicates(MetadataQueryTestCase):

    def setUp(self):
        super().setUp()
        # These names cannot be represented literally by the query language's
        # quoted name strings and would have special meaning in LIKE patterns.
        special_name = "Both '\" quotes %_\\ name"
        self.db.executemany('INSERT INTO entities VALUES (?, ?, ?)', [
            (3, 'person', special_name), (4, 'source', special_name),
            (5, 'keyword', special_name), (6, 'tourney', special_name)])
        self.db.executemany('INSERT INTO entities_to_problems VALUES (?, ?, ?)', [
            (1, 3, 'author'), (3, 3, 'author'), (5, 3, 'author'),
            (1, 4, 'source'), (3, 4, 'reprint'),
            (5, 4, 'source'), (5, 4, 'reprint'),
            (1, 5, 'keyword'), (3, 5, 'keyword'), (5, 5, 'keyword'),
            (4, 6, 'tourney'), (2, 1, 'source')])

    def test_entity_id_searches_every_supported_role(self):
        cases = [('author', 1, [1, 5]), ('judge', 1, [2, 5]),
                 ('versionist', 1, [3, 5]), ('corrector', 1, [4, 5]),
                 ('source', 4, [1, 5]), ('reprint', 4, [3, 5]),
                 ('tourney', 6, [4]), ('keyword', 5, [1, 3, 5])]
        for role, entity_id, expected in cases:
            with self.subTest(role=role):
                self.assertEqual(self.matches("EntityId('%s', %d)" % (role, entity_id)), expected)
        self.assertEqual(self.matches("EntityId('author', 999)"), [])

    def test_contributor_id_creative_roles_type_and_duplicates(self):
        self.assertEqual(self.matches('ContributorId(1)'), [1, 3, 4, 5])
        self.assertEqual(self.matches('ContributorId(3)'), [1, 3, 5])
        self.assertEqual(self.matches('ContributorId(2)'), [])
        self.assertEqual(self.matches('ContributorId(999)'), [])
        self.assertEqual(self.matches("EntityId('judge', 1)"), [2, 5])

    def test_entity_id_membership_does_not_duplicate_matching_links(self):
        self.db.execute("INSERT INTO entities_to_problems VALUES (5, 1, 'author')")
        self.assertEqual(self.matches("EntityId('author', 1)"), [1, 5])

    def test_published_in_id_source_reprint_type_and_duplicates(self):
        self.assertEqual(self.matches('PublishedInId(4)'), [1, 3, 5])
        self.assertEqual(self.matches('PublishedInId(2)'), [6])
        self.assertEqual(self.matches('PublishedInId(1)'), [])
        self.assertEqual(self.matches('PublishedInId(999)'), [])

    def test_invalid_and_wildcard_ids_and_roles_are_rejected(self):
        for declaration in ("EntityId('author', %s)", 'ContributorId(%s)', 'PublishedInId(%s)'):
            for value in ("'*'", '*', '0', '-1', "'1.5'", "'invalid'", "'1 OR 1=1'", "'1\n'"):
                text = declaration % value
                with self.subTest(query=text), self.assertRaises(ValueError):
                    self.query(text)
        for role in ('*', 'unknown', 'author-extra', 'extra-keyword', 'author\n'):
            with self.subTest(role=role), self.assertRaises(ValueError):
                self.query("EntityId('%s', 1)" % role)

    def test_exact_ids_do_not_depend_on_names_or_patterns(self):
        before = {text: self.matches(text) for text in (
            'ContributorId(3)', 'PublishedInId(4)', "EntityId('keyword', 5)")}
        self.db.execute("UPDATE entities SET name='Unrelated name'")
        for text, expected in before.items():
            self.assertEqual(self.matches(text), expected)
            query = self.query(text)
            self.assertNotIn('name', query.q)
            self.assertNotIn('like', query.q.lower())

    def test_ids_and_roles_are_bound_parameters(self):
        for text, parameters in (("EntityId('keyword', '005')", ['keyword', 5]),
                                 ('ContributorId(3)', [3]), ('PublishedInId(4)', [4])):
            with self.subTest(query=text):
                query = self.query(text)
                self.assertEqual(query.ps, parameters)
                self.assertEqual(query.q.count('%s'), len(parameters))
                self.assertEqual(query.ts, [])
                self.assertEqual(query.preExecute, [])

    @staticmethod
    def role_union(roles, entity_id):
        return '(' + ' OR '.join("EntityId('%s', %d)" % (role, entity_id) for role in roles) + ')'

    def test_pairwise_shortcuts_agree_with_explicit_role_unions(self):
        person1 = self.role_union(('author', 'versionist', 'corrector'), 1)
        person3 = self.role_union(('author', 'versionist', 'corrector'), 3)
        source4 = self.role_union(('source', 'reprint'), 4)
        keyword5 = "EntityId('keyword', 5)"
        cases = [('ContributorId(1) AND ContributorId(3)', person1 + ' AND ' + person3),
                 ('ContributorId(1) AND PublishedInId(4)', person1 + ' AND ' + source4),
                 ('ContributorId(1) AND ' + keyword5, person1 + ' AND ' + keyword5),
                 ('PublishedInId(4) AND ContributorId(1)', source4 + ' AND ' + person1)]
        for shortcut, explicit in cases:
            with self.subTest(query=shortcut):
                self.assertEqual(self.matches(shortcut), [1, 3, 5])
                self.assertEqual(self.matches(shortcut), self.matches(explicit))

    def test_legacy_roles_remain_searchable(self):
        self.db.execute("DELETE FROM entities_to_problems WHERE link_type IN ('versionist', 'corrector')")
        self.assertEqual(self.matches('ContributorId(1)'), [1, 5])
        self.assertEqual(self.matches('PublishedInId(4)'), [1, 3, 5])
        self.assertEqual(self.matches("EntityId('judge', 1)"), [2, 5])
        self.assertEqual(self.matches("EntityId('versionist', 1)"), [])
        self.assertEqual(self.matches("EntityId('corrector', 1)"), [])

    def test_documentation_and_typeaheads_need_no_registration(self):
        for storage in (self.storage, PredicateStorage(self.directory)):
            docs = storage.getDocumentation()
            declarations = {'EntityId': 'EntityId(REFTYPE role, INTEGER id)',
                            'ContributorId': 'ContributorId(INTEGER id)',
                            'PublishedInId': 'PublishedInId(INTEGER id)'}
            for name, declaration in declarations.items():
                self.assertEqual(docs[name]['declaration'], declaration)
                self.assertIn(name + '()', storage.getEditorTypeAheads())
                self.assertIn('positive integer', docs[name]['doc'])
                self.assertIn('wildcards', docs[name]['doc'])
                self.assertIn('once', docs[name]['doc'])
            self.assertIn('judge', docs['EntityId']['doc'])
            self.assertIn('transliterations', docs['EntityId']['doc'])
            for role in ('author', 'versionist', 'corrector'):
                self.assertIn(role, docs['ContributorId']['doc'])
            self.assertIn('Judge-only', docs['ContributorId']['doc'])
            for role in ('source', 'reprint'):
                self.assertIn(role, docs['PublishedInId']['doc'])


if __name__ == '__main__':
    unittest.main()
