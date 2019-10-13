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

    def test_CastlingInRotationTwin(self):
        e = tests.unit.data.problems['rotateandcastle']
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validate.SemanticValidationVisitor())

    def test_RebirthAtArrivalNotAllowed(self):
        try:
            e = tests.unit.data.problems['rebirthatarrival']
            p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
            solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
            b = model.Board()
            b.fromAlgebraic(e["algebraic"])
            b.stm = b.getStmByStipulation(e["stipulation"])
            solution.traverse(b, validate.SemanticValidationVisitor())
        except Exception as ex:
            self.assertIn("rebirth at arrival", str(ex).lower())
        else:
            self.assertTrue(False, "Should throw semantic validation error")
