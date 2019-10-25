# -*- coding: utf-8 -*-

import hashlib
import yaml
import re

import board


class NoDatesSafeLoader(yaml.SafeLoader):
    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove):
        """
        Remove implicit resolvers for a particular tag

        Takes care not to modify resolvers in super classes.

        We want to load datetimes as strings, not dates, because we
        go on to serialise as json which doesn't have the advanced types
        of yaml, and leads to incompatibilities down the track.
        """
        if not 'yaml_implicit_resolvers' in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [(tag, regexp)
                                                         for tag, regexp in mappings
                                                         if tag != tag_to_remove]

NoDatesSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')

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
    yamltext = re.sub(r'stipulation: =([^\n]*)', r'stipulation: "=\1"', yamltext)
    yamltext = yamltext.replace("stipulation: =", 'stipulation: "="')
    yamltext = yamltext.replace('\t', '  ')
    e = yaml.load(yamltext, Loader=NoDatesSafeLoader)
    if "solution" in e:
        e["solution"] = unquote(str(e["solution"]))
    if "stipulation" in e:
        e["stipulation"] = str(e["stipulation"])
    if 'algebraic' in e:
        b = board.Board()
        b.fromAlgebraic(e["algebraic"])
        e["legend"] = b.getLegend()
    return e

def migrate_v1_0_v1_1(entry):
    pass

