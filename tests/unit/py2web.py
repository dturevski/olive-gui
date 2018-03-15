import unittest

import model
import p2w
import tests.unit.data
import validate


class TestParser(unittest.TestCase):

    def test_CanParseOrthodox(self):
        e = tests.unit.data.problems['orthodox']
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validate.DummyVisitor()) # to assign origins
