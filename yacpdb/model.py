# -*- coding: utf-8 -*-

# standard
import json
import re
import copy
import datetime

# 3rd party
import yaml

# local
import yacpdb.legacy.popeye
import yacpdb.legacy.chess
from .board import *

def myint(string):
    f, s = False, []
    for char in string:
        if char in "0123456789":
            s.append(char)
            f = True
        elif f:
            break
    try:
        return int(''.join(s))
    except ValueError:
        return 0


def mergeInto(target, source):
    for k, v in source.items():
        if type(v) is str:
            if v.strip() != '':
                target[k] = v.strip()
            elif k in target:
                del target[k]
        elif (type(v) is dict) or (type(v) is list):
            if len(v) > 0:
                target[k] = v
            elif k in target:
                del target[k]
        else:
            target[k] = v
    return target

def notEmpty(hash, key):
    if key not in hash:
        return False
    return len(str(hash[key])) != 0


def filterAndJoin(dict, keys, separator):
    return separator.join(map(lambda x: str(dict[x]), filter(lambda x: x in dict, keys)))

def splitAndStrip(text):
    return [x.strip() for x in str(text).split("\n") if x.strip() != '']


def displayStipulation(entry):
    return entry.get('non-standard-stipulation') or entry.get('stipulation', '')


def attribution(entry, Lang):
    details = []

    def relationship(label, field=None, names=None):
        names = ' & '.join(names or [])
        reference = '>>' + str(entry[field]) if field and notEmpty(entry, field) else ''
        details.append({'label': Lang.value(label), 'names': names,
                        'reference': reference, 'by': Lang.value('CO_By') if names else '',
                        'of': Lang.value('CO_Of') if reference else ''})

    has_version = notEmpty(entry, 'version-of')
    # Retain the established display of corrections recorded with version-of.
    if entry.get('versionists') or (has_version and not entry.get('correctors')):
        relationship('EP_Version', 'version-of', entry.get('versionists'))
    if notEmpty(entry, 'after'):
        details.append({'label': Lang.value('EP_After'), 'reference': '>>' + str(entry['after'])})
    if entry.get('correctors') or notEmpty(entry, 'correction-of'):
        parent = 'correction-of' if notEmpty(entry, 'correction-of') else 'version-of'
        relationship('EP_Correction', parent, entry.get('correctors'))
    if notEmpty(entry, 'anticipated-by'):
        details.append({'label': Lang.value('EP_Anticipated_by'),
                        'reference': '>>' + str(entry['anticipated-by'])})
    return details


def attributionLines(entry, Lang):
    return [' '.join(str(detail[key]) for key in ('label', 'by', 'names', 'of', 'reference')
                     if detail.get(key)) for detail in attribution(entry, Lang)]


def formatDate(dict):
    return filterAndJoin(dict, ['year', 'month', 'day'], '/')


def formatIssueAndProblemId(dict):
    return filterAndJoin(dict, ['issue', 'problemid'], '/')

def parseYear(year):
    return int(year) if re.compile("^[0-9]{4}$").match(year) else year


class Distinction:
    suffixes = ['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th']
    pattern = re.compile(
        '^(?P<special>special )?((?P<lo>\d+)[stnrdh]{2}-)?((?P<hi>\d+)[stnrdh]{2} )?(?P<name>(prize)|(place)|(hm)|(honorable mention)|(commendation)|(comm\.)|(cm))(, (?P<comment>.*))?$')
    names = {
        'prize': 'Prize',
        'place': 'Place',
        'hm': 'HM',
        'honorable mention': 'HM',
        'commendation': 'Comm.',
        'comm.': 'Comm.',
        'cm': 'Comm.'}
    lang_entries = {
        'Prize': 'DSTN_Prize',
        'Place': 'DSTN_Place',
        'HM': 'DSTN_HM',
        'Comm.': 'DSTN_Comm'}

    def __init__(self):
        self.special = False
        self.lo, self.hi = 0, 0
        self.name = ''
        self.comment = ''

    def __str__(self):
        if self.name == '':
            return ''
        retval = self.name
        lo, hi = self.lo, self.hi
        if(self.hi < 1) and (self.lo > 0):
            lo, hi = hi, lo
        if hi > 0:
            retval = str(hi) + Distinction.pluralSuffix(hi) + ' ' + retval
            if lo > 0:
                retval = str(lo) + Distinction.pluralSuffix(lo) + '-' + retval
        if self.special:
            retval = 'Special ' + retval
        if self.comment.strip() != '':
            retval = retval + ', ' + self.comment.strip()
        return retval

    def toStringInLang(self, Lang):
        if self.name == '':
            return ''
        retval = Lang.value(Distinction.lang_entries[self.name])
        lo, hi = self.lo, self.hi
        if(self.hi < 1) and (self.lo > 0):
            lo, hi = hi, lo
        if hi > 0:
            retval = str(
                hi) + Distinction.pluralSuffixInLang(hi, Lang) + ' ' + retval
            if lo > 0:
                retval = str(
                    lo) + Distinction.pluralSuffixInLang(lo, Lang) + '-' + retval
        if self.special:
            retval = Lang.value('DSTN_Special') + ' ' + retval
        if self.comment.strip() != '':
            retval = retval + ', ' + self.comment.strip()
        return retval

    def pluralSuffixInLang(integer, Lang):
        if Lang.current == 'en':
            return Distinction.pluralSuffix(integer)
        else:
            if Lang.current == 'de':
                return '.'
            else:
                return ''
    pluralSuffixInLang = staticmethod(pluralSuffixInLang)

    def pluralSuffix(integer):
        integer = [integer, -integer][integer < 0]
        integer = integer % 100
        if(integer > 10) and (integer < 20):
            return Distinction.suffixes[0]
        else:
            return Distinction.suffixes[integer % 10]
    pluralSuffix = staticmethod(pluralSuffix)

    def fromString(string):
        retval = Distinction()
        string = string.lower().strip()
        m = Distinction.pattern.match(string)
        if not m:
            return retval
        match = {}
        for key in ['special', 'hi', 'lo', 'name', 'comment']:
            if m.group(key) is None:
                match[key] = ''
            else:
                match[key] = m.group(key)
        retval.special = match['special'] == 'special '
        retval.name = Distinction.names[match['name']]
        retval.lo = myint(match['lo'])
        retval.hi = myint(match['hi'])
        retval.comment = match['comment']
        return retval
    fromString = staticmethod(fromString)



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


