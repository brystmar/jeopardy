import sqlite3, re, datetime
print("")
print("***** ***** ***** *****")

def decode(a):
    a = a.replace("\\'","'")
    return html.unescape(str(a))

def pause():
    #print("")
    programPause = input("...")#input("Press the <ENTER> key to continue...")

# open & initialize the db
jdata_conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = jdata_conn.cursor()
jtemp_conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
jtemp = jtemp_conn.cursor()

jtemp.execute('SELECT * FROM commbreak order by 1,2')
cbdata = jtemp.fetchall()

i = 0
for c in cbdata:
    #print(len(c), len(cbdata))
    game_id = int(c[0])
    try: cbb = int(c[1])
    except: cbb = None
    #pause()
    jdata.execute('UPDATE game SET clues_before_break = ? WHERE id = ?', (cbb, game_id))

    i += 1

print("Wrote", i, "values")

jdata_conn.commit()
jdata_conn.close()
# """
