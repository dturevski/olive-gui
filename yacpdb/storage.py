import MySQLdb, MySQLdb.cursors
import entry

database = MySQLdb.connect(host = "localhost", user = "root", passwd = "", db = "yacpdb", cursorclass=MySQLdb.cursors.DictCursor)

"""
alter table problems2 add ash varchar(32);
alter table problems2 add key(ash);

create table auto_index (
    ash varchar(32) not null,
    updated datetime not null,
    valid integer not null,
    error varchar(255),
    primary key(ash)
);
"""


def commit(query, params):
    c = database.cursor(MySQLdb.cursors.Cursor)
    try:
        c.execute(query, params)
        database.commit()
    except Exception as ex:
        database.rollback()
        print ex
        print c._last_executed


def calculateHashes(count):
    c = database.cursor()
    c.execute("""
      select p.id, y.yaml from
      problems2 p join yaml y on (p.id = y.problem_id)
      where p.ash is NULL
      order by p.id limit %s
    """, (count,))

    ok, failed = 0, 0

    for row in c:
        try:
            e = entry.entry(row["yaml"])
        except Exception as ex:
            print "============ ID = %d" % row["id"]
            print ex
            failed += 1
            continue
        ash = entry.ash(e)
        database.cursor().execute("update problems2 set ash=%s where id=%s", (ash, row["id"]))
        ok += 1
        #print ash, row["id"]

    print "ok: %d, failed: %d" % (ok, failed)


def allEntries():
    c = database.cursor()
    c.execute("select p.id, y.yaml from problems2 p join yaml y on (p.id = y.problem_id) order by p.id")
    for row in c:
        try:
            e = entry.entry(row["yaml"])
            yield row["id"], entry.ash(e), e
        except:
            pass

def queryProblems():
    c = database.cursor()
    c.execute("""
        select
            p.id, y.yaml
        from
            problems2 p join
            yaml y on (p.id = y.problem_id) join
            auto_index ai on (p.ash = ai.ash)
        where
            ai.error like '\\'None%'
        order by p.id""")
    for row in c:
        e = entry.entry(row["yaml"])
        yield row["id"], entry.ash(e), e



def insertAuto(ash, valid, message):
    commit("""
          replace into auto_index
          (ash, valid, error, updated) values
          (%s, %s, %s, now())""", (ash, valid, message))


def search(query, params, page, pageSize=100):
    limits = " limit %d, %d" % ((page-1)*pageSize, pageSize)
    c, matches = database.cursor(), []
    c.execute(query + limits, params)
    lastExecuted = c._last_executed
    for row in c:
        e = entry.entry(row["yaml"])
        e["id"] = row['problem_id']
        matches.append(e)
    c.execute("select FOUND_ROWS() fr")
    return {'entries':matches, 'count': c.fetchone()["fr"], 'q':lastExecuted}




