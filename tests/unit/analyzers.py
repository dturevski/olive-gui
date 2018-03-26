import unittest

import model
import p2w.parser
import tests.unit.data
import validate
import yacpdb.indexer.analyzers.trajectories
import yacpdb.indexer.metadata
import yacpdb.indexer.predicate

predicateStorage = yacpdb.indexer.metadata.PredicateStorage('./')

class TestTrajectories(unittest.TestCase):

    def prepare(self, e):
        solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
        b = model.Board()
        b.fromAlgebraic(e["algebraic"])
        b.stm = b.getStmByStipulation(e["stipulation"])
        solution.traverse(b, validate.DummyVisitor()) # assign origins
        return solution, b

    def test_CWalkAndCycle(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['caillaudtempobishop']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn("ClosedWalk(wB, 7, Captureless)", resultsAccumulator.counts)
        self.assertIn("LinearCycle(wB, 3, Captureless)", resultsAccumulator.counts)
        self.assertIn("TraceBack(bP, 1, Captureless)", resultsAccumulator.counts)


    def test_PW(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['pw']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn('PW(3)', str(resultsAccumulator.counts))
        self.assertEqual(3, resultsAccumulator.counts["PWPiece(nQ)"])

        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['pw2']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn('PW(2)', str(resultsAccumulator.counts))
        self.assertIn('PWPiece(wK)', str(resultsAccumulator.counts))
        self.assertIn('PWPiece(wR)', str(resultsAccumulator.counts))

    def test_C2C(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['c2c']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn('CornerToCorner(wK)', str(resultsAccumulator.counts))

    def test_Pattern(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['doublealbino']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertEqual(resultsAccumulator.counts['PseudoAlbino(wP)'], 2)

    def test_TraceBack(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['longtraceback']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn("TraceBack(wB, 3, true)", resultsAccumulator.counts)

    def test_CWalkAndCycle(self):
        resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)
        e = tests.unit.data.problems['caillaudtempobishop']
        solution, b = self.prepare(e)
        yacpdb.indexer.analyzers.trajectories.Analyzer().analyze(e, solution, b, resultsAccumulator)
        self.assertIn("ClosedWalk(wB, 7, false)", resultsAccumulator.counts)
        self.assertIn("LinearCycle(wB, 3, false)", resultsAccumulator.counts)
        self.assertIn("TraceBack(bP, 1, false)", resultsAccumulator.counts)
    """
    """
