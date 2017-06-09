import copy

import board
from legacy.common import all_different

PATTERNS = {
    'Star': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
    'Big star': [(2, 2), (2, -2), (-2, 2), (-2, -2)],
    'Cross': [(0, 1), (0, -1), (-1, 0), (1, 0)],
    'Big cross': [(0, 2), (0, -2), (-2, 0), (2, 0)],
    'Wheel': [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)],
    'PseudoAlbino': [(-1, -1), (1, -1), (0, -1), (0, -2)],
    'PseudoPickaninny': [(-1, 1), (1, 1), (0, 1), (0, 2)],
}

CORNERS = [0, 7, 56, 63]


def run(entry, solution, board):
    retval = []
    trajs = TrajectoriesBuilder.build(solution, board)
    search([], trajs, retval)
    corners(trajs, retval)

    return retval


class TrajectoriesBuilder:

    def __init__(self):
        self.result = {}

    def visit(self, board, node, front={}):

        node.make(board)

        for origin, departure, arrival in self.displacements(board, front):
            tnode = TNode(arrival, origin, board.board[arrival].toPredicatePieceDomain())
            if departure == -1:
                self.result[origin] = tnode
                front[origin] = tnode
            else:
                front[origin].branches.append(tnode)
                front_ = {}
                for o in front:
                    front_[o] = front[o] if o != origin else tnode
                front = front_

        for ch in node.children:
            self.visit(board, ch, front)

        node.unmake(board)

    def displacements(self, b, front):
        for square, piece in board.Pieces(b):
            if piece.origin not in front:
                yield piece.origin, -1, square
            elif front[piece.origin].square != square:
                yield piece.origin, front[piece.origin].square, square

    def build(solution, board):
        tb = TrajectoriesBuilder()
        tb.visit(board, solution)
        return [tb.result[k] for k in tb.result.iterkeys() if len(tb.result[k].branches) > 0]
    build = staticmethod(build)


class TNode:

    def __init__(self, square, origin, piece):
        self.square, self.origin, self.piece, self.branches = square, origin, piece, []

    def dump(self, level):
        print " " * level, '->', self.piece + model.idxToAlgebraic(self.square)
        for tn in self.branches:
            tn.dump(level + 1)


def patternize(square):
    square = board.Square(square)
    for (name, vecs) in PATTERNS.items():
        squares = []
        for (a, b) in vecs:
            s = board.Square(square.x + a, square.y + b)
            if s.oob():
                break
            squares.append(s)
        else:
            yield name, squares


def search(head, tail, retval):
    # patterns
    if len(head) > 0 and len(head[-1].branches) > 3:
        for name, squares in patternize(head[-1].square):
            if len(squares) == len([y for y in squares if y in [x.square for x in head[-1].branches]]):
                retval.append("%s(%s)" % (name, head[-1].piece))

    # cycles
    if len(head) > 2:
        # search the head backwards to find its last element
        for i in xrange(len(head) - 2, -1, -1):
            if head[i].square == head[-1].square:
                squares = [x.square for x in head[i + 1:]]
                if len(squares) > 2 and all_different(squares):  # cycle length > 2
                    if not oneline(squares):
                        retval.append("RoundTrip(%s, %d)" % (head[i].piece, len(squares)))
                    else:
                        retval.append("LinearRoundTrip(%s, %d)" % (head[i].piece, len(squares)))
                else:
                    retval.append("SwitchBack(%s, %d)" % (head[i].piece, len(squares)))

    # c2c
    if len(head) > 1 and head[-1].square in CORNERS:
        for i in xrange(len(head) - 2, -1, -1):
            if head[i].square != head[-1].square and head[i].square in CORNERS:
                retval.append("CornerToCorner(%s)" % head[i].piece)
                break

    for tnode in tail:
        new_head = copy.copy(head)
        new_head.append(tnode)
        search(new_head, tnode.branches, retval)


def oneline(squares):
    if len(squares) < 3:
        return True
    squares = map(lambda x: board.Square(x), squares)
    x, y = squares[1].x - squares[0].x, squares[1].y - squares[0].y
    for i in xrange(2, len(squares)):
        x_, y_ = squares[i].x - squares[0].x, squares[i].y - squares[0].y
        if x*y_ != x_*y:
            return False
    return True


def findLast(squares, elem, start):
    for i in xrange(len(squares) - 1, start, -1):
        if elem == seq[i]:
            return i
    return -1


# iterate simple subcycles
def cycles(cwalk):
    for i, square in enumerate(cwalk):
        j = findLast(cwalk, square, i)
        if j > i:
            cycles(cwalk[:i] + cwalk[j:])
            cycles(cwalk[i:j])
            break
    else:
        yield cycle


def cwalk(seq):
    i = 0
    while i < len(seq):
        j = findLast(cwalk, seq[i], i)
        if j > i:
            maxlen = 0
            for cycle in cycles(seq[i:j]):
                maxlen = max(len(cycle), maxlen)
                if len(cycle) > 2:
                    ## Linear/Areal Cycle
                    pass
            if maxlen < j - i:
                pass # ClosedWalk
            elif maxlen == 2:
                pass # TraceBack
            i = j
        i += 1


def corners(trajs, retval, tnode = None, result = {}):
    if tnode != None:
        if tnode.square in CORNERS:
            if tnode.origin not in result:
                result[tnode.origin] = {}
            result[tnode.origin][tnode.square] = True
        for branch in tnode.branches:
            corners(None, retval, branch, result)
    else:
        for tnode in trajs:
            corners(None, retval, tnode, result)
        for tnode in trajs:
            if tnode.origin in result and len(result[tnode.origin]) == len(CORNERS):
                retval.append("FourCorners(%s)" % tnode.piece)



