# -*- coding: utf-8 -*-

# standard
import array
import copy

# local
import popeye

# globals
PIECES = 'KkQqRrBbSsPp'
BLACK = False
WHITE = True

NAME = 0
PREV = 1
NEXT = 2
ID   = 3

# the main structure to store & manipulate the position
class Board:
    def __init__(self):
        self.clear()
    
    def add(self, piece, at, id): # adding new piece to the head of the list
        if((at > 63) or (at < 0)):
            return
        if(piece in 'kK'):
            self.kings[piece == 'K'] = at
        if(self.board[at][NAME] != ''):
            self.drop(at)
        if(self.head != -1):
            self.board[self.head][PREV] = at
        self.board[at] = [piece, -1, self.head, id]
        self.head = at
        self.interferers[at] = 1

    def drop(self, at):
        if((at > 63) or (at < 0)):
            return
        if(self.board[at][PREV] != -1):
            self.board[self.board[at][PREV]][NEXT] = self.board[at][NEXT]
        if(self.board[at][NEXT] != -1):
            self.board[self.board[at][NEXT]][PREV] = self.board[at][PREV]
        if(at == self.head):
            self.head = self.board[at][NEXT]
        self.board[at] = ['', -1, -1, -1]
        self.interferers[at] = 0
    
    def move(self, dep, arr):
        self.board[arr] = self.board[dep]
        if(self.board[arr][NEXT] != -1):
            self.board[self.board[arr][NEXT]][PREV] = arr
        if(self.board[arr][PREV] != -1):
            self.board[self.board[arr][PREV]][NEXT] = arr
        else:
            self.head = arr
        self.board[dep] = ['', -1, -1, -1]

        self.interferers[dep] = 0
        self.interferers[arr] = 1
        
        if(self.board[arr][NAME] in 'kK'):
            self.kings[self.board[arr][NAME] == 'K'] = arr
        

    def clear(self):
        self.kings = [-1, -1]
        self.head, self.board, self.interferers = -1, [], BitBoard()
        self.ep = -1 # square where an en passant capture is possible
        self.castling = [[True, True], [True, True]] # castling rights
        
        for i in xrange(64):
            self.board.append(['', -1, -1, -1])
            
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
        b = Board()
        for color in [BLACK, WHITE]:
            for name, square in Pieces(self, color):
                new_x, new_y = func((square%8, square >> 3))
                b.add(name, new_x + 8*new_y, new_x + 8*new_y)
        self.from_fen(b.to_fen())
    
    def from_algebraic(self, algebraic):
        self.clear()
        if algebraic.has_key('neutral'):
            raise UnsupportedError('neutral')
        for color in algebraic.keys():
            for piecedecl in algebraic[color]:
                if(len(piecedecl) != 3) or (not piecedecl[0] in PIECES):
                    raise UnsupportedError(piecedecl)
                self.add([piecedecl[0].lower(), piecedecl[0].upper()][color=='white'], \
                    from_xy(piecedecl[1:]), from_xy(piecedecl[1:]))
        
    def from_fen(self, fen):
        self.clear()
        fields = fen.split()
        if len(fields) < 1:
            return
        if len(fields) == 6:
            self.castling = [['q' in fields[2], 'k' in fields[2]], \
                ['Q' in fields[2], 'K' in fields[2]]]
            if (len(fields[3]) == 2) and (fields[3][0] in 'abcdefgh') \
                and (fields[3][1] in '87654321'):
                self.ep = '87654321'.find(fields[3][1])*8 + \
                    'abcdefgh'.find(fields[3][0])
        i, j = 0, 0
        while((j < 64) and (i < len(fields[0]))):
            if('12345678'.find(fields[0][i]) != -1):
                j = j + int(fields[0][i])
            if(PIECES.find(fields[0][i]) != -1):
                self.add(fields[0][i], j, j)                
                j = j + 1
            i = i + 1
    
    def to_fen(self):
        fen, blanks = '', 0
        for i in xrange(64):
            if((i > 0) and (i % 8 == 0)): # new row
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + "/"
                blanks = 0
            if(self.board[i][NAME] != ''):
                if(blanks > 0):
                    fen = fen + ("%d" % (blanks))
                fen = fen + self.board[i][NAME]
                blanks = 0
            else:
                blanks = blanks + 1
        if(blanks > 0):
            fen = fen + ("%d" % (blanks))
        return fen

    def is_of(piece, color):
        return (piece.lower() == piece) ^ color
    is_of = staticmethod(is_of)
    
    def is_attacked(self, square, color):
        for (piece, pos) in Pieces(self, color):
            if((LUT.att[piece][pos][square] == 1) and \
                (LUT.btw[pos][square] & self.interferers).is_zero()):
                return True
        return False
    
    def can_castle(self, color, short):
        # check: pieces have moved
        if(not self.castling[color][short]):
            return False
        king, rook = LUT.castling[color][0], LUT.castling[color][1][short]
        # check: king is at the initial square
        if(self.kings[color] != king):
            return False
        # check: rook is at the initial square and has the same color
        if(self.board[rook][NAME] == ''):
            return False
        if((not (self.board[rook][NAME] in 'rR')) or \
            (Board.is_of(self.board[rook][NAME], not color))):
            return False
        # check: there's noone between the king and rook
        if not (LUT.btw[king][rook] & self.interferers).is_zero():
            return False
        # check: king is not under attack by opposite side
        if(self.is_attacked(king, not color)):
            return False
        # squares between the king and arrival are not attacked:
        arrival = LUT.castling[color][2][short]
        for i in SetBits(LUT.btw[king][arrival]):
            if(self.is_attacked(i, not color)):
                return False
        # check that arrival square is not attacked will be made by LegalMoves
        return True
    
    def has_legal_moves(self, color):
        for move in LegalMoves(self, color):
            move.unmake(self)
            return True
        return False
    
    # returns array of Phases
    def mate_in_1(self):
        retval = []
        for move in LegalMoves(self, WHITE):
            if self.is_attacked(self.kings[BLACK], WHITE):
                if(not self.has_legal_moves(BLACK)):
                    move.is_check = move.is_mate = True
                    retval.append(Phase(move))
        return retval
    
    # returns array of Phases
    # recurses: f(N, N) -> f(N, N-1) -> ... -> f(N, 1) -> mate_in_1()
    # the first argument is only needed to tell when to include tries
    def mate_in_n(self, n, depth):

        # invalid position
        if self.is_attacked(self.kings[BLACK], WHITE):
            return []

        # recursion base
        if(depth == 1):
            return self.mate_in_1()

        # try to shortcut
        shortmates = self.mate_in_n(n, depth - 1)
        if len(shortmates) > 0:
            return shortmates
        
        retval = []
        for wmove in LegalMoves(self, WHITE):
            phase = Phase(wmove)
            for bmove in LegalMoves(self, BLACK):
                variation = Phase(bmove)
                variation.variations = self.mate_in_n(n, depth - 1)
                if len(variation.variations) == 0: # bmove is refutation
                    phase.refutations.append(variation)
                    # breaking on first or second refutation, depending on depth
                    if len(phase.refutations) > [0, 1][n == depth]:   
                        bmove.unmake(self)
                        break
                else:
                    phase.variations.append(variation)
            if len(phase.variations) + len(phase.refutations) != 0:
                # else stalemate
                # phase.refutations.append(NullMove())
                if len(phase.refutations) <= [0, 1][n == depth]:
                    retval.append(phase)
        return retval
    
    def dump(self):
        for i in xrange(64):
            if self.board[i][NAME] != '':
                print self.board[i][NAME],
            else:
                print '-',
            if((i > 0) and (i % 8 == 7)):
                print
        print 'ep:', self.ep
        print 'black:',
        for x, y in Pieces(self, BLACK):
            print "%s%s" % (x, to_xy(y)),
        print
        print 'white:',
        for x, y in Pieces(self, WHITE):
            print "%s%s" % (x, to_xy(y)),
        print
    
    def check_integrity(self):
        retval = True
        for color in [BLACK, WHITE]:
            for x, y in Pieces(b, color):
                if x == '':
                    retval = False
        return retval

