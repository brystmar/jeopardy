"""
Using each game's showscores.html page, extract each player's score after every clue and write to the game_score_hist table.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime
print("")
print("***** ***** ***** *****")
filename = "ja_score_history.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()
conn_ja = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite')
ja = conn_ja.cursor()

ja.execute('SELECT max(game_id) from games_scraped where scores is not null')
max_game_db = int(ja.fetchone()[0])
#max_game_db = 5883

jdata.execute('SELECT max(game_id) from game_score_hist')
next_game = int(jdata.fetchone()[0]) + 1

first_game = next_game
max_game = max_game_db
'''first_game = input("Starting game_id: ")
if first_game == '0': quit()
try: first_game = int(first_game)
except: quit()
max_game = input("Max game_id: ")
if max_game == None or max_game == '' or max_game == '0': max_game = first_game
try: max_game = int(max_game)
except: max_game = first_game'''
max_game = min(max_game, max_game_db)
if first_game > max_game: first_game = max_game
total_games = max_game - first_game + 1
print("Parsing scores for games " + str(first_game) + " to " + str(max_game) + ",", max_game - first_game + 1, "total.")
#print("Max db game:", max_game_db)
print("")

fj_notes = list()
cm_notes = list()
cy_notes = list()
players = list()
game_id = first_game
loop_counter = 0
errors = {'new': 0, 'dupes': 0, 'missing': 0}

i=0
j=0
k=0

def pause(): pz = input("====")
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
    pause()
def printdict(items):
    #if 'card' not in str(items): return 0
    for i in items:
        print(i, items[i])
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

    if crtid == None or crtid == '': crtid = 'n/a'

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

    print("Error:", game_id, notes)
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
    else: pass # error has already been recorded

    print("Missing data:", game_id, rnd, crtid, typ, type_info, notes)
    #conn_jdata.commit()
def cash_to_int(a):
    a = str(a)
    a = a.replace('$','').replace(',','').strip()
    return int(a)
def define_players(c, game_id):
    global players
    pids = re.findall('\?player_id=(\d+)', str(c)) #returns a list of strings
    for p in pids:
        #if p == '3': t='4'
        #game_id += 1 # validate the player_ids from this html page against the players stored in the db, and grab the same nickname used there, if possible
        jdata.execute('''SELECT distinct gp.player_id, prr.nickname
            FROM game_player gp
            LEFT JOIN player_round_result prr on gp.game_id = prr.game_id and gp.player_id = prr.player_id
            WHERE gp.game_id = ? and gp.player_id = ?''', (game_id, int(p)))
        pdata = jdata.fetchone()

        if pdata == None or pdata[0] == None: #not found in db
            write_errors(game_id, None, "Player_id mismatch between scores html and game_player table for game " + str(game_id) + ", player_id=" + str(p) + ".  Found these other players: " + str(players) + ".")
            missing(game_id, None, None, "Players", "Score history for player_id=" + str(p), "Player_id mismatch between scores html and game_player table for game " + str(game_id) + ", player_id=" + str(p) + ".  Found these other players: " + str(players) + ".")
            unsure = True
            print("Error with player_id=" + p)
            pause()

        players.append([pdata[0], pdata[1], True])
    players.reverse() #reverse the order so it mirrors the way data is organized in the score tables below
def format_coryat(text):
    # condense multi-line notes onto a single line
    text = text.replace('<td class="score_remarks">', '')
    text = text.replace('</td>', '')
    text = text.replace('<br />', ' ')
    text = text.replace('<br/>', ' ')
    text = text.replace('\n', ' ').strip()

    # replace R and W abbreviations
    text = text.replace('R','right')
    return text.replace('W','wrong')
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
def write_score(game_id, rnd, owr, player_id, nick, score, notes):
    # find the clue_id
    jdata.execute('SELECT distinct id FROM clue WHERE game_id = ? and round_id = ? and order_within_round = ?', (game_id, rnd, owr))
    try: clue_id = jdata.fetchone()[0]
    except: clue_id = None

    # if the player doesn't yet exist for r1 of this game, write zeroes first
    jdata.execute('SELECT game_id, round_id, player_id FROM game_score_hist WHERE round_id = 1 and game_id = ? and player_id = ?', (game_id, player_id))
    try: val = jdata.fetchone()[0]
    except: val = None
    if val == None:
        jdata.execute('''INSERT INTO game_score_hist (game_id, round_id, clue_owr, player_id, score)
            VALUES ''' + qmarks(5), (game_id, 1, 0, player_id, 0))

    # validation before writing score data
    jdata.execute('SELECT game_id, round_id, clue_owr, player_id FROM game_score_hist WHERE game_id = ? and round_id = ? and clue_owr = ? and player_id = ?', (game_id, rnd, owr, player_id))
    try: val = jdata.fetchone()[0]
    except: val = None
    if val == None:
        jdata.execute('''INSERT INTO game_score_hist (game_id, round_id, clue_owr, player_id, score, clue_id, notes)
            VALUES ''' + qmarks(7), (game_id, rnd, owr, player_id, score, clue_id, notes))
    else:
        print("Score history exists for game " + str(game_id) + ", round " + str(rnd) + ", owr " + str(owr) + ", player " + str(player_id) + ", clue_id " + str(clue_id) + ".")
        #write_errors(game_id, None, "Score history exists for game " + str(game_id) + ", round " + str(rnd) + ", owr " + str(owr) + ", player " + str(player_id) + ", clue_id " + str(clue_id) + ".")

while game_id <= max_game: #for each game retrieved
    absent = False
    players.clear()
    fj_notes.clear()
    cm_notes.clear()
    cy_notes.clear()
    #print("Game", game_id)#, end='. ')

    # retrieve the next block of data to parse
    ja.execute('SELECT scores FROM games_scraped WHERE game_id = ?', (game_id,))
    try: data = ja.fetchone()[0]
    except: absent = True

    if absent == True or data == None or len(data) == 0:
        # no data for the game retrieved
        missing(game_id, None, None, "Game", "Everything", "Game has no scores data")
        print("No data for game",game_id)
        i += 1
        game_id += 1
        loop_counter += 1
        continue
    else:
        # create a distinct div to separate FJ from the coryat scores
        html = data.replace('<h3>Game dynamics:</h3>', '</div>\n<div id="coryat">\n<h3>Game dynamics:</h3>')
        # add a distinct div for the cumulative score data in tourneys
        html = html.replace('<h3>Cumulative scores:</h3>', '</div>\n<div id="cumulative_scores">\n<h3>Cumulative scores:</h3>')

    soup = BeautifulSoup(html, "html.parser")

    contestants = soup.find_all("p", class_="contestants")
    define_players(contestants, game_id)

    rounds = [[BeautifulSoup(str(soup.find_all("div", id="jeopardy_round")), "html.parser"), 1], [BeautifulSoup(str(soup.find_all("div", id="double_jeopardy_round")), "html.parser"), 2], [BeautifulSoup(str(soup.find_all("div", id="final_jeopardy_round")), "html.parser"), 3], [BeautifulSoup(str(soup.find_all("div", id="cumulative_scores")), "html.parser"), 5], [BeautifulSoup(str(soup.find_all("div", id="coryat")), "html.parser"), 6]]
    #rounds = [soup.find_all("div", id="jeopardy_round"), soup.find_all("div", id="double_jeopardy_round"), soup.find_all("div", id="final_jeopardy_round")]

    # extract notes for each ending round.  doing different variables for each because i'm a newbie
    fjn = BeautifulSoup(str(soup.find_all("div", id="final_jeopardy_round")), "html.parser")
    cmn = BeautifulSoup(str(soup.find_all("div", id="cumulative_scores")), "html.parser")
    cyn = BeautifulSoup(str(soup.find_all("div", id="coryat")), "html.parser")
    for fj in fjn("td", class_="score_remarks"): fj_notes.append(fj.text.strip())
    for cm in cmn("td", class_="score_remarks"): cm_notes.append(cm.text.strip())
    for cy in cyn("td", class_="score_remarks"): cy_notes.append(format_coryat(str(cy)))

    '''print("FJ notes:")
    printlists(fj_notes)
    print("Cumulative Scores:")
    printlists(cm_notes)
    print("Coryat:")
    printlists(cy_notes)'''

    round_count = 1
    print("Game", game_id, "Round", end=' ', flush=True)
    for r in rounds:
        rnd = r[1]
        # fancy printing
        if round_count == 1: print(rnd, end='', flush=True)
        else: print(',', rnd, end='', flush=True)
        i_row = 1
        for row in r[0]("tr"):
            #print("Game", game_id, "Round", rnd, "Row", i_row)
            if 'www.j-archive.com' in str(row) or '"score_player_nickname"' in str(row):
                i_row += 1
                continue
            owr = None
            i_td = 1
            notes = None
            score_count = 0
            for td in row("td"):
                #print("td", i_td)
                if rnd >= 3: #data are organized differently for FJ, cumulative scores, coryat
                    if rnd == 3:
                        owr = 1
                        try: notes = fj_notes[score_count]
                        except: notes = None
                    elif rnd == 5:
                        owr = None
                        try: notes = cm_notes[score_count]
                        except: notes = None
                    elif rnd == 6:
                        owr = None
                        try: notes = cy_notes[score_count]
                        except: notes = None
                    if 'class="score_player_nickname' in str(td): continue
                    elif 'class="score_positive' in str(td) or 'class="score_negative' in str(td):
                        score = cash_to_int(td.text)
                        write_score(game_id, rnd, owr, players[score_count][0], players[score_count][1], score, notes)
                        score_count += 1
                elif i_td == 1: #first row has the order_within_round value
                    if len(td.text) > 0: owr = int(td.text)
                elif 'class="ddred"' in str(td) or re.findall('<td>(\d+)</td>', str(td)) == True:
                    # last row also has the order_within_clue value, so skip it
                    pass
                elif 'class="score_positive' in str(td) or 'class="score_negative' in str(td):
                    if owr == None:
                        write_errors(game_id, None, "OWR missing from row " + str(i_row) + ": " + str(row))
                        print("OWR missing from row " + str(i_row) + ": " + str(row))
                        score_count += 1
                        continue

                    score = cash_to_int(td.text)
                    #print("score_count:", score_count)
                    #print(rnd, owr, score, players[score_count][0], players[score_count][1]) #round, owr, player_id, nickname
                    write_score(game_id, rnd, owr, players[score_count][0], players[score_count][1], score, None)
                    score_count += 1

                #pause()
                i_td += 1
            #print(game_id, rnd, row)
            #if i % 500 == 17: print(i, "COMMIT")
                #pause()
            i += 1
            i_row += 1
            #print("")
        round_count += 1

    print('', end='\n', flush=True)
    i += 1
    game_id += 1
    loop_counter += 1
    conn_jdata.commit()
    if errors['new'] > 1500:
        print("")
        print("Too many new errors; stopping")
        break

print("")
print("Missing:", errors['missing'])
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")

conn_jdata.commit()
conn_jdata.close()
conn_ja.close()
quit()
# """
