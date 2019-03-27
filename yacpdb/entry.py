# -*- coding: utf-8 -*-

import hashlib
import yaml
import re

try: from .. import board
except ImportError as e: import board
except ValueError as e: import board

def unquote(str):
    str = str.strip()
    if len(str) < 2:
        return str
    if str[0] == '"' and str[-1] == '"':
        return unquote(str[1:-1])
    elif str[0] == "'" and str[-1] == "'":
        return unquote(str[1:-1])
    else:
        return str


# ASH = Algebraic + Solution/Stipulation Hash
# ASH only make sense if the problem passes validation
def ash(e):
    if "solution" not in e or "stipulation" not in e or "algebraic" not in e:
        return ""
    message = e["stipulation"]
    for color in ["white", "black", "neutral"]:
        if color in e["algebraic"]:
            message += "".join(sorted([x for x in e["algebraic"][color]]))
    message += "".join(unquote(e["solution"]).split())
    m = hashlib.md5(message.lower())
    return m.hexdigest()


def entry(yamltext):
    yamltext = yamltext.replace(">>", "//")
    yamltext = re.sub(r'stipulation: =([^\\n]*)', r'stipulation: "=\1"', yamltext)
    yamltext = yamltext.replace("stipulation: =", 'stipulation: "="')
    e = yaml.load(yamltext)
    if "solution" in e:
        e["solution"] = unquote(str(e["solution"]).encode("utf8"))
    if "stipulation" in e:
        e["stipulation"] = str(e["stipulation"]).encode("utf8")
    if 'algebraic' in e:
        b = board.Board()
        b.fromAlgebraic(e["algebraic"])
        e["legend"] = b.getLegend()
    return e