class BitBoard:
    
    def __init__(self, lo = 0, hi = 0):
        self.v = array.array('L', [lo, hi])
    
    def is_zero(self):
        return self.v[0] == 0 and self.v[1] == 0
    
    def __setitem__(self, pos, item):
        if item:
            self.v[pos > 31] |= 1 << (pos % 32)
        else:
            self.v[pos > 31] &= 0xffffffff ^ (1 << (pos % 32))

    def __getitem__(self, pos):
        return (self.v[pos > 31] >> (pos % 32)) & 1
    
    def __and__(self, that):
        return BitBoard(self.v[0] & that.v[0], self.v[1] & that.v[1])
    
    def __or__(self, that):
        return BitBoard(self.v[0] | that.v[0], self.v[1] | that.v[1])

    def __xor__(self, that):
        return BitBoard(self.v[0] ^ that.v[0], self.v[1] ^ that.v[1])

    def __invert__(self):
        return BitBoard(~self.v[0] & 0xffffffff, ~self.v[1] & 0xffffffff)

    def __eq__(self, that):
        return (self.v[0] == that.v[0]) and (self.v[1] == that.v[1])

    def __iter__(self):
        self.pos = 0

    def count_set_bits(self):
        retval = 0
        for bit in SetBits(self):
            retval += 1
        return retval

    def next(self):
        if(self.pos > 63):
            raise StopIteration
        # return self[self.pos++] :) 
        retval = self[self.pos]
        self.pos += 1
        return retval 
    
    def __str__(self):
        retval = ''
        for i in xrange(64):
            retval += '-*'[self[i]]
            if((i > 0) and (i % 8 == 7)):
                retval += "\n"
        return retval
    
