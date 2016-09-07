from nodes import *
import ply.yacc as yacc

# lex & yacc transform the popeye output into a list of Nodes
# the final rule - BuildTree - transforms this list into a tree


def p_BuildTree(t):
    'BuildTree : Solution'
    t[1][0].unflatten(t[1], 1)
    t[1][0].linkContinuedTwins()
    t[0] = t[1][0]


def p_Solution_Movelist(t):
    'Solution : MoveList'
    t[0] = [Node(), VirtualTwinNode()] + t[1]


def p_Solution_TwinList(t):
    'Solution : TwinList'
    t[0] = [Node()] + t[1]


def p_Solution_Comments(t):
    'Solution : Comments Solution'
    t[0] = t[2]
    t[0][0].setv('comments', t[1])


def p_Comments(t):
    '''Comments : COMMENT
        | COMMENT Comments'''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = [t[1]] + t[2]

def p_Solution_empty(t):
    'Solution : '
    t[0] = [Node()]  # empty input

def p_TwinList(t):
    '''TwinList : Twin
                | TwinList Twin'''
    if len(t) == 2:
        t[0] = t[1]
    else:
        t[0] = t[1] + t[2]


def p_Twin(t):
    'Twin : TwinHeader MoveList'
    t[0] = [t[1]] + t[2]


def p_TwinHeader_TwinBullet(t):
    'TwinHeader : TwinBullet'
    t[0] = t[1]


def p_TwinHeader_CommandList(t):
    'TwinHeader : TwinBullet CommandList'
    t[0] = t[1].setv('commands', t[2])


def p_TwinHeader_Comments(t):
    'TwinHeader : TwinHeader Comments'
    t[0] = t[1].setv('comments', t[2])


def p_TwinBullet(t):
    '''TwinBullet :  TWIN_ID
                | PLUS TWIN_ID'''
    if t[1] != '+':
        t[0] = TwinNode(t[1], False)
    else:
        t[0] = TwinNode(t[2], True)


def p_CommandList(t):
    '''CommandList : Command
                | CommandList Command'''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] = t[1] + [t[2]]


def p_Command(t):
    '''Command : LongPieceDecl SQUARE LONG_ARROW SQUARE
            | LongPieceDecl SQUARE DOUBLE_POINTED_ARROW LongPieceDecl SQUARE
            | DASH LongPieceDecl SQUARE
            | PLUS LongPieceDecl SQUARE
            | ROTATE INT
            | MIRROR SQUARE DOUBLE_POINTED_ARROW SQUARE
            | SHIFT SQUARE LONG_DOUBLE_ARROW SQUARE
            | POLISH_TYPE
            | IMITATOR SquareList
            | LongPieceDecl SQUARE'''
    if len(t) == 5 and t[3] == '-->':
        t[0] = TwinCommand("Move", [t[2], t[4]])
    elif len(t) == 6 and t[3] == '<-->':
        t[0] = TwinCommand("Exchange", [t[2], t[5]])
    elif t[1] == '-':
        t[0] = TwinCommand("Remove", [t[3]])
    elif t[1] == '+':
        t[0] = TwinCommand("Add", [t[2], t[3]])
    elif t[1] == 'rotate':
        t[0] = TwinCommand("Rotate", [t[2]])
    elif t[1] == 'mirror':
        t[0] = TwinCommand("Mirror", [t[2], t[4]])
    elif t[1] == 'shift':
        t[0] = TwinCommand("Shift", [t[2], t[4]])
    elif t[1] == 'PolishType':
        t[0] = TwinCommand("PolishType", [])
    elif t[1] == 'Imitator':
        t[0] = TwinCommand("Imitator", t[2])
    elif len(t) == 3:
        t[0] = TwinCommand("Add", [t[1], t[2]])


def p_LongPieceDecl(t):
    '''LongPieceDecl : ColorPrefix PIECE_NAME
        | ColorPrefix FAIRY_PROPERTIES PIECE_NAME'''
    if len(t) == 3:
        t[0] = model.Piece(t[2], t[1], "")
    else:
        t[0] = model.Piece(t[3], t[1], t[2])


