import MySQLdb, MySQLdb.cursors
import logging, traceback
import entry

database = MySQLdb.connect(host = "localhost", user = "root", passwd = "", db = "yacpdb", cursorclass=MySQLdb.cursors.DictCursor)
database.cursor().execute("SET NAMES utf8")

def commit(query, params):
    c = database.cursor(MySQLdb.cursors.Cursor)
    try:
        c.execute(query, params)
        database.commit()
    except Exception as ex:
        database.rollback()
        print ex
        print c._last_executed

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
            logging.error("Failed to unyaml entry %d" % row["id"])
            logging.error(traceback.format_exc(ex))


class Dao:

    def __init__(self): pass

    def ixr_getEntriesWithoutAsh(self, count):
        c = database.cursor()
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
        entries(c)

    def ixr_updateEntryAsh(self, eid, ash):
        database.cursor().execute("update problems2 set ash=%s where id=%s", (ash, eid))

    def allEntries(self):
        c = database.cursor()
        c.execute("""
          SELECT
            p.id, y.yaml
          FROM
            problems2 p join
            yaml y on p.id = y.problem_id
          ORDER BY
            p.id
            """)
        entries(c)

    def ixr_updateCruncherLog(self, ash, error):
        commit("""
          REPLACE INTO
            cruncher_timestamps
            (ash, checked, error)
          VALUES
            (%s, now(), %s)
          """, (ash, error))

    def ixr_getNeverChecked(self, maxcount):
        c = database.cursor()
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
          limit %s
          """, (str(maxcount), ))
        entries(c)

    def ixr_getNotCheckedSince(self, since, maxcount):
        c = database.cursor()
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
          limit %s
          """, (str(maxcount), mysqldt(since)))

    def search(self, query, params, page, pageSize=100):
        limits = " limit %d, %d" % ((page-1)*pageSize, pageSize)
        c, matches = database.cursor(), []
        for p in params:
           logging.debug(str(p) + ", " + str(type(params[0])))
        c.execute(query + limits, params)
        lastExecuted = c._last_executed
        for row in c:
            e = entry.entry(row["yaml"])
            e["id"] = row['problem_id']
            matches.append(e)
        c.execute("select FOUND_ROWS() fr")
        return {'entries':matches, 'count': c.fetchone()["fr"], 'q':lastExecuted}

dao = Dao()