# iterators
class SetBits:
    def __init__(self, qword):
        self.pos, self.qword = -1, qword
    def __iter__(self):
        return self
    def next(self):
        while(True):
            self.pos = self.pos + 1
            if(self.pos > 63):
                raise StopIteration
            if(self.qword[self.pos] == 1):
                return self.pos

class Move:
    
    # params are tuples: ([char Piece], int position)
    def __init__(self, dep, arr, cap):
        self.dep, self.arr, self.cap = dep, arr, cap
        self.captured_piece_id = -1
        self.departing_piece_id = -1

        # if move is a pawn doublestep set up an e.p. square
        if((self.dep[0] in 'pP') and (not LUT.btw[dep[1]][arr[1]].is_zero())):
            for i in SetBits(LUT.btw[dep[1]][arr[1]]): # there's just 1 bit
                self.ep = i
        else: # void further ep possibility
            self.ep = -1
        
        # if move is made by king - void that side castling rights
        self.castling = [[True, True], [True, True]]
        if(self.dep[0] in 'kK'):
            self.castling[self.dep[0] == 'K'] = [False, False]                
        
        # if something arrives to initial position of the rook: void castling
        for (color, short) in \
            [(BLACK, False), (BLACK, True), (WHITE, False), (WHITE, True)]:
            if(arr[1] == LUT.castling[color][1][short]):
                self.castling[color][short] = False

        # castling is set from the outside
        self.is_castling = False
        self.rook_before, self.rook_after = -1, -1
        
        # visuals
        self.is_stalemate, self.is_check, self.is_mate, self.disambiguation, self.letter, self.disambiguation_int, self.mark = \
            False, False, False, '', '', 0, ''
            
        self.cpd = '' # cross phase digest
    
    def make(self, board):
        #print '->', self
        
        # saving castlings and ep
        self.old_castling = copy.deepcopy(board.castling)
        self.old_ep = board.ep

        # saving departing piece id
        self.departing_piece_id = board.board[self.dep[1]][ID]
        
        # applying new castlings and ep
        board.ep = self.ep
        for (color, short) in \
            [(BLACK, False), (BLACK, True), (WHITE, False), (WHITE, True)]:
            board.castling[color][short] = \
                board.castling[color][short] and self.castling[color][short]
        
        # removing the captured piece
        if(self.cap[1] != -1):
            self.captured_piece_id = board.board[self.cap[1]][ID]
            board.drop(self.cap[1])
        
        # moving the piece
        board.move(self.dep[1], self.arr[1])
        
        # promoting the piece
        board.board[self.arr[1]][NAME] = self.arr[0]
        
        # moving the rook, if castled
        if(self.is_castling):
            board.move(self.rook_before, self.rook_after)
            
    
    def unmake(self, board):
        #print '<-', self
        
        # uncastling the rook
        if(self.is_castling):
            board.move(self.rook_after, self.rook_before)
        
        # moving the piece back
        board.move(self.arr[1], self.dep[1])
        
        # unpromoting
        board.board[self.dep[1]][NAME] = self.dep[0]
        
        # returning the captured piece
        if(self.cap[1] != -1):
            board.add(self.cap[0], self.cap[1], self.captured_piece_id)

        # restoring castling and ep
        board.castling = copy.deepcopy(self.old_castling)
        board.ep = self.old_ep
    
    # short algebraic notation can be ambiguous
    def disambiguate(self, board):
        if(self.dep[0] in 'pPkK'):
            self.disambiguation = '' # pawn & king moves can't be ambiguous
            return
        mx, my = LookupTables.to_xy(self.dep[1])
        file, rank = '', ''
        for m in LegalMoves(board, Board.is_of(self.dep[0], WHITE)):
            if (m.dep[0] == self.dep[0]) and (m.arr[1] == self.arr[1]) and \
                (m.dep[1] != self.dep[1]):
                sx, sy = LookupTables.to_xy(m.dep[1])
                if sx == mx:
                    self.disambiguation_int += 8*my
                    rank = '87654321'[my]
                else:
                    self.disambiguation_int += mx
                    file = 'abcdefgh'[mx]
        self.disambiguation = file + rank
    
    def __str__(self):

        checkmate = ['', '+', '#'][self.is_check + self.is_mate]
        checkmate = [checkmate, '='][self.is_stalemate]
        
        if self.is_castling:
            return ['O-O', 'O-O-O'][self.rook_before in [0, 56]] + checkmate
        
        piece = [self.dep[0], ''][self.dep[0] in 'pP'].upper()
        depfile = ['', 'abcdefgh'[self.dep[1]%8]][(self.cap[1] != -1) and (self.dep[0] in 'pP')]
        action = ['', 'x'][self.cap[1] != -1]
        arrival = 'abcdefgh'[self.arr[1]%8] + '87654321'[int(self.arr[1]/8)]
        ep = ['', ' e.p.'][(self.cap[1] != -1) and (self.cap[1] != self.arr[1])]
        promotion = ['', '='+self.arr[0].upper()][self.dep[0] != self.arr[0]]
        letter = ['', '[' + self.letter + ']'][self.letter != '']
        retval = piece+self.disambiguation+depfile+action+arrival+ep+promotion+\
                checkmate+letter+self.mark
        return retval
    
    def __eq__(self, that):
        if isinstance(that, NullMove):
            return False
        return (self.dep == that.dep) and (self.arr == that.arr)
    
    def hash(self):
        return to_xy(self.departing_piece_id) + self.arr[0] + to_xy(self.arr[1])

