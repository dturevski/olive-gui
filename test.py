# -*- coding: utf-8 -*-
import sys
import yaml
import base, model
import p2w.parser
import p2w.lexer
import re
#import yacpdb.storage

import yacpdb.indexer.trajectories
import validate
import yacpdb.indexer.predicate
import yacpdb.indexer.ql
import yacpdb.indexer.metadata

from board import *

e = model.makeSafe(yaml.load("""---
algebraic:
  white: [Kc7, Qb2, Rg8, Sf2]
  black: [Kg2, Pg3, Pf4]
stipulation: "#3"
solution: |
  "1.Sf2-g4 + !
        1...Kg2-f1 {(g1)}
            2.Rg8-a8 threat:
                    3.Ra8-a1 #
        1...Kg2-h3
            2.Sg4-h2 !
                2...g3*h2
                    3.Qb2-h8 #
        1...Kg2-h1
            2.Qb2-h2 + !
                2...g3*h2
                    3.Sg4-f2 #
        1...Kg2-f3
            2.Qb2-c2 zugzwang.
                2...g3-g2
                    3.Qc2-d3 #"
"""))

solution = p2w.parser.parser.parse(e["solution"], debug=0, lexer=p2w.lexer.lexer)
b = model.Board()
b.fromAlgebraic(e["algebraic"])
b.stm = b.getStmByStipulation(e["stipulation"])
solution.traverse(b, validate.DummyVisitor()) # to assign origins

print yacpdb.indexer.trajectories.run(e, solution, b)

stor = yacpdb.indexer.metadata.PredicateStorage('./')

s = "Source(diagrammes) and Author(Туревский%) and DateAfter(1990) and (not DateAfter('1990-12-31')) and Id"
s = "Matrix('wKa1 bRb33')"
s = "Author('Bakcsi%') and not Author('Bakcsi%')"
x = yacpdb.indexer.ql.parser.parse(s, lexer=yacpdb.indexer.ql.lexer)

x.validate(stor)

query = x.sql(stor)
print query
print query.ps