def unquoteKeys(dict, keys):
    for key in keys:
        if key in dict:
            try:
                dict[key] = unquote(str(dict[key]))
            except:
                pass


def makeSafe(e):
    if not isinstance(e, dict):
        return {}
    # string scalars
    unquoteKeys(e, ['intended-solutions', 'stipulation', 'non-standard-stipulation', 'solution'])
    # string dicts
    if 'source' in e:
        unquoteKeys(e['source'], ['name', 'issue', 'volume', 'round', 'problemid'])
    if 'award' in e:
        unquoteKeys(e['award'], ['distinction'])
        if 'tourney' in e['award']:
            unquoteKeys(e['award']['tourney'], ['name'])
    # string lists
    for k in ['keywords', 'options', 'authors', 'versionists', 'correctors', 'comments']:
        if k in e and isinstance(e[k], list):
            e[k] = [unquote(str(x)) for x in e[k]]
        elif k in e:
            del e[k]
    # date
    #k = 'date'
    #if k in e:
    #    if isinstance(e[k], int):
    #        r[k] = str(e[k])
    #    elif isinstance(e[k], str):
    #        r[k] = e[k]
    #    elif isinstance(e[k], datetime.date):
    #        r[k] = str(e[k])

    for k in ['algebraic', 'twins']:
        if k in e and not isinstance(e[k], dict):
            del e[k]
    return e



def createPrettyTwinsText(e, latex = False):
    if 'twins' not in e:
        return ''
    formatted, prev_twin = [], None
    for k in sorted(e['twins'].keys()):
        try:
            twin = yacpdb.legacy.chess.TwinNode(k, e['twins'][k], prev_twin, e)
        except (yacpdb.legacy.popeye.ParseError, yacpdb.legacy.chess.UnsupportedError) as exc:
            formatted.append('%s) %s' % (k, e['twins'][k]))
        else:
            formatted.append(twin.as_text())
            prev_twin = twin
    if latex:
        nl = " \\newline\n"
    else:
        nl = "<br/>"
    return nl.join(formatted)


def hasFairyConditions(e):
    if 'options' not in e:
        return False
    for option in e['options']:
        if not FairyHelper.instance.is_popeye_option(option):
            return True
    return False


def hasFairyPieces(e):
    return len([p for p in getFairyPieces(e)]) > 0


def getFairyPieces(e):
    if 'algebraic' not in e:
        return
    board = Board()
    board.fromAlgebraic(e['algebraic'])
    for s, p in Pieces(board):
        if isFairy(p):
            yield p


def isFairy(p):
    return (p.color not in ['white', 'black']) or (
        len(p.specs) != 0) or (p.name.lower() not in 'kqrbsp')


def hasFairyElements(e):
    return hasFairyConditions(e) or hasFairyPieces(e)

def transformEntryOptionsAndTwins(e, transform):
    if 'options' in e:
        e['options'] = [transformPopeyeInput(option, transform) for option in e['options']]
    if 'twins' in e:
        for twinId, twin in e['twins'].items():
            e['twins'][twinId] = transformPopeyeInput(twin, transform)

# exclude cases like Type1 -> Typf1 etc
RE_ALGEBRAIC_SQUARE = re.compile("((?<!Typ)[a-h][1-8])")
def transformPopeyeInput(input, transform):
    return re.sub(RE_ALGEBRAIC_SQUARE, lambda m: transformAlgebraicSquare(m.group(1), transform), input)

def transformAlgebraicSquare(square, transform):
    s = Square(algebraicToIdx(square))
    x, y = transform((s.x, s.y))
    x, y = (x + 8) % 8, (y + 8) % 8
    return idxToAlgebraic(Square(x, y).value)