class NullMove: #for threats and setplay
    def __init__(self):
        pass
    def make(self, board):
        # to avoid "1.a2-a4 threating 2. b2xa3 e.p."
        self.old_ep = board.ep 
        board.ep = -1
    def unmake(self, board):
        board.ep = self.old_ep
    def __eq__(self, that):
        return isinstance(that, NullMove)
    def hash(self):
        return '-'
    
class LookupTables:
    
    def __init__(self):
        self.att = {} # attack bitboards for each piece and square
        self.mov = {} # move lists for each piece and square
        self.btw = [] # between bitboards for each pair of squares
        
        # squares: KingDep, Rook1Dep, Rook2Dep, King1Arr, King2Arr
        # Rook1Arr, Rook2Arr
        self.castling = [[4, [0, 7], [2, 6], [3, 5]], \
                         [60, [56, 63], [58, 62], [59, 61]]]
        
        self.promotions = ['qrbn', 'QRBN']
        
        for piece in PIECES:
            self.att[piece] = []
            self.mov[piece] = []

        self.vecB = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        self.vecR = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        self.vecN = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
        self.vecBP = [(-1, 1), (1, 1)];
        self.vecWP = [(-1, -1), (1, -1)];
        self.vecPs = [ [(0, 1)], [(0, -1)] ]
        
        rules = []
        rules.append({'pieces':'rR', 'vecs':self.vecR, 'range':7})
        rules.append({'pieces':'bB', 'vecs':self.vecB, 'range':7})
        rules.append({'pieces':'sS', 'vecs':self.vecN, 'range':1})
        rules.append({'pieces':'qQ', 'vecs':self.vecR + self.vecB, 'range':7})
        rules.append({'pieces':'kK', 'vecs':self.vecR + self.vecB, 'range':1})
        rules.append({'pieces':'p', 'vecs':self.vecBP, 'range':1})
        rules.append({'pieces':'P', 'vecs':self.vecWP, 'range':1})
        
        # attack bitboards & move lists
        for i in xrange(64):
            for rule in rules:
                (att, mov) = self.trace(i, rule['vecs'], rule['range'])
                for piece in rule['pieces']:
                    self.att[piece].append(att)
                    self.mov[piece].append(mov)
            # for pawns we will also need single and double step moves
            (att, mov) = self.trace(i, self.vecPs[0], [1, 2][int(i/8) == 1]) # 7th rank
            self.mov['p'][i] += mov
            (att, mov) = self.trace(i, self.vecPs[1], [1, 2][int(i/8) == 6]) # 2nd rank
            self.mov['P'][i] += mov

        # between bitboards
        for i in xrange(64):
            self.btw.append([])
            for j in xrange(64):
                if(self.att['q'][i][j] == 1): 
                    self.btw[i].append(self.trace_to(i, j))
                else:
                    self.btw[i].append(BitBoard())

    def trace(self, start, vectors, range):
        bitboard, movelist = BitBoard(), []
        (a, b) = LookupTables.to_xy(start)
        for (x_, y_) in vectors:
            x, y = a + x_, b + y_
            r, trace = range, []
            while((not LookupTables.oob(x, y)) and (r > 0)):
                bitboard[LookupTables.from_xy(x, y)] = 1
                trace.append(LookupTables.from_xy(x, y))
                x, y = x + x_, y + y_
                r -= 1
            if(trace != []):
                movelist.append(trace)
        return (bitboard, movelist)
    
    def trace_to(self, start, end):
        retval = BitBoard()
        (sx, sy), (ex, ey) = LookupTables.to_xy(start), LookupTables.to_xy(end)
        sign = lambda x: [-1, 0, 1][(x >= 0) + (x > 0)] 
        vx, vy = sign(ex - sx), sign(ey - sy)
        sx, sy = sx + vx, sy + vy
        while((sx, sy) != (ex, ey)):
            retval[LookupTables.from_xy(sx, sy)] = 1
            sx, sy = sx + vx, sy + vy
        return retval
    
    def to_xy(i):
        return (i % 8, int(i/8))
    to_xy = staticmethod(to_xy)
    
    def from_xy(x, y):
        return y*8 + x;
    from_xy = staticmethod(from_xy)
    
    def oob(x, y):
        return (x < 0) or (x > 7) or (y < 0) or (y > 7)
    oob = staticmethod(oob)
    
    # calculate the position of the pawn captured en passant
    # e.g. ep(a4, b3) = b4
    def ep(departure, arrival):
        dx, dy = LookupTables.to_xy(departure)
        ax, ay = LookupTables.to_xy(arrival)
        return LookupTables.from_xy(ax, dy)
    ep = staticmethod(ep)


