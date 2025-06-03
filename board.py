import re, copy, json, yaml
from base import read_resource_file, get_write_dir

class Square:

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self.value = args[0]
            self.x = self.value % 8
            self.y = self.value >> 3
        elif len(args) == 2:
            self.x, self.y = args[0], args[1]
            self.value = 8*self.y + self.x
        else:
            raise Exception("Wrong count of arguments")

    def alg(self):
        return idxToAlgebraic(self.value)

    def oob(self):
        return self.x < 0 or self.x > 7 or self.y < 0 or self.y > 7

    def __str__(self):
        return self.alg()


COLORS = ['black', 'white', 'neutral']
COLORS_SHORT = {'b': 'black', 'w': 'white', 'n': 'neutral'}
FAIRYSPECS = ['Chameleon', 'Jigger', 'Kamikaze', 'Paralysing',
              'Royal', 'Volage', 'Functionary', 'HalfNeutral',
              'HurdleColourChanging', 'Protean', 'Magic', 'Uncapturable',
              'Bul', 'Dob', 'Anda', 'AndaInverse']

RE_COMMON_STIPULATION = re.compile(
    '^(?P<intro>[0-9]+->)?' +
    '(?P<exact>exact-)?' +
    '(?P<mod>ser-|pser-|phser-|semi-|reci-)?' +
    '(?P<play>(h|s|r|hs|hr|)?)' +
    '(?P<aim>(#=|!=|!#|00|%|~|ep|#|=|==|\\+|(z[a-h][1-8])|x|##|##!|ct|<>|ctr|<>r|c81|(k[a-h][1-8])|pg|dia)) *' +
    '(?P<length>[0-9.]+)$',
    re.IGNORECASE
)

def algebraicToIdx(a1):
    return ord(a1[0]) - ord('a') + 8 * (7 + ord('1') - ord(a1[1]))


def idxToAlgebraic(idx):
    return 'abcdefgh'[idx % 8] + '87654321'[idx >> 3]

def makePieceFromXfen(fen):
    specs = []
    color = 'white'
    if '!' in fen:
        color = 'neutral'
    elif fen == fen.lower():
        color = 'black'
    name = 'P'
    base_glyph = fen.replace('!', '').lower()
    fh = FairyHelper.instance
    if base_glyph in fh.overrides:
        name = fh.overrides[base_glyph]['name'].upper()
        specs = fh.overrides[base_glyph]['specs']
    elif base_glyph in fh.defaults:
        name = fh.defaults[base_glyph].upper()
    return Piece(name, color, specs)


def first_word_in_lowercase(s):
    return s.split(" ")[0].lower()


class FairyHelper:

    def __init__(self):
        self.defaults, self.overrides, self.glyphs, self.fontinfo = {}, {}, {}, {}
        self.RE_PROPER_GLYPH = re.compile('^[kqrbspeaofwdx][1-3]?$')
        self.options, self.conditions = [], []
        f = open(get_write_dir() + '/conf/fairy-pieces.txt', encoding='utf-8')
        for entry in [x.strip().split("\t") for x in f.readlines()]:
            self.glyphs[entry[0]] = {'name': entry[1]}
            if len(entry) > 2:
                if '' != entry[2].strip():
                    self.glyphs[entry[0]]['glyph'] = entry[2]
                else:
                    self.glyphs[entry[0]]['glyph'] = 'x'
            else:
                self.glyphs[entry[0]]['glyph'] = 'x'
            if len(entry) > 3:
                if 'd' == entry[3]:
                    self.defaults[entry[2]] = entry[0]
        f.close()

        for entry in [x.strip().split("\t") for x in read_resource_file(':/fonts/xfen.txt')]:
            self.fontinfo[entry[0]] = {'family': entry[1], 'chars': [
                chr(int(entry[2])), chr(int(entry[3]))]}
        f.close()

        f = open(get_write_dir() + '/conf/py-options.txt')
        self.options = [x.strip() for x in f.readlines()]
        f.close()

        f = open(get_write_dir() + '/conf/py-conditions.txt')
        self.conditions = [x.strip() for x in f.readlines()]
        f.close()

        with open(get_write_dir() + '/conf/fairy-property-colors.yaml', 'r', encoding="utf8") as f:
            self.highlight_colors = yaml.safe_load(f)

    def is_popeye_option(self, s):
        command = first_word_in_lowercase(s)
        return any([first_word_in_lowercase(o) == command for o in self.options])

    def is_special_condition(self, s):
        # TotalInvisible is special in a sense that it is implemented as "pseudo color" (sic)
        # in popeye which somewhat breaks the input logic
        return first_word_in_lowercase(s) == "totalinvisible"

    # add more workarounds here if needed (hopefully not)
    def handle_special_condition(self, s, pieces_clause):
        if self.is_special_condition(s):
            pieces_clause = "\n".join([p for p in [pieces_clause, "  " + s] if p != ''])  # total invisible
        return pieces_clause

    def to_html(self, glyph, square, specs):
        html = self.fontinfo[glyph]['chars'][((square >> 3) + (square % 8)) % 2]
        if len(specs) > 0:
            color = self.highlight_colors[hash("".join(specs)) % len(self.highlight_colors)]
            html = '<font color="%s">%s</font>' % (color, html)
        return html

    def get_glyph_by_piece_name(self, piece_name, overridden_glyphs):
        key = piece_name.lower()
        return overridden_glyphs.get(key, self.glyphs[key]['glyph'])

    def is_proper_glyph(self, glyph):
        return bool(self.RE_PROPER_GLYPH.match(glyph))


