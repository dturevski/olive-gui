# -*- coding: utf-8 -*-

# system
import sys

# libs
import json
import jsonschema

# local
import model
from p2w.parser import parser
from yacpdb.storage import dao

LIST_COMMON_STIPULATIONS = ["=", "+", "= black to move", "+ black to move", "see text"]

def load_schema():
    with open("yacpdb/schemas/v1.0.json") as f:
        return json.load(f)

json_schema = load_schema()

def main():
    try:
        with open(sys.argv[1], 'r') as f:
            entry = json.load(f)
            print(json.dumps(validate(entry)))
    except Exception as e:
        print(json.dumps({'success': False, "errors": [str(e)]}))
        sys.exit(-1)


class StipulationError(Exception): pass

def validateStipulation(stip):
    stip = stip.lower()
    if stip in LIST_COMMON_STIPULATIONS:
        return
    matches = model.RE_COMMON_STIPULATION.match(stip)
    if not matches:
        raise StipulationError("Unrecognized stipulation. Accepted are: simple popeye stipulations, PG, '+/= [Black to move]' and 'See text'")
    if matches.group("aim") == "" and matches.group("play").lower() != "pg":
        raise StipulationError("Incorrect stipulation, no aim specified, but play type is not ProofGame'")


class SemanticValidationVisitor:

    def __init__(self): pass

    def visit(self, node, board): node.assertSemantics(board)


class DummyVisitor:

    def __init__(self):
        self.count = 0

    def visit(self, node, board):
        self.count += 1



def validate(entry, propagate_exceptions=True):

    try:
        jsonschema.validate(instance=entry, schema=json_schema)
        validateStipulation(entry["stipulation"])
        solution = parser.parse(entry["solution"], debug=0)
        b = model.Board()
        b.fromAlgebraic(entry["algebraic"])
        b.stm = b.getStmByStipulation(entry["stipulation"])
        solution.traverse(b, SemanticValidationVisitor())
    except (jsonschema.ValidationError, StipulationError) as ex:
        if propagate_exceptions:
            raise ex
        return {'success': False, "errors": [ex.message]}
    except Exception as ex:
        if propagate_exceptions:
            raise ex
        return {'success': False, "errors": [str(ex)]}

    return {'success': True, 'orthodox': not model.hasFairyElements(entry)}


def validateSchema(entries):
    for e in entries:
        entry_id = e['id']
        for key in ["id", "ash", "legend", "authors"]:
            e.pop(key, None)
        for key in ["source", "keywords", "comments", "options"]:
            if key in e and e[key] is None:
                e.pop(key, None)
        try:
            jsonschema.validate(instance=e, schema=json_schema)
        except jsonschema.ValidationError as ex:
            print(entry_id, ex.message)


if __name__ == '__main__':
    #main()
    validateSchema(dao.allEntries())