# -*- coding: utf-8 -*-
import sys
import json
import base, model
from p2w.parser import parser
import re
import yacpdb.storage

RE_COMMON_STIPULATION = re.compile('^(?P<intro>[0-9]+->)?(?P<serial>ser-)?(?P<play>h|s|r|hs|pg|)(?P<aim>[#=])(?P<length>[0-9\.]+)$', re.IGNORECASE)
LIST_COMMON_STIPULATIONS = ["=", "+", "= black to move", "+ black to move", "see text"]

def main():
#    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print json.dumps(validate(entry))
#    except Exception as e:
#        print json.dumps({'success': False, "errors": [str(e)]})
#        sys.exit(-1)

def validateStipulation(stip, r):
    stip = stip.lower()
    matches = RE_COMMON_STIPULATION.match(stip)
    if not matches and not stip in LIST_COMMON_STIPULATIONS:
        r['errors'].append("Unrecognized stipulation. Accepted are: simple popeye stipulations, PG, '+/= [Black to move]' and 'See text'")
        return False
    return True

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
    b.stm = stm(entry["stipulation"])
    solution.validate(b)

    return {'success': True}

def stm(stipulation):
    if stipulation.lower in ["= black to move", "+ black to move"]:
        return "black"
    matches = RE_COMMON_STIPULATION.match(stipulation.lower())
    if not matches:
        return 'white'
    if matches.group('serial') == 'ser-' and matches.group("play") == "hs":
        return "black" # it even has some sense :)
    if matches.group('play') == "h":
        return "black"
    else:
        return "white"

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