import logging
import sys
import datetime
import os
import argparse

from yacpdb.storage import dao
import yacpdb.entry
import validate
import model
from p2w.parser import parser
import yacpdb.indexer.predicate

import yacpdb.indexer.hma
import yacpdb.indexer.trajectories


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


class Analyzer0:

    def __init__(self):
        self.workers = [
            yacpdb.indexer.trajectories.Analyzer(),
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

def parseCla():
    parser = argparse.ArgumentParser(description='Crunch yacpdb entries through analyzers, save results.')
    parser.add_argument("-c", "--calculate-ash-globally")
    parser.add_argument("-m", "--max-count", type=int, default=10)
    return parser.parse_args(sys.argv)

def main():
    logging.basicConfig(filename='~/logs/cruncher.log', level=logging.DEBUG)
    os.nice(19)
    params = parseCla()
    if params.c:
        calculateAshGlobally()
    else:
        a0 = Analyzer0();
        a0.runBatch(params.m)

if __name__ == '__main__':
    main()
