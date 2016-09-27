
import model

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


class Node(object):

    def __init__(self):
        self.depth = 0
        self.childIsThreat = False
        self.comments = []
        self.displacements = []

    def setv(self, k, v):
        setattr(self, k, v)
        return self

    def unflatten(self, nodes, offset):

        self.children = []

        while offset < len(nodes):

            # case 1: nodes[offset] is a direct child of this --> add to
            # children and recurse
            if (self.depth + 1 == nodes[offset].depth):
                self.children.append(nodes[offset])
                offset = nodes[offset].unflatten(nodes, offset + 1)

            # case 2: nodes[offset] is a grand-child of this --> create
            # intermediate null-nodes
            elif self.depth + 1 < nodes[offset].depth:
                nn = NullNode(self.depth + 1, self.childIsThreat)
                self.children.append(nn)
                offset = nn.unflatten(nodes, offset)

            # case 3: nodes[offset] is not a child of this
            else:
                return offset

        return len(nodes)

    def linkContinuedTwins(self):
        for i in xrange(1, len(self.children)):
            if self.children[i].isContinued:
                self.children[i].anticipator = self.children[i - 1]

    def make(self, board):
        pass

    def unmake(self, board):
        pass

    def __str__(self):
        return "***"

    def shortPrefix(self):
        return "" if self.depth % 2 != 0 else "%d." % (self.depth >> 1)

    def fullPrefix(self):
        r, d = "", self.depth
        r += "\n" if d < 3 else " " * (d - 2)
        r += str(d >> 1)
        r += "..." if d%2 != 0 else "."
        return r;

    def dump(self, acc = ""):
        acc += str(self)
        for ch in self.children:
            if(self.depth < 2):
                acc += ch.fullPrefix()
            else:
                acc += ch.shortPrefix() if len(self.children) == 1 else "\n" + ch.fullPrefix()
            acc = ch.dump(acc)
        return acc

    def traverse(self, board, visitor):

        if self.depth == 0: # root node
            for square, piece in model.Pieces(board):
                piece.origin = str(square) + "/0"

        visitor.visit(self, board)
        self.make(board)
        for ch in self.children:
            ch.traverse(board, visitor)
        self.unmake(board)

    def assertSemantics(self, b): pass


class NullNode(Node):

    def __init__(self, depth, isThreat):
        super(NullNode, self).__init__()
        self.depth = depth
        self.isThreat = isThreat

    def __str__(self): return "~ " if self.isThreat else ""

    def fullPrefix(self): return ""

    def make(self, board):
        board.flip()

    def unmake(self, board):
        board.flip()


class TwinNode(Node):

    def __init__(self, twinId, isContinued):
        super(TwinNode, self).__init__()
        self.depth = 1

        self.twinId = twinId
        self.isContinued = isContinued
        self.anticipator = None
        self.commands = []

    def make(self, board):

        self.oldBoard = board.serialize()

        if not self.anticipator is None:
            self.anticipator.make(board)

        for command in self.commands:
            command.execute(board, self.twinId)

    def unmake(self, board):
        board.unserialize(self.oldBoard)

    def __str__(self): return self.twinId + ')'

    def fullPrefix(self): return "\n\n"

class VirtualTwinNode(TwinNode):

    def __init__(self):
        super(VirtualTwinNode, self).__init__("a", False)

    def __str__(self): return ''

    def fullPrefix(self): return ''

    def shortPrefix(self): return ''


class TwinCommand:

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def execute(self, b, twinId):
        if 'Move' == self.name:
            b.move(self.args[0], self.args[1])
        elif 'Exchange' == self.name:
            p = b.board[self.args[1]]
            b.move(self.args[0], self.args[1])
            b.add(p, self.args[0])
        elif 'Remove' == self.name:
            b.drop(self.args[0])
        elif 'Add' == self.name:
            self.args[0].origin = str(self.args[1]) + "/" + twinId
            b.add(self.args[0], self.args[1])
        elif 'Rotate' == self.name:
            b.rotate(str(self.args[0]))
        elif 'Mirror' == self.name:
            b.mirror(self.args[0], self.args[1])
        elif 'Shift' == self.name:
            b.shift(self.args[0], self.args[1])
        elif 'PolishType' == self.name:
            b.polishTwin()
        elif 'Imitator' == self.name:
            b.imitators = self.args


