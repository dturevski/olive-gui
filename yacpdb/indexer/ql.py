import ply.yacc
import ply.lex
import predicate

# tokens

t_ignore = " \t\r\n"
literals = "(,)"
tokens = ('CMP', 'NOT', 'AND', 'OR', 'INT', 'TCS', 'SSTR', 'DSTR', 'USTR')

t_CMP = r'[><=]'

def t_AND(t):
    r'[Aa][Nn][Dd]'
    t.value = t.value.upper()
    return t

def t_NOT(t):
    r'[Nn][Oo][Tt]'
    t.value = t.value.upper()
    return t

def t_OR(t):
    r'[Oo][Rr]'
    t.value = t.value.upper()
    return t

def t_INT(t):
    r'[1-9][0-9]*'
    t.value = int(t.value)
    return t

def t_TCS(t):
    r'([A-Z][a-z0-9]*)+'
    return t

def t_SSTR(t):
    r'\'[^\']*\''
    t.value = t.value[1:-1]
    return t

def t_DSTR(t):
    r'\"[^\"]*\"'
    t.value = t.value[1:-1]
    return t

def t_USTR(t):
    r'[^\'\"\(\),<>=]+'
    return t

def t_error(t):
    raise Exception("Illegal character '%s'" % t.value[0])

# rules

def p_Expr(t):
    '''Expr : Pred
        | Pred CMP INT
        | '(' Expr ')'
        | NOT Expr
        | Expr AND Expr
        | Expr OR Expr'''
    if len(t) == 2:
        t[0] = t[1]
    elif len(t) == 3:
        t[0] = predicate.ExprNegation(t[2])
    elif t[2] in ["AND", "OR"]:
        t[0] = predicate.ExprJunction(t[2], t[1], t[3])
    elif t[1] == '(':
        t[0] = t[2]
    else:
        t[0] = t[1]
        t[0].cmp = t[2]
        t[0].ord = t[3]

def p_Pred(t):
    '''Pred : TCS
        | TCS '(' ParamList ')' '''
    t[0] = predicate.ExprPredicate(t[1])
    if len(t) > 2:
        t[0].params = t[3]

def p_ParamList(t):
    '''ParamList : Param
        | Param ',' ParamList'''
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[0] =[t[1]] + t[3]

def p_Param(t):
    '''Param : INT
        | Str'''
    t[0] = t[1]

def p_Str(t):
    '''Str : SSTR
        | DSTR
        | USTR'''
    t[0] = t[1]


def p_error(t):
    if not t is None:
        raise Exception("Syntax error at '%s', line %d, char %d" % (t.value, t.lineno, t.lexpos))
    else:
        raise Exception("Terminating syntax error")

lexer=ply.lex.lex(debug=0)
parser = ply.yacc.yacc()