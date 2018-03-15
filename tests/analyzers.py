import base, unittest
import data, model, validate
import p2w.parser
import yacpdb.indexer.trajectories
import yacpdb.indexer.metadata
import yacpdb.indexer.predicate

predicateStorage = yacpdb.indexer.metadata.PredicateStorage('./')

class TestTrajectories(unittest.TestCase):

    def test_C2C(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['c2c']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn('CornerToCorner(wK)', str(resultsAccumulator.counts))

    def test_Pattern(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['doublealbino']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertEqual(resultsAccumulator.counts['PseudoAlbino(wP)'], 2)

    def test_TraceBack(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['longtraceback']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn("TraceBack(wB, 3, WithCaptures)", resultsAccumulator.counts)

    def test_CWalkAndCycle(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = data.problems['caillaudtempobishop']
        solution, b = self.prepare(e)
        yacpdb.indexer.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn("ClosedWalk(wB, 7, Captureless)", resultsAccumulator.counts)
        self.assertIn("LinearCycle(wB, 3, Captureless)", resultsAccumulator.counts)
        self.assertIn("TraceBack(bP, 1, Captureless)", resultsAccumulator.counts)

    def prepare(self, e):
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validate.DummyVisitor()) # assign origins
        return solution, b
