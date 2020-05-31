# standard
import re

# local
from . import chess


RE_PY_TWINS = [re.compile('^' + expr, re.IGNORECASE) for expr in [
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
RE_PY_CONT = re.compile('^Cont(inued)?', re.IGNORECASE)

RE_PY_STIP = re.compile(
    '^(?P<style>h|s|r|(hs)|())(?P<aim>[#=])(?P<movecount>[0-9\.]+)$',
    re.IGNORECASE)

# regular expressions to parse popeye output
RE_PY_MOVEHEAD = re.compile('^(?P<moveno>[0-9]+)(?P<side>\.+)')
RE_PY_REGULARMOVE = re.compile(
    '^(?P<dep_piece>[KQRBS]?)(?P<dep_square>[a-h][1-8])(?P<cap_mod>[\-\*])(?P<arr_square>[a-h][1-8])')
RE_PY_PROMOTION = re.compile(
    '^(?P<dep_square>[a-h][1-8])(?P<cap_mod>[\-\*])(?P<arr_square>[a-h][1-8])=(?P<promotion>[QRBS])')
RE_PY_CASTLING = re.compile('^(?P<castling>0-0(-0)?)')
RE_PY_EPCAPTURE = re.compile(
    '^(?P<dep_square>[a-h][1-8])\*(?P<arr_square>[a-h][1-8]) ep\.')
RE_PY_MOVETAIL = re.compile('^(?P<checkstalemate>[\+=#])?( +)?(?P<mark>[!?]?)')
RE_PY_TWINSTART = re.compile('^\+?(?P<twin_id>[a-z])\)(?P<twin_descr>.*)')
RE_PY_TRASH = re.compile('^\s*(zugzwang\.)|(threat:)|(but)\s*')


def parse_ply_tail(ply, text):
    m = RE_PY_MOVETAIL.match(text)
    ply['move'].mark = m.group('mark')
    if m.group('checkstalemate') == '+':
        ply['move'].is_check = True
    if m.group('checkstalemate') == '#':
        ply['move'].is_check, ply['move'].is_mate = True, True
    if m.group('checkstalemate') == '=':
        ply['move'].is_stalemate = True
    text = re.sub(RE_PY_MOVETAIL, '', text).strip()
    return text, ply

# actual solution. That is black in helpmates and white otherwise
# side_to_move - side which is on move on the first ply of the


def parse_ply(text, side_to_move):

    ply, text = {}, re.sub(RE_PY_TRASH, '', text).strip()

    m = RE_PY_MOVEHEAD.match(text)
    if m:
        ply['move_no'], ply['side'] = m.group('moveno'), m.group('side')
        text = re.sub(RE_PY_MOVEHEAD, '', text).strip()
    else:
        ply['side'] = '...'
    side_to_move = [
        chess.BLACK, chess.WHITE][
        ((side_to_move == chess.WHITE) and (
            ply['side'] == '.')) or (
                (side_to_move == chess.BLACK) and (
                    ply['side'] == '...'))]

    m = RE_PY_PROMOTION.match(text)
    if m:
        dep_square = chess.from_xy(m.group('dep_square'))
        arr_square = chess.from_xy(m.group('arr_square'))
        dep_piece = 'pP'[side_to_move == chess.WHITE]
        arr_piece = [
            m.group('promotion').lower(),
            m.group('promotion')][
            side_to_move == chess.WHITE]
        capture = ('', -1)
        ply['move'] = chess.Move(
            (dep_piece, dep_square), (arr_piece, arr_square), capture)
        text = re.sub(RE_PY_PROMOTION, '', text).strip()
        return parse_ply_tail(ply, text)

    #RE_PY_EPCAPTURE = re.compile('^(?P<dep_square>[a-h][1-8])\*(?P<arr_square>[a-h][1-8]) ep\.')
    # ep must be tried befor reg move
    m = RE_PY_EPCAPTURE.match(text)
    if m:
        dep_square = chess.from_xy(m.group('dep_square'))
        arr_square = chess.from_xy(m.group('arr_square'))
        dep_piece = 'pP'[side_to_move == chess.WHITE]
        arr_piece = dep_piece
        capture = (
            'pP'[
                side_to_move == chess.BLACK],
            chess.LookupTables.ep(
                dep_square,
                arr_square))
        ply['move'] = chess.Move(
            (dep_piece, dep_square), (arr_piece, arr_square), capture)
        text = re.sub(RE_PY_EPCAPTURE, '', text).strip()
        return parse_ply_tail(ply, text)

    m = RE_PY_REGULARMOVE.match(text)
    if m:
        dep_square = chess.from_xy(m.group('dep_square'))
        arr_square = chess.from_xy(m.group('arr_square'))
        dep_piece = [m.group('dep_piece'), 'P'][m.group('dep_piece') == '']
        dep_piece = [dep_piece.lower(), dep_piece][side_to_move == chess.WHITE]
        arr_piece = dep_piece
        capture = ('', -1)
        ply['move'] = chess.Move(
            (dep_piece, dep_square), (arr_piece, arr_square), capture)
        text = re.sub(RE_PY_REGULARMOVE, '', text).strip()
        return parse_ply_tail(ply, text)

    m = RE_PY_CASTLING.match(text)
    if m:
        if m.group('castling') == '0-0':
            if side_to_move == chess.BLACK:
                ply['move'] = chess.Move(
                    ('k', chess.from_xy('e8')), ('k', chess.from_xy('g8')), ('', -1))
                ply['move'].is_castling, ply['move'].rook_before, ply[
                    'move'].rook_after = True, chess.from_xy('h8'), chess.from_xy('f8')
            else:
                ply['move'] = chess.Move(
                    ('K', chess.from_xy('e1')), ('K', chess.from_xy('g1')), ('', -1))
                ply['move'].is_castling, ply['move'].rook_before, ply[
                    'move'].rook_after = True, chess.from_xy('h1'), chess.from_xy('f1')
        else:
            if side_to_move == chess.BLACK:
                ply['move'] = chess.Move(
                    ('k', chess.from_xy('e8')), ('k', chess.from_xy('c8')), ('', -1))
                ply['move'].is_castling, ply['move'].rook_before, ply[
                    'move'].rook_after = True, chess.from_xy('a8'), chess.from_xy('d8')
            else:
                ply['move'] = chess.Move(
                    ('K', chess.from_xy('e1')), ('K', chess.from_xy('c1')), ('', -1))
                ply['move'].is_castling, ply['move'].rook_before, ply[
                    'move'].rook_after = True, chess.from_xy('a1'), chess.from_xy('d1')
        text = re.sub(RE_PY_CASTLING, '', text).strip()
        return parse_ply_tail(ply, text)

    raise ParseError(
        "Can't match next ply:\n%s" %
        "\n".join(
            text.split("\n")[
                :3]))


def create_input(problem, sstip, sticky, pieces_clause, is_py_option):
    lines = ["BeginProblem"]
    # stipulation
    if 'stipulation' in problem:
        lines.append(["Stipulation ", "SStipulation "]
                     [sstip] + problem['stipulation'])
    #options and conditions
    options, conditions = sticky, []
    if 'options' in problem:
        for option in problem['options']:
            if not option in options and is_py_option(option):
                options.append(option)
            else:
                conditions.append(option)

    lines.append("Option " + " ".join(options))
    if len(conditions) > 0:
        lines.append("Condition " + " ".join(conditions))
    # pieces
    if pieces_clause != '':
        lines.append("Pieces")
        lines.append(pieces_clause)
    # for color in ['white', 'black', 'neutral']:
    #    if problem['algebraic'].has_key(color):
    #        lines.append("  " + color + " " + " ".join(problem['algebraic'][color]))
    # twins
    if 'twins' in problem:
        for key in sorted(problem['twins'].keys()):
            lines.append(['Twin', 'Zero'][key == 'a'] +
                         " " + problem['twins'][key])

    lines.append("EndProblem")
    return "\n".join(lines)


def parse_output(problem, output):
    # removing popeye header (version) and footer (solving time)
    lines = output.strip().split("\n")
    if len(lines) < 2:
        raise ParseError("Output too short")
    lines = lines[1:-1]

    # parsing twins
    if 'twins' in problem:
        is_zero = ('a' == sorted(problem['twins'].keys())[0])
        twins, twin_re, acc, cur_twin_id = {}, re.compile(
            RE_PY_TWINSTART), [], ''
        for line in lines:
            m = twin_re.match(line)
            if m:
                if cur_twin_id != '':
                    twins[cur_twin_id] = "\n".join(acc)
                cur_twin_id, acc = m.group('twin_id'), []
            else:
                acc.append(line)
        twins[cur_twin_id] = "\n".join(acc)
    else:
        twins = {'a': "\n".join(lines)}

    root = chess.Node()
    b = chess.Board()
    b.from_algebraic(problem['algebraic'])
    prev_twin = None
    for k in sorted(twins.keys()):
        if 'twins' in problem and k in problem['twins']:
            twin = chess.TwinNode(k, problem['twins'][k], prev_twin, problem)
        else:
            twin = chess.TwinNode(k, '', prev_twin, problem)
        twin.parse_solution(twins[k], b, twin.stipulation.side_to_move(), 0)
        twin.calculate_digest()
        root.siblings.append(twin)
        prev_twin = twin
    return root


def parse_twin(text):
    is_continued, commands, arguments = False, [], []
    if RE_PY_CONT.match(text):
        is_continued = True
        text = RE_PY_CONT.sub('', text).strip()
    while text != '':
        for expr in RE_PY_TWINS:
            m = expr.match(text)
            if expr.match(text):
                commands.append(m.group('command').lower())
                if not m.group('command') in ['PolishType']:
                    arguments.append(m.group('args').split())
                else:
                    arguments.append([])
                text = expr.sub('', text).strip()
                break
        else:
            raise ParseError("Cant parse twin: '%s'" % text)
    return is_continued, commands, arguments


class ParseError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Stipulation:

    def __init__(self, str):
        self.is_supported = False
        m = re.match(RE_PY_STIP, str)
        if m:
            self.is_supported = True
            self.style = m.group('style')
            self.aim = m.group('aim')
            self.ply_count = int(2 * float(m.group('movecount')))
            if self.style in ['', 'hs']:
                self.ply_count = self.ply_count - 1
            self.starts_with_null = False
            if m.group('movecount').find('.') != -1:
                self.starts_with_null = True
                self.ply_count = self.ply_count + 1
        if not self.is_supported:
            raise chess.UnsupportedError(str)

    def side_to_move(self):
        return [chess.BLACK, chess.WHITE][self.style != 'h']
