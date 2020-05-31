# -*- coding: utf-8 -*-

# standard
import json
import re
import copy
import datetime

# 3rd party
import yaml

# local
import legacy.popeye
import legacy.chess
from board import *
from base import get_write_dir

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
    unquoteKeys(e, ['intended-solutions', 'stipulation', 'solution'])
    # string dicts
    if 'source' in e:
        unquoteKeys(e['source'], ['name', 'issue', 'volume', 'round', 'problemid'])
    if 'award' in e:
        unquoteKeys(e['award'], ['distinction'])
        if 'tourney' in e['award']:
            unquoteKeys(e['award']['tourney'], ['name'])
    # string lists
    for k in ['keywords', 'options', 'authors', 'comments']:
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


class Model:
    file = get_write_dir() + '/conf/default-entry.yaml'

    def __init__(self):
        f = open(Model.file, 'r', encoding="utf8")
        try:
            self.defaultEntry = yaml.safe_load(f)
        finally:
            f.close()
        self.current, self.entries, self.dirty_flags, self.board = -1, [], [], Board()
        self.pieces_counts = []
        self.add(copy.deepcopy(self.defaultEntry), False)
        self.is_dirty = False
        self.filename = ''

    def cur(self):
        return self.entries[self.current]

    def setNewCurrent(self, idx):
        self.current = idx
        if 'algebraic' in self.entries[idx]:
            self.board.fromAlgebraic(self.entries[idx]['algebraic'])
        else:
            self.board.clear()

    def insert(self, data, dirty, idx):
        self.entries.insert(idx, data)
        self.dirty_flags.insert(idx, dirty)
        if 'algebraic' in data:
            self.board.fromAlgebraic(data['algebraic'])
        else:
            self.board.clear()
        self.pieces_counts.insert(idx, self.board.getPiecesCount())
        self.current = idx
        if(dirty):
            self.is_dirty = True

    def onBoardChanged(self):
        self.pieces_counts[self.current] = self.board.getPiecesCount()
        self.dirty_flags[self.current] = True
        self.is_dirty = True
        self.entries[self.current]['algebraic'] = self.board.toAlgebraic()

    def markDirty(self):
        self.dirty_flags[self.current] = True
        self.is_dirty = True

    def add(self, data, dirty):
        self.insert(data, dirty, self.current + 1)

    def delete(self, idx):
        self.entries.pop(idx)
        self.dirty_flags.pop(idx)
        self.pieces_counts.pop(idx)
        self.is_dirty = True
        if(len(self.entries) > 0):
            if(idx < len(self.entries)):
                self.setNewCurrent(idx)
            else:
                self.setNewCurrent(idx - 1)
        else:
            self.current = -1

    def parseDate(self):
        y, m, d = '', 0, 0
        if 'date' not in self.entries[self.current]:
            return y, m, d
        parts = str(self.entries[self.current]['date']).split("-")
        if len(parts) > 0:
            y = parts[0]
        if len(parts) > 1:
            m = myint(parts[1])
        if len(parts) > 2:
            d = myint(parts[2])
        return y, m, d

    def twinsAsText(self):
        if 'twins' not in self.entries[self.current]:
            return ''
        return "\n".join([k + ': ' + self.entries[self.current]['twins'][k]
                          for k in sorted(self.entries[self.current]['twins'].keys())])

    def saveDefaultEntry(self):
        f = open(Model.file, 'wb')
        try:
            f.write(yaml.dump(self.defaultEntry, encoding='utf8', allow_unicode=True))
        finally:
            f.close()

    def toggleOption(self, option):
        if 'options' not in self.entries[self.current]:
            self.entries[self.current]['options'] = []
        if option in self.entries[self.current]['options']:
            self.entries[self.current]['options'].remove(option)
        else:
            self.entries[self.current]['options'].append(option)
        self.markDirty()


def createPrettyTwinsText(e):
    if 'twins' not in e:
        return ''
    formatted, prev_twin = [], None
    for k in sorted(e['twins'].keys()):
        try:
            twin = legacy.chess.TwinNode(k, e['twins'][k], prev_twin, e)
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as exc:
            formatted.append('%s) %s' % (k, e['twins'][k]))
        else:
            formatted.append(twin.as_text())
            prev_twin = twin
    return "<br/>".join(formatted)


def hasFairyConditions(e):
    if 'options' not in e:
        return False
    for option in e['options']:
        if not FairyHelper.is_popeye_option(option):
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

RE_ALGEBRAIC_SQUARE = re.compile("([a-h][1-8])")
def transformPopeyeInput(input, transform):
    return re.sub(RE_ALGEBRAIC_SQUARE, lambda m: transformAlgebraicSquare(m.group(1), transform), input)

def transformAlgebraicSquare(square, transform):
    s = Square(algebraicToIdx(square))
    x, y = transform((s.x, s.y))
    x, y = (x + 8) % 8, (y + 8) % 8
    return idxToAlgebraic(Square(x, y).value)