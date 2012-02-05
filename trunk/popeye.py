import re, yaml, os, subprocess, tempfile, array, copy, sys

# regular expressions to parse popeye options
RE_PY_OPTIONS = [re.compile('^'+expr+'$') for expr in [
    "Defence [1-9][0-9]*",
    "SetPlay",
    "Threat [1-9][0-9]*",
    "Variation",
    "MoveNumbers",
    "Duplex",
    "MaxFlightsquares [1-9][0-9]*",
    "EnPassant [a-h][36]( [a-h][36])?",
    "HalfDuplex",
    "PostKeyPlay",
    "NoCastling( [a-h][1-8])+",
    "Hole [a-h][1-8]",
    "Quodlibet"]]

RE_PY_TWINS = [re.compile('^'+expr) for expr in [
    "(?P<command>Stipulation)\s+(?P<args>\S+)",
    "(?P<command>Condition)\s+(?P<args>\S+)",
    "(?P<command>Move)\s+(?P<args>[a-h][1-8]\s+[a-h][1-8])",
    "(?P<command>Exchange)\s+(?P<args>[a-h][1-8]\s+[a-h][1-8])",
    "(?P<command>Remove)\s+(?P<args>[a-h][1-8])",
    "(?P<command>Substitute)\s+(?P<args>[QRBSP]\s+[QRBSP])",
    "(?P<command>Add)\s+(?P<args>((white)|(black)|(neutral))\s+[QRBSP][a-h][1-8])",
    "(?P<command>Rotate)\s+(?P<args>[0-9]+)",
    "(?P<command>Mirror)\s+(?P<args>[a-h][1-8]\s+[a-h][1-8])",
    "(?P<command>Shift)\s+(?P<args>[a-h][1-8]\s+[a-h][1-8])",
    "(?P<command>PolishType)"]]
RE_PY_CONT = re.compile('^Cont(inued)?')

# regular expressions to parse popeye output
RE_PY_MOVEHEAD = re.compile('^(?P<moveno>[0-9]+)(?P<side>\.+)')
RE_PY_REGULARMOVE = re.compile('^(?P<dep_piece>[KQRBS]?)(?P<dep_square>[a-h][1-8])(?P<cap_mod>[\-\*])(?P<arr_square>[a-h][1-8])')
RE_PY_PROMOTION = re.compile('^(?P<dep_square>[a-h][1-8])(?P<cap_mod>[\-\*])(?P<arr_square>[a-h][1-8])=(<promotion>[QRBS])')
RE_PY_CASTLING = re.compile('^(?P<castling>0-0(-0)?)')
RE_PY_EPCAPTURE = re.compile('^(?P<dep_square>[a-h][1-8])\*(?P<arr_square>[a-h][1-8]) ep\.')
RE_PY_MOVETAIL = re.compile('^(?P<checkstalemate>[\+=#])?( +)?(?P<mark>[!?]?)')
RE_PY_TWINSTART = re.compile('^(?P<twin_id>[a-z])\)(?P<twin_descr>.*)')
RE_PY_TRASH = re.compile('^\s*(zugzwang\.)|(threat:)|(but)\s*')

def create_popeye_input(problem, sstip):
    lines = ["BeginProblem"]
    # stipulation
    lines.append(["Stipulation ", "SStipulation "][sstip] + problem['stipulation'])
    #options and conditions
    options, conditions = ['Variation', 'NoBoard'], []
    if problem.has_key('options'):
        for option in problem['options']:
            for pattern in RE_PY_OPTIONS:
                if pattern.match(option) :
                    options.append(option)
                    break
            else:
                conditions.append(option)
    lines.append("Option " + " ".join(options))
    if len(conditions) > 0:
        lines.append("Condition " + " ".join(conditions))
    # pieces
    lines.append("Pieces")
    for color in ['white', 'black', 'neutral']:
        if problem['algebraic'].has_key(color):
            lines.append("  " + color + " " + " ".join(problem['algebraic'][color]))
    # twins
    if problem.has_key('twins'):
        for key in sorted(problem['twins'].keys()):
            lines.append(['Twin', 'Zero'][key == 'a'] + " " + problem['twins'][key])
    
    lines.append("EndProblem")
    return "\n".join(lines)