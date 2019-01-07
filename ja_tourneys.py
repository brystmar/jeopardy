"""
Hammer out the distinct tourneys, load them into the tourneys table
"""
import sqlite3, re
print("")
print("***** ***** ***** *****")
print("")

# open & initialize the db
conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
cur = conn.cursor()

cur.execute('SELECT distinct season_id, notes FROM game WHERE type = "T" ORDER BY notes')
games = cur.fetchall()

cur.execute('SELECT distinct id, name FROM tournament_type ORDER BY id')
types = cur.fetchall()

i=0
tid = 1
tourneys = list()
raw = list()

for g in games:
    season_id = g[0]
    notes = g[1]
    name = ""
    year = None
    ttype = None
    val = None

    print(g)

    if "Million Dollar Celebrity Invitational" in notes: year = 2010
    if "Battle of the Decades" in notes:
        year = 2014
        name = "2014 Battle of the Decades"
    else: year = int(g[1][:4])

    if "1998 Teen Reunion Tournament" in notes:
        name = "1998 Teen Reunion Tournament"
        ttype = 7 #"Teen"
    elif "Ultimate Tournament of Champions" in notes:
        name = "2005 Ultimate Tournament of Champions"
        ttype = 1 #"Ultimate Tournament of Champions"
    elif "Battle of the Decades" in notes:
        name = "2014 Battle of the Decades"
        ttype = 8
    else:
        name = re.findall('(^.*) \w*[f|F]inal',notes)[0]
        #ttype = re.findall('\d* (.*) \w*[f|F]inal',notes)[0]
        j=0
        for t in types:
            if t[1] in name:
                ttype = int(t[0])


    #print(i, name + ".", "Type:",ttype)
    #if i % 50 == 0: x = input("Pausing...")
    #if x == 0: quit()
    n2 = name
    cur.execute('SELECT * FROM t2 WHERE name = ?',(name,))
    val = cur.fetchone()
    if val == None:
        cur.execute('INSERT INTO t2 (id,name,year,season_id,type_id) VALUES (?,?,?,?,?)', (tid,name,year,season_id,ttype))
        conn.commit()
        tid += 1
    #if i > 300: quit()
    i += 1

conn.commit()
conn.close()
quit()

tourney_items = list(set(tourneys))
tourney_items.sort()
raw_items = list(set(raw))
raw_items.sort()

j=0

print(len(raw_items))
for r in raw_items:
    print(r)
x = input("Pausing...")

print(len(tourney_items))
for item in tourney_items:
    print(item)
#print(i, season_id, year, name)
# """
