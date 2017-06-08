from predicate import *

titleCase = '([A-Z][a-z0-9]*)+'

class PredicateStorage:

    def __init__(self):
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
        self.load('./yacpdb/indexer/indexer.md')

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
        if name in globals():
            return globals()[name](name, params)
        else:
            return Predicate(name, params)


class Id(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.id " + cmp + " %d", [ord], [])


class Stip(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.stipulation  rlike %s'", ["^" + params[0] + "$"], [])


class Author(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query(
            "au.name like %s", [params[0]],
            ['authorship aus on (p2.id = aus.problem_id)', 'authors au on (aus.author_id = au.id)']
        )


class Source(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query(
            "s.name like %s", [params[0]],
            ['sources s on (p2.source_id = s.id)']
        )





class DateAfter(Predicate):

    def __init__(self, name, params):
        Predicate.__init__(self, name, params)

    def sql(self, params, cmp, ord):
        return Query("p2.published > %s", [params[0]], [])

