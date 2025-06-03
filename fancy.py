# 3rd party
import yaml

# local
import model

# order matters, copied from the end of the binary fancy.exe (v2.9)
FANCY_PIECES = [
    '15', '16', '24', '25', '35', '37', 'al', 'am', 'an', 'ao', 'ar',
    'b', 'bh', 'bk', 'bl', 'bp', 'br', 'bs', 'bt', 'bu', 'c', 'ca', 'cg',
    'ch', 'cr', 'ct', 'cy', 'da', 'dg', 'dr', 'ds', 'du', 'ea', 'eh', 'ek', 'em',
    'eq', 'fe', 'fr', 'g', 'g2', 'g3', 'gh', 'gi', 'gl', 'gn', 'gr', 'gt', 'ha',
    'k', 'ka', 'kh', 'l', 'lb', 'le', 'li', 'ln', 'lr', 'm', 'ma', 'mo',
    'n', 'nd', 'ne', 'nh', 'o', 'oa', 'ok', 'or', 'p', 'pa', 'pr', 'q',
    'r', 'rb', 'rf', 'rh', 'rl', 'rn', 'ro', 'rp', 'rr', 's', 'si', 'sk',
    'sp', 'sq', 'ss', 'sw', 'tr', 'uu', 'va', 'wa', 'we', 'wr', 'z', 'zh',
    'zr', 'ag', 'be', 'bi', 'bm', 'bw', 'do', 'et', 'f', 'mg', 'ml', 'mm',
    'na', 'nl', 'ra', 're', 'rm', 'rw', 'so', '36', 'b1', 'b2', 'b3', 'bo', 'cp',
    'qe', 'qf', 'qq', 'rt', 'pp', 'rk', 'ze'
]
FANCY_SPECS = ['Chameleon', 'Jigger', 'Kamikaze', 'Paralysing',
               'Royal', 'Volage', 'Beamtet', 'Functionary', 'HalfNeutral',
               'HurdleColourChanging', 'Protean', 'Magic', 'Uncapturable',
               'Bul', 'Dob', 'Anda', 'AndaInverse']


def fancyCodeToPiece(code):
    if code <= 16:
        fancy = 'prsbqkgn'
        color = ['black', 'white'][code % 2]
        return model.Piece(fancy[(code - 1) >> 1], color, [])
    try:
        color = ['white', 'black', 'neutral'][(code % 100) - 17]
        name = FANCY_PIECES[((code // 100) % 1000) - 1]
        specs = []
        if (code // 100000) > 0:
            specs.append(FANCY_SPECS[(code // 100000) - 1])
        return model.Piece(name, color, specs)
    except:
        return model.Piece('du', 'black', [])


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
        if word == '' or word.lower() == 'imitator':
            continue
        if isConditionStartWord(word):
            if len(acc):
                conditions.append(' '.join(acc))
            acc = [word]
        else:
            print('not starting', word)
            acc.append(word)
    if len(acc):
        conditions.append(' '.join(acc))
    return conditions


def isConditionStartWord(word):
    word = word.lower()
    for c in model.FairyHelper.instance.conditions:
        if len(c) >= len(word) and word == (c[0:len(word)]).lower():
            return True
    return False


def readCvv(fileName, encoding):
    h = open(str(fileName), 'r')
    contents = "\n".join([x.strip() for x in h.readlines()])
    contents = str(contents.decode(encoding))
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
        e = yaml.safe_load(chunk)

        # creating yacpdb-like entry
        entry = {}
        board = model.Board()
        imitators = []
        for i in range(64):
            code = e[i >> 3][i % 8]
            if code:
                if code == 20:
                    imitators.append(model.idxToAlgebraic(i))
                else:
                    board.add(fancyCodeToPiece(code), i)
        entry['algebraic'] = board.toAlgebraic()
        if e[8][0] != '':
            entry['authors'] = [e[8][0]]
        if e[9][0] != '':
            entry['source'] = { 'name': e[9][0] }
        if e[10][0] != '':
            entry['solution'] = "\n".join(e[10][0].split('\\n'))
        extra = e[11][0].split('\\n')
        stip_cond = extra[0].split(' ')
        entry['stipulation'] = stip_cond[0]
        entry['options'] = []
        if len(imitators):
            entry['options'].append('Imitator ' + ''.join(imitators))
        if len(stip_cond) > 1:
            entry['options'].extend(parseConditions(stip_cond[1:]))
        if len(extra) > 1:
            entry['twins'] = parseTwins(extra[1:])

        entries.append(entry)
    return entries