class Pieces:
    def __init__(self, board, color):
        # it is very important to save a copy of the pieces because board will be altered
        # between the calls to next() (by move::make/unmake)
        self.pieces, p, bk = [], board.head, -1
        while(p != -1):
            if(Board.is_of(board.board[p][NAME], color)):
                if board.board[p][NAME] == 'k':
                    bk = p
                else:
                    self.pieces.append((board.board[p][NAME], p))
            p = board.board[p][NEXT]
        if(bk != -1):
            self.pieces.append(('k', bk)) # make the black king always be returned first
        
    def __iter__(self):
        return self
    def next(self):
        if not len(self.pieces):
            raise StopIteration
        return self.pieces.pop()

class Moves:
    def __init__(self, board, color):
        self.brd, self.color = board, color
        self.pieces = Pieces(self.brd, self.color)
        self.piece = ('', -1)
    def __iter__(self):
        return self
    def next(self):
        # init iteration
        if(self.piece == ('', -1)):
            self.next_piece()
        # if we're out of castlings - switch to next piece
        if(self.castling > 1): # there are only 2 castlings: 0 and 1
            self.next_piece()
            return self.next()
        # if we're out of promotions - switch to next range (trace)
        if(self.promotion >= len(LUT.promotions[self.color])):
            self.next_range()
            return self.next()
        # if we're out of traces - check if we can try castlings ...
        if(self.trace >= len(LUT.mov[self.piece[0]][self.piece[1]])):
            if self.can_castle():
                if self.brd.can_castle(self.color, self.castling):
                    move = Move((self.piece), (self.piece[0], \
                        LUT.castling[self.color][2][self.castling]), ('', -1))
                    move.is_castling = True
                    move.rook_before = LUT.castling[self.color][1][self.castling]
                    move.rook_after = LUT.castling[self.color][3][self.castling]
                    self.next_castling()
                    return move
                else:
                    self.next_castling()
                    return self.next()
            # ... or switch to next piece
            else:
                self.next_piece()
                return self.next()
        # if we're out of ranges - switch to next trace
        if(self.range >= len(LUT.mov[self.piece[0]][self.piece[1]][self.trace])):
            self.next_trace()
            return self.next()


        # here piece, trace, range and promotion pointing to smth valid:
        arrival = LUT.mov[self.piece[0]][self.piece[1]][self.trace][self.range]

        # not pawns first:
        if not self.piece[0] in 'pP':
            if(self.brd.interferers[arrival] == 0): # arrival is empty
                # non-capturing move
                move = Move(self.piece, (self.piece[0], arrival), ('', -1))
                self.next_range()
                return move
            elif(Board.is_of(self.brd.board[arrival][NAME], not self.color)):
                # arrival is occupied by opposite color, capturing move
                move = Move(self.piece, (self.piece[0], arrival), \
                    (self.brd.board[arrival][NAME], arrival))
                self.next_trace()
                return move
            else: # selfblock
                self.next_trace()
                return self.next()
            pass
        else: # now pawns:
            # pawn captures
            if LUT.att[self.piece[0]][self.piece[1]][arrival] == 1:
                if(arrival == self.brd.ep):
                    # e.p. captures
                    pwned = LookupTables.ep(self.piece[1], arrival)
                    move = Move(self.piece, (self.piece[0], arrival), \
                        (self.brd.board[pwned][NAME], pwned))
                    self.next_trace()
                    return move
                elif (self.brd.board[arrival][NAME] == '') or \
                    Board.is_of(self.brd.board[arrival][NAME], self.color):
                    # nothing to capture or same color
                    self.next_trace()
                    return self.next()
                elif self.can_promote():
                    # promotion captures
                    move = Move(self.piece, \
                        (LUT.promotions[self.color][self.promotion], arrival), \
                        (self.brd.board[arrival][NAME], arrival))
                    self.next_promotion()
                    return move
                else:
                    # normal captures
                    move = Move(self.piece, (self.piece[0], arrival), \
                        (self.brd.board[arrival][NAME], arrival))
                    self.next_trace()
                    return move
                pass
            # pawn advances
            else:
                if(self.brd.interferers[arrival] or \
                    (not (self.brd.interferers & \
                        LUT.btw[self.piece[1]][arrival]).is_zero())):
                    # blocked
                    self.next_trace()
                    return self.next()
                elif self.can_promote():
                    # promotion advance
                    move = Move(self.piece, \
                        (LUT.promotions[self.color][self.promotion], arrival), \
                        ('', -1))
                    self.next_promotion()
                    return move
                else:
                    # normal advance
                    move = Move(self.piece, (self.piece[0], arrival), ('', -1))
                    self.next_range()
                    return move
            
    def next_piece(self):
        self.piece = self.pieces.next()
        self.trace, self.range, self.promotion, self.castling = 0, 0, 0, 0
    def next_range(self):
        self.range += 1
        self.promotion, self.castling = 0, 0
    def next_trace(self):
        self.trace += 1
        self.promotion, self.castling, self.range = 0, 0, 0
    def next_promotion(self):
        self.promotion += 1
        self.castling = 0
    def next_castling(self):
        self.castling += 1
        self.promotion = 0
    def can_promote(self):
        return ((self.piece[0] == 'p') and (int(self.piece[1]/8) == 6)) or \
            ((self.piece[0] == 'P') and (int(self.piece[1]/8) == 1))
    def can_castle(self):
        return self.piece[0] in 'kK'


