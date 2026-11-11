import sqlite3,sys
db=sqlite3.connect("file:<runtime>/worldkit/cp_zmb.sqlite?mode=ro",uri=True)
def q(s,a=()):
    return db.execute(s,a).fetchall()
if __name__=="__main__":
    for r in q("select name,sql from sqlite_master"): print(r[0]); print(r[1]);print()
    for r in q("select * from meta limit 50"): print(r)
