import unittest

import model
import p2w
import tests.unit.data
import validate


class TestParser(unittest.TestCase):

    def validate(self, key, validator):
        e = tests.unit.data.problems[key]
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validator)

    def test_CanParseOrthodox(self):
        self.validate('orthodox', validate.DummyVisitor())

    def test_CastlingInRotationTwin(self):
        self.validate('rotateandcastle', validate.SemanticValidationVisitor())

    def test_RebirthAtArrivalNotAllowed(self):
        try:
            self.validate('rebirthatarrival', validate.SemanticValidationVisitor())
        except Exception as ex:
            self.assertIn("rebirth at arrival", str(ex).lower())
        else:
            self.assertTrue(False, "Should throw semantic validation error")

    def test_AnticirceRebirth(self):
        self.validate('simple_anticirce', validate.SemanticValidationVisitor())