class MoveNode(Node):

    def __init__(self, dep, arr, cap):
        self.departure = dep
        self.arrival = arr
        self.departant = None
        self.promotion = None
        self.capture = cap
        self.recolorings = {"white":[], "black":[], "neutral":[]}
        self.rebirths = []
        self.antirebirths = []
        self.promotions = []
        self.imitators = []
        self.removals = []
        self.annotation = ''
        self.checksign = ''

        super(MoveNode, self).__init__()

    def setEnPassant(self):
        dep = Square(self.departure)
        arr = Square(self.arrival)
        self.capture = Square(arr.x, dep.y).value
        return self

    def make(self, b):

        self.assertSemantics(b)
        self.oldBoard = b.serialize()

        if self.promotion == None:
            self.promotion = b.board[self.departure]
        else:
            self.promotion.origin = b.board[self.departure].origin

        if self.promotion.color == 'u':
            if b.board[self.departure].color != 'u':
                self.promotion.color = b.board[self.departure].color
            else:
                self.promotion.color = b.stm

        # capturing
        captureOrigin = -1
        if self.capture != -1:
            captureOrigin = b.board[self.capture].origin
            b.drop(self.capture)

        # moving and promoting
        b.drop(self.departure)
        b.add(self.promotion, self.arrival)
        b.flip()

        # recoloring
        for k, v in self.recolorings.iteritems():
            for square in v:
                if b.board[square] is not None:
                    b.board[square].color = k

        # antirebirths
        for arb in self.antirebirths:
            b.move(arb["from"], arb["to"])
            if arb["prom"] is not None:
                b.board[arb["to"]].name = arb["prom"].name
                b.board[arb["to"]].specs = arb["prom"].specs

        # rebirths
        for rb in self.rebirths:
            piece = rb["unit"] if rb["prom"] is None else rb["prom"]
            if captureOrigin != -1:
                piece.origin = captureOrigin
            else: # sentinels, etc
                piece.origin = "%d/%d" % (rb["at"], self.depth)
            b.add(piece, rb["at"])

        # promotions
        for prom in self.promotions:
            b.board[prom["at"]].name = prom["unit"].name
            if prom["unit"].specs != '':
                b.board[prom["at"]].specs = prom["unit"].specs

        # imitators
        b.imitators = self.imitators

        # removals
        for rm in self.removals: b.drop(rm)

    def unmake(self, b):
        b.unserialize(self.oldBoard)

    def assertSemantics(self, b):
        err = None
        if b.board[self.departure] is None:
            err = "Departure from empty square " + model.idxToAlgebraic(self.departure)
        elif b.board[self.arrival] is not None and self.capture == -1 and self.arrival != self.departure:
            err = "Arrival square " + model.idxToAlgebraic(self.arrival) + " is occupied but no capture is specified"
        elif b.board[self.arrival] is not None and self.capture != self.arrival and self.arrival != self.departure:
            err = "Arrival square " + model.idxToAlgebraic(self.arrival) + \
                  " is occupied but capture is specified at " + model.idxToAlgebraic(self.capture)
        elif self.capture != -1 and b.board[self.capture] is None:
            err = "Capture at empty square " + model.idxToAlgebraic(self.capture)

        # todo: rebirth, recolorings

        if err is not None:
            raise Exception("Semantic error at depth %d: %s" % (self.depth, err))

    def __str__(self):
        return "%s%s-%s " % (self.departant.name, model.idxToAlgebraic(self.departure), model.idxToAlgebraic(self.arrival))


class CastlingNode(MoveNode):

    def __init__ (self, kingside):
        self.kingside = kingside
        super(CastlingNode, self).__init__(-1, -1, -1)

    def make(self, b):
        self.oldBoard = b.serialize()

        shift = 0 if b.stm == 'black' else 56

        a8, c8, d8, e8, f8, g8, h8 = 0, 2, 3, 4, 5, 6, 7
        if self.kingside:
            b.move(e8 + shift, g8 + shift)
            b.move(h8 + shift, f8 + shift)
        else:
            b.move(e8 + shift, c8 + shift)
            b.move(a8 + shift, d8 + shift)

        b.flip()

    def assertSemantics(self, b):

        shift = 0 if b.stm == 'black' else 56

        a8, c8, d8, e8, f8, g8, h8 = 0, 2, 3, 4, 5, 6, 7
        if b.board[e8+shift] is None:
            raise Exception("Can't castle - the king square is empty")
        if self.kingside and b.board[h8+shift] is None:
            raise Exception("Can't castle - the kingside rook square is empty")
        if not self.kingside and b.board[a8+shift] is None:
            raise Exception("Can't castle - the queenside rook square is empty")
