# -*- coding: utf-8 -*-

import hashlib
import yaml
import re


# ASH = Algebraic + Solution/Stipulation Hash
def ash(e):
    if "solution" not in e or "stipulation" not in e or "algebraic" not in e:
        return ""
    m = hashlib.md5(e["stipulation"].lower())
    for color in ["white", "black", "neutral"]:
        if color in e["algebraic"]:
            m.update("".join(sorted([x.lower() for x in e["algebraic"][color]])))
    m.update("".join(e["solution"].lower().split()))
    return m.hexdigest()


def entry(yamltext):
    yamltext = yamltext.replace(">>", "//")
    yamltext = re.sub(r'stipulation: =([^\\n]*)', r'stipulation: "=\1"', yamltext)
    yamltext = yamltext.replace("stipulation: =", 'stipulation: "="')
    e = yaml.load(yamltext)
    if "solution" in e:
        e["solution"] = unicode(e["solution"]).encode("utf8")
    if "stipulation" in e:
        e["stipulation"] = unicode(e["stipulation"]).encode("utf8")
    return e

