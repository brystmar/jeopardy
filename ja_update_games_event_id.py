"""
Match html events to the events table, then write prize data to the event_prizes table.
Also adds data to the event_round_game table.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime, itertools
print("")
print("***** ***** ***** *****")
filename = "ja_update_games_event_id.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

i=0
j=0
k=0
gcount = 0
err = list()
errors = {'new': 0, 'dupes': 0, 'missing': 0}

def pause(): pz = input("====")
def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i += 1
    return q[:-1] + ")"
def pp(item):
    print("")
    print(item)
    pause()
def printlist(items):
    newlist = list()
    ditems = set(items)
    for d in ditems:
        newlist.append(d)
    newlist.sort()
    for n in newlist:
        print(items.count(n), n)
    pause()
def printlists(items):
    for i in items:
        print(i)
    #pause()
def printdict(items):
    #if 'card' not in str(items): return 0
    for i in items:
        print(i, items[i])
    pause()
    print("")
def remove_html_tags(t):
    t = str(t)
    # find & fix erroneous starting tags, ex: </i>text</i>
    if re.search('^</([a-zA-Z])>', t.strip()):
        t = "<" + re.findall('^</([a-zA-Z])>', t.strip())[0] + ">" + t[4:]
    # prep for soupification
    t = t.strip()
    t = "<td>" + str(t) + "</td>"
    soup = BeautifulSoup(t, "html.parser")
    return soup.td.text.strip() #soup returns the text string without formatting tags like <b>, <u>, <i>
def write_errors(game_id, crtid, notes):
    global errors
    global filename

    # save the timestamp
    timestamp = datetime.datetime.now()
    timestamp = timestamp.isoformat(timespec='seconds')
    timestamp = str(timestamp).replace("T", " ")

    if crtid == None: crtid = 'n/a'

    jdata.execute('SELECT distinct game_id, crtid, notes FROM errors WHERE game_id = ? and crtid = ? and notes = ?', (game_id, crtid, notes))
    val = jdata.fetchone()
    if val == None:
        # new error
        jdata.execute('INSERT INTO errors (game_id, crtid, timestamp, filename, notes) VALUES ' + qmarks(5), (game_id, crtid, timestamp, filename, notes))
        errors['new'] += 1
    elif val[0] != game_id or val[1] != crtid or val[2] != notes:
        # new error
        jdata.execute('INSERT INTO errors (game_id, crtid, timestamp, filename, notes) VALUES ' + qmarks(5), (game_id, crtid, timestamp, filename, notes))
        errors['new'] += 1
    else:
        # error has already been recorded
        print('Error data already exists for', game_id, crtid)
        errors['dupes'] += 1

    #conn_jdata.commit()

jdata.execute('SELECT distinct id, notes FROM game WHERE event_id is null and event_theme is not null order by 1')
games = jdata.fetchall()

if games == None:
    print("No games to update.")
    quit()

jdata.execute('SELECT distinct id, name FROM event order by 1')
events = jdata.fetchall()

i=0
updated = list()
for g in games:
    event_id = None
    game = None
    name = None
    e = None

    for e in events:
        if e[1] in g[1]:
            event_id = e[0]
            name = e[1]
            break

    game = int(re.findall('game (\d+)', g[1])[0])

    #print(event_id, game, g[1].split('.')[0])
    if event_id != None and game != None:
        jdata.execute('UPDATE game SET event_id = ?, event_game = ? WHERE id = ?', (event_id, game, g[0]))
        updated.append(g[0])
        i += 1

print(i, "updates made. List length:", len(updated))
print("Games updated:", updated)
conn_jdata.commit()
conn_jdata.close()

# """