class LegalMoves:
    def __init__(self, board, color):
        self.board, self.moves, self.color = board, Moves(board, color), color
        self.move = None
    def __iter__(self):
        return self
    def next(self):
        if not (self.move is None):
            self.move.unmake(self.board)
        self.move = self.moves.next()
        self.move.make(self.board)
        legal = not self.board.is_attacked(self.board.kings[self.color], \
            not self.color)
        if(legal):
            return self.move
        else:
            return self.next()

class Node:
    def __init__(self):
        self.siblings, self.digest = [], ''
        self.ply_no = 0
        self.is_set, self.is_try, self.is_threat, self.is_refutation = False, False, False, False
    def make(self, board):
        pass
    def unmake(self, board):
        pass
    def parse_solution(self, solution, board, side_to_move, ply_no):
        self.ply_no = ply_no
        if solution == '':
            self.make(board) # to save DPI and properly calc digests
            self.unmake(board)
            return '', {}
        
        self.make(board)
        
        tail, ply = popeye.parse_ply(solution, side_to_move)

        while True:
            if not ply.has_key('move'):
                self.unmake(board)
                return tail, ply
            if ply.has_key('move_no'):
                ply['ply_no'] = int(ply['move_no'])*2 - 1
                if ply['side'] == '...':
                    ply['ply_no'] = ply['ply_no'] + 1
            else:
                ply['ply_no'] = self.ply_no + 1
            # case 1: our child - create node + recurse
            if ply['ply_no'] == self.ply_no + 1:
                for sibling in self.siblings:
                    if not isinstance(sibling.move, NullMove):
                        if (sibling.move.dep == ply['move'].dep) and (sibling.move.arr == ply['move'].arr):
                            tail, ply = sibling.parse_solution(tail, board, side_to_move, ply['ply_no'])
                            break
                else:
                    sibling = MoveNode(ply['move'])
                    if ply['ply_no'] != 1 and ply['move'].mark == '!':
                        sibling.is_refutation = True
                        self.is_try = True
                    self.siblings.append(sibling)
                    tail, ply = sibling.parse_solution(tail, board, side_to_move, ply['ply_no'])
            # case 2: our child via null move (setplay, threat) - create 2 nodes + recurse
            elif ply['ply_no'] == self.ply_no + 2:
                sibling = MoveNode(ply['move'])
                tail, ply = sibling.parse_solution(tail, board, side_to_move, ply['ply_no'])
                nullnode = None
                for node in self.siblings:
                    if isinstance(node.move, NullMove):
                        nullnode = node
                        break
                else:
                    nullnode = MoveNode(NullMove())
                    nullnode.ply_no = self.ply_no + 1
                    self.siblings.append(nullnode)
                nullnode.siblings.append(sibling)
                if self.ply_no == 0:
                    nullnode.is_set = True
                else:
                    nullnode.is_threat = True
            # case 3: not our child - up
            elif ply['ply_no'] <= self.ply_no:
                self.unmake(board)
                return tail, ply
            else:
                raise UnsupportedError("Popeye semantics 1")
        
        raise UnsupportedError("Popeye semantics 2")
        
    def dump(self, board, so, self_as_text = ''):
        #if not isinstance(self.move, NullMove):
        #    self.move.disambiguate(board)
        #    print "ret from dis for ", str(self.move)
        if self_as_text == '':
            self_as_text = self.as_text(board)
        self.make(board)
        so.add(self_as_text, board, not isinstance(self.move, NullMove))
        sibling_move_no = str(((self.ply_no + 1 + 1) >> 1))
        ellipsis = ['...', '.'][(self.ply_no + 1)%2]
        
        # grouping siblings with same digests
        groups = {}
        for sibling in self.siblings:
            if groups.has_key(sibling.digest):
                groups[sibling.digest].append(sibling)
            else:
                groups[sibling.digest] = [sibling]
        
        # first threats, last refutations
        metagroups = [[], [], []]
        for digest in groups:
            if groups[digest][0].is_threat:
                metagroups[0].append(digest)
            elif groups[digest][0].is_refutation:
                metagroups[2].append(digest)
            else:
                metagroups[1].append(digest)
        
        # only dump variations for 1 rep from the group
        for metagroup in metagroups:
            for digest in metagroup:
                if len(self.siblings) > 1:
                    if not isinstance(groups[digest][0].move, NullMove):
                        so.add("\n", board, False)
                        for i in xrange(self.ply_no + 1):
                            so.add(" ", board, False)
                        if groups[digest][0].is_refutation:
                            so.add('but: ', board, False)
                        so.add(sibling_move_no+ellipsis, board, False)
                else:
                    if groups[digest][0].is_refutation:
                        so.add('but: ', board, False)
                    if (self.ply_no + 1)%2 == 1:
                        so.add(sibling_move_no + '.', board, False)
                text = '/'.join([s.as_text(board) for s in groups[digest]])
                groups[digest][0].dump(board, so, text)
        
        self.unmake(board)
    
    def calculate_digest(self):
