"""
Parse html from each clue's cleaned javascript div to fill the clue_response table.
Requires data stored in two temp tables:
    "clue_div"  (game_id, crtid, html)
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime
print("")
print("***** ***** ***** *****")
filename = "ja_clue_responses.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

first_game = 1#5695
max_game = 5883#5695
#game_id = int(input("Starting game_id: "))
#max_game = input("Max game_id: ")
games_per_loop = 6000
try: max_game = int(max_game)
except: max_game = first_game
if first_game == 0: quit()
if max_game < first_game: max_game = first_game
max_game = min(max_game, 5883)
gmin = first_game
gmax = min(max_game, first_game + games_per_loop - 1)
total_games = max_game - first_game + 1
total_loops = int(total_games / games_per_loop) + (total_games % games_per_loop > 0) #if the second part evaluates to True, the addition rounds it up
print("Parsing data for games " + str(first_game) + " to " + str(max_game) + ",", max_game - first_game + 1, "total.")
print("")
#crtid_input = input("Enter crtid: ")

ini = list()
in2 = list()
clue = dict()
players = list()
initials = dict()
loop_counter = 0
game_id = first_game
errors = {'new': 0, 'dupes': 0, 'missing': 0}

i=0
j=0
k=0
s = None

def clear_cr():
    clue_response = {
        'clue_id': None,
        'ja_clue_id': None,
        'game_id': None,
        'crtid': None,
        'player_id': None,
        'nickname': "",
        'round_id': None,
        'correct': None,
        'order_within_clue': None,
        'ts': 0,
        'end_of_round': None,
        'player_score': None, #not on first pass
        'player_score_impact': None,
        'response': None,
        'response_details': None, #will be combined w/notes before inserting
        'notes': None,
        'banter': None,
        'unsure': 0,
        'html': None,
        'value': None }
    return clue_response
def clear_clue():
    clue = {
        'ja_clue_id': None,
        'value': None,
        'cat_id': None,
        'round_id': None,
        'order_within_round': None,
        'dd': None,
        'notes': None }
    return clue
def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i += 1
    return q[:-1] + ")"
def pause(): pz = input("====")
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

    conn_jdata.commit()
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
def load_clue_data(clue_id):
    global clue

    jdata.execute('SELECT value, round_id, category_id, order_within_round, dd, ja_clue_id, notes, game_id, crtid FROM clue WHERE id = ' + str(clue_id))
    ctemp = jdata.fetchone()
    clue['round_id'] = ctemp[1]
    clue['cat_id'] = ctemp[2]
    clue['order_within_round'] = ctemp[3]
    clue['dd'] = ctemp[4]
    clue['ja_clue_id'] = ctemp[5]
    clue['notes'] = ctemp[6]

    return clue
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
def find_responses(text, name, p_alex):
    text = str(text)
    resp = ""
    i=0

    text = remove_responses(text, "Alex Trebek")

    if p_alex:
        text = remove_responses(text, "Alex T\.")
        text = remove_responses(text, "Alex T")

    # enclosed by () or []
    #responses = re.findall('([\[|\(]' + name + ':.*[\]|\)])')
    # enclosed by () only
    all_responses = re.findall('(\(' + name + '.*?:.*\))', text)
    if all_responses == None: return None
    #if all_responses[0] == None: return None

    while i < len(all_responses):
        resp += all_responses[i] + "\n"
        i +=1
    return resp.strip()
def find_owc(nick, players, banter, cr):
    order = dict()
    #print(banter)
    banter = remove_responses(banter, "Alex Trebek")
    banter = remove_responses(banter, "Alex T.")
    banter = remove_responses(banter, "Alex T")

    if "Alex" not in players[0]: banter = remove_responses(banter, "Alex")
    #print("++++++")
    #print(banter)
    #pause()

    for p in players:
        if banter.find(p[0]) != -1:
            order[p[0]] = banter.find(p[0])

    order_sorted = [(k, order[k]) for k in sorted(order, key=order.get)]

    i = 1
    for os in order_sorted:
        if os[0] == nick: return i
        i += 1
    # if we got this far, we didn't find the right player
    write_errors(cr['game_id'], cr['crtid'], "Couldn't determine the number of incorrect responses for this clue.")
    missing(cr['game_id'], cr['round_id'], cr['crtid'], "Clue", "Partial", "Missing player response order for incorrect responses for nickname " + nick + ".")
    return -1
def remove_responses(text, name):
    text = remove_html_tags(str(text)).strip()
    while re.search(name, text):
        text = text.replace(re.findall('([\[|\(]' + name + '.*?:.*[\]|\)])', text)[0], '').strip()
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
def write_cr(cr):
    if cr['player_id'] == None:
        jdata.execute('SELECT id FROM cr_test WHERE clue_id = ? and player_id is null', (cr['clue_id'],))
    else: jdata.execute('SELECT id FROM cr_test WHERE clue_id = ? and player_id = ?', (cr['clue_id'], cr['player_id']))

    try: val = jdata.fetchone()[0]
    except: val = jdata.fetchone()
    if val == None:
        jdata.execute('''insert INTO cr_test (clue_id, player_id, response, correct, order_within_clue, end_of_round, player_score_impact, notes, unsure)
            VALUES ''' + qmarks(9), (cr['clue_id'], cr['player_id'], cr['response'], cr['correct'], cr['order_within_clue'], cr['end_of_round'], cr['player_score_impact'], cr['notes'], cr['unsure']))
    else:
        print("Write_CR validation. val =", val)
        pause()
        write_errors(cr['game_id'], cr['crtid'], "Clue response for " + cr['nickname'] + " (player " + str(cr['player_id']) + ") already exists")
def update_notes(game_id, crtid, banter, banter_orig):
    jdata.execute("SELECT distinct game_id FROM clue_div WHERE cr_notes like '%(_:%' and game_id = ? and crtid = ?", (game_id, crtid))
    val = jdata.fetchone()

    if val == None or val[0] == None: return 0
    else: jdata.execute('UPDATE clue_div SET cr_notes = ? WHERE game_id = ? and crtid = ?', (banter, game_id, crtid))

def write_clue_notes(cr, banter):
    jdata.execute('SELECT notes FROM clue WHERE id = ' + str(cr['clue_id']))
    try: val = jdata.fetchone()[0]
    except: val = jdata.fetchone()
    #print("write clue notes -- val:", val, type(val))
    if val == None:
        jdata.execute('UPDATE clue SET notes = ? WHERE id = ?', (banter, cr['clue_id']))
    else:
        write_errors(cr['game_id'], cr['crtid'], "Notes/banter already exist for clue_id=" + str(cr['clue_id']))

    #conn_jdata.commit()

while loop_counter < total_loops: #for each chunk of games retrieved...
    num_players = 0
    players = [["",0,0]]
    print("Starting loop", loop_counter + 1, "of", total_loops)

    # retrieve the next block of data to parse
    jdata.execute("SELECT distinct game_id, crtid, cr_notes, html FROM clue_div WHERE cr_notes like '%(_:%' order by 1,2,3")
    data = jdata.fetchall()
    print(len(data), " total responses to adjust")

    if data == None:
        # no data for any of the games retrieved
        while game_id <= gmax:
            write_errors(game_id, None, "Game has no clue data")
            missing(game_id, None, None, "Game", "Everything", "Game has no clue data")
            print("No data for game",game_id)
            game_id += 1
        loop_counter += 1
        continue
    k=0
    for d in data: #for every clue within those games...
        if d[1] == None: #crtid should never be null
            print("The clue after " + str(game_id) + " " + crtid + " has a null crtid")
            print(d)
            write_errors(d[0], "the clue after " + crtid, "The clue after " + str(game_id) + " " + crtid + " has a null crtid")
            pause()
            continue
        # reset variables
        cr = clear_cr()
        clue = clear_clue()
        p_alex = False
        game_id = d[0]
        crtid = d[1]
        html = d[3]
        banter = remove_html_tags(d[2])
        soup = BeautifulSoup(html, "html.parser")
        banter_lines = banter.count('\n')
        letters = None
        if banter == "None": banter = None

        #if crtid != "clue_FJ": continue #crtid_input: continue
        #if game_id != 112: continue

        # load data into local dictionaries
        cr['game_id'] = game_id
        cr['crtid'] = crtid
        cr['notes'] = banter

        # round_id
        if crtid[5] == 'J': rnd = 1
        elif crtid[5] == 'D': rnd = 2
        elif crtid[5] == 'F': rnd = 3
        elif crtid[5] == 'T': rnd = 4
        cr['round_id'] = rnd
        if game_id not in games:
            games.append(game_id)

        if players[0][2] != game_id:
            a_name = False
            jdata.execute('SELECT distinct prr.nickname, prr.player_id, prr.game_id, substr(prr.nickname,1,1) as letter FROM player_round_result prr join game_player as gp on prr.player_id = gp.player_id and prr.game_id = gp.game_id WHERE prr.game_id = ' + str(game_id) + ' order by player_position')
            players = jdata.fetchall()
            num_players = len(players)
            repeated_letter = ""
            initials[game_id] = ""
            plist = ""

            for player in players:
                plist += player[0] + ", "

            plist = plist[:-2]
            for pl in players:
                if pl[0] == "Alex":
                    p_alex = True
                    print("p_alex = True for game", game_id, players)
                    pause()

                if pl[0][0] in initials[game_id]:
                    ini.append([game_id, plist])
                    repeated_letter = pl[0][0]
                #if "A" in initials[game_id]:
                #    ini.append([game_id, plist])
                if pl[3] == 'A':
                    a_name = True

                initials[game_id] = initials[game_id] + pl[0][0]


        # find letters matching the pattern (_:%
        letters = re.findall('\(([A-Z]):', banter)
        #print(game_id, crtid, banter.replace('\n',' '))
        #print("Letters:",letters)
        #print("")

        for l in letters:
            for p in players:
                if l == p[3] and l in p[0]:
                    banter = banter.replace('(' + l + ':', '(' + p[0] + ':')
                    update_notes(game_id, crtid, banter, cr['notes'])
                    j += 1
                #print(game_id, crtid, l, letters.count(l), letters)

        #print(j, cr['notes'].replace('\n',' '))
        #print(j, banter.replace('\n',' '))
        #if repeated_letter != "" and repeated_letter in letters:
        #    in2.append([game_id, plist, banter.replace('\n','').strip()])
        if k % 100 == 0:
            conn_jdata.commit()
            print("COMMIT")
        k += 1
        print(k)

    s = None
    initials_sorted = [(s, initials[s]) for s in sorted(initials, key=initials.get)]
    #print(initials_sorted)
    #print(data[:500])
    #pause()
    i += 1
    gmin = game_id + 1
    gmax = min(max_game, gmin + games_per_loop - 1)
    loop_counter += 1
    if errors['new'] > 150: break

print("")
print("Loops completed:", loop_counter)
print("")
print("Missing:", errors['missing'])
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")
print("Re-wrote",j,"abbreviations in",k,"cycles.")

conn_jdata.commit()
conn_jdata.close()
quit()
# """
