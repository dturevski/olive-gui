import chess
import copy
import common


sw, w, nw, n, ne, e, se, s = (-1, -1), (-1, 0), (-1, 1), (0, 1), \
                             (1, 1), (1, 0), (1, -1), (0, -1)
traversals = [
    [sw, w, nw, n, ne, e, se, s], [sw, s, se, e, ne, n, nw, w],
    [nw, n, ne, e, se, s, sw, w], [nw, w, sw, s, se, e, ne, n],
    [ne, e, se, s, sw, w, nw, n], [ne, n, nw, w, sw, s, se, e],
    [se, s, sw, w, nw, n, ne, e], [se, e, ne, n, nw, w, sw, s]
]


def add(square, dir):
    x, y = chess.LookupTables.to_xy(square)
    x, y = x + dir[0], y + dir[1]
    if chess.LookupTables.oob(x, y):
        return -1
    return chess.LookupTables.from_xy(x, y)


def inc_id(id_map, key, next_id):
    if key in id_map:
        return id_map, id_map[key], next_id
    id_map[key] = next_id
    return id_map, next_id, next_id + 1


def analyze(board, mated):
    board.interferers[board.kings[mated]] = 0
    retval = _analyze(board, mated)
    board.interferers[board.kings[mated]] = 1
    return retval


def _analyze(board, mated):
    retval = {
        'ideal': False,
        'model': False,
        'pure': False,
        'hash': 0,
        'traversal': -1,
        'mated': board.kings[mated],
        'octet': False,
        'pins': 0}

    mating = [chess.WHITE, chess.BLACK][mated == chess.WHITE]
    mated_king = 'kK'[mated == chess.WHITE]
    participants, attackers = chess.BitBoard(), {}

    king_area = chess.BitBoard(
        chess.LUT.att[mated_king][
            board.kings[mated]].v[0], chess.LUT.att[mated_king][
            board.kings[mated]].v[1])
    king_area[board.kings[mated]] = 1

    for square in chess.SetBits(king_area):
        attackers[square] = get_attackers(board, square, mating)
        if len(attackers[square]) > 1:
            return retval
        if len(attackers[square]) == 1:
            participants[attackers[square][0][1]] = 1
        if square == board.kings[mated]:
            continue
        blocker = board.board[square][chess.NAME]
        if (blocker == '') or chess.Board.is_of(blocker, mating):
            continue
        participants[square] = 1
        # both blocked & once attacked => need to check pinning
        if (len(attackers[square]) == 1):
            if not chess.LUT.btw[
                    attackers[square][0][1]][
                    board.kings[mated]][square]:
                return retval
            # checking that mate exploits pinning - black must have legal moves
            # if pinner is removed
            # nice bug: bk is transparent!
            board.interferers[board.kings[mated]] = 1
            id = board.board[attackers[square][0][1]][chess.ID]
            board.drop(attackers[square][0][1])
            if not board.has_legal_moves(mated):
                board.add(attackers[square][0][0], attackers[square][0][1], id)
                board.interferers[board.kings[mated]] = 0
                return retval
            board.interferers[board.kings[mated]] = 0
            board.add(attackers[square][0][0], attackers[square][0][1], id)
            retval['pins'] = retval['pins'] + 1

    retval['model'], retval['pure'] = True, True
    for name, pos in chess.Pieces(board, mating):
        if (not name in ['pk', 'PK'][mating == chess.WHITE]) and (
                not participants[pos]):
            retval['model'] = False
            break
    retval['ideal'] = retval['model'] and (participants == board.interferers)

    # checking unit has id = 0
    init_id_map, retval['hash'] = {}, 999999999999
    if len(attackers[board.kings[mated]]) > 0:
        init_id_map[attackers[board.kings[mated]][0][1]] = 0  # checking unit
    # id of other participants depend on traversal
    for i in xrange(len(traversals)):
        # if i <> 2: continue
        id_map, hash, pinmask, next_id = copy.deepcopy(init_id_map), 0, 0, 1
        for j in xrange(len(traversals[i])):
            participant_id = -1
            square = add(board.kings[mated], traversals[i][j])
            if -1 == square:  # board edge
                id_map, participant_id, next_id = inc_id(id_map, -1, next_id)
            elif board.board[square][chess.NAME] != '' and \
                    chess.Board.is_of(board.board[square][chess.NAME], mated):  # blocked
                # blockers have same id as board edge
                id_map, participant_id, next_id = inc_id(id_map, -1, next_id)
                if len(attackers[square]) > 0:  # additionally pinned
                    pinmask = pinmask | (1 << j)
            else:  # the square is once attacked
                id_map, participant_id, next_id = inc_id(
                    id_map, attackers[square][0][1], next_id)
            hash = (hash << 3) + participant_id
        hash = hash | (pinmask << 24)
        if int(hash) < int(retval['hash']):
            retval['hash'] = hash
            retval['traversal'] = i
    if retval['hash'] == 2739136:
        retval['hash'] = 0
    return retval


