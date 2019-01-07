"""
Match html events to the events table, then write prize data to the event_prizes table.
Also adds data to the event_round_game table.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime, itertools
print("")
print("***** ***** ***** *****")
filename = "ja_event_prizes.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

# open the html file
filename = 'event_payouts.html'
fh = open(filename, "r", encoding="utf-8")
html = fh.read()

i=0
j=0
k=0
ecount = 0
pcount = 0
gcount = 0
err = list()
tlist = list()
places = list()
prizes = list()
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
def find_games(tr, event_id):
    data = list()
    gtemp = 1
    tr = tr.replace('[','')
    tr = tr.replace(']','')
    strings = re.findall('\?game_id=(.+?)</a>', tr)

    for s in strings:
        s = s.replace('"','')
        game_id = int(s.split('>')[0])
        rg = s.split('>')[1]

        # determine the round
        if 'rnd=' in str(tr): #if the round is specified, use it
            rnd = re.findall('rnd=\"([a-zA-Z0-9]+?)\"', str(tr))[0]
        elif len(rg) <= 5: #for games with coded round/game data
            if 'QF' in rg: rnd = 'Q'
            elif 'SF' in rg: rnd = 'S'
            elif 'F' in rg: rnd = 'F'
            elif 'P' in rg: rnd = '1'
            else: rnd = None
        else: #for the events with descriptive game links, assign the game number in the listed order
            rnd = None
            game = gtemp
            gtemp += 1

        if re.search('\d', rg) and gtemp == 1: game = re.findall('(\d+)', rg)[0]
        elif gtemp == 1: game = None

        # if there's only one finals game, it's game 1
        if rnd == 'F' and game == None: game = 1

        data.append([event_id, rnd, game, game_id])
    return data
def find_prize(tr, event_id, ptype):
    if tr == None or str(tr) == 'None': return 0
    global prizes, ep
    amount = None
    fixed = True

    prize_text = tr.find_all('td', id='prize')[0].text.strip()
    if ptype in ['Cash','Donation','Giftcard','Grant']:
        # fixed or variable cash amount?
        fixed = not re.search('\(.*whichever.*\)', prize_text)

        # find the actual amount
        if prize_text[0:1] == '$' and ' ' in prize_text:
            amount = int(prize_text[1:prize_text.index(' ')].replace(',', '').strip())
        elif prize_text[0:1] == '$': amount = int(prize_text[1:].replace(',', '').strip())

        # classify all celebrity winnings as donations
        if 'celebrity' in ep['tname'].lower(): ptype = 'Donation'
        if 'power play' in ep['tname'].lower(): ptype = 'Donation'

    # create a list of unique prizes
    prizes.append(ptype + ' ' + prize_text)

    if amount == None: fixed = None

    ep['amount'] = amount
    ep['ptype'] = ptype
    ep['prize'] = prize_text
    if fixed == None: ep['fixed'] = None
    elif fixed == True: ep['fixed'] = 'Y'
    elif fixed == False: ep['fixed'] = 'N'
def min_round(div):
    # return the round_id of the first round in this event
    div = str(div)
    if div == None or div == 'None': return '0'
    elif '<b>2nd Round' in div: return '2'
    elif '<b>1st Round' in div: return '1'
    elif '<b>Quarterfinal' in div: return 'Q'
    elif '<b>Semifinal' in div: return 'S'
    elif '<b>Champion' in div or '<b>1st runner' in div or '<b>2nd runner' in div: return 'F'
    elif '<b>Winner' in div or '<b>2nd place' in div or '<b>3rd place' in div: return None
    else: return '0'
def write_event_games(games):
    if games == None or games[0][0] == None or games[0] == None: return 0
    global gcount, ep

    for g in games: #games is a list of lists
        # variable insertion into queries doesn't work properly when there's a null value
        if g[1] == None:
            jdata.execute('SELECT distinct event_id, event_round, event_game, game_id FROM event_round_game WHERE event_id = ? and event_round is null and event_game = ?', (g[0], g[2]))
        else:
            jdata.execute('SELECT distinct event_id, event_round, event_game, game_id FROM event_round_game WHERE event_id = ? and event_round = ? and event_game = ?', (g[0], g[1], g[2]))

        val = jdata.fetchone()
        if val == None:
            # doesn't exist yet
            jdata.execute('INSERT INTO event_round_game (event_id, event_round, event_game, game_id) VALUES ' + qmarks(4), (g[0], g[1], g[2], g[3]))
            gcount += 1
        else:
            print("Data already exists for event, round, game, game_id:", g)
            errors['dupes'] += 1
def write_prizes(ep, gtype):
    global pcount

    # variable insertion into queries doesn't work properly when there's a null value
    if ep['round'] == None:
        jdata.execute('SELECT distinct event_id, event_round, place, amount, amount_fixed, prize, prize_type, game_type FROM event_prize WHERE event_id = ? and event_round is null and place = ? and prize = ?', (ep['id'], ep['place'], ep['prize']))
    else:
        jdata.execute('SELECT distinct event_id, event_round, place, amount, amount_fixed, prize, prize_type, game_type FROM event_prize WHERE event_id = ? and event_round = ? and place = ? and prize = ?', (ep['id'], ep['round'], ep['place'], ep['prize']))

    val = jdata.fetchone()
    if val == None or len(val) == 0:
        # doesn't exist yet
        jdata.execute('INSERT INTO event_prize (event_id, event_round, place, amount, amount_fixed, prize, prize_type, game_type) VALUES ' + qmarks(8), (ep['id'], ep['round'], ep['place'], ep['amount'], ep['fixed'], ep['prize'], ep['ptype'], gtype))
        pcount += 1
    else:
        print("Prize data already exists: " + str(ep))
        errors['dupes'] += 1
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

    conn_jdata.commit()
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

# retrieve the list of themes from the db
jdata.execute('SELECT name, id FROM event_theme order by 1')
themes = jdata.fetchall()

# add a div to encapsulate each event
html = html.replace('<h3', '<div id="event">\n<h3')
html = html.replace('</table>', '</table>\n</div>')

# soupify the html
soup = BeautifulSoup(html, "html.parser")
divs = soup.find_all(id='event')

ep = dict()
stuff = list()
games = list()

for d in divs: #for each event
    skip = False
    again = False
    place = None
    prize = None
    ptype = None
    gtype = None
    fixed = None
    amount = None
    event_id = None
    num_players = 3
    ep.clear()
    games.clear()

    # tourney or exhibition?
    if 'champion' in str(d).lower():
        gtype = 'T'
        rnd = 'Unknown'
    else:
        gtype = 'X'
        rnd = None

    title = d.find_all('h3')[0].text.strip()
    if title == None: continue
    tname = re.findall('(\d\d\d\d.*?)\(', title)[0].strip()
    year = int(tname[:4])

    # events w/unique structures that I'll add manually
    if "Ultimate Tournament of Champions" in tname:
        event_id = 100
        skip = True
    elif "Million Dollar Celebrity Invitational" in tname:
        event_id = 118
        skip = True

    if tname[4:6] == "-A":
        tname = tname.replace("-A","")
        tname = tname + " (A)"
    elif tname[4:6] == "-B":
        tname = tname.replace("-B","")
        tname = tname + " (B)"
    elif tname[4:6] == "-C":
        tname = tname.replace("-C","")
        tname = tname + " (C)"

    # get the event_id
    if event_id == None:
        jdata.execute('SELECT id FROM event WHERE name = ? and year = ?', (tname, year))
        try: event_id = jdata.fetchone()[0]
        except:
            print("Unable to find event_id for", tname)
            pause()

    ep['tname'] = tname
    ep['id'] = event_id
    for tr in d.find_all('tr'): #for each prize within this event
        trx = str(tr)
        again = False

        # skip the notes since they are event-level, not prize-level
        if 'id="notes"' in trx: continue

        # extract prize type from the td class
        if 'class=' in trx:
            ptype = re.findall('class=\"(.*?)\"', trx)[0]
            ptype = ptype[0:1].upper() + ptype[1:]
        else: ptype = None

        # set the place and round
        if '<b>Champion' in trx:
            rnd = 'F'
            place = 1
        elif '<b>1st runner' in trx:
            rnd = 'F'
            place = 2
        elif '<b>2nd runner' in trx:
            rnd = 'F'
            place = 3
        elif '<b>Semifinalist' in trx:
            rnd = 'S'
            place = 1
            again = True
        elif '<b>Quarterfinalist' in trx:
            rnd = 'Q'
            place = 1
            again = True
        elif '<b>Winner' in trx:
            rnd = None
            place = 1
        elif '<b>2nd place' in trx:
            rnd = None
            place = 2
        elif '<b>3rd place' in trx:
            rnd = None
            place = 3
        elif '<b>Contestant' in trx:
            # when all contestants earn a prize, award this to every contestant from the first round of the event
            rnd = min_round(d)
            place = 1
            again = True

        ep['round'] = rnd

        if "Super Jeopardy" in tname and rnd == 'Q': num_players = 4

        # get the games info
        if 'id="games"' in trx:
            games = find_games(str(tr), event_id)
            #print("Games for event:", tname)
            #printlists(games)
            write_event_games(games)

        while place <= num_players and 'id="prize"' in trx:
            if skip == True: break #manually adding the prize info for these tourneys since their structure is snowflakey
            ep['place'] = place
            find_prize(tr, event_id, ptype)
            #printdict(ep)
            write_prizes(ep, gtype)

            if again == False: break
            else: place += 1

        for pl in tr.find_all('td', id='place'):
            places.append(pl.text[:-1])
            #print("Added:", place.text[:-1])

    # commit changes after each event
    #conn_jdata.commit()
    ecount += 1

    if ecount % 50 == 0:
        print(ecount, "events parsed;", pcount, "prizes,", gcount, "games written.  Pausing...")
        #pause()

#print("Total events:", len(events))
print("Total events parsed:", ecount)
print("Total prizes written:", pcount)
print("Total games written:", gcount)
#tlist = sorted(tlist, key=lambda item: item[0])

if len(err) > 0: print(err)

#conn_jdata.commit()
conn_jdata.close()
fh.close()

# """
