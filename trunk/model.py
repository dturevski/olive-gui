# standard
import re
import exceptions
import copy
import datetime

# 3rd party
import yaml

# local
import legacy.popeye
import legacy.chess

COLORS = ['black', 'white',  'neutral']
FAIRYSPECS = ['Chameleon', 'Jigger', 'Kamikaze', 'Paralysing', \
    'Royal', 'Volage', 'Functionary', 'HalfNeutral', \
    'HurdleColourChanging', 'Protean', 'Magic']

def algebraicToIdx(a1):
    return ord(a1[0]) - ord('a') + 8*(7 + ord('1') - ord(a1[1]))
def idxToAlgebraic(idx):
    return 'abcdefgh'[idx%8] + '87654321'[idx>>3]
def myint(string):
    f, s = False,  []
    for char in string:
        if char in '0123456789':
            s.append(char)
            f = True
        elif f:
            break
    try:
        return int(''.join(s))
    except exceptions.ValueError:
        return 0

def notEmpty(hash, key):
    if not hash.has_key(key):
        return False
    return len(unicode(hash[key])) != 0

def makePieceFromXfen(fen):
    color = 'white'
    if '!' in fen:
        color = 'neutral'
    elif fen == fen.lower():
        color = 'black'
    name = 'P'
    base_glyph = fen.replace('!', '').lower()
    if FairyHelper.defaults.has_key(base_glyph):
        name = FairyHelper.defaults[base_glyph].upper()
    return Piece(name, color, [])
    
class FairyHelper:
    defaults, glyphs, fontinfo = {}, {}, {}
    options, conditions = [], []
    f = open('conf/fairy-pieces.txt')
    for entry in map(lambda x: x.strip().split("\t"), f.readlines()):
        glyphs[entry[0]] =  {'name': entry[1]}
        if len(entry) > 2:
            if '' <> entry[2].strip():
                glyphs[entry[0]]['glyph'] = entry[2]
            else:
                glyphs[entry[0]]['glyph'] = 'x'
        else:
            glyphs[entry[0]]['glyph'] = 'x'
        if len(entry) > 3:
            if 'd' == entry[3]:
                defaults[entry[2]] = entry[0]
    f.close()

    f = open('resources/fonts/xfen.txt')
    for entry in map(lambda x: x.strip().split("\t"), f.readlines()):
        fontinfo[entry[0]] = {'family':entry[1], 'chars':[chr(int(entry[2])), chr(int(entry[3]))]}
    f.close()

    f = open('conf/py-options.txt')
    options = map(lambda x: x.strip(), f.readlines())
    f.close()

    f = open('conf/py-conditions.txt')
    conditions = map(lambda x: x.strip(), f.readlines())
    f.close()
    
class Distinction:
    suffixes = ['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th']
    pattern = re.compile('^(?P<special>special )?((?P<lo>\d+)[stnrdh]{2}-)?((?P<hi>\d+)[stnrdh]{2} )?(?P<name>(prize)|(place)|(hm)|(honorable mention)|(commendation)|(comm\.)|(cm))(, (?P<comment>.*))?$')
    names = {'prize':'Prize', 'place':'Place', 'hm':'HM', 'honorable mention':'HM', 'commendation':'Comm.', 'comm.':'Comm.', 'cm':'Comm.'}
    
    def __init__(self):
        self.special = False
        self.lo, self.hi = 0, 0
        self.name = ''
        self.comment = ''
    def __str__(self):
        if self.name == '': return ''
        retval = self.name
        lo, hi = self.lo, self.hi
        if(self.hi < 1) and (self.lo > 0):
            lo, hi = hi, lo
        if hi > 0:
            retval = str(hi) + Distinction.pluralSuffix(hi) + ' ' +retval
            if lo > 0:
                retval = str(lo) + Distinction.pluralSuffix(lo) + '-' +retval
        if self.special:
            retval = 'Special ' + retval
        if self.comment.strip() != '':
            retval = retval + ', ' + self.comment.strip()
        return retval
    def pluralSuffix(integer):
        integer = [integer, -integer][integer < 0]
        integer = integer % 100
        if(integer > 10) and (integer < 20): return Distinction.suffixes[0]
        else: return Distinction.suffixes[integer % 10]
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
    
