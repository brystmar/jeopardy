"""
Find players with punctuation in their nicknames, and remove that punctuation from the db
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime

time_start = datetime.datetime.now()
time_start = time_start.isoformat(timespec='seconds')
time_start = str(time_start).replace("T", " ")
print("***** ***** **** ***** *****")
print(" Start:", time_start)
print("***** ***** **** ***** *****")
print("")
filename = "ja_nickname_punct.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

def pause(): pz = input("====")
def commit(db):
    #db.commit()
    return 0
def pp(item):
    print("")
    print(item)
    pause()
def pl(items):
    for i in items: print(i)
    print("Total items:",len(items))
    pause()
def pl_sorted(items):
    newlist = list()
    ditems = set(items)
    for d in ditems:
        newlist.append(d)
    newlist.sort()
    for n in newlist:
        print(items.count(n), n)
    pause()
def pd(items):
    #if 'card' not in str(items): return 0
    for i in items: print(i, items[i])
    pause()
    print("")
def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i += 1
    return q[:-1] + ")"
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

    commit(conn_jdata)
def missing(game_id, rnd, crtid, typ, type_info, notes):
    # save the timestamp
    timestamp = datetime.datetime.now()
    timestamp = timestamp.isoformat(timespec='seconds')
    timestamp = str(timestamp).replace("T", " ")

    if rnd == None and crtid == None: jdata.execute('SELECT distinct game_id, round_id, crtid, type, type_info FROM missing_data WHERE game_id = ? and type = ? and type_info = ?', (game_id, typ, type_info))
    elif crtid == None: jdata.execute('SELECT distinct game_id, round_id, crtid, type, type_info FROM missing_data WHERE game_id = ? and round_id = ? and type = ? and type_info = ?', (game_id, rnd, typ, type_info))
    else: jdata.execute('SELECT distinct game_id, round_id, crtid, type, type_info FROM missing_data WHERE game_id = ? and round_id = ? and crtid = ? and type = ? and type_info = ?', (game_id, rnd, crtid, typ, type_info))
    val = jdata.fetchone()

    if val == None:
        # new error
        jdata.execute('INSERT INTO missing_data (game_id, round_id, crtid, type, type_info, notes, timestamp) VALUES ' + qmarks(7), (game_id, rnd, crtid, typ, type_info, notes, timestamp))
        errors['missing'] += 1
    elif val[0] != game_id or val[1] != rnd or val[2] != crtid or val[3] != typ or val[4] != type_info:
        # new error
        jdata.execute('INSERT INTO missing_data (game_id, round_id, crtid, type, type_info, notes, timestamp) VALUES ' + qmarks(7), (game_id, rnd, crtid, typ, type_info, notes, timestamp))
        errors['missing'] += 1
    else:
        # error has already been recorded
        pass

    commit(conn_jdata)
def match_player(nick, cr, p):
    # match this player's nickname p[0] to their player_id p[1] for this game_id p[2]
    nick = str(nick)
    for p in players:
        # double-checking to ensure it's the same game
        if p[2] != cr['game_id']:
            write_errors(cr['game_id'], cr['crtid'], "Wrong players for this game.  Loaded players for game " + str(cr['game_id']) + " instead.")
            return cr

        if p[0] == nick: return [p[0], p[1]]
    # shouldn't get this far
    write_errors(cr['game_id'], cr['crtid'], "Didn't find a player matching the nickname '" + nick + "' in " + players)
    missing(cr['game_id'], cr['round_id'], cr['crtid'], "Clue", "Partial", "Didn't find a player matching the nickname '" + nick + "' in " + players)
    return [None, None]
def remove_responses(text, name):
    global cr
    if text == None or text == "None": return text
    text = remove_html_tags(str(text)).strip()
    text = text.replace('"','\"')
    text = text.replace('.', '\.')
    text = text.replace(' :)', '')
    text = text.replace(' =)', '')
    while re.search(name, text):
        try: text = text.replace(re.findall('([\[|\(]' + name + '.*?:.*[\]|\)])', text)[0], '').strip()
        except:
            write_errors(cr['game_id'], cr['crtid'], "Newlines in banter screwing up RegEx. " + text)
            missing(cr['game_id'], cr['round_id'], cr['crtid'], "Banter", "Partial", "Newlines in banter screwing up RegEx. " + text)
            text = text.replace('\n\n','\n')
            break
        text = text.replace('\n\n','\n')
    text.replace('\n...', '')
    while '\n\n' in text: text = text.replace('\n\n','\n')
    while '\n \n' in text: text = text.replace('\n \n','\n')

    return text.strip()
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
def find_round(crtid):
    if crtid[5] == 'J': return 1
    elif crtid[5] == 'D': return 2
    elif crtid[5] == 'F': return 3
    elif crtid[5] == 'T': return 4
    else: return None

players = list()
wagers = None
loop_counter = 0
errors = {'new': 0, 'dupes': 0, 'missing': 0}

i=0
j=0
k=0

jdata.execute("SELECT distinct player_id, nickname from game_player as gp order by 1,2")
data = jdata.fetchall()
#jdata.execute("SELECT distinct player_id, nickname from player_round_result as prr order by 1,2 limit 11753")
#prrdata = jdata.fetchall()

"""if gpdata == prrdata: pp("Same")
else:
    print(len(gpdata), len(prrdata))
    pp("Different")
    while i < len(gpdata):
        if j > 25:
            print("max 25")
            break
        if gpdata[i] != prrdata[i]:
            print(i, gpdata[i])
            print(i, prrdata[i])
            j += 1
        i += 1

quit()"""

for d in data:
    if d[1] == None: continue
    #if players != None and len(players) > 20: break

    if re.search('[^a-zA-Z \.\-]', d[1]):
        print(d)
        players.append(d)


print("")
print("Players:", + len(players))
#for p in players: print(p)
print("")

commit(conn_jdata)
conn_jdata.close()
quit()
# """
