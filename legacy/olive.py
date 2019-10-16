#import re, yaml, os, subprocess, tempfile, array, copy, sys

import yaml
from . import yacpdb

# todo:
# - dual underpromotions Q+R Q+B


problem = yaml.load("""---
    authors:
      - Ferrarini, A.
    source-id: 16/593 (corr.)
    date: 1970-05
    algebraic:
      white: [Ke2, Bb8, Sa7, Pf3]
      black: [Kf5, Ra5, Bf4]
    stipulation: "h#3"
    twins:
      b: Remove a7
    solution: |
      a) 1.Bc7 Sb5  2.Kf4 Sxc7  3.Rf5 Se6#
      b) 1.Bg5 Ba7  2.Kf4 Bg1  3.Rf5 Bh2#
    comments:
      - Correction by the author in the same magazine.
      - Indefinite first name. This problem may be by Angelo or by Alberto.""")


problem = yaml.load("""---
    ash: 1b53f979b446601600a999c07030e257
    authors:
      - Ferrarini, A.
    source-id: 16/593 (corr.)
    date: 1970-05
    algebraic:
      white: [Ke2, Bb8, Sa7, Pf3]
      black: [Kf5, Ra5, Bf4]
    stipulation: "h#3"
    twins:
      b: Remove a7
    solution: |
      a) 1.Bc7 Sb5  2.Kf4 Sxc7  3.Rf5 Se6#
      b) 1.Bg5 Ba7  2.Kf4 Bg1  3.Rf5 Bh2#
    comments:
      - Correction by the author in the same magazine.
      - Indefinite first name. This problem may be by Angelo or by Alberto.""")


problem = yaml.load("""---
    ash: ebbd14c5b1875f291c2289f4d52770c2
    algebraic:
      white: [Ka3, Rg4, Pe2, Pb2]
      black: [Kc5, Sg1]
    stipulation: "h#3"
    twins:
      b: PolishType
""")
problem = yaml.load("""---
    ash: ebbd14c5b1875f291c2289f4d52770c2
    algebraic:
      white: [Kf4, Qg4, Rd1, Rc2, Pc6, Pb7]
      black: [Kc7]
    stipulation: "#2"
""")

problem = yaml.load("""---
    ash: 14af7da3a1e7e0e36af1095378977c86
    algebraic:
      white: [Ka5, Bf3, Se2, Pf4, Pc2]
      black: [Kc4, Pf7, Pf5, Pd7, Pc5, Pa6]
    stipulation: "#4"
""")

problem = yaml.load("""---
    ash: ebbd14c5b1875f291c2289f4d52770c2
    algebraic:
      white: [Kf4, Qg4, Rd1, Rc2, Pc6, Pb7]
      black: [Kc7]
    stipulation: "#2"
""")

problem = yaml.load("""---
    ash: 14af7da3a1e7e0e36af1095378977c86
    algebraic:
      white: [Ka5, Bf3, Se2, Pf4, Pc2]
      black: [Kc4, Pf7, Pf5, Pd7, Pc5, Pa6]
    stipulation: "#4"
""")


problem = yaml.load("""---
    ash: 14af7da3a1e7e0e36af1095378977c86
    algebraic:
      white: [Kc5, Bc1, Pd2, Pb2]
      black: [Kc7, Qd8, Rc8, Rb7, Be8, Pf6, Pf4, Pd4, Pd3, Pb4, Pb3]
    stipulation: "h#5"
""")

problem = yaml.load("""---
    ash: 14af7da3a1e7e0e36af1095378977c86
    algebraic:
      white: [Kd2, Rf5, Bg4, Pg2, Pb3]
      black: [Ke4]
    stipulation: "#4"
""")


result = yacpdb.process(problem)

print(yaml.dump(result))