def p_ColorPrefix(t):
    '''ColorPrefix : COLOR_NEUTRAL
        | COLOR_WHITE
        | COLOR_BLACK'''
    t[0] = t[1]


def p_PieceDecl(t):
    'PieceDecl : PIECE_NAME'
    t[0] = model.Piece(t[1], "u", "")


def p_PieceDecl_Neutral(t):
    'PieceDecl : COLOR_NEUTRAL PIECE_NAME'
    t[0] = model.Piece(t[2], t[1], "")


def p_PieceDecl_Neutral_Fairy(t):
    'PieceDecl : COLOR_NEUTRAL FAIRY_PROPERTIES PIECE_NAME'
    t[0] = model.Piece(t[3], t[1], t[2])


def p_PieceDecl_Fairy(t):
    'PieceDecl : FAIRY_PROPERTIES PIECE_NAME'
    t[0] = model.Piece(t[2], "u", t[1])


def p_SquareList(t):
    '''SquareList : SQUARE
        | SQUARE COMMA SquareList
        | SQUARE SquareList '''
    if len(t) == 2:
        t[0] = [t[1]]
    elif t[2] == ",":
        t[0] = [t[1]] + t[3]
    else:
        t[0] = [t[1]] + t[2]

def p_MoveList(t):
    '''MoveList : Move
            | Move MoveList 	'''
    if len(t) == 2:
        t[0] = t[1]
    else:
        t[0] = t[1] + t[2]


def p_Move(t):
    '''Move : BUT MOVE_NUMBER HALF_ELLIPSIS HalfMove
            | MOVE_NUMBER HALF_ELLIPSIS ELLIPSIS
            | MOVE_NUMBER HALF_ELLIPSIS HalfMove
            | MOVE_NUMBER HalfMove THREAT
            | MOVE_NUMBER HalfMove ZUGZWANG
            | MOVE_NUMBER HalfMove HalfMove
            | MOVE_NUMBER HalfMove'''

    if t[1] == "but":
        t[0] = [t[4].setv("depth", t[2] + 1)]
    elif t[2] == ".." and t[3] == "...":
        t[0] = [NullNode(t[1], False)]
    elif t[2] == "..":
        t[0] = [t[3].setv("depth", t[1] + 1)]
    elif len(t) > 3 and t[3] == "threat:":
        t[0] = [t[2].setv("depth", t[1]).setv('childIsThreat', True)]
    elif len(t) > 3 and t[3] == "zugzwang.":
        t[0] = [t[2].setv("depth", t[1])]
    elif len(t) == 4:
        t[0] = [t[2].setv("depth", t[1]), t[3].setv("depth", t[1] + 1)]
    else:
        t[0] = [t[2].setv("depth", t[1])]


def p_HalfMove_Check(t):
    'HalfMove : Ply CheckSign'
    t[0] = t[1].setv("checksign", t[2])


def p_HalfMove_Ply(t):
    'HalfMove : Ply'
    t[0] = t[1]


def p_HalfMove_Annotation(t):
    'HalfMove : HalfMove ANNOTATION'
    t[0] = t[1].setv("annotation", t[2])


def p_HalfMove_Comments(t):
    'HalfMove : HalfMove Comments'
    t[0] = t[1].setv("comments", t[2])


def p_CheckSign(t):
    '''CheckSign : PLUS
        | OTHER_CHECK_SIGN'''
    t[0] = t[1]

def p_Ply_Body(t):
    'Ply : Body'
    t[0] = t[1]


def p_Ply_ColorPrefix(t):
    'Ply : Ply EQUALS ColorPrefix'
    color = model.COLORS_SHORT[t[3]]
    t[1].recolorings[color].append(t[1].arrival)
    t[0] = t[1]


def p_Ply_Promotion(t):
    ''' Ply : Ply EQUALS PieceDecl
        | Ply EQUALS LongPieceDecl
        | Ply EQUALS'''
    if len(t) != 3:
        t[0] = t[1].setv('promotion', t[3])
    else:
        t[0] = t[1].setv("checksign", t[2])