#        if isinstance(self, MoveNode):
#            if not isinstance(self.move, NullMove):
#                print self.move, self.move.departing_piece_id

        for sibling in self.siblings:
            sibling.calculate_digest()
        self.digest = ''.join(sorted([sibling.hash() + sibling.digest for sibling in self.siblings]))

    def hash(self, board):
        return '-'
    
    def traverse(self, board, visitor, with_threats = True):
        if with_threats and isinstance(self, MoveNode) and self.is_threat:
            return
        self.make(board)
        side_moved = BLACK
        if isinstance(self, MoveNode):
            if not isinstance(self.move, NullMove):
                side_moved = [WHITE, BLACK][self.move.dep[0].lower() == self.move.dep[0]]
        visitor.visit(self, board, [WHITE, BLACK][side_moved == WHITE])
        for sibling in self.siblings:
            sibling.traverse(board, visitor)
        self.unmake(board)

class MoveNode(Node):
    def __init__(self, move):
        self.move = move
        Node.__init__(self)
    def make(self, board):
        if not isinstance(self.move, NullMove):
            if(board.board[self.move.arr[1]][NAME] != ''):
                self.move.cap = (board.board[self.move.arr[1]][NAME], self.move.arr[1])
        self.move.make(board)
    def unmake(self, board):
        self.move.unmake(board)
    def as_text(self, board):
        if isinstance(self.move, NullMove):
            if self.is_set:
                return 'setplay: '
            if self.is_threat:
                return 'threat: '
        else:
            self.move.disambiguate(board)
        return str(self.move)
    
    def hash(self):
        return self.move.hash()
        