class Piece:
    def __init__(self, name, color, specs):
        self.name, self.color, self.specs = name, color, sorted(specs)
        self.next,  self.prev = -1, -1
        
    def fromAlgebraic(algebraic):
        parts = algebraic.split(' ')
        return Piece(parts[-1], parts[0], parts[1:-1])
    fromAlgebraic = staticmethod(fromAlgebraic)
    
    def toFen(self):
        glyph = FairyHelper.glyphs[self.name.lower()]['glyph']
        if self.color == 'white':
            glyph = glyph.upper()
        else:
            glyph = glyph.lower()
        if self.color == 'neutral':
            glyph = '!' + glyph
        if len(glyph) > 1:
            glyph = '(' + glyph + ')'
        return glyph
        
    def toAlgebraic(self):
        retval = self.name.upper()
        if len(self.specs) > 0:
            retval = ' '.join(sorted(self.specs)) + ' ' + retval
        return retval
    def __str__(self):
        retval = FairyHelper.glyphs[self.name.lower()]['name']
        if len(self.specs) > 0:
            retval = ' '.join(sorted(self.specs)) + ' ' + retval
        return self.color + ' ' + retval
    def serialize(self):
        return self.color + ' ' + self.toAlgebraic()

class Board:
    def __init__(self):
        self.clear()
    
    def add(self, piece, at): # adding new piece to the head of the list
        if((at > 63) or (at < 0)):
            return
        if(not self.board[at] is None):
            self.drop(at)
        if(self.head != -1):
            self.board[self.head].prev = at
        piece.prev, piece.next = -1, self.head
        self.head = at
        self.board[at] = piece

    def drop(self, at):
        if((at > 63) or (at < 0)):
            return
        if(self.board[at].prev != -1):
            self.board[self.board[at].prev].next = self.board[at].next
        if(self.board[at].next != -1):
            self.board[self.board[at].next].prev = self.board[at].prev
        if(at == self.head):
            self.head = self.board[at].next
        self.board[at] = None        

    def clear(self):
        self.head, self.board = -1, []        
        for i in xrange(64):
            self.board.append(None)

    def fromAlgebraic(self, algebraic):
        self.clear()
        for color in COLORS:
            if not algebraic.has_key(color): continue
            for piecedecl in algebraic[color]:
                parts = [x.strip() for x in piecedecl.split(' ')]                
                self.add(Piece(parts[-1][:-2], color, parts[:-1]), algebraicToIdx(parts[-1][-2:]))
    def toAlgebraic(self):
        retval = {}
        for square, piece in Pieces(self):
            if not retval.has_key(piece.color):
                retval[piece.color] = []
            retval[piece.color].append(piece.toAlgebraic() + idxToAlgebraic(square))
        return retval
        
    def getPiecesCount(self):
        counts = {}
        for color in COLORS:
            counts[color] = 0
        for square, piece in Pieces(self):
            counts[piece.color] = counts[piece.color] + 1
            
        retval = str(counts['white']) + '+' + str(counts['black'])
        if(counts['neutral'] > 0):
            retval = retval + '+' + str(counts['neutral'])
        return retval
        
    def rotate(self, angle):
        rot90 = lambda (x, y):  (y, 7-x)
        transform = {'90': rot90, \
                    '180':lambda (x, y): rot90(rot90((x, y))), \
                    '270':lambda (x, y): rot90(rot90(rot90((x, y)))), }
        self.transform(transform[angle])
        
    def mirror(self, axis):
        transform = {'a1<-->h1':lambda (x, y): (7-x, y), \
                    'a1<-->a8': lambda (x, y): (x, 7-y), \
                    'a1<-->h8': lambda (x, y): (y, x), \
                    'h1<-->a8': lambda (x, y): (7-y, 7-x)}
        self.transform(transform[axis])

    def shift(self, x, y):
        self.transform(lambda (a, b): (x+a, y+b))

    def transform(self, func):
        b = copy.deepcopy(self)
        self.clear()
        for square, piece in Pieces(b):
            new_x, new_y = func((square%8, square >> 3))
            if new_x < 0 or new_y < 0 or new_x > 7 or new_y > 7: continue
            self.add(Piece(piece.name, piece.color, piece.specs), new_x + 8*new_y)
            
    def invertColors(self):
        b = copy.deepcopy(self)
        self.clear()
        colors_map = {'white':'black', 'black':'white', 'neutral':'neutral'}
        for square, piece in Pieces(b):
            self.add(Piece(piece.name, colors_map[piece.color], piece.specs), square)
                 
    def fromFen(self, fen):
        self.clear()
        fen = str(fen)
        fen = fen.replace('N', 'S').replace('n', 's')
        i, j = 0, 0
        while((j < 64) and (i < len(fen))):
            if fen[i] in '12345678':
                j = j + int(fen[i])
            elif('(' == fen[i]):
                idx = fen.find(')', i)
                if idx != -1:
                    self.add(makePieceFromXfen(fen[i+1:idx]), j)
                    j = j + 1
                    i = idx
            elif fen[i].lower() in 'kqrbspeofawdx':
                self.add(makePieceFromXfen(fen[i]), j)
                j = j + 1
            i = i + 1
    
    def toFen(self):
        fen, blanks = '', 0
        for i in xrange(64):
            if((i > 0) and (i % 8 == 0)): # new row
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + "/"
                blanks = 0
            if(self.board[i] != None):
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + self.board[i].toFen()
                blanks = 0
            else:
                blanks = blanks + 1
        if(blanks > 0):
            fen = fen + ("%d" % (blanks))
        return fen

    def getLegend(self):
        legend = {}
        for square, piece in Pieces(self):
            t = []
            if len(piece.specs) > 0: 
                t.append(" ".join(piece.specs))
            if piece.color == 'neutral':
                t.append('Neutral')
            if (not piece.name.lower() in ['k', 'q', 'r', 'b', 's', 'p']) or (len(t) > 0):
                t.append((FairyHelper.glyphs[piece.name.lower()]['name']).title())
            if len(t) > 0:
                str = " ".join(t)
                if not legend.has_key(str):
                    legend[str] = []
                legend[str].append(idxToAlgebraic(square))
        return legend
        
    def toPopeyePiecesClause(self):
        c = {}
        for s, p in Pieces(self):
            if not c.has_key(p.color):
                c[p.color] = {}
            specs = " ".join(p.specs)
            if not c[p.color].has_key(specs):
                c[p.color][specs] = {}
            if not c[p.color][specs].has_key(p.name):
                c[p.color][specs][p.name] = []
            c[p.color][specs][p.name].append(idxToAlgebraic(s))

        lines = []
        for color in c.keys():
            for specs in c[color]:
                line = '  ' + color + ' ' + specs + ' ' + \
                    ' '.join([name + ''.join(c[color][specs][name]) for name in c[color][specs].keys()])
                lines.append(line)
        return "\n".join(lines)
    

