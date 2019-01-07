"""
Parse html from games to fill data points in the player_round_result table.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html
print("")
print("***** ***** ***** *****")
missing_data = [320, 1088, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1150, 1151, 1153, 1165, 1182, 1183, 1218, 1220, 1221, 1385, 1387, 1389, 1434, 1435, 1436, 1437, 1438, 1443, 1444, 1445, 1449, 1665, 1667, 1720, 1721, 1723, 1724, 1725, 1726, 1727, 1728, 1731, 1732, 1733, 1734, 1735, 1736, 1748, 1750, 1752, 3552, 3575, 4246, 4256, 4264, 4271, 4273, 4284, 4757, 4758, 4759, 4760, 4763, 4764, 4765, 4766, 4767, 4960, 4983, 5348, 5361, 5773, 5877]

# open & initialize the db
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive_decoded.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
conn_w2 = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()
w2 = conn_w2.cursor()

# save the starting timestamp
import datetime
now = datetime.datetime.now()
now = now.isoformat(timespec='seconds')

"""
# find the largest game we've already parsed data for
write.execute('select max(game_id) FROM cat')
try: latest_game = int(write.fetchone()[0])
except: latest_game = 1
game_id = latest_game
read.execute('select max(game_id) FROM games_scraped')
max_game = int(read.fetchone()[0])"""
game_id = 5695 #1349
max_game = 5695 #1349
game_id = 1152
game_id = 4591
game_id = 1001
game_id = int(input("Starting game_id: "))
if game_id == 0: quit()
max_game = 1005
max_game = int(input("Max game_id: "))
if max_game == 0 or game_id > max_game: quit()
per_loop = 20
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id + 1, "total.")
print("")
if max_game < game_id:
    print("Max game_id must be > " + str(game_id) + " <= 5883")
    game_id = int(input("Enter a new max game_id: "))

def round_results(scores_html, players, game_id):
    # create a variable for the dictionary keys found in the <td> data
    scorelabels = ['nick','score','notes']
    scores = list()
    place = list()
    tied = list()
    written = 0
    i_r = 0


    for r in scores_html: #for every round in this game that has a score summary table (tiebreakers don't have their own summary)
        #if i_r == 0: print("Entering s loop")
        scores.clear()
        place.clear()
        tied.clear()
        rnd = int(re.findall('round=\"(\d+)\">', str(r))[0])
        #print("*** Round",rnd,"***")

        i_tr = 0
        for tr in r.find_all("tr"): #for every group of data in this round (data are stored in a <tr>, which contains a group of <td>s)
            #if i_tr == 0: print("Entering tr loop")
            i_td = 0
            for td in tr.find_all("td"): #for every <td> data point in this group of data
                #if i_td == 0: print("Entering -td loop")
                i_p = 0
                if players[i_td]['pos'] == i_td + 1:
                    # score processing
                    if i_tr == 1:
                        # convert score $ amount to an integer
                        stemp = str(td.text).replace('$','')
                        stemp = stemp.replace(',','')
                        players[i_td][scorelabels[i_tr]] = int(stemp)
                        #except: players[i_td][scorelabels[i_tr]] = td.text

                        # add each score to a local variable for comparison later
                        scores.append(int(stemp))
                    # if notes are blank, use None instead of an empty string
                    elif i_tr == 2 and len(td.text) < 1:
                        players[i_td][scorelabels[i_tr]] = None
                    # if these are the Coryat score notes, replace newlines with spaces and "R" with "right", "W" with "wrong"
                    elif i_tr == 2 and rnd == 6:
                        n2 = nobr(td.contents).replace('R','right')
                        players[i_td][scorelabels[i_tr]] = n2.replace('W','wrong')
                    else:
                        # clean the notes text for lock games
                        if td.text == '(lock game)':
                            players[i_td][scorelabels[i_tr]] = 'Lock game'
                        else:
                            players[i_td][scorelabels[i_tr]] = td.text
                    i_p += 1
                i_td += 1
            i_tr += 1

        # put the scores in descending order
        scores.sort(reverse = True)

        # determine each player's rank at the end of this round, including ties
        place.clear()
        tied.clear()
        n = 0
        while n < len(scores):
            if n >= 1 and scores[n] == scores[n-1]: #if current score is same as the prev, use the same place
                place.append(place[n-1])
                tied[n-1] = 1 #mark the prev score as tied
                tied.append(1) #tied
            else:
                place.append(n + 1)
                tied.append(0) #not tied
            n += 1

        j = 0
        k = 0
        while j < len(scores):
            k = 0
            while k < len(players):
                if players[j]['score'] == scores[k]:
                    players[j]['place'] = place[k]
                    players[j]['tied'] = tied[k]
                k += 1
            #print(scores[n], place[n], tied[n])
            j += 1

        # write this round's results to the player_round_result table
        for p in players:
            #print("== Write round data to the db here ==")
            write.execute('select game_id, round_id, player_id from player_round_result where game_id = ? and round_id = ? and player_id = ?', (game_id,rnd,p['id']))
            val_prr = write.fetchone()
            # validation
            if val_prr == None or len(val_prr) < 1:
                write.execute('INSERT INTO player_round_result (game_id, round_id, player_id, nickname, score, place, tied, notes) VALUES (?,?,?,?,?,?,?,?)', (game_id,rnd,p['id'],p['nick'],p['score'],p['place'],p['tied'],p['notes']))
                written += 1
            else: print("Data already exists for game " + str(game_id) + ", round " + str(rnd) + ", player " + str(p['id']) + ".")

            conn_write.commit()
            #print(game_id,rnd,p['id'],p['nick'],p['score'],p['place'],p['tied'],p['notes'])

        #print("")
        #pause()
        i_r += 1

    # commit changes after each game
    conn_write.commit()
    return players

def identify_players(player_html):
    # link the player nicknames (first names) listed in the responses to their player_id
    global players
    players.clear()
    i = 0
    j = 0

    for p in player_html:
        player = {
            'pos':  abs(i-len(player_html)),
            'id':   int(re.findall('player_id=(\d+)\"', str(p))[0]),
            'name': re.findall('<a .*>(.+)</a>', str(p))[0],
            'nick': None,
            'score': None,
            'place': None,
            'tied': None,
            'notes': None
            }
        players.append(player)
        i += 1
    # reverse the player order to match how it's listed on the rest of the page (L -> R)
    players.reverse()

    return players

def CommBreak(game_id, html):
    # finds & writes the number of clues revealed before the first commercial break
    inc = None
    val_r0 = None
    r0_clues = None

    w2.execute('select distinct game_id from commbreak where game_id = ' + str(game_id))
    try: #insurance against incomplete data sets
        val_r0 = w2.fetchone()
        r0_clues = int(re.findall('\(.*clue (\d+)\):</h3>',str(html))[0])
    except:
        #html data is likely incomplete
        r0_clues = None
        write.execute('select incomplete_data from game where id = ' + str(game_id))
        inc = write.fetchone()
        if inc == 0:
            print("Can't find CommBreak value, html prob incomplete; game " + str(game_id) + " is NOT marked properly!")
            errors.append([game_id, "Can't find CommBreak value, html prob incomplete; game " + str(game_id) + " is NOT marked properly!"])
            write_errors(game_id, "Can't find CommBreak value, html prob incomplete; game " + str(game_id) + " is NOT marked properly!")
        else:
            errors.append([game_id, "Can't find CommBreak value, html prob incomplete; game is marked properly."])
            write_errors(game_id, "Can't find CommBreak value, html prob incomplete; game is marked properly.")

    # validation
    if val_r0 == None or len(val_r0) < 1:
        w2.execute('insert into commbreak (game_id, clues_before_break) VALUES (?,?)', (game_id, r0_clues))
        conn_w2.commit()
    else: print("CommBreak already exists for " + str(game_id))# + ". ", end="")

def nobr(lines):
    # condense multi-line notes onto a single line
    i = 0
    for line in lines:
        #print(type(line.string), str(line.string), str(line))
        if line.string == None:
            i += 1
            continue
        if i == 0: a = str(line.string)
        else: a = a + ' ' + str(line.string)
        i += 1
    return a

def write_errors(game_id, msg):
    global errors
    global now

    with open('ja_errors.txt', 'a') as f:
        # add a header if this is the first time we're writing to this file
        if len(errors) < 1:
            f.write("\n")
            f.write("[script: ja_prr.py on " + str(now).replace('T',' at ') + "]\n")
            f.write(str(game_id) + " " + msg + "\n")
        else:
            f.write(str(game_id) + " " + msg + "\n")

def decode(a):
    #print("SENT TO DECODE")
    return html.unescape(str(a))

def pause():
    print("")
    programPause = input("Press the <ENTER> key to continue...")

i = 0
j = 0
k = 0
erz = list()
raw = list()
errors = list()
modded = list()
newdivs = list()
players = list()
player_results = list()

while gmin <= max_game:
    raw.clear()
    modded.clear()
    newdivs.clear()
    players.clear()
    player_results.clear()
    # retrieve the gamedata html for this game
    #  'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    read.execute('SELECT game_id, gamedata FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id <= ' + str(gmax) + ' order by game_id asc')
    raw = read.fetchall()

    # header cleanup before processing
    for r in raw:
        # set the game_id
        game_id = r[0]
        print("Cleaning html for game",str(game_id))

        ## add & clean some tags to make searching easier ##
        # insert a placeholder <td> tag before each round for easier category sorting in the UDF
        rah = r[1].replace('<div id="jeopardy_round">', '<div id="jeopardy_round"> <td class="category" id="round">CAT_R1</td> <td class="clue" id="round">CLUE_R1</td>')
        rah = rah.replace('<div id="double_jeopardy_round">', '<div id="double_jeopardy_round"> <td class="category" id="round">CAT_R2</td> <td class="clue" id="round">CLUE_R2</td>')

        # remove markup from the category names
        rah = rah.replace('<em class="underline">', '')
        #rah = rah.replace('</em>', '')

        # identify the score summary tables for each round
        rah = rah.replace('):</h3>\n<table>', '):</h3>\n<table id="scores" round="0">') #first commercial break
        rah = rah.replace('the Jeopardy! Round:</h3>\n<table>', 'the Jeopardy! Round:</h3>\n<table id="scores" round="1">') #end of J round
        rah = rah.replace('the Double Jeopardy! Round:</h3>\n<table>', 'the Double Jeopardy! Round:</h3>\n<table id="scores" round="2">') #end of DJ round
        rah = rah.replace('Final scores:</h3>\n<table>', 'Final scores:</h3>\n<table id="scores" round="3">') #end of FJ round
        rah = rah.replace('Cumulative scores:</h3>\n<table>', 'Cumulative scores:</h3>\n<table id="scores" round="5">') #cumulative tourney scores
        rah = rah.replace('Coryat scores</a>:</h3>\n<table>', 'Coryat scores</a>:</h3>\n<table id="scores" round="6">') #coryat scores

        # extract the number of clues before the first commercial break
        #CommBreak(game_id, r)

        # rename soup-breaking tags in the javascript divs
        divs = re.findall('<div.*onclick=.*\'\)\">\n',rah)
        newdiv_id = None
        newdiv = None

        for div in divs:
            og_div = div
            # these particular table headers impact soup's ability to parse everything, so rename them
            div = div.replace("<table","<jstable")
            div = div.replace("</table","</jstable")
            newdiv_id = re.findall('onclick=.*(clue_.*)_stuck.\)',div)[0]
            newdiv = "<div id=\"" + newdiv_id + "\">" + newdiv_id

            newdivs.append([og_div,newdiv])

        k = 0
        while k < len(newdivs):
            rah = rah.replace(newdivs[k][0],newdivs[k][1])
            k += 1
        modded.append((r[0],rah))

    i = 1
    # parse data about players & rounds for the retrieved games
    for m in modded:
        # set the game_id
        game_id = m[0]
        print("Parsing game",game_id)

        # soupify the modded html
        soup = BeautifulSoup(m[1], "html.parser")

        # extract the html sections needed for each parsing function
        player_html = soup.find_all("p", class_="contestants")
        scores_html = soup.find_all("table", id="scores")
        cat_html = soup.find_all("td", class_="category")
        fj_html = soup.find_all("table", class_="final_round")
        #clues = soup.find_all("td", class_="clue")

        # send the player html to be parsed
        players = identify_players(player_html)
        # get the round results for each player-round and write them to the db
        player_results = round_results(scores_html, players, game_id)

        #players = identify_players(player_html, game_id)
        #print("Players:",players)
        #quit()

        i += 1 #counter for gamedata html lines
        #n += 1 #counter for games written since last commit

    """if n % (per_loop * 2) == 0:
        print("Writing",game_id,"...")
        conn_write.commit()
        n = 0"""
    j += 1

    # send this chunk of data to be written before getting the next block of html to parse
    #write_cats(cats)

    # update boundaries for the next chunk of html gamedata
    gmin = game_id + 1
    gmax = min(max_game, game_id + per_loop + 1)

print("")
if errors != None and len(errors) > 0:
    for e in errors:
        if e[0] not in missing_data:
            print("Error in game " + str(e[0]) + ":",e[1])
            erz.append(e[0])
    print("")
    print(len(erz),"Prev unknown errors:",erz)
    print("")
    print(len(errors),"Errors:")
    for e2 in errors:
        print(e2)

else: print("No errors!")
print("")

conn_w2.commit()
conn_w2.close()
conn_write.commit()
conn_write.close()
conn_read.close()
quit()
# """
