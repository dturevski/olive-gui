
from predicate import *
try:
    from board import *
except ImportError as e:
    from olive.board import *


class PredicateStorage:

    def __init__(self, dir):
        self.ds = {
            'CAPTUREFLAG': Domain('CAPTUREFLAG', '(WithCaptures)|(Captureless)'),
            'COLOR': Domain('COLOR', '[wbn]'),
            'DATE': Domain('DATE', r'[0-9]{4}(\-[0-9]{2}(\-[0-9]{2})?)?'),
            'INTEGER': Domain('INTEGER', '[0-9]+'),
            'PIECENAME': Domain('PIECENAME', '[0-9A-Z][0-9A-Z]?'),
            'PIECE': Domain('PIECE', '[wbn][0-9A-Z][0-9A-Z]?'),
            'STRING': Domain('STRING', '.*'),
        }
        self.ps = {}
        self.load(dir + 'yacpdb/indexer/indexer.md')

    fmt1 = re.compile('^\* `(' + titleCase + ')\((.*)\)`$') # non-zero arity
    fmt2 = re.compile('^\* `(' + titleCase + ')`$') # zero arity

    def get(self, arity, name):
        if arity not in self.ps or name not in self.ps[arity]:
            raise NameError("Unknown %d-nary predicate '%s'" % (arity, name))
        return self.ps[arity][name]

    def load(self, fname):
        with open(fname) as f:
            for line in f.readlines():
                try:
                    p = None
                    match = PredicateStorage.fmt1.match(line.strip())
                    if match:
                        p = self.createInstance(match.group(1),
                                      [Param.parse(s.strip(), self.ds) for s in match.group(3).split(',')])
                    else:
                        match = PredicateStorage.fmt2.match(line.strip())
                        if match:
                            p = self.createInstance(match.group(1), [])
                    if p is not None:
                        arity = len(p.params)
                        if arity not in self.ps: self.ps[arity] = {}
                        self.ps[arity][p.name] = p
                except ValueError as e:
                    raise ValueError("%s in '%s'" % (str(e), line.strip()))

    def createInstance(self, name, params):
        return (globals()[name] if name in globals() else Predicate)(name, params)

    def validate(self, analysisResult):
        arity = len(analysisResult.params)
        if (arity not in self.ps) or (analysisResult.name not in self.ps[arity]):
            raise ValueError("Predicate %s with arity %d is not in the predicate storage"
                             % (analysisResult.name, arity))
        self.ps[arity][analysisResult.name].validate(analysisResult.params)


class Matrix(Predicate):

    transformations = [
        ((1, 0), (0, 1)),
        ((0, 1), (-1, 0)),
        ((-1, 0), (0, -1)),
        ((0, -1), (1, 0)),
        ((1, 0), (0, -1)),
        ((-1, 0), (0, 1)),
        ((0, 1), (1, 0)),
        ((0, 1), (1, 0))
    ]

    rePieceDeclaration = re.compile(r'^([wnb][a-z0-9][a-z0-9]?)([a-h][1-8])$')

    # select piece, count(*) c from coords group by piece order by c;
    frequency = ['bq', 'wq', 'br', 'bs', 'bb', 'wr', 'wk', 'bk', 'wb', 'ws', 'wp', 'bp']

    class Placement:

        def __init__(self, name, square):
            self.name, self.square = name, square

    temporaryTableIndex = 0

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)
        self.placements = []

    def validate(self, params):
        Predicate.validate(self, params)
        self.placements = [self.parse(spec.strip().lower()) for spec in params[0].split(" ") if spec != ""]

    def parse(self, spec):
        match = Matrix.rePieceDeclaration.match(spec)
        if not match:
            raise ValueError("'%s' is not a valid piece specification in Matrix(piecelist)" % spec)
        return Matrix.Placement(match.group(1), Square(algebraicToIdx(match.group(2))))

    def compare(self, a, b):
        ia, ib = len(Matrix.frequency), len(Matrix.frequency)
        try: ia, ib = Matrix.frequency.index(a.name), Matrix.frequency.index(b.name)
        except: pass
        return ia - ib

    def transform(self, cs, T):
        return [Matrix.Placement(c.name, Square(
                T[0][0]*c.square.x + T[0][1]*c.square.y,
                T[1][0]*c.square.x + T[1][1]*c.square.y,
                )) for c in cs]

    def sql(self, params, cmp, ord):

        table, alias = "matrix%d" % Matrix.temporaryTableIndex, "tmpMatrix%d" % Matrix.temporaryTableIndex
        Matrix.temporaryTableIndex += 1
        query = Query("1", [], ["%s %s on p2.id=%s.id" % (table, alias, alias)])
        query.preExecute.append(("create temporary table %s (id "
                                 "integer not null, primary key(id)) "
                                 "engine=memory" % table, []))

        cs = sorted(self.placements, cmp=self.compare)
        for i, p in enumerate(cs):
            if i > 0: p.square = Square(p.square.x - cs[0].square.x, p.square.y - cs[0].square.y)
        for T in Matrix.transformations:
            cs_, q = self.transform(cs, T), ""
            for i in xrange(1, len(cs_)):
                q += "join coords c{i} on (c{i}.piece={n} and c{i}.problem_id = c0.problem_id and " \
                     "c{i}.x = c0.x + ({x}) and c{i}.y = c0.y + ({y}))\n" \
                    .format(i=i, n=Matrix.pieceCode(cs_[i].name), x=cs_[i].square.x, y=cs_[i].square.y)
            q = "insert ignore into %s (id) select c0.problem_id from coords c0\n %s where c0.piece=%d" %\
                (table, q,  Matrix.pieceCode(cs_[0].name))
            query.preExecute.append((q, []))

        return query

    def pieceCode(piece):
        code = 0
        for char in piece.lower():
            code = code*256 + ord(char)
        return code
    pieceCode = staticmethod(pieceCode)


class Id(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.id " + cmp + " %s", [str(ord)], [])

class Author(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query(
            "au.name like %s", [params[0]],
            ['authorship aus on (p2.id = aus.problem_id) join authors au on (aus.author_id = au.id)']
        )


class Source(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("s.name like %s", [params[0]], ['sources s on (p2.source_id = s.id)'])


class IssueId(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.issue_id = %s", [params[0]], [])


class SourceId(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.local_id = %s", [params[0]], [])


class DateAfter(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.published > %s", [params[0]], [])



class Stip(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.stipulation  rlike %s'", ["^" + params[0] + "$"], [])


class Option(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        if params[0] == Domain.wildcard:
            return self.wildcard(cmp, ord)
        return Query("p2.id in (select problem_id from options where o=%s)", [params[0]], [])

    def wildcard(self, cmp, ord):
        return Query("p2.id in (select id from problems2 p2 where "
                     "(select count(*) from options o where o.problem_id=p2) " + cmp + " %d", [ord], [])


class Keyword(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.id in (select problem_id from "
                     "tags_to_problems tp join "
                     "tags t on tp.tag_id=t.id "
                     "where t.name like %s)", [params[0]], [])


class With(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        raise NotImplementedError()
        if params[0] == Domain.wildcard:
            return self.wildcard(cmp, ord)
        return Query("p2.id in (select problem_id from options where o=%s)", [params[0]], [])