class Pieces:
    def __init__(self, board):
        self.current = board.head
        self.board = board
    def __iter__(self):
        return self
    def next(self):
        if self.current == -1:
            raise StopIteration
        old_current = self.current
        self.current = self.board.board[self.current].next
        return old_current, self.board.board[old_current]

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

def makeSafe(e):
    r = {}
    if not isinstance(e, dict):
        return r
    # ascii scalars
    for k in ['distinction', 'intended-solutions', 'stipulation']:
        if e.has_key(k):
            try:
                r[k] = unquote(str(e[k]))
            except:
                pass
    # utf8 scalars
    for k in ['source', 'solution', 'source-id', 'distinction']:
        if e.has_key(k):
            try:
                r[k] = unquote(unicode(e[k]))
            except:
                pass

    # ascii lists
    for k in ['keywords', 'options']:
        if e.has_key(k) and isinstance(e[k], list):
            try:
                r[k] = []
                for element in e[k]:
                    r[k].append(unquote(str(element)))
            except:
                del r[k]
    # utf8 lists
    for k in ['authors', 'comments']:
        if e.has_key(k) and isinstance(e[k], list):
            try:
                r[k] = []
                for element in e[k]:
                    r[k].append(unquote(unicode(element)))
            except:
                del r[k]
    # date
    k = 'date'
    if e.has_key(k):
        if isinstance(e[k], int):
            r[k] = str(e[k])
        elif isinstance(e[k], str):
            r[k] = e[k]
        elif isinstance(e[k], datetime.date):
            r[k] = str(e[k])
    # date
    for k in ['algebraic', 'twins']:
        if e.has_key(k) and isinstance(e[k], dict):
            r[k] = e[k]
    return r

