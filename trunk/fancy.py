# 3rd party
import yaml

# local
import model

def fancyCodeToPiece(code):
    fancy = 'prsbqkgn'
    color = ['black', 'white'][code % 2]
    if code > 16:
        return model.Piece('DU', color, [])
    return model.Piece(fancy[(code-1) >> 1], color, [])
    
def parseTwins(lines):
    twins = {}
    id = 'b'
    if len(lines[0]) > 4 and str(lines[0][0:3]).lower() == 'zero':
        id = 'a'
    for line in lines:
        if line.strip() == '':
            continue
        twins[id] = (' '.join((line.split(' '))[1:])).strip()
        id = chr(ord(id) + 1)
    return twins

def parseConditions(words):
    conditions = []
    acc = []
    for word in words:
        word = word.strip()
        if word == '':
            continue
        if isConditionStartWord(word):
            if len(acc):
                conditions.append(' '.join(acc))
            acc = [word]
        else:
            acc.append(word)
    if len(acc):
        conditions.append(' '.join(acc))
    return conditions

def isConditionStartWord(word):
    word = word.lower()
    for c in model.FairyHelper.conditions:
        if len(c) >= len(word) and word == (c[0:len(word)]).lower():
            return True
    return False
    
def readCvv(fileName, encoding):
    h = open(unicode(fileName), 'r')
    contents = "\n".join([x.strip() for x in h.readlines()])
    contents = unicode(contents.decode(encoding))
    h.close()
    entries = []
    for chunk in contents.split("\n\n"):
        lines = chunk.strip().split("\n")
        if len(lines) < 2:
            continue
        # removing Dg[x]=new Array line 
        lines = lines[1:]
        # removing trailing semicolon
        lines[-1] = lines[-1][:-1]
        # changing brackets to square brackets:
        chunk = ''.join(lines)
        chunk = '[' + chunk[1:-1] + ']'
        e = yaml.load(chunk)
        
        # creating yacpdb-like entry
        entry = {}
        board = model.Board()
        for i in xrange(64):
            code = e[i>>3][i%8]
            if code:
                board.add(fancyCodeToPiece(code), i)
        entry['algebraic'] = board.toAlgebraic()
        if e[8][0] != '':
            entry['authors'] = [e[8][0]]
        if e[9][0] != '':
            entry['source'] = e[9][0]
        if e[10][0] != '':
            entry['solution'] = "\n".join(e[10][0].split('\\n'))
        extra = e[11][0].split('\\n')
        stip_cond = extra[0].split(' ')
        entry['stipulation'] = stip_cond[0]
        if len(stip_cond) > 1:
            entry['options'] = parseConditions(stip_cond[1:])
        if len(extra) > 1:
            entry['twins'] = parseTwins(extra[1:])
        
        entries.append(entry)
    return entries