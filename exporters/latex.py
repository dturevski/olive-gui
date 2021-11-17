# -*- coding: utf-8 -*-

# local
import model
import board
import gui
import logging

# 3rd party
import yaml
from PyQt5 import QtCore, QtGui, QtWidgets


def string2LaTeX(s):
    s = s.replace("#", "\\#")
    s = s.replace("&", "\\&")
    s = s.replace("%", "\\%")
    s = s.replace("*", "{\\x}")
    s = s.replace("->", "$\\to$")
    return s

def indent(s):
    return "    " + "\n    ".join([line for line in s.splitlines(False) if line.strip() != ""]) + "\n"

def head():
    return ("\\documentclass{article}\n\n" +
        "\\usepackage[T2A,T1]{fontenc}\n" +
        "\\usepackage[utf8]{inputenc}\n" +
        "\\usepackage[russian]{babel}\n" +
        "\\usepackage{diagram}%\n\n" +
        "\\begin{document}%\n\n")

def entry(e, Lang):
    text = "\\begin{diagram}%\n"
    # authors
    if 'authors' in e:
        text = (text + "  \\author{" +
                  '; '.join(e['authors']) + "}%\n")

    # source
    if 'source' in e:
        sourcenr = ""
        source = ""
        issue = ""
        day = ""
        month = ""
        year = ""
        s = e['source']
        if 'name' in s:
            source = "\\source{" + string2LaTeX(s['name']) + "}"
            if 'problemid' in s:
                sourcenr = "\\sourcenr{" + s['problemid'] + "}"
            if 'issue' in s:
                issue = "\\issue{" + s['issue'] + "}"

        if 'date' in s:
            d = s['date']
            if 'day' in d:
               day = "\\day{" + str(d['day']) + "}"
            if 'month' in d:
               month = "\\month{" + str(d['month']) + "}"
            if 'year' in d:
               year = "\\year{" + str(d['year']) + "}"

        text = text + "  " + sourcenr + source + issue + day + month + year + "%\n"

    # distinction
    if 'award' in e:
        a = e['award']
        tourney = ""
        dist = ""
        if 'tourney' in a:
            tourney = "\\tournament{" + a['tourney']['name'] + "}"
        if 'distinction' in a:
            d = model.Distinction.fromString(a['distinction'])
            dist = "\\award{" + d.toStringInLang(Lang) + "}"

        text = text + "  " + dist + tourney + "%\n"

    # pieces
    b = model.Board()
    if 'algebraic' in e:
        b.fromAlgebraic(e['algebraic'])
        pieces = b.toLaTeX()
        text = (text + "  \\pieces{" + pieces + "}%\n")

    # stipulation
    text = text + "  \\stipulation{" + string2LaTeX(e['stipulation'])

    # add number of solutions
    if model.notEmpty(e, 'intended-solutions'):
        text = text + " \ " + e['intended-solutions']
        if '.' not in e['intended-solutions']:
            text = text + " " + Lang.value('EP_Intended_solutions_shortened')

    # add duplex
    if 'options' in e:
        if 'Duplex' in e['options']:
            text = text + " \ Duplex"
    text = text + "}%\n"

    # conditions
    if 'options' in e:
        # extract conditions by excluding Popeye options
        conditions = [cond for cond in e['options']
                       if not board.FairyHelper.is_popeye_option(cond)]
        if conditions != []:
            text = (text +
                "  \\condition{%\n"
                + indent("\\newline\n".join(conditions)) + "  }%\n")

    # twins
    if 'twins' in e:
        text = (text +
            "  \\twins{%\n" + indent(model.createPrettyTwinsText(e, True)) + "  }%\n")

    # remarks = legend
    # list fairy pieces
    legend = b.getLegend(True)
    if len(legend) != 0:
        text = (text +
            "  \\remark{%\n" + 
            indent("\\newline\n".join([", ".join(legend[k]) + ': ' + k for k in list(legend.keys())]))
            + "  }%\n")

    # solution
    if 'solution' in e:
        text = (text +
            "  \\solution{%\n" +
            indent(string2LaTeX(e['solution'])) + "  }%\n")

    # themes = keywords
    if 'keywords' in e:
        text = (text +
            "  \\themes{%\n    " + string2LaTeX(
            ', '.join(e['keywords'])) +
            "\n  }%\n")

    # comment(s)
    if 'comments' in e:
        text = (text +
            "  \\comment{%\n" +
            indent(string2LaTeX("\\\\\n".join(e['comments']))) + "  }%\n")

    text = text + "\\end{diagram}%\n"

    return text

def tail():
    return ("\\putsol\n\n" +
        "\\end{document}%")

