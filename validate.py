# -*- coding: utf-8 -*-
import sys
import json
from . import base, model
from .p2w.parser import parser
import re
#import yacpdb.storage

LIST_COMMON_STIPULATIONS = ["=", "+", "= black to move", "+ black to move", "see text"]

def main():
    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print(json.dumps(validate(entry)))
    except Exception as e:
        print(json.dumps({'success': False, "errors": [str(e)]}))
        sys.exit(-1)

def validateStipulation(stip, r):
    stip = stip.lower()
    if stip in LIST_COMMON_STIPULATIONS:
        return True
    matches = model.RE_COMMON_STIPULATION.match(stip)
    if not matches:
        r['errors'].append("Unrecognized stipulation. Accepted are: simple popeye stipulations, PG, '+/= [Black to move]' and 'See text'")
        return False
    if matches.group("aim") == "" and matches.group("play").lower() != "pg":
        r['errors'].append("Incorrect stipulation, no aim specified, but play type is not ProofGame")
        return False
    return True


class SemanticValidationVisitor:

    def __init__(self): pass

    def visit(self, node, board): node.assertSemantics(board)


class DummyVisitor:

    def __init__(self):
        self.count = 0

    def visit(self, node, board):
        self.count += 1



def validate(entry, propagate_exceptions=True):

    r = {'success': False, "errors": []}

    if not "solution" in entry or entry["solution"].strip() == "":
        r["errors"].append("No solution")
        return r

    if not "algebraic" in entry:
        r["errors"].append("No position")
        return r

    if not "stipulation" in entry:
        r["errors"].append("No stipulation")
        return r

    if not validateStipulation(entry["stipulation"], r):
        return r

    try:
        solution = parser.parse(entry["solution"], debug=0)
        b = model.Board()
        b.fromAlgebraic(entry["algebraic"])
        b.stm = b.getStmByStipulation(entry["stipulation"])
        solution.traverse(b, SemanticValidationVisitor())
    except Exception as ex:
        if propagate_exceptions:
            raise ex
        r["errors"].append(str(ex))
        return r

    return {'success': True, 'orthodox': not model.hasFairyElements(entry)}


if __name__ == '__main__':
    main()
    #validateAll(yacpdb.storage.queryProblems())