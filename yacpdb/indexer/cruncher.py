import datetime
import logging
import os
import sys

sys.path.insert(0, os.getcwd())

import model
import validate
import yacpdb.entry
import yacpdb.indexer.analyzers.hma
import yacpdb.indexer.analyzers.trajectories
import yacpdb.indexer.predicate
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
            print "%s: %s" % (e["id"], ash)
        else:
            pass
            # print str(e["id"]) + ": failed - " + "; ".join(r['errors'])
    print "tried: %d, succeeded: %d" % (tried, succeded)


def calculateOrthoGlobally():
    i = 0
    for e in dao.allEntries():
        dao.ixr_updateEntryOrtho(e["id"], not model.hasFairyElements(e))
        i += 1
        if i % 10000 == 0:
            print i


class Analyzer0:

    def __init__(self):
        self.workers = [
            yacpdb.indexer.analyzers.trajectories.Analyzer(),
            #yacpdb.indexer.hma.Analyzer()
        ]
        self.version = datetime.datetime(2018, 3, 14)

    def analyze(self, entry, solution, board, acc):
        rs = {}
        for worker in self.workers:
            for predicate in worker.analyze(entry, solution, board, acc):
                rs[predicate] = True
        return rs

    def runOne(self, entry):
        error = None
        try:
            predicateStorage = yacpdb.indexer.metadata.PredicateStorage('./')
            resultsAccumulator = yacpdb.indexer.predicate.AnalyzisResultAccumulator(predicateStorage)

            solution = parser.parse(entry["solution"], debug=0)
            board = model.Board()
            board.fromAlgebraic(entry["algebraic"])
            board.stm = board.getStmByStipulation(entry["stipulation"])
            rs = self.analyze(entry, solution, board, resultsAccumulator)
        except Exception as ex:
            error = str(ex)
        finally:
            dao.ixr_updateCruncherLog(entry["ash"], error)

    def runBatch(self, size):
        done = 0
        for entry in dao.ixr_getNeverChecked(size):
            self.runOne(entry)
            done += 1
        if done == size:
            return
        for entry in dao.ixr_getNotCheckedSince(self.version, size - done):
            self.runOne(entry)


def main():
    logging.basicConfig(filename='~/logs/cruncher.log', level=logging.DEBUG)
    os.nice(19)
    if "--calculate-ash-globally" in sys.argv:
        calculateAshGlobally()
    elif "--calculate-ortho-globally" in sys.argv:
        calculateOrthoGlobally()
    elif False:
        a0 = Analyzer0();
        a0.runBatch(1)

if __name__ == '__main__':
    main()
