"""Run explicitly: python -m unittest tests.integration.orthodox_rebuild.

Creates and drops a unique fixture database; never updates the wiki database.
"""
import unittest
import uuid
from unittest.mock import patch

import pymysql
import yaml

from yacpdb import model
from yacpdb.indexer.cruncher import calculateOrthoGlobally
from yacpdb.storage import Connection


class OrthodoxRebuildTest(unittest.TestCase):
    def setUp(self):
        self.database = 'yacpdb_ortho_test_' + uuid.uuid4().hex
        self.admin = pymysql.connect(host='localhost', user='root', autocommit=True)
        self.addCleanup(self.admin.close)
        with self.admin.cursor() as cursor:
            cursor.execute('CREATE DATABASE `' + self.database + '`')
        self.addCleanup(self.drop_database)
        self.writer = pymysql.connect(host='localhost', user='root', database=self.database,
                                      cursorclass=pymysql.cursors.DictCursor)
        self.addCleanup(self.writer.close)
        with self.writer.cursor() as cursor:
            cursor.execute('CREATE TABLE problems2 (id INT PRIMARY KEY, orthodox BOOLEAN) ENGINE=InnoDB')
            cursor.execute('CREATE TABLE yaml (problem_id INT PRIMARY KEY, yaml TEXT) ENGINE=InnoDB')
            for eid, extra in ((4, {}), (5, {'neutral': ['Sc5']}), (6, {})):
                entry = {'algebraic': dict(white=['Kf5'], black=['Kg8'], **extra)}
                if eid == 6:
                    entry['options'] = ['KoeKo']
                cursor.execute('INSERT INTO problems2 VALUES (%s,%s)', (eid, eid == 5))
                cursor.execute('INSERT INTO yaml VALUES (%s,%s)', (eid, yaml.safe_dump(entry)))
        self.writer.commit()
        self.connection_patch = patch.object(Connection, 'instance', self.writer)
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)

    def drop_database(self):
        with self.admin.cursor() as cursor:
            cursor.execute('DROP DATABASE `' + self.database + '`')

    def persisted_flags(self):
        # A separate connection verifies committed data rather than writer state.
        with self.admin.cursor() as cursor:
            cursor.execute('SELECT orthodox FROM `' + self.database + '`.problems2 ORDER BY id')
            return [row[0] for row in cursor.fetchall()]

    def test_rebuild_commits_classification(self):
        calculateOrthoGlobally()
        self.assertEqual([1, 0, 0], self.persisted_flags())

    def test_failure_rolls_back_and_propagates(self):
        classify = model.hasFairyElements

        def fail_on_neutral(entry):
            if entry['algebraic'].get('neutral'):
                raise RuntimeError('fixture classification failure')
            return classify(entry)

        with patch.object(model, 'hasFairyElements', side_effect=fail_on_neutral):
            with self.assertRaisesRegex(RuntimeError, 'fixture classification failure'):
                calculateOrthoGlobally()
        # Committing later must not accidentally persist the first row's update.
        self.writer.commit()
        self.assertEqual([0, 1, 0], self.persisted_flags())


if __name__ == '__main__':
    unittest.main()
