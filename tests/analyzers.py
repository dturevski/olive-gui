import base, unittest
import data, model, validate
import p2w.parser
import yacpdb.indexer.trajectories
import yacpdb.indexer.metadata
import yacpdb.indexer.predicate

predicateStorage = yacpdb.indexer.metadata.PredicateStorage('./')

class TestParser(unittest.TestCase):

    def est_C2C(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['c2c']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertTrue(str(resultsAccumulator) == 'CornerToCorner(wB): 1')

    def test_SwitchBack(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['switchbacks']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        print resultsAccumulator


    def prepare(self, e):
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validate.DummyVisitor()) # assign origins
        return solution, b