FairyHelper.instance = FairyHelper()



def twinId(twin_index):
    if twin_index < 26:
        return chr(ord("a") + twin_index)
    else:
        return "z%d" % (twin_index - 25)

class Piece:

    def __init__(self, name, color, specs):
        if color in COLORS_SHORT:
            color = COLORS_SHORT[color]
        self.name, self.color, self.specs = name, color, sorted(specs)
        self.next, self.prev = -1, -1
        self.assignOrigin(-1, 0)

    def fromAlgebraic(algebraic):
        parts = algebraic.split(' ')
        return Piece(parts[-1], parts[0], parts[1:-1])
    fromAlgebraic = staticmethod(fromAlgebraic)

    def toFen(self, overridden_glyphs):
        glyph = FairyHelper.instance.get_glyph_by_piece_name(self.name, overridden_glyphs)
        if self.color == 'white':
            glyph = glyph.upper()
        else:
            glyph = glyph.lower()
        if self.color == 'neutral':
            glyph = '!' + glyph
        if len(glyph) > 1:
            glyph = '(' + glyph + ')'
        return glyph

    def toLaTeX(self, overridden_glyphs):
        glyph = FairyHelper.instance.get_glyph_by_piece_name(self.name, overridden_glyphs)
        if self.color == 'white':
            piece = 'w'
        if self.color == 'black':
            piece = 's'
        if self.color == 'neutral':
            piece = 'n'
        # King
        glyph= glyph.replace("k", "K")
        # Queen
        glyph= glyph.replace("q", "D")
        # Rook
        glyph= glyph.replace("r", "T")
        # Bishop
        glyph= glyph.replace("b", "L")
        # Knight
        glyph= glyph.replace("s", "S")
        # Pawn
        glyph= glyph.replace("p", "B")
        # "Orphan"
        glyph= glyph.replace("o", "C")
        # "Equihopper"
        glyph= glyph.replace("e", "X")
        # rest
        glyph= glyph.replace("a", "C")
        glyph= glyph.replace("f", "C")
        glyph= glyph.replace("x", "C")

        # rotation of pieces
        glyph= glyph.replace("1", "R")
        glyph= glyph.replace("2", "U")
        glyph= glyph.replace("3", "L")
        piece = piece + glyph
        return piece

    def toAlgebraic(self):
        retval = self.name.upper()
        if len(self.specs) > 0:
            retval = ' '.join(sorted(self.specs)) + ' ' + retval
        return retval

    def toPredicatePieceDomain(self):
        return self.color[0] + self.name.upper()

    def __str__(self):
        retval = FairyHelper.instance.glyphs[self.name.lower()]['name']
        if len(self.specs) > 0:
            retval = ' '.join(sorted(self.specs)) + ' ' + retval
        return self.color + ' ' + retval

    def serialize(self):
        return self.color + ' ' + self.toAlgebraic()

    def serialize2(self):
        return self.toAlgebraic() + "@" + self.origin

    def unserialize2(serialized):
        ps = serialized.split("@")
        p = Piece.fromAlgebraic(ps[0])
        p.origin = ps[1]
        return p
    unserialize2 = staticmethod(unserialize2)

    def assignOrigin(self, square, twin):
        if isinstance(twin, int):
            twin = twinId(twin)
        alg = "a0" if square < 0 or square > 63 else idxToAlgebraic(square)
        self.origin = twin.upper() + alg

