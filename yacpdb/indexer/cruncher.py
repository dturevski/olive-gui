import datetime
import logging
import os
import sys
import traceback

sys.path.insert(0, os.getcwd())

import model
import validate
import yacpdb.entry
import yacpdb.indexer.analyzers.hma
import yacpdb.indexer.analyzers.trajectories
import yacpdb.indexer.analyzers.miscellaneous
import yacpdb.indexer.analyzers.hma
import yacpdb.indexer.predicate
import yacpdb.indexer.metadata
from p2w.parser import parser
from yacpdb.storage import dao


def calculateAshGlobally():
    tried, succeded = 0, 0
    for e in dao.ixr_getEntriesWithoutAsh(5000000):
        r = validate.validate(e, propagate_exceptions=False)
        tried += 1
        if r['success']:
            ash = yacpdb.entry.ash(e)
            dao.ixr_updateEntryAsh(e["id"], ash)
            succeded += 1
            print("%s: %s" % (e["id"], ash))
        else:
            pass
            # print str(e["id"]) + ": failed - " + "; ".join(r['errors'])
    print("tried: %d, succeeded: %d" % (tried, succeded))


def calculateOrthoGlobally():
    i = 0
    for e in dao.allEntries():
        dao.ixr_updateEntryOrtho(e["id"], not model.hasFairyElements(e))
        i += 1
        if i % 10000 == 0:
            print(i)


def crunch(count):
    predicateStorage = yacpdb.indexer.metadata.PredicateStorage('./')
    a0 = Analyzer0(["trajectories", "miscellaneous"], predicateStorage)
    a0.runBatch(count)


class Analyzer0:

    def __init__(self, workernames, pstor):
        self.workers, self.pstor = [], pstor
        if "trajectories" in workernames:
            self.workers.append(yacpdb.indexer.analyzers.trajectories.Analyzer())
        if "miscellaneous" in workernames:
            self.workers.append(yacpdb.indexer.analyzers.miscellaneous.Analyzer())
        if "hma" in workernames:
            self.workers.append(yacpdb.indexer.analyzers.hma.Analyzer())

        self.version = datetime.datetime(2018, 4, 4)

    def analyze(self, entry, solution, board, acc):
        for worker in self.workers:
            worker.analyze(entry, solution, board, acc)

    def runOne(self, entry):
        resultsAccumulator = yacpdb.indexer.predicate.AnalysisResultAccumulator(self.pstor)
        for k in ["solution", "stipulation", "algebraic"]:
            if k not in entry:
                raise Exception("No %s" % k)
        visitor = validate.DummyVisitor()
        try:
            solution = parser.parse(entry["solution"], debug=0)
            board = model.Board()
            board.fromAlgebraic(entry["algebraic"])
            board.stm = board.getStmByStipulation(entry["stipulation"])
            solution.traverse(board, visitor) # assign origins
            solution.size = visitor.count
        except Exception:
            raise RuntimeError("invalid solution")

        print(entry["id"], solution.size)

        if solution.size > 140:
            raise RuntimeError("solution too long")

        self.analyze(entry, solution, board, resultsAccumulator)

        return resultsAccumulator

    def runOneAndSave(self, entry):
        try:
            analysisResults = self.runOne(entry)
            dao.ixr_deleteAnalysisResults(entry["ash"])
            dao.ixr_saveAnalysisResults(entry["ash"], analysisResults)
            dao.ixr_updateCruncherLog(entry["ash"], None)
        except RuntimeError as rerr:
            dao.ixr_updateCruncherLog(entry["ash"], str(rerr))
        except Exception as ex:
            print(traceback.format_exc(ex))
            dao.ixr_updateCruncherLog(entry["ash"], str(ex))

    def runBatch(self, size):
        done = 0
        for entry in dao.ixr_getNeverChecked(size):
            self.runOneAndSave(entry)
            done += 1
        if done == size:
            return
        for entry in dao.ixr_getNotCheckedSince(self.version, size - done):
            self.runOneAndSave(entry)


def main():
    logging.basicConfig(filename='~/logs/cruncher.log', level=logging.DEBUG)
    os.nice(19)
    if "--crunch" in sys.argv:
        print("started", datetime.datetime.now())
        crunch(1000)
        print("finished", datetime.datetime.now())
    elif "--calculate-ash-globally" in sys.argv:
        calculateAshGlobally()
    elif "--calculate-ortho-globally" in sys.argv:
        calculateOrthoGlobally()
    elif False:
        a0 = Analyzer0();
        a0.runBatch(1)

if __name__ == '__main__':
    main()