def p_Ply_Rebirth_Promotion(t):
    'Ply : Ply LEFT_SQUARE_BRACKET PLUS LongPieceDecl SQUARE EQUALS PieceDecl RIGHT_SQUARE_BRACKET'
    t[1].rebirths.append({
        'unit': t[4], 'at': t[5], 'prom': t[7]
    })
    t[0] = t[1]

def p_Ply_Rebirth(t):
    'Ply : Ply LEFT_SQUARE_BRACKET PLUS LongPieceDecl SQUARE RIGHT_SQUARE_BRACKET'
    t[1].rebirths.append({
        'unit': t[4], 'at': t[5], 'prom': None
    })
    t[0] = t[1]


def p_Ply_Antirebirth_Promotion(t):
    'Ply : Ply LEFT_SQUARE_BRACKET LongPieceDecl SQUARE ARROW SQUARE EQUALS PieceDecl RIGHT_SQUARE_BRACKET'
    t[1].antirebirths.append({
        'unit': t[3], 'from': t[4], 'to': t[6], 'prom': t[8]
    })
    t[0] = t[1]


def p_Ply_Antirebirth(t):
    'Ply : Ply LEFT_SQUARE_BRACKET LongPieceDecl SQUARE ARROW SQUARE RIGHT_SQUARE_BRACKET'
    t[1].antirebirths.append({
        'unit': t[3], 'from': t[4], 'to': t[6], 'prom': None
    })
    t[0] = t[1]


# remote promotion happens eg in KobulKings capture
def p_Ply_Remote_Promotion(t):
    'Ply : Ply LEFT_SQUARE_BRACKET SQUARE EQUALS PieceDecl RIGHT_SQUARE_BRACKET'
    t[1].promotions.append({
        'unit': t[5],
        'at': t[3]
    })
    t[0] = t[1]


def p_Ply_Recoloring(t):
    'Ply : Ply LEFT_SQUARE_BRACKET SQUARE EQUALS ColorPrefix RIGHT_SQUARE_BRACKET'
    t[1].recolorings[model.COLORS_SHORT[t[5]]].append(t[3])
    t[0] = t[1]


def p_Ply_Removal(t):
    'Ply : Ply LEFT_SQUARE_BRACKET DASH SQUARE RIGHT_SQUARE_BRACKET'
    t[1].removals.append(t[4])
    t[0] = t[1]


def p_Ply_Imitators(t):
    'Ply : Ply IMITATOR_MOVEMENT_OPENING_BRACKET SquareList RIGHT_SQUARE_BRACKET'
    t[1].imitators = t[3]
    t[0] = t[1]

def p_Body_Normal(t):
    'Body : PieceDecl Squares'
    t[0] = t[2].setv("promotion", t[1]).setv("departant", t[1])


def p_Body_Castling(t):
    'Body : Castling'
    t[0] = t[1]


def p_Body_PawnMove(t):
    'Body : PawnMove'
    t[0] = t[1]


def p_PawnMove(t):
    '''PawnMove : Squares
        | PawnMove EN_PASSANT'''
    if len(t) == 2:
        t[0] = t[1].setv("promotion", model.Piece("P", "u", "")).setv("departant", model.Piece("P", "u", ""))
    else:
        t[0] = t[1].setEnPassant()


def p_Squares(t):
    '''Squares : SQUARE DASH SQUARE
        | SQUARE ASTERISK SQUARE
        | SQUARE ASTERISK SQUARE DASH SQUARE'''
    if len(t) == 4 and t[2] == "-":
        t[0] = MoveNode(t[1], t[3], -1)
    elif len(t) == 4 and t[2] == "*":
        t[0] = MoveNode(t[1], t[3], t[3])
    else:
        t[0] = MoveNode(t[1], t[5], t[3])


def p_Castling(t):
    '''Castling : KINGSIDE_CASTLING
        | QUEENSIDE_CASTLING'''
    t[0] = CastlingNode(t[1] == "0-0")


def p_error(t):
    if not t is None:
        raise Exception("Syntax error at '%s', line %d, char %d" % (t.value, t.lineno, t.lexpos))
    else:
        raise Exception("Terminating syntax error")


from lexer import *
parser = yacc.yacc()