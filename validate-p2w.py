# -*- coding: utf-8 -*-
import sys
import json
import base, model
from p2w.parser import parser

def main():
    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print json.dumps(validate(entry))
    except:
        die()


def die():
    print "{success: false}"
    sys.exit(-1)


def validate(entry):

    r = {'success': False, "errors": []}

    if not "solution" in entry or entry["solution"].strip() == "":
        r["errors"].append("No solution")
        return r

    if not "algebraic" in entry:
        r["errors"].append("No position")
        return r

    try:
        solution = parser.parse(entry["solution"], debug=0)
        b = model.Board()
        b.fromAlgebraic(entry["algebraic"])
        solution.validate(b)
    except Exception as e:
        r["errors"].append(unicode(e).encode("utf8"))
        return r

    return {'success': True}

if __name__ == '__main__':
    main()
