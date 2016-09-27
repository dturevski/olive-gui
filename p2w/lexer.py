import ply.lex as lex
import model

# A string containing ignored characters
t_ignore = " \t\r\n"

# List of token names.
tokens = (
    'ROTATE',
    'IMITATOR_MOVEMENT_OPENING_BRACKET',
    'LEFT_SQUARE_BRACKET',
    'RIGHT_SQUARE_BRACKET',
    'COMMENT',
    'DASH',
    'ASTERISK',
    'PLUS',
    'EQUALS',
    'ANNOTATION',
    'MIRROR',
    'SHIFT',
    'POLISH_TYPE',
    'IMITATOR',
    'MOVE_NUMBER',
    'KINGSIDE_CASTLING',
    'QUEENSIDE_CASTLING',
    'INT',
    'SQUARE',
    'COLOR_NEUTRAL',
    'COLOR_WHITE',
    'COLOR_BLACK',
    'ELLIPSIS',
    'HALF_ELLIPSIS',
    'EN_PASSANT',
    'THREAT',
    'BUT',
    'ZUGZWANG',
    'TWIN_ID',
    'ARROW',
    'LONG_ARROW',
    'LONG_DOUBLE_ARROW',
    'DOUBLE_POINTED_ARROW',
    'FAIRY_PROPERTIES',
    'COMMA',
    'OTHER_CHECK_SIGN',
    'PIECE_NAME',
)

# tokens



t_LEFT_SQUARE_BRACKET = r'\['
t_RIGHT_SQUARE_BRACKET = r'\]'


def t_COMMENT(t):
    r'\{[^\{]*\}'
    t.value = t.value[1:-1]
    return t

t_DASH = r'\-'
t_ASTERISK = r'\*'
t_PLUS = r'\+'
t_EQUALS = r'='
t_OTHER_CHECK_SIGN = r'[#]'
t_ANNOTATION = r'[!\?][!\?]?'


# before INT
def t_MOVE_NUMBER(t):
    r'[0-9]+\.'
    t.value = 2 * int(t.value[:-1])
    return t

t_KINGSIDE_CASTLING = r'0\-0'
t_QUEENSIDE_CASTLING = r'0\-0\-0'

def t_INT(t):
    r'[1-9][0-9]*'
    t.value = int(t.value)
    return t


def t_SQUARE(t):
    r'[a-h][1-8]'
    t.value = model.algebraicToIdx(t.value)
    return t

t_COLOR_NEUTRAL = r'n'
t_COLOR_WHITE = r'w'
t_COLOR_BLACK = r'b'
t_ELLIPSIS = r'\.\.\.'
t_HALF_ELLIPSIS = r'\.\.'
t_EN_PASSANT = r'ep\.'
t_THREAT = r'threat:'
t_BUT = r'but'
t_ZUGZWANG = r'zugzwang\.'


def t_TWIN_ID(t):
    r'[a-z]\)'
    t.value = str(t.value[0])
    return t

t_ARROW = r'\->'
t_LONG_ARROW = r'\-\->'
t_LONG_DOUBLE_ARROW = r'==>'
t_DOUBLE_POINTED_ARROW = r'<\-\->'

def t_ROTATE(t):
    r'rotate'
    return t

t_MIRROR = r'mirror'
t_SHIFT = r'shift'
t_POLISH_TYPE = r'PolishType'
t_IMITATOR = r'Imitator'
t_IMITATOR_MOVEMENT_OPENING_BRACKET = r'\[I'
t_COMMA = r','

t_FAIRY_PROPERTIES = r'[cjkprvfhmu]+'
t_PIECE_NAME = r'([0-9A-Z][0-9A-Z])|[A-Z]'


def t_error(t):
    raise Exception("Illegal character '%s'" % t.value[0])

# Build the lexer
lexer = lex.lex()