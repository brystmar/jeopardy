"""
Parse html from each clue's cleaned javascript div to fill the clue_response table.
Requires data stored in two temp tables:
    jdata.clue_div      (game_id, crtid, html, answer, cr_notes)
    jwagers.wager       (game_id, clue_id, crtid, wager) [for DD wagers]
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
filename = "ja_fix_errors_cr.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()
conn_jwagers = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jwagers.sqlite')
jwagers = conn_jwagers.cursor()

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
    for i in items:
        print(i, items[i])
    pause()
    print("")
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
        'wager': None,
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

    if clue['dd'] == 1:
        jwagers.execute('SELECT wager FROM wager WHERE game_id = ? and crtid = ?', (ctemp[7], ctemp[8]))
        clue['value'] = jwagers.fetchall()[0][0]
    else: clue['value'] = ctemp[0]

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
    name = name.replace('"','\"')
    name = name.replace('.', '\.')
    name = name.replace(' :)', '')
    name = name.replace(' =)', '')
    all_responses = re.findall('(\(' + name + '.*?:.*\))', text)
    if all_responses == None: return None
    #if all_responses[0] == None: return None

    while i < len(all_responses):
        resp += all_responses[i] + "\n"
        i +=1
    return resp.strip()
def find_owc(nick, players, banter, cr):
    if banter == None or banter == 'None':
        write_errors(cr['game_id'], cr['crtid'], "Banter was null, so couldn't determine the number of incorrect responses for this clue.")
        missing(cr['game_id'], cr['round_id'], cr['crtid'], "Clue", "Partial", "Banter was null, so couldn't determine the number of incorrect responses for this clue.")
        return -1
    order = dict()
    #print(banter)
    banter = remove_responses(banter, "Alex Trebek")

    if "Alex" not in players[0]: banter = remove_responses(banter, "Alex")
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
def write_cr(cr):
    if cr['player_id'] == None: jdata.execute('SELECT id FROM clue_response WHERE clue_id = ? and player_id is null', (cr['clue_id'],))
    else: jdata.execute('SELECT id FROM clue_response WHERE clue_id = ? and player_id = ?', (cr['clue_id'], cr['player_id']))

    try: val = jdata.fetchone()[0]
    except: val = jdata.fetchone()

    #validate cr_test
    if cr['player_id'] == None: jdata.execute('SELECT id FROM cr_test WHERE clue_id = ? and player_id is null', (cr['clue_id'],))
    else: jdata.execute('SELECT id FROM cr_test WHERE clue_id = ? and player_id = ?', (cr['clue_id'], cr['player_id']))
    try: val_test = jdata.fetchone()[0]
    except: val_test = jdata.fetchone()

    if val == None and val_test == None:
        jdata.execute('''insert INTO cr_test (clue_id, player_id, response, correct, order_within_clue, end_of_round, player_score_impact, notes, unsure, game_id, crtid)
            VALUES ''' + qmarks(11), (cr['clue_id'], cr['player_id'], cr['response'], cr['correct'], cr['order_within_clue'], cr['end_of_round'], cr['player_score_impact'], cr['notes'], cr['unsure'], cr['game_id'], cr['crtid']))
    else:
        print("Write_CR validation: cr_val =", val)
        print("Write_CR validation: cr_test_val =", val_test)
        write_errors(cr['game_id'], cr['crtid'], "Clue response for " + cr['nickname'] + " (player " + str(cr['player_id']) + ") already exists")
def write_clue_notes(cr, banter):
    jdata.execute('SELECT notes FROM clue WHERE id = ' + str(cr['clue_id']))
    try: val = jdata.fetchone()[0]
    except: val = jdata.fetchone()
    #if val == None: jdata.execute('UPDATE clue SET notes = ? WHERE id = ?', (banter, cr['clue_id']))
    #else: write_errors(cr['game_id'], cr['crtid'], "Notes/banter already exist for clue_id=" + str(cr['clue_id']))

    commit(conn_jdata)

#jdata.execute("SELECT distinct game_id, crtid, game_id || '-' || crtid as gcrtid FROM errors WHERE lower(notes) like '%nickname match returned empty%' order by 1,2,3")
jdata.execute("SELECT distinct game_id, crtid, game_id || '-' || crtid as gcrtid FROM errors WHERE lower(notes) like '%nickname match returned empty%' and game_id in(5070,5082) order by 1,2,3")
datav2 = jdata.fetchall()

"""first_game = 41#5695
max_game = 0#5695
first_game = int(input("Starting game_id: "))
max_game = input("Max game_id: ")
games_per_loop = 1
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
print("")"""

#first_game = datav2[0][0]

clue = dict()
players = list()
wagers = None
loop_counter = 0
#game_id = first_game
crtid_input = None
bonus_clues = [4779,4785,4791,4795,4799,69952,69958,69964,69969,69975,71564,71570,71574,71579,71583]
errors = {'new': 0, 'dupes': 0, 'missing': 0}

i=0
j=0
k=0
dv=0 #datav2 list counter

while dv < len(datav2): #iterates through every value in the retrieved datav2 set
    num_players = 0
    players = [["",0,0]]
    game_id = datav2[dv][0]
    crtid = datav2[dv][1]
    gcrtid = datav2[dv][2]

    """# skip if this is the same game_id as before
    if dv > 0 and datav2[dv][0] == datav2[dv-1][0]:
        loop_counter += 1
        dv += 1
        continue
    """
    print("Starting clue", gcrtid)

    # retrieve the next block of data to parse
    jdata.execute("""select distinct d.game_id, c.id, d.crtid, d.html, d.cr_notes, c.correct_response, g.clues_before_break, d.game_id || '-' || d.crtid as gcrtid FROM clue_div d JOIN clue c on d.crtid = c.crtid and d.game_id = c.game_id JOIN game g on c.game_id = g.id WHERE d.game_id = ? and d.crtid = ? order by 1,2,3""", (game_id,crtid))
    data = jdata.fetchall()[0]
    #except: data = jdata.fetchall()[0]

    if data == None or len(data) == 0:
        # query returns null clue data
        print("No data for clue", gcrtid)
        missing(game_id, find_round(crtid), crtid, "Clue", "Partial", "No clue data for " + gcrtid)
        loop_counter += 1
        dv += 1
        continue

    #pl(datav2)

    # reset variables
    cr = clear_cr()
    clue = clear_clue()
    p_alex = False
    html = data[3]
    banter = remove_html_tags(data[4])
    correct_response = remove_html_tags(data[5])
    cbb = data[6]
    soup = BeautifulSoup(html, "html.parser")
    banter_lines = banter.count('\n')
    if banter == "None": banter = None

    #if crtid_input == None: crtid_input = input("Enter crtid: ")
    #if crtid != crtid_input: continue #crtid_input: continue

    # load data into local dictionaries
    cr['game_id'] = game_id
    cr['clue_id'] = data[1]
    cr['crtid'] = crtid
    cr['notes'] = banter
    clue = load_clue_data(cr['clue_id'])
    cr['value'] = clue['value']

    # round_id
    rnd = find_round(crtid)
    cr['round_id'] = rnd

    # retrieve the players for this game
    if players[0][2] != game_id:
        jdata.execute('SELECT distinct prr.nickname, prr.player_id, prr.game_id FROM player_round_result prr join game_player as gp on prr.player_id = gp.player_id and prr.game_id = gp.game_id WHERE prr.game_id = ' + str(game_id) + ' order by player_position')
        players = jdata.fetchall()
        num_players = len(players)
        for pl in players: if pl[0] == "Alex": p_alex = True
        #print("New Players for game", str(game_id) + ":", num_players, players[0][2], game_id, players)

    if banter != None: write_clue_notes(cr, banter)
    # unfortunately, this owc method won't work.  Player responses are listed in their podium order, not the order they rang in.
    owc = 1 #order within clue counter
    if rnd != 3:
        for td in soup.find_all("td"): #each line has id=right/wrong, plus the person's name
            if 'ple stumper' in str(td).lower(): #works for triple and quadruple stumpers
                continue
            cr['ts'] = None
            cr['notes'] = None
            cr['unsure'] = None
            cr['correct'] = None
            cr['response'] = None
            cr['player_id'] = None
            cr['end_of_round'] = None
            cr['order_within_clue'] = None
            cr['player_score_impact'] = None

            # during J! round when it's the last response provided for the last clue before the commercial break, mark it as EOR
            #print(crtid, clue['order_within_round'], cbb)
            #print(owc, html.count('id="name"'))
            if rnd == 1 and owc == html.count('id="name"') - html.lower().count('ple stumper') and clue['order_within_round'] == cbb: cr['end_of_round'] = 0
            elif rnd == 1 and owc == html.count('id="name"') - html.lower().count('ple stumper') and clue['order_within_round'] == 30: cr['end_of_round'] = 1 #low-hanging fruit
            elif rnd == 2 and owc == html.count('id="name"') - html.lower().count('ple stumper') and clue['order_within_round'] == 30: cr['end_of_round'] = 2 #more low-hanging fruit

            if 'ple stumper' in str(td).lower(): #works for triple and quadruple stumpers
                continue
                """
                cr['ts'] = 1
                cr['notes'] = None
                cr['unsure'] = 0
                cr['correct'] = None
                cr['player_id'] = None
                cr['order_within_clue'] = None
                cr['player_score_impact'] = None
                """
            elif 'class="right"' in str(td):
                cr['correct'] = 1
                cr['unsure'] = 0
                cr['player_score_impact'] = clue['value']
                cr['response'] = correct_response

                # match this player's nickname to their player_id
                plyr = match_player(td.text, cr, players)
                cr['nickname'] = plyr[0]
                cr['player_id'] = plyr[1]
                cr['response'] = correct_response

                # filter out everyone else's responses
                cr['notes'] = find_responses(banter, cr['nickname'], p_alex)

                # find the order_within_clue -- easy for the correct response
                if str(soup).count('class="right"') > 1: #when a response is initially ruled incorrect but later accepted by the judges
                    cr['order_within_clue'] = find_owc(cr['nickname'], players, banter, cr)
                    cr['notes'] = banter #even if notes already exist, replace them with the full banter
                else:
                    cr['order_within_clue'] = str(soup).count('id="name"')

            elif 'class="wrong"' in str(td):
                cr['correct'] = 0
                cr['player_score_impact'] = -cr['value']

                # match this player's nickname to their player_id
                plyr = match_player(td.text, cr, players)
                cr['nickname'] = plyr[0]
                cr['player_id'] = plyr[1]
                cr['response'] = find_responses(banter, cr['nickname'], p_alex)
                if len(cr['response']) == 0: #text nickname probably didn't match the player's stored nickname
                    write_errors(game_id, crtid, "Nickname match returned empty for an incorrect response. " + td.text + cr['nickname'] + str(players))
                    missing(game_id, rnd, crtid, "Clue", "Partial", "Nickname match returned empty for an incorrect response. " + td.text + cr['nickname'] + str(players))
                else:
                    if cr['response'].count("\n") > 0: cr['unsure'] = 1
                    else: cr['unsure'] = 0

                    cr['response'] = cr['response'].replace('(' + cr['nickname'] + ': ', '')
                    cr['response'] = cr['response'].replace('(' + cr['nickname'] + ':', '')
                    cr['response'] = cr['response'].replace(')\n', '\n').strip()
                    #print(plyr)
                    #print(cr['response'], type(cr['response']))
                    if cr['response'][-1] == ')': cr['response'] = cr['response'][:-1]

                if banter == None: #shouldn't be null when there's an incorrect response
                    missing(game_id, rnd, crtid, "Clue", "Partial", "Missing incorrect responses from players.")
                    cr['order_within_clue'] = None

                # find the order_within_clue -- tricky for incorrect responses
                incorrect_responses = str(soup).count('class="wrong" id="name"') - str(soup).lower().count('ple stumper')
                if incorrect_responses == 1: cr['order_within_clue'] = 1
                elif incorrect_responses > 1 and banter != None:
                    cr['order_within_clue'] = find_owc(cr['nickname'], players, banter, cr)
                else:
                    write_errors(game_id, crtid, "Couldn't determine the number of incorrect responses for this clue.")
                    missing(game_id, rnd, crtid, "Clue", "Partial", "Missing player response order for incorrect responses.")
                    cr['order_within_clue'] = -1

            else: #shouldn't ever get here
                print("Error in right/wrong/TS clue response detection")
                print(game_id, crtid, td)
                pause()
                write_errors(game_id, crtid, "Error in right/wrong/TS clue response detection")
                if owc == 1: missing(game_id, rnd, crtid, "Clue", "Partial", "Error in right/wrong/TS clue response detection")
                cr['correct'] = None

            if rnd == 4: cr['player_score_impact'] = 0
            if cr['notes'] == "": cr['notes'] = None
            if banter != None and ("originally" in banter.lower() or "judges" in banter.lower() or "incorrect" in banter.lower()):
                unsure = 1
            if cr['unsure'] == 1: cr['notes'] = banter
            if cr['clue_id'] in bonus_clues: cr['unsure'] = 2

            write_cr(cr)
            owc += 1
    else: #final jeopardy html is structured a bit differently
        cr['notes'] = None
        for tr in soup.find_all("tr"):
            for td in tr.find_all("td"):
                # owc works for FJ since responses are revealed in the same order as on the show (rather than in podium order)
                cr['order_within_clue'] = owc
                # player info
                if 'id="name"' in str(td):
                    plyr = match_player(td.text.strip(), cr, players)
                    cr['nickname'] = plyr[0]
                    cr['player_id'] = plyr[1]
                    if 'class="right"' in str(td): cr['correct'] = 1
                    elif 'class="wrong"' in str(td): cr['correct'] = 0
                    else:
                        write_errors(game_id, crtid, "Can't determine if FJ answer was right or wrong.")
                        missing(game_id, rnd, crtid, "Clue", "Partial", "Can't determine if FJ answer was right or wrong for " + cr['nickname'] + ", player_id=" + cr['player_id'] + ".")
                # their written response
                if 'id="response"' in str(td): cr['response'] = td.text.strip()
                # amount wagered
                if 'id="wager"' in str(td):
                    wager = td.text
                    wager = wager.replace('$', '')
                    wager = wager.replace(',', '').strip()
                    if cr['correct'] == 1: cr['player_score_impact'] = int(wager)
                    else: cr['player_score_impact'] = -int(wager)

            if cr['notes'] == "": cr['notes'] = None
            if banter != None and ("originally" in banter.lower() or "judges" in banter.lower() or "incorrect" in banter.lower()):
                unsure = 1
            if cr['unsure'] == 1: cr['notes'] = banter

            write_cr(cr)
            owc += 1

    #print("")
    #print()

    commit(conn_jdata)
    print(i, "COMMIT")
    i += 1
    gmin = game_id + 1
    gmax = min(max_game, gmin + games_per_loop - 1)
    loop_counter += 1
    dv += 1
    if errors['new'] > 1500:
        print("Too many new errors; stopping")
        break

print("")
print("Loops completed:", loop_counter)
print("")
print("Missing:", errors['missing'])
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")

commit(conn_jdata)
conn_jdata.close()
conn_jwagers.close()
quit()
# """
