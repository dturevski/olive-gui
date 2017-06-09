import re

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


class Query:

    def __init__(self):
        self.q, self.ps, self.ts = "", [], []

    def __init__(self, q, ps):
        self.q, self.ps, self.ts = q, ps, []

    def __init__(self, q, ps, ts):
        self.q, self.ps, self.ts = q, ps, ts

    def __str__(self):
        ts = ["problems2 p2"] + sorted(set(self.ts))
        return "select * from\n" + " join\n".join(ts) + "\nwhere " + self.q


class Predicate:

    def __init__(self, name, params):
        self.name, self.params = name, params

    def validate(self, params):
        for i, v in enumerate(params):
            if not self.params[i].domain.test(v):
                raise ValueError("'%s' is not a valid %s in %s(.. %s ..)" %
                                 (v, self.params[i].domain.name, self.name, self.params[i].name))

    def sql(self, params, cmp, ord):
        cs = ["pd.problem_id=p2.id", "pd.name=%s"]
        ps = [self.name]
        for i, val in enumerate(params):
            if val != Domain.wildcard:
                cs.append("exists (select * from predicate_params where pid=pd.id and pos=%d and val=%s)\n")
                ps.append(i)
                ps.append(val)
        return Query("(select count(*) from predicates pd where (%s)) %s %d\n" % (") and\n(".join(cs), cmp, ord),
                     ps)


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
        return Query(
                "(%s) %s\n(%s)" % (qleft.q, self.op, qright.q),
                qleft.ps + qright.ps, qleft.ts + qright.ts
            )


"""
create table predicates (
  id INTEGER not NULL AUTO_INCEREMENT,
  name VARCHAR (255) not null,
  problem_id INTEGER not NULL,

  PRIMARY key(id),
  key(problem_id, name)
)

create table predicate_params (
  pid INTEGER not NULL,
  pos INTEGER not NULL,
  val VARCHAR (255) not null,

  UNIQUE key(pid, pos),
  key(pid, pos, val)
)

"""