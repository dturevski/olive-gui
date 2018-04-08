import re
from .. import storage
import logging

titleCase = '([A-Z][a-z0-9]*)+'

class Domain:

    wildcard = "*"

    def __init__(self, name, regexp):
        self.name, self.regexp = name, re.compile('^' + regexp + '$')

    def test(self, value):
        return (value == Domain.wildcard) or (self.regexp.match(str(value).decode("utf8")) is not None)


class Param:

    def __init__(self, name, domain):
        self.name, self.domain = name, domain

    def parse(line, ds):
        ps = [x.strip() for x in line.split(' ')]
        if len(ps) != 2:
            raise ValueError("'%s' is not a valid param declaration" % line)
        if ps[0] not in ds:
            raise ValueError("'%s': unknown domain" % ps[0])
        return Param(ps[1], ds[ps[0]])
    parse = staticmethod(parse)

    def getDeclarationString(self):
        return "%s %s" % (self.domain.name, self.name)



class Query:

    # q, ps, ts = query, parameters, tables
    def __init__(self, q, ps, ts):
        self.q, self.ps, self.ts = q, ps, ts
        self.preExecute = []

    def __str__(self):
        ts = ["problems2 p2 join yaml y on p2.id=y.problem_id"] + sorted(set(self.ts))
        return "select SQL_CALC_FOUND_ROWS y.*, p2.ash from\n" + " join\n".join(ts) + "\nwhere " + self.q

    def execute(self, page):
        for (q, ps) in self.preExecute:
            storage.commit(q, ps)
        return storage.dao.search(str(self), tuple(self.ps), page)


class Predicate:

    def __init__(self, name, params):
        self.name, self.params, self.doc = name, params, ""

    def validate(self, params):
        for i, v in enumerate(params):
            if not self.params[i].domain.test(v):
                raise ValueError("'%s' is not a valid %s in %s(.. %s ..)" %
                                 (v, self.params[i].domain.name, self.name, self.params[i].name))

    def sql(self, params, cmp, ord):
        cs = ["pd.ash=p2.ash", "pd.name_id=%d" % storage.dao.ixr_getPredicateIdByName(self.name)]
        ps = []
        for i, val in enumerate(params):
            # todo: unbound params
            if val != Domain.wildcard:
                cs.append("exists (select * from predicate_params where pid=pd.id and pos=%s and val=%s)\n")
                ps.append(str(i))
                ps.append(val)
        return Query("(select COALESCE(sum(pd.matchcount), 0) from predicates pd where (%s)) %s %d\n" % (") and\n(".join(cs), cmp, ord),
                     ps, [])

    def getDeclarationString(self):
        if len(self.params) == 0:
            return self.name
        return "%s(%s)" % (self.name, ", ".join([p.getDeclarationString() for p in self.params]))


class ExprPredicate:

    def __init__(self, name):
        self.name, self.params, self.cmp, self.ord = name, [], '>', 0

    def validate(self, stor):
        p = stor.get(len(self.params), self.name).validate(self.params)

    def sql(self, stor):
        return stor.get(len(self.params), self.name).sql(self.params, self.cmp, self.ord)


class ExprNegation:

    def __init__(self, expr):
        self.expr = expr

    def validate(self, stor):
        self.expr.validate(stor)

    def sql(self, stor):
        q = self.expr.sql(stor)
        q.q = "not (%s)" % q.q
        return q


class ExprJunction:

    def __init__(self, op, left, right):
        self.op, self.left, self.right = op, left, right

    def validate(self, stor):
        self.left.validate(stor)
        self.right.validate(stor)

    def sql(self, stor):
        qleft = self.left.sql(stor)
        qright = self.right.sql(stor)
        q = Query(
                "(%s) %s\n(%s)" % (qleft.q, self.op, qright.q),
                qleft.ps + qright.ps, qleft.ts + qright.ts
            )
        q.preExecute = qleft.preExecute + qright.preExecute
        return q


class AnalysisResult:

    RE_NO_PARAMS = re.compile('^' + titleCase + '$')
    RE_HAS_PARAMS = re.compile('^(?P<name>' + titleCase + ')\((?P<params>.*)\)$')

    def __init__(self, name, params):
        self.name, self.params = name, params

    def __str__(self):
        if len(self.params) == 0:
            return self.name
        else:
            return "%s(%s)" % (self.name, ", ".join(self.params))

    def fromString(s):
        if AnalysisResult.RE_NO_PARAMS.match(s):
            return AnalysisResult(s, [])
        matches = AnalysisResult.RE_HAS_PARAMS.match(s)
        if matches:
            return AnalysisResult(matches.group("name"), matches.group("params").split(", "))
        raise NameError("%s is not a valid AnalyzisResult identificator" % s)
    fromString=staticmethod(fromString)


class AnalysisResultAccumulator:

    def __init__(self, predicateStorage):
        self.counts, self.predicates, self.predicateStorage = {}, {}, predicateStorage

    def push(self, s):
        ar = AnalysisResult.fromString(s)
        self.predicateStorage.validate(ar)
        self.predicates[s] = ar;
        if s in self.counts:
            self.counts[s] += 1
        else:
            self.counts[s] = 1

    def __str__(self):
        return "\n".join(["%s: %d" % (k, self.counts[k]) for k in sorted(self.counts.keys())])
