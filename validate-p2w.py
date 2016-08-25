# -*- coding: utf-8 -*-
import sys
import json
import base, model
from p2w.parser import parser
import re

RE_COMMON_STIPULATION = re.compile('^(?P<play>ser-h|h|s|r|hs|)(?P<aim>[#=])(?P<length>[0-9\.]+)$', re.IGNORECASE)

def main():
    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print json.dumps(validate(entry))
    except Exception as e:
        print json.dumps({'success': False, "errors": [str(e)]})
        sys.exit(-1)



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

    try:
        solution = parser.parse(entry["solution"], debug=0)
        b = model.Board()
        b.fromAlgebraic(entry["algebraic"])
        b.stm = stm(entry["stipulation"])
        #raise Exception(b.stm)
        solution.validate(b)
    except Exception as e:
        r["errors"].append(unicode(e).encode("utf8"))
        return r

    return {'success': True}

def stm(stipulation):
    matches = RE_COMMON_STIPULATION.match(stipulation.lower())
    if not matches:
        return 'white'
    if matches.group('play') == "h":
        return "black"
    elif matches.group('play') == "ser-h":
        return "black"
    else:
        return "white"

if __name__ == '__main__':
    main()