def get_attackers(board, square, color):
    retval = []
    for name, pos in chess.Pieces(board, color):
        if chess.LUT.att[name][pos][square] and \
                (chess.LUT.btw[pos][square] & board.interferers).is_zero():
            retval.append((name, pos))
    return retval


def print_bin(i):
    s = ''
    while i != 0:
        s = str(1 & i) + s
        i = i >> 1
    print s


class FinalesVisitor:

    def __init__(self):
        self.by_hash = {}
        self.different = {}

    def visit(self, node, board, side_on_move):
        if not isinstance(node, chess.MoveNode):
            return
        if isinstance(node.move, chess.NullMove):
            return
        if not (node.move.is_mate or node.move.is_stalemate):
            return
        info = analyze(board, side_on_move)
        if not info['pure']:
            return
        info['stale'] = node.move.is_stalemate

        if info['hash'] in self.by_hash:
            self.by_hash[info['hash']].append(info)
        else:
            self.by_hash[info['hash']] = [info]

        extended_key = str(info['hash']) + \
            str(info['mated']) + str(info['traversal'])
        if extended_key in self.different:
            self.different[extended_key].append(info)
        else:
            self.different[extended_key] = [info]


def provides():
    return [
        'Model mates',
        'Model stalemates',
        'Ideal mates',
        'Ideal satelemates',
        'Echo',
        'Chameleon echo',
        'Octet',
        'Models with pin',
        'Models with two pins',
        'Models with three pins']


def check(problem, board, solution):
    visitor = FinalesVisitor()
    solution.traverse(board, visitor)
    if len(visitor.by_hash) > 0:
        problem['pure-finales'] = [key for key in visitor.by_hash]
    retval = {}
    for keyword in provides():
        retval[keyword] = False

    mm, msm, im, ism = 0, 0, 0, 0
    for dif in visitor.different:
        mm_, msm_, im_, ism_ = 0, 0, 0, 0
        for info in visitor.different[dif]:
            if info['model'] and info['stale']:
                msm_ = 1
            if info['model'] and not info['stale']:
                mm_ = 1
            if info['ideal'] and info['stale']:
                ism_ = 1
            if info['ideal'] and not info['stale']:
                im_ = 1
            if info['octet']:
                retval['Octet'] = True
            if info['pins'] > 0:
                retval['Models with pin'] = True
            if info['pins'] > 1:
                retval['Models with two pins'] = True
            if info['pins'] > 2:
                retval['Models with three pins'] = True
        mm, msm, im, ism = mm + mm_, msm + msm_, im + im_, ism + ism_
    retval['Model mates'], retval['Model stalemates'], retval[
        'Ideal mates'], retval['Ideal satelemates'] = mm > 1, msm > 1, im > 1, ism > 1

    if retval['Model mates']:
        octet = ''
        for piece, pos in chess.Pieces(board, chess.WHITE):
            if piece in 'QRSB':
                octet = octet + piece
        retval['Octet'] = ''.join(sorted(octet)) == 'BBQRRSS'

    # now echoes
    for hash in visitor.by_hash:
        if len(visitor.by_hash[hash]) < 2:
            continue
        for info1, info2 in common.tuples(visitor.by_hash[hash], 2, False):
            if info1['mated'] != info2['mated'] or info1[
                    'traversal'] != info2['traversal']:
                retval['Echo'] = True
            if square_color(info1['mated']) != square_color(info2['mated']):
                retval['Chameleon echo'] = True

    return retval


def square_color(square):
    return (square % 2) ^ (square >> 3) % 2