class TwinNode(Node):
    def __init__(self, id, text, anticipator, problem):
        self.old_fen = ''
        self.id = id
        is_continued, self.commands, self.arguments = popeye.parse_twin(text)
        self.anticipator = [None, anticipator][is_continued]
        
        if 'Stipulation' in self.commands:
            self.stipulation = popeye.Stipulation(self.args[self.commands.find('Stipulation')])
        elif not self.anticipator is None:
            self.stipulation = self.anticipator.stipulation
        else:
            self.stipulation = popeye.Stipulation(problem['stipulation'])
        Node.__init__(self)
    
    def make(self, board):
        self.old_fen = board.to_fen()
        if not self.anticipator is None:
            self.anticipator.make(board)
        for i in xrange(len(self.commands)):
            if 'Move' == self.commands[i]:
                board.drop(from_xy(self.arguments[i][1]))
                board.move(from_xy(self.arguments[i][0]), from_xy(self.arguments[i][1]))
            if 'Exchange' == self.commands[i]:
                piece = copy.deepcopy(board.board[from_xy(self.arguments[i][1])])
                board.drop(from_xy(self.arguments[i][1]))
                board.move(from_xy(self.arguments[i][0]), from_xy(self.arguments[i][1]))
                board.add(piece[NAME], from_xy(self.arguments[i][0]), piece[ID])
            if 'Remove' == self.commands[i]:
                board.drop(from_xy(self.arguments[i][0]))
            if 'Substitute' == self.commands[i]:
                for color in [BLACK, WHITE]:
                    new_name = [self.arguments[i][1].lower(), self.arguments[i][1].upper()][color==WHITE]
                    for piece, square  in Pieces(board, color):
                        if piece.lower() == self.arguments[i][0].lower():
                            board.board[square][NAME] = new_name
            if 'Add' == self.commands[i]:
                new_piece = [self.arguments[i][1][0].lower(), self.arguments[i][1][0].upper()][self.arguments[i][1] == 'white']
                board.add(new_piece, from_xy(self.arguments[i][1][1:]), from_xy(self.arguments[i][1][1:]))
            if 'Rotate' == self.commands[i]:
                board.rotate(self.arguments[i][0])
            if 'Mirror' == self.commands[i]:
                board.mirror(self.arguments[i][0])
            if 'Shift' == self.commands[i]:
                x = 'abcdefgh'.find(self.arguments[i][0][0]) - 'abcdefgh'.find(self.arguments[i][1][0])
                y = '87654321'.find(self.arguments[i][0][1]) - '87654321'.find(self.arguments[i][1][1])
                board.shift(x, y)
            if 'PolishType' == self.commands[i]:
                aux_board = Board()
                for color in [BLACK, WHITE]:
                    for name, square in Pieces(board, color):
                        new_name = [name.upper(), name.lower()][name == name.upper()]
                        aux_board.add(new_name, square, square)
                board.from_fen(aux_board.to_fen())
    
    def unmake(self, board):
        if self.old_fen == '':
            raise UnsupportedError("trying to un-twin not yet twinned position")
        board.from_fen(self.old_fen)
    
    def as_text(self):
        retval = self.id + ') '
        if not self.anticipator is None:
            retval = self.id + '=' + self.anticipator.id + ') '
        
        if len(self.commands) == 0:
            #retval += 'Diagram'
            return retval
        parts = []
        for i in xrange(len(self.commands)):
            if 'Move' == self.commands[i]:
                parts.append(u'%s→%s' % (self.arguments[i][0], self.arguments[i][1]))
            if 'Exchange' == self.commands[i]:
                parts.append(u'%s↔%s' % (self.arguments[i][0], self.arguments[i][1]))
            if 'Remove' == self.commands[i]:
                parts.append(u'-%s' % self.arguments[i][0])
            if 'Substitute' == self.commands[i]:
                parts.append(u'%s→%s' % (self.arguments[i][0].upper(), self.arguments[i][1].upper()))
            if 'Add' == self.commands[i]:
                parts.append(u'+%s %s ' % (self.arguments[i][0], self.arguments[i][1]))
            if 'Rotate' == self.commands[i]:
                board.rotate(self.arguments[i][0])
            if 'Mirror' == self.commands[i]:
                board.mirror(self.arguments[i][0])
            if 'Shift' == self.commands[i]:
                parts.append(u'%s⇒%s' % (self.arguments[i][0], self.arguments[i][1]))
            if 'PolishType' == self.commands[i]:
                parts.append(u'Polish')
        #retval += " ".join([self.commands[i] + " " + " ".join(self.arguments[i]) for i in xrange(len(self.commands))])
        return retval + ' '.join(parts)
    def dump(self, board, so, quiet = False):
        self.make(board)
        
        if not quiet:
            so.add(self.as_text(), board, True)
        sibling_move_no = str(((self.ply_no + 1 + 1) >> 1))
        ellipsis = ['...', '.'][(self.ply_no + 1)%2]
        
        # first set, then tries
        groups = [[], [], []]
        for sibling in self.siblings:
            if sibling.is_set:groups[0].append(sibling)
            elif sibling.is_try: groups[1].append(sibling)
            else: groups[2].append(sibling)
        for group in groups:
            for sibling in group:
                so.add("\n", board, False)
                if len(self.siblings) > 1:
                    if not isinstance(sibling.move, NullMove):
                        so.add("\n", board, False)
                        for i in xrange(self.ply_no + 1):
                            so.add(" ", board, False)
                        so.add(sibling_move_no+ellipsis, board, False)
                else:
                    if (self.ply_no + 1)%2 == 1:
                        so.add(sibling_move_no + '.', board, False)
                sibling.dump(board, so)
        self.unmake(board)

    def keyplay(self):
        keyplay = Node()
        if self.stipulation.starts_with_null:
            keyplay.siblings = self.siblings
        else:
            keyplay.siblings = [x for x in self.siblings if not x.is_try and not x.is_set]
        return keyplay
        
    def hash(self):
        return '-'

class SolutionOutput:
    def __init__(self, embed_fen = False):
        self.embed_fen = embed_fen
        self.cur_node_id = 0
        self.boardshots = []
        self.solution = ''

    def add(self, text, board, is_move):
        if not is_move:
            self.solution += text
        elif not self.embed_fen and is_move:
            self.solution += text + ' '
        else:
            self.solution += '<' + str(self.cur_node_id) + ' ' + text + '> '
            self.boardshots.append(board.to_fen())
            self.cur_node_id += 1
    def create_output(self, root_node, board):
        for twin in root_node.siblings:
            twin.dump(board, self, 1 == len(root_node.siblings))
            self.solution += "\n\n"
        self.solution = self.solution.strip()

class UnsupportedError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
        
def from_xy(xy):
    return '87654321'.find(xy[1])*8 + 'abcdefgh'.find(xy[0])
def to_xy(square):
    return 'abcdefgh'[square%8] + '87654321'[int(square/8)]


LUT = LookupTables()
