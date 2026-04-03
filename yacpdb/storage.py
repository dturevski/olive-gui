import os, sys
import pymysql, pymysql.cursors
import logging, traceback
from . import entry


class Connection:
    instance = None
    
    def get():
        if Connection.instance is None:
            Connection.instance = pymysql.connect(host = "localhost", user = "root", passwd = "", db = "yacpdb",
                                   cursorclass=pymysql.cursors.DictCursor)
            Connection.instance.cursor().execute("SET NAMES utf8")
        return Connection.instance
    get = staticmethod(get)


def commit(query, params):
    c = Connection.get().cursor(pymysql.cursors.Cursor)
    try:
        c.execute(query, params)
        Connection.get().commit()
    except Exception as ex:
        Connection.get().rollback()
        print(ex)
        print(c._last_executed)


def mysqldt(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def entries(cursor):
    for row in cursor:
        try:
            e = entry.entry(row["yaml"])
            for key in ["id", "ash"]:
                if key in row:
                    e[key] = row[key]
            yield e
        except Exception as ex:
            pass
            #logging.error("Failed to unyaml entry %d" % row["id"])
            #logging.error(traceback.format_exc(ex))


def scalar(query, params):
    c = Connection.get().cursor(pymysql.cursors.Cursor)
    c.execute(query, params)
    for row in c:
        return row[0]
    return None


class Dao:

    def __init__(self):
        self.caches = None
        pass

    def ixr_getPredicateNameById(self, id_):
        self.ixr_initCache()
        return self.caches["in"][int(id_)]

    def ixr_getPredicateIdByName(self, name):
        self.ixr_initCache()
        try:
            return self.caches["ni"][name]
        except KeyError:
            Connection.get().cursor().execute("INSERT INTO predicate_names (name) VALUES (%s)", (name,))
            self.caches["ni"][name] = Connection.get().insert_id()
            return self.caches["ni"][name]

    def ixr_initCache(self):
        if self.caches != None:
            return
        self.caches = {"ni": {}, "in": {}}
        c = Connection.get().cursor()
        c.execute("SELECT id, name FROM predicate_names")
        for row in c:
            self.caches["ni"][row["name"]], self.caches["in"][row["id"]] = row["id"], row["name"]


    def ixr_getEntriesWithoutAsh(self, count):
        c = Connection.get().cursor()
        c.execute("""
          SELECT
            p.id, y.yaml
          FROM
            problems2 p JOIN
            yaml y ON p.id = y.problem_id
          WHERE
            p.ash IS NULL
          ORDER BY
            p.id
          LIMIT %s
        """, (count,))
        return entries(c)

    def ixr_updateEntryAsh(self, eid, ash):
        Connection.get().cursor().execute("update problems2 set ash=%s where id=%s", (ash, eid))

    def ixr_updateEntryOrtho(self, eid, ortho):
        Connection.get().cursor().execute("update problems2 set orthodox=%s where id=%s", ("1" if ortho else "0", eid))

    def allEntries(self):
        c = Connection.get().cursor()
        c.execute("""
          SELECT
            p.id, y.yaml
          FROM
            problems2 p join
            yaml y on p.id = y.problem_id
          ORDER BY
            p.id
            """)
        return entries(c)

    def ixr_updateCruncherLog(self, ash, error):
        commit("""
          REPLACE INTO
            cruncher_timestamps
            (ash, checked, error)
          VALUES
            (%s, now(), %s)
          """, (ash, error))

    def ixr_getLastRun(self, ash):
        return scalar("SELECT checked from cruncher_timestamps WHERE ash=%s", (ash,))

    def ixr_getNeverChecked(self, maxcount):
        c = Connection.get().cursor()
        c.execute("""
          SELECT
            p.id, p.ash, y.yaml
          FROM 
            problems2 p JOIN
            yaml y ON p.id = y.problem_id LEFT JOIN 
            cruncher_timestamps ct ON p.ash = ct.ash
          WHERE 
            p.ash IS NOT NULL and ct.ash IS NULL
          ORDER BY p.id
          LIMIT %d
          """ % maxcount)
        return entries(c)

    def ixr_getNotCheckedSince(self, since, maxcount):
        c = Connection.get().cursor()
        c.execute("""
          SELECT
            p.id, p.ash
          FROM 
            problems2 p JOIN
            yaml y ON p.id = y.problem_id JOIN 
            cruncher_timestamps ct ON p.ash = ct.ash
          WHERE 
            ct.checked < %s
          ORDER BY
            ct.checked
          limit 
          """ + str(maxcount), (mysqldt(since),))
        return entries(c)

    def ixr_saveAnalysisResults(self, ash, analysisResults):
        c = Connection.get().cursor()
        for key, predicate in analysisResults.predicates.items():
            c.execute("INSERT INTO predicates (name_id, ash, matchcount) VALUES (%s, %s, %s)",
                      (self.ixr_getPredicateIdByName(predicate.name), ash, str(analysisResults.counts[key])))
            pid = Connection.get().insert_id()
            for i, param in enumerate(predicate.params):
                c.execute("INSERT INTO predicate_params (pid, pos, val) VALUES (%s, %s, %s)",
                          (str(pid), str(i), param))

    def ixr_deleteAnalysisResults(self, ash):
        c, c2 = Connection.get().cursor(), Connection.get().cursor()
        c.execute("SELECT id FROM predicates WHERE ash=%s", (ash,))
        for row in c:
            c2.execute("DELETE FROM predicate_params WHERE pid=%s", (row["id"],))
        c.execute("DELETE FROM predicates WHERE ash=%s", (ash,))

    def ixr_getPredicatesByAsh(self, ash):
        c, c2, ps = Connection.get().cursor(), Connection.get().cursor(), {}
        c.execute("""SELECT id, name_id, matchcount FROM  predicates WHERE ash = %s""", (ash,))
        for row in c:
            params = []
            c2.execute("SELECT val FROM predicate_params where pid=%s ORDER BY pos", (row["id"],))
            for row2 in c2:
                params.append(row2["val"])
            name = self.ixr_getPredicateNameById(row["name_id"])
            if len(params) > 0:
                name = "%s(%s)" % (name, ", ".join(params))
            ps[name] = row["matchcount"]
        return ps


    def search(self, query, params, page, pageSize=100):
        limits = " limit %d, %d" % ((page-1)*pageSize, pageSize)
        c, matches = Connection.get().cursor(), []
        for p in params:
           logging.debug(str(p) + ", " + str(type(params[0])))
        c.execute(query + limits, params)
        #lastExecuted = c._last_executed
        for row in c:
            try:
                e = entry.entry(row["yaml"])
                e["id"] = row['problem_id']
                e["ash"] = row['ash']
                matches.append(e)
            except Exception as ex:
                logging.error("Bad YAML: %d" % row['problem_id'])
        c.execute("select FOUND_ROWS() fr")
        return {
            'entries':matches,
            'count': c.fetchone()["fr"],
            # 'q':lastExecuted
        }

    def findByFen(self, fen):
        return scalar("select id from problems2 where fen=%s", (fen,))

dao = Dao()



