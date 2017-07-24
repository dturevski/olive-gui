# -*- coding: utf-8 -*-
import sys
import json
import base, model
from p2w.parser import parser
import re
#import yacpdb.storage

LIST_COMMON_STIPULATIONS = ["=", "+", "= black to move", "+ black to move", "see text"]

def main():
    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print json.dumps(validate(entry))
    except Exception as e:
        print json.dumps({'success': False, "errors": [unicode(e)]})
        sys.exit(-1)

def validateStipulation(stip, r):
    stip = stip.lower()
    matches = model.RE_COMMON_STIPULATION.match(stip)
    if not matches and not stip in LIST_COMMON_STIPULATIONS:
        r['errors'].append("Unrecognized stipulation. Accepted are: simple popeye stipulations, PG, '+/= [Black to move]' and 'See text'")
        return False
    return True


class SemanticValidationVisitor:

    def __init__(self): pass

    def visit(self, node, board): node.assertSemantics(board)


class DummyVisitor:

    def __init__(self): pass

    def visit(self, node, board): pass



def validate(entry):

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

    solution = parser.parse(entry["solution"], debug=0)
    b = model.Board()
    b.fromAlgebraic(entry["algebraic"])
    b.stm = b.getStmByStipulation(entry["stipulation"])
    solution.traverse(b, SemanticValidationVisitor())

    return {'success': True}



def validateAll(iterator):
    for id, ash, e in iterator:
        print id,
        e = model.makeSafe(e)
        valid, message = 0, ""
        try:
            r = validate(e)
            if r["success"]:
                valid = 1
            else:
                message = r["errors"][0][:15]
        except Exception as e:
            message = str(e)
        print ash, valid, message
        yacpdb.storage.insertAuto(ash, valid, message)


if __name__ == '__main__':
    main()
    #validateAll(yacpdb.storage.queryProblems())