class Board:

    def __init__(self):
        self.clear()

    def add(self, piece, at):  # adding new piece to the head of the list
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
        self.head, self.board, self.stm = -1, [], 'black'
        for i in range(64):
            self.board.append(None)

    def flip(self):
        self.stm = 'black' if self.stm == 'white' else 'white'

    def move(self, dep, arr):
        if(self.board[arr] is not None):
            self.drop(arr)
        self.board[arr] = self.board[dep]
        if(self.board[arr].next != -1):
            self.board[self.board[arr].next].prev = arr
        if(self.board[arr].prev != -1):
            self.board[self.board[arr].prev].next = arr
        else:
            self.head = arr
        self.board[dep] = None

    def fromAlgebraic(self, algebraic, withOrigins=False):
        self.clear()
        for color in COLORS:
            if color not in algebraic:
                continue
            for piecedecl in algebraic[color]:
                if withOrigins:
                    square = algebraicToIdx(piecedecl[-2:])
                    piece = Piece.unserialize2(piecedecl[:-2]) if withOrigins else piece.fromAlgebraic(piecedecl[:-2])
                    piece.color = color
                    self.add(piece, square)
                else:
                    parts = [x.strip() for x in piecedecl.split(' ')]
                    self.add(Piece(parts[-1][:-2], color, parts[:-1]),
                             algebraicToIdx(parts[-1][-2:]))

    def toAlgebraic(self, withOrigins = False):
        retval = {}
        for square, piece in Pieces(self):
            if piece.color not in retval:
                retval[piece.color] = []
            s = piece.serialize2() if withOrigins else piece.toAlgebraic()
            retval[piece.color].append(s + idxToAlgebraic(square))
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
        rot90 = lambda x_y6: (x_y6[1], 7 - x_y6[0])
        transform = {
            '90': rot90, '180': lambda x_y: rot90(
                    rot90(
                            (x_y[0], x_y[1]))), '270': lambda x_y1: rot90(
                    rot90(
                            rot90(
                                    (x_y1[0], x_y1[1])))), }
        self.transform(transform[angle])

    def mirror(self, axis):
        transform = {'a1<-->h1': lambda x_y2: (7 - x_y2[0], x_y2[1]),
                     'a1<-->a8': lambda x_y3: (x_y3[0], 7 - x_y3[1]),
                     'a1<-->h8': lambda x_y4: (x_y4[1], x_y4[0]),
                     'a8<-->h1': lambda x_y5: (7 - x_y5[1], 7 - x_y5[0])}
        self.transform(transform[axis])

    def shift(self, x, y):
        self.transform(lambda a_b: (x + a_b[0], y + a_b[1]))

    def transform(self, func):
        b = copy.deepcopy(self)
        self.clear()
        for square, piece in Pieces(b):
            new_x, new_y = func((square % 8, square >> 3))
            if new_x < 0 or new_y < 0 or new_x > 7 or new_y > 7:
                continue
            new_piece = Piece(piece.name, piece.color, piece.specs)
            new_piece.origin = piece.origin
            self.add(new_piece, new_x + 8 * new_y)
        self.stm = b.stm

    def getTransformByName(name):
        try:
            return  {
                'Shift_up': lambda s: (s[0], s[1]-1),
                'Shift_down': lambda s: (s[0], s[1]+1),
                'Shift_left': lambda s: (s[0]-1, s[1]),
                'Shift_right': lambda s: (s[0]+1, s[1]),
                'Rotate_CW': lambda s: (7 - s[1], s[0]),
                'Rotate_CCW': lambda s: (s[1], 7 - s[0]),
                'Mirror_horizontal': lambda s: (s[0], 7 - s[1]),
                'Mirror_vertical': lambda s: (7 - s[0], s[1]),
            } [name]
        except KeyError:
            return None
    getTransformByName = staticmethod(getTransformByName)

    def invertColors(self):
        b = copy.deepcopy(self)
        self.clear()
        colors_map = {'white': 'black', 'black': 'white', 'neutral': 'neutral'}
        for square, piece in Pieces(b):
            new_piece = Piece(piece.name, colors_map[piece.color], piece.specs)
            new_piece.origin = piece.origin
            self.add(new_piece, square)

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
                    self.add(makePieceFromXfen(fen[i + 1:idx]), j)
                    j = j + 1
                    i = idx
            elif fen[i].lower() in 'kqrbspeofawdx':
                self.add(makePieceFromXfen(fen[i]), j)
                j = j + 1
            i = i + 1

    def toFen(self, overridden_glyphs):
        fen, blanks = '', 0
        for i in range(64):
            if((i > 0) and (i % 8 == 0)):  # new row
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + "/"
                blanks = 0
            if(self.board[i] is not None):
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + self.board[i].toFen(overridden_glyphs)
                blanks = 0
            else:
                blanks = blanks + 1
        if(blanks > 0):
            fen = fen + ("%d" % (blanks))
        return fen

    def toLaTeX(self, overriden_glyphs):
        return ", ".join([self.board[i].toLaTeX(overriden_glyphs) + idxToAlgebraic(i)
                       for i in range(64) if self.board[i] is not None])

    def getLegend(self, latex = False):
        legend = {}
        for square, piece in Pieces(self):
            t = []
            if len(piece.specs) > 0:
                t.append(" ".join(piece.specs))
            if not latex:
                if piece.color == 'neutral':
                    t.append('Neutral')
            if (not piece.name.lower() in [
                'k', 'q', 'r', 'b', 's', 'p']) or (len(t) > 0):
                t.append(
                        (FairyHelper.instance.glyphs[
                             piece.name.lower()]['name']).title())
            if len(t) > 0:
                str = " ".join(t)
                if str not in legend:
                    legend[str] = []
                legend[str].append(idxToAlgebraic(square))
        return legend

    def toPopeyePiecesClause(self):
        c = {}
        for s, p in Pieces(self):
            if p.color not in c:
                c[p.color] = {}
            specs = " ".join(p.specs)
            if specs not in c[p.color]:
                c[p.color][specs] = {}
            if p.name not in c[p.color][specs]:
                c[p.color][specs][p.name] = []
            c[p.color][specs][p.name].append(idxToAlgebraic(s))

        lines = []
        for color in list(c.keys()):
            for specs in c[color]:
                line = '  ' + color + ' ' + specs + ' ' + \
                       ' '.join([name + ''.join(c[color][specs][name]) for name in list(c[color][specs].keys())])
                lines.append(line)
        return "\n".join(lines)

    def serialize(self):
        return {'algebraic':self.toAlgebraic(withOrigins=True), 'stm':self.stm }

    def unserialize(self, s):
        self.fromAlgebraic(s['algebraic'], withOrigins=True)
        self.stm = s['stm']

    def __str__(self):
        return json.dumps(self.serialize())

    def getStmByStipulation(self, stipulation):
        if stipulation.lower in ["= black to move", "+ black to move"]:
            return "black"
        matches = RE_COMMON_STIPULATION.match(stipulation.lower())
        if not matches:
            return 'white'
        if matches.group('mod') == 'ser-' and matches.group("play") == "hs":
            return "black" # it even has some sense :)
        if matches.group('play') == "h":
            return "black"
        else:
            return "white"

    def getSideToCompleteLineByStipulation(self, stipulation):
        matches = RE_COMMON_STIPULATION.match(stipulation.lower())
        if not matches:
            return 'white'
        if matches.group("play") in ["s", "r", "hs"]:
            return "black"
        else:
            return "white"


class Pieces:

    def __init__(self, board):
        self.current = board.head
        self.board = board

    def __iter__(self):
        return self

    def __next__(self):
        if self.current == -1:
            raise StopIteration
        old_current = self.current
        self.current = self.board.board[self.current].next
        return old_current, self.board.board[old_current]