class Model:
    file = 'conf/default-entry.yaml'
    def __init__(self):
        f = open(Model.file, 'r')
        try:
            self.defaultEntry = yaml.load(f)
        finally:
            f.close()
        self.current, self.entries, self.dirty_flags, self.board = -1, [], [],  Board()
        self.pieces_counts = []
        self.add(copy.deepcopy(self.defaultEntry),  False)
        self.is_dirty = False
        self.filename = '';
    
    def cur(self):
        return self.entries[self.current]
    
    def setNewCurrent(self,  idx):
        self.current = idx
        if self.entries[idx].has_key('algebraic'):
            self.board.fromAlgebraic(self.entries[idx]['algebraic'])
        else:
            self.board.clear()
            
    def insert(self,  data,  dirty,  idx):
        self.entries.insert(idx,  data)
        self.dirty_flags.insert(idx, dirty)
        if data.has_key('algebraic'):
            self.board.fromAlgebraic(data['algebraic'])
        else:
            self.board.clear()
        self.pieces_counts.insert(idx, self.board.getPiecesCount())
        self.current = idx
        if(dirty): self.is_dirty = True
    def onBoardChanged(self):
        self.pieces_counts[self.current] = self.board.getPiecesCount()
        self.dirty_flags[self.current] = True
        self.is_dirty = True
        self.entries[self.current]['algebraic'] = self.board.toAlgebraic()
    def markDirty(self):
        self.dirty_flags[self.current] = True
        self.is_dirty = True
    def add(self, data, dirty):
        self.insert(data, dirty, self.current+1)
    
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
    def parseSourceId(self):
        issue_id, source_id = '', ''
        if not self.entries[self.current].has_key('source-id'):
            return issue_id, source_id
        parts = unicode(self.entries[self.current]['source-id']).split("/")
        if len(parts) == 1:
            source_id = parts[0]
        else:
            issue_id, source_id = parts[0], "/".join(parts[1:])
        return issue_id, source_id

    def parseDate(self):
        y, m, d = '', 0, 0
        if not self.entries[self.current].has_key('date'):
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
        if not self.entries[self.current].has_key('twins'):
            return ''
        return "\n".join([k + ': ' + self.entries[self.current]['twins'][k] for k in sorted(self.entries[self.current]['twins'].keys())])
    
    def saveDefaultEntry(self):
        f = open(Model.file, 'w')
        try:
            f.write(unicode(yaml.dump(self.defaultEntry, encoding=None, allow_unicode=True)).encode('utf8'))
        finally:
            f.close()
            
    def toggleOption(self, option):
        if not self.entries[self.current].has_key('options'):
            self.entries[self.current]['options'] = []
        if option in self.entries[self.current]['options']:
            self.entries[self.current]['options'].remove(option)
        else:
            self.entries[self.current]['options'].append(option)
        self.markDirty()
            
def createPrettyTwinsText(e):
    if not e.has_key('twins'):
        return ''
    formatted, prev_twin = [], None
    for k in sorted(e['twins'].keys()):
        try:
            twin = legacy.chess.TwinNode(k, e['twins'][k], prev_twin, e)
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as exc:
            formatted.append('%s) %s' %(k, e['twins'][k]))
        else:
            formatted.append(twin.as_text())
            prev_twin = twin
    return "<br/>".join(formatted)
    
def hasFairyConditions(e):
    if not e.has_key('options'):
        return False
    for option in e['options']:
        if not legacy.popeye.is_py_option(option):
            return True
    return False

def hasFairyPieces(e):
    if not e.has_key('algebraic'):
        return False
    board = Board()
    board.fromAlgebraic(e['algebraic'])
    for p in Pieces(board):
        if (p.color not in ['white', 'black']) or (len(p.specs) != 0) or (p.name.lower() not in 'kqrbsp'):
            return True
    return False

def hasFairyElements(e):
    return hasFairyConditions(e) or hasFairyPieces(e)