import sqlite3, datetime
print("")
print("***** ***** ***** *****")
def pause(): pz = input("<...>")
def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i += 1
    return q[:-1] + ")"
errors = {'new': 0, 'dupes': 0, 'missing': 0}

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

jdata.execute('SELECT distinct game_id, crtid FROM missing_data WHERE round_id is null and crtid is not null order by 1,2')
data = jdata.fetchall()

i=0
print(len(data))
for d in data:
    if d[1][5] == 'J': rnd = 1
    elif d[1][5] == 'D': rnd = 2
    elif d[1][5] == 'F': rnd = 3
    elif d[1][5] == 'T': rnd = 4

    jdata.execute('UPDATE missing_data SET round_id = ? WHERE game_id = ? and crtid = ?', (rnd,d[0],d[1]))
    conn_jdata.commit()
    print(d)
    #if i % 5 == 0: pause()

    i+=1


print("Wrote missing data for",i,"values")
