# -*- coding: utf-8 -*-

import base, unittest

import yacpdb.indexer.ql
import yacpdb.indexer.metadata
from yacpdb.storage import dao

stor = yacpdb.indexer.metadata.PredicateStorage('./')

class TestQl(unittest.TestCase):

    def test_MatrixEx(self):
        self.runYacpdbQuery("MatrixExtended('bKg3 wKc2', false, false, 'Mirror') AND Stip('#20')", 1) # >>100282

    def test_OrthodoxRules(self):
        self.runYacpdbQuery("NOT Fairy AND Fairy", 0)

    def test_With(self):
        self.runYacpdbQuery("Id(36411) AND With('wR wR wR')", 1)

    def test_PCount(self):
        self.runYacpdbQuery("PCount(w)=56", 1)

    def test_ExistingId(self):
        self.runYacpdbQuery("Id(26026)", 1)

    def test_NonExistingId(self):
        self.runYacpdbQuery("Id(1)", 0) # there's no such id

    def test_Or(self):
        self.runYacpdbQuery("Id(26026) or Id(4)", 2)

    def test_And(self):
        self.runYacpdbQuery("Id(26026) and not Id(26026)", 0)

    def test_Not(self):
        self.runYacpdbQuery("(Id(26026) or Id(4)) and not Id(4)", 1)

    def test_Date(self):
        rs = self.runYacpdbQuery("PublishedAfter('2017-09-11') and not PublishedAfter('2017-09-12') ", 1)

    def test_Unicode(self):
        rs = self.runYacpdbQuery("Id(26026)", 1)
        self.assertEqual(rs['entries'][0]['authors'][0], "Туревский, Дмитрий Евгеньевич")

    def test_Matrix(self):
        rs = self.runYacpdbQuery("Matrix('wKg3 bEQg1 bGg4')", 1)

    def test_Stip(self):
        rs = self.runYacpdbQuery("Stip('hs=8')", 1)

    def test_Text(self):
        rs = self.runYacpdbQuery("Text('%Предновогодняя%')", 1)

    def test_AuthorSourceStip(self):
        rs = self.runYacpdbQuery("Author('Туревский, Дмитрий Евгеньевич') and Source('Mat Plus') and Stip('#9')", 1)

    def test_EntityJudge(self):
        rs = self.runYacpdbQuery("Entity('judge', 'Стёпочкин, Анатолий Викторович') and Id(347014)", 1)

    def test_ReprintType(self):
        rs = self.runYacpdbQuery("ReprintType('newspaper') and Id(4)", 1)

    def test_GetPredicatesByAsh(self):
        dao.ixr_getPredicatesByAsh("3c4a9b80c8edec94e7f33fcd09960457")

    def runYacpdbQuery(self, query, expected_match_count):

        print("Running query: %s" % query)

        # parsing query to expression
        expr = yacpdb.indexer.ql.parser.parse(query, lexer=yacpdb.indexer.ql.lexer)
        # validating semantics
        expr.validate(stor)
        # converting expression to sql statements
        sql = expr.sql(stor)
        # exequting sql
        results = sql.execute(1)

        print("Got %d results" % len(results['entries']))

        if expected_match_count >= 0:
            self.assertEqual(len(results['entries']), expected_match_count)

        return results
