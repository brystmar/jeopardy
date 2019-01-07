"""
Parse html from games to fill clue-based data in the clue table.  clue_response data will be a separate script.
Since I'm a newb, I'm creating a temp table to hold game_id, crtid, html, and the clue_response notes to stage & test against before writing to the jdata db
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime
print("")
print("***** ***** ***** *****")

# open & initialize the db
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive_decoded.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
conn_w2 = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
conn_write_wager = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jwagers.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()
write_wager = conn_write_wager.cursor()
w2 = conn_w2.cursor()

"""
# find the largest game we've already parsed data for
write.execute('select max(game_id) FROM cat')
try: latest_game = int(write.fetchone()[0])
except: latest_game = 1
game_id = latest_game
read.execute('select max(game_id) FROM games_scraped')
max_game = int(read.fetchone()[0])"""
game_id = 1349
max_game = 1349
#game_id = 1152
#game_id = 4591
#game_id = 1001
#game_id = 5695
game_id = int(input("Starting game_id: "))
if game_id == 0: quit()
max_game = 1005
max_game = input("Max game_id: ")
try: max_game = int(max_game)
except: max_game = game_id
if max_game < game_id: max_game = game_id
max_game = min(max_game, 5883)
per_loop = 30
gmin = game_id
gmax = min(max_game, game_id + per_loop)
total_games = max_game - game_id + 1
total_loops = int(total_games / per_loop) + (total_games % per_loop > 0) #if the second part evaluates to True, the addition rounds it up
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id + 1, "total.")
print("")

def clear_clue():
    clue = {
        'ja_clue_id': None,
        'game_id': None,
        'crtid': None,
        'value': None,
        'wager': None, #to help determine player_score_impact
        'cat_id': None,
        'round_id': None,
        'order_within_round': None,
        'type_id': 'N',
        'pos_x': None, #for category_id lookup
        'pos_y': None,
        'dd': None,
        'text': None,
        'correct_response': None,
        'response_details': None, #for the temp table
        'notes': None,
        'media': None }
    return clue
def clear_clue_response():
    clue_response = {
        'ja_clue_id': None,
        'game_id': None,
        'crtid': None,
        'player_id': None,
        'round_id': None,
        'correct': None,
        'order_within_clue': None,
        'ts': None,
        'EOR': None,
        'player_score': None, #not on first pass
        'player_score_impact': None,
        'response': None,
        'response_details': None, #will be combined w/notes before inserting
        'notes': None,
        'banter': None,
        'html': None }
    return clue_response

def parse_clues(clues_html, game_id, grc):
    global players
    global clues
    global clue_responses
    clue = dict()
    clue_response = dict()
    xpos = [1,2,3,4,5,6]

    #print("")
    #print("clues_html length:", len(clues_html), len(divdata))
    i_c = 0
    clue_count = 0
    clue_response_count = 0
    for c in clues_html: #for every clue in this game, which is defined by <div class="cluedata">
        # initialize session vars
        clue = clear_clue()
        clue_response = clear_clue_response()

        # extract the crtid from the div header
        try: clue['crtid'] = re.findall('class=\"cluedata\" id=\"(clue_\S+)\"', str(c))[0]
        except:
            write_errors(game_id, "n/a", "Unable to find the crtid for " + str(c))
            i_c += 1
            continue
        if clue['crtid'] == None:
            write_errors(game_id, "n/a", "Unable to find the crtid for " + str(c))
            i_c += 1
            continue

        # store the game_id for each
        clue['game_id'] = game_id
        clue_response['game_id'] = game_id

        # decode the js div into the clue & clue_response dictionaries
        temp = unpack_clue(c, clue, clue_response, game_id)
        clue = temp[0]
        clue_response = temp[1]

        # moving clue response parsing to its own script
        """
        temp = unpack_clue_response(clue, clue_response, game_id)
        clue = temp[0]
        clue_response = temp[1]
        """

        # get the category_id number for this clue
        clue['cat_id'] = find_cat(clue['round_id'], clue['pos_x'], clue['crtid'], clue['game_id'])

        if clue['ja_clue_id'] == None and clue['crtid'] == None: pass
        else:
            clues.append(clue)
            clue_count += 1

        if clue_response['ja_clue_id'] == None and clue_response['crtid'] == None: pass
        else:
            clue_responses.append(clue_response)
            if clue_response['correct'] != None: clue_response_count += 1
        """if clue['crtid'] == "clue_J_3_4":
            print(clue['text'])
            print(clue['correct_response'])
            print(clue['notes'])
            print(clue['response_details'])
            pause()"""
        i_c += 1

    # find the original DD clue value from an adjacent clue
    dd_updates = 0
    found = False
    for u in clues:
        if u['dd'] == 1 and u['value'] == None and u['round_id'] in (1,2):
            newclue = u
            dd_crtid = u['crtid']
            for x in xpos:
                if x == u['pos_x']: continue
                test_crtid = dd_crtid[:-3] + str(x) + dd_crtid[-2] + dd_crtid[-1]
                for e in clues:
                    if e['dd'] == 0 and e['value'] != None and e['crtid'] == test_crtid:
                        newclue['value'] = e['value']
                        clues.remove(u)
                        clues.append(newclue)
                        dd_updates += 1
                        found = True
                        break
                if found == True: break

    return [clue_count, clue_response_count]

def unpack_clue(c_html, clue, clue_response, game_id):
    # two parts to this UDF:
    ## 1) pull data from the <td>s for [ja_]clue_id, value, order_within_round, DD, pos_y
    ## 2) parse clue_text, answer, player responses, etc. from the javascript divs
    global divdata
    crtid = clue['crtid']
    audio_extensions = [".mp3", ".mpa", ".m4a", ".aac", ".ac3", ".mp5"]
    # videos & images fall under the same type_id
    video_extensions = [".mpg", ".mpeg", ".mp4", ".m4v", ".avi", ".mkv", ".wmv", ".mov", ".gif", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".svg", "J_29"]
    i = 0
    j = 0

    #print(c_html)
    #pause()

    # pt1: get data from <td>s
    if crtid == "clue_FJ": #none of this is needed for FJ & tiebreak rounds
        clue['round_id'] = 3
        clue['pos_x'] = 0
        clue['pos_y'] = 0
        clue['order_within_round'] = 1
    elif crtid == "clue_TB":
        clue['round_id'] = 4
        clue['pos_x'] = 0
        clue['pos_y'] = 0
        clue['order_within_round'] = 1
    else:
        # position attributes
        clue['pos_x'] = int(re.findall('clue_\S+_(\d)_\d', clue['crtid'])[0])
        clue['pos_y'] = int(clue['crtid'][-1])

        for td in c_html.find_all("td"):
            if "clue_unstuck" in str(td): continue #nothing of value here
            elif "clue_value_daily_double" in str(td):
                # daily double clue
                clue['dd'] = 1
                vtemp = td.text.replace('DD:','')
                vtemp = vtemp.replace('$','')
                vtemp = vtemp.replace(',','').strip()
                clue['value'] = None #we'll find the original clue value later
                clue['wager'] = int(vtemp)
            elif "clue_value" in str(td):
                # regular clue
                clue['dd'] = 0
                vtemp = td.text.replace('$','')
                vtemp = vtemp.replace(',','').strip()
                clue['value'] = int(vtemp)
                #clue_response['player_score_impact'] = value
            elif "clue_order_number" in str(td):
                # [ja_]clue_id number using RegEx
                try: clue['ja_clue_id'] = int(re.findall('\?clue_id=(\d+)\"', str(td))[0])
                except: clue['ja_clue_id'] = None #missing from some games like 940: <td class="clue_order_number">4</td>
                clue['order_within_round'] = int(td.text.strip())

    # round_id
    if clue['crtid'][5] == 'J': clue['round_id'] = 1
    elif clue['crtid'][5] == 'D': clue['round_id'] = 2
    elif clue['crtid'][5] == 'F': clue['round_id'] = 3
    elif clue['crtid'][5] == 'T': clue['round_id'] = 4

    # pt2: parse data from the js divs
    # splits the div into question text, correct response, player/Alex banter, and contestant response data + html
    dparts = split_div(divdata[str(game_id) + '-' + crtid])

    # validate the data returned
    if dparts[0] == None:
        write_errors(game_id, clue['crtid'], "Splitting the div for clue " + clue['crtid'] + " returned null question text.")
        return [clue, clue_response]
    elif dparts[1] == None:
        write_errors(game_id, clue['crtid'], "Splitting the div for clue " + clue['crtid'] + " returned null correct response.")
        return [clue, clue_response]
    elif dparts[3] == None: #null banter is okay
        write_errors(game_id, clue['crtid'], "Splitting the div for clue " + clue['crtid'] + " returned null contestant response data & html.")
        return [clue, clue_response]

    # extract any links from the question text
    if "<a href=" in dparts[0]:
        # store links as the clue 'media' attribute
        links = re.findall('href=\"(http.*?://\S+?)\"', dparts[0])
        for link in links:
            # append if there's already a value for clue notes
            if clue['media'] != None: clue['media'] = clue['media'] + "\n" + link
            else: clue['media'] = link
            # determine the clue type (Normal, Audio, Visual, or Multiple) based on notes & question text
            ext = link[-4:]
            if ext in audio_extensions or "[audio" in dparts[0].lower() or "audio daily double" in dparts[0].lower():
                # multiple types identifier
                if clue['type_id'] in('V','M'): clue['type_id'] = 'M'
                else: clue['type_id'] = 'A'
                # append to clue notes
                if "audio daily double" in dparts[0].lower():
                    if clue['notes'] != None: clue['notes'] = "Audio Daily Double.\n" + clue['notes']
                    else: clue['notes'] = "Audio Daily Double."
            if ext in video_extensions or "[video" in dparts[0].lower() or "video daily double" in dparts[0].lower():
                if clue['type_id'] in('A','M'): clue['type_id'] = 'M'
                else: clue['type_id'] = 'V'
                if "video daily double" in dparts[0].lower():
                    if clue['notes'] != None: clue['notes'] = "Video Daily Double.\n" + clue['notes']
                    else: clue['notes'] = "Video Daily Double."
        # remove the href tags
        hrefs = re.findall('(<a href=\"http.*?://\S+?\".*?>)', dparts[0])
        for href in hrefs: dparts[0] = dparts[0].replace(href,'')
        dparts[0] = dparts[0].replace('</a>','')
        dparts[0] = dparts[0].strip()

    # remove 'audio/video daily double' text


    # specific adjustments for two games
    if game_id == 1608 and clue['crtid'] == "clue_DJ_4_5": clue_response['ts'] = None
    if game_id == 2747:
        if clue['crtid'] == "clue_DJ_3_2":
            clue['value'] = 800
            clue['wager'] = 1347
            clue_response['correct'] = 2 #nullified
            clue_response['player_score_impact'] = 0
            clue_response['notes'] = "[Originally judged incorrect]\n[NOTE: Before Final Jeopardy!, the judges ruled that the clue was imprecise and restored Mike's money, but did not credit him with a correct response.  JA accounted for the $ discrepancy in WHAT'VE YOU GOT THERE? $1200, the last clue Mike got right, but TB chose to account for this in a more streamlined fashion.  As a side effect, Mike's Coryat score is incorrect as displayed on the J! Archive.]"
            clue_response['notes'] += "(Alex: And you have just increased your lead.)\n(Mike: Let's go $1,347.)\n[Laughter]\n(Alex: I have to ask--what is the significance of that?)\n(Mike: No one ever does it.)\n[Laughter]\n(Alex: So you're just being silly. It's sort of like playing strip Jeopardy! isn't it? You're--)\n(Mike: Not as much fun.)\n[Laughter]\n(Alex: You're messing--Oh, hello. All right. Here comes the clue. Let's get serious.)"

        if clue['crtid'] == "clue_DJ_6_3":
            clue['value'] = 1200
            clue_response['correct'] = 1 #correct
            clue_response['player_score_impact'] = 1200
            clue_response['notes'] = "Since Mike answered this correctly, JA made an adjustment to this clue's impact to account for the nullified DD ruling in question 4.  TB chose a more streamlied approach to addressing the issue."

    # store the cleaned text in the clue dictionary
    clue['text'] = dparts[0]

    # capitalize the first letter of the correct response, then store it
    clue['correct_response'] = dparts[1][0].upper() + dparts[1][1:]

    # store the banter and html for later processing
    clue_response['banter'] = dparts[2]
    clue_response['html'] = dparts[3]
    clue_response['ja_clue_id'] = clue['ja_clue_id']
    clue_response['crtid'] = clue['crtid']
    clue_response['round_id'] = clue['round_id']

    """z = 0
    for dp in dparts:
        print(z,dp)
        z += 1
    pause()"""
    return [clue, clue_response]

def unpack_clue_response(clue, clue_response, game_id):
    global players

    """# fix some oddities found in the data
    if clue['ja_clue_id'] == 241057: clue_response['notes'] = "Incomplete data"
    if clue['ja_clue_id'] == 281845: clue_response['notes'] = "Incomplete data"
    if game_id == 4261 and clue['order_within_round'] <= 14: clue_response['notes'] = "Incomplete data"

    if clue_response['notes'] == "Incomplete data": clue_response = clear_incompletes(clue_response)"""

    return [clue, clue_response]

def split_div(div):
    # split a javascript-filled div into its components: clue text, correct response, player responses + html
    onclick = re.findall("(onclick=\"togglestick\('clue_\S+_stuck'\)\")", div)[0]
    # mouseout is the clue text, including href= tags
    mouseout = re.findall("onmouseout=\"toggle\('.+?_stuck',.'(.+?)'\)\"", div)[0]
    mouseout = decode(mouseout.replace("<br />","\n"))
    # mouseover includes the correct response plus some html-encoded transactional data
    mouseover = re.findall("onmouseover=\"toggle\(.+?_stuck',.'(.+?)'\)\"", div)[0]
    mouseover = mouseover.replace("<br />","\n")

    # extract the correct response
    mouseover = decode(mouseover.replace('class=\\"correct_response\\"', 'class="correct_response"'))
    correct_response = re.findall('<em.class=\"correct_response\">(.+?)</em', mouseover)[0]
    if correct_response[0] == "<":
        correct_response = remove_html_tags(correct_response).strip()

    # since we're sending the answer separately, strip out the <em> answer block from the mouseover html
    try:
        remove1 = re.findall('(<em.class=.+?</em><br./><br./>)', mouseover)[0]
        mouseover = mouseover.replace(remove1, "")
    except: pass
    try:
        remove2 = re.findall('(<em.class=.+?</em><br./>)', mouseover)[0]
        mouseover = mouseover.replace(remove2, "")
    except: pass
    try:
        remove3 = re.findall('(<em.class=.+?</em>)', mouseover)[0]
        mouseover = mouseover.replace(remove3, "")
    except: pass
    mouseover = mouseover.replace("\n\n","\n").strip()

    # separate contestant responses and any Alex/player banter from the html block
    if mouseover.find('<table') == 0: #no incorrect responses or banter
        banter = None
        cresp_html = mouseover
    else:
        banter = mouseover[:mouseover.find('<table')].strip()
        cresp_html = mouseover.replace(banter, '').strip()

    # edit the responses html to more easily identify its parts
    cresp_html = cresp_html.replace('<td class="right"', '<td id="name" class="right"')
    cresp_html = cresp_html.replace('<td class="wrong"', '<td id="name" class="wrong"')
    cresp_html = cresp_html.replace('<td rowspan="2" valign="top"', '<td id="response"') #unnecessary; only applies to FJ
    cresp_html = cresp_html.replace('</tr><tr><td>', '<td id="wager">$') #consolidate rows, add id tag, normalize score display; only FJ
    cresp_html = cresp_html.replace('<td id="wager">$$', '<td id="wager">$') #remove double $s; only FJ

    return [mouseout, correct_response, banter, mouseover] #onclick appears to be useless

def round_results(scores_html, game_id):
    global players
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

        """
        # write this round's results to the player_round_result table
        for p in players:
            #print("== Write round data to the db here ==")
            write.execute('select game_id, round_id, player_id from player_round_result where game_id = ? and round_id = ? and player_id = ?', (game_id,rnd,p['id']))
            val_prr = write.fetchone()
            # validation
            if val_prr == None or len(val_prr) < 1:
                write.execute('insert INTO player_round_result (game_id, round_id, player_id, nickname, score, place, tied, notes) VALUES (?,?,?,?,?,?,?,?)', (game_id,rnd,p['id'],p['nick'],p['score'],p['place'],p['tied'],p['notes']))
                written += 1
            else:
                pass
                print("Data already exists for game " + str(game_id) + ", round " + str(rnd) + ", player " + str(p['id']) + ".")

            #conn_write.commit()
            #print(game_id,rnd,p['id'],p['nick'],p['score'],p['place'],p['tied'],p['notes'])

        #print("")
        #pause()
        """
        i_r += 1

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
    try: r0_clues = int(re.findall('\(.*clue (\d+)\):</h3>',str(html))[0])
    except:
        r0_clues = None #html data is likely incomplete
        write_errors(game_id, "n/a", "html data to determine CommBreak is likely incomplete")

    # validation
    write.execute('SELECT distinct order_within_round from clue as c join clue_response as cr on c.id = cr.clue_id where cr.game_id = ? and cr.round_id = ? and end_of_round is not null order by 1 desc', (game_id, 1))
    val = write.fetchone()

    if r0_clues == None: pass
    elif val == None:
        write.execute('INSERT INTO clue (game_id, clues_before_break) VALUES (?,?)', (game_id, r0_clues))
        #conn_w2.commit()
        print("Wrote the CommBreak value for " + str(game_id) + ":", r0_clues)
    elif r0_clues != int(val):
        write_errors(game_id, "n/a", "Different value found for clues_before_break. Current: " + val + ", new: " + str(r0_clues))
    else: pass #same CommBreak value as the db

def nobr(lines):
    # collapse multi-line strings onto a single line
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

def find_cat(rnd, pos_x, crtid, game_id):
    # returns the category_id for this clue
    global grc
    if rnd == None or pos_x == None or crtid == None or game_id == None: return 0
    else: return grc[str(game_id) + '-' + str(rnd) + '-' + str(pos_x)]

def write_clues():
    #print("Entering UDF write_clues()...")
    for c in clues:
        #print(c)
        old = ""
        new = ""
        # validation
        write.execute('SELECT game_id,crtid,value,round_id,category_id,dd,type_id,text,correct_response,notes,pos_y,order_within_round,ja_clue_id,media FROM clue WHERE game_id = ? and crtid = ?', (c['game_id'],c['crtid']))
        val = write.fetchone()
        if val == None:
            write.execute('''insert INTO clue (game_id,crtid,value,round_id,category_id,dd,type_id,text,correct_response,notes,pos_y,order_within_round,ja_clue_id,media) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (c['game_id'],c['crtid'],c['value'],c['round_id'],c['cat_id'],c['dd'],c['type_id'],c['text'],c['correct_response'],c['notes'],c['pos_y'],c['order_within_round'],c['ja_clue_id'],c['media']))
        else:
            for v in val:
                old += str(v) + " "
            new = str(c['game_id'])+" "+str(c['crtid'])+" "+str(c['value'])+" "+str(c['round_id'])+" "+str(c['cat_id'])+" "+str(c['dd'])+" "+str(c['type_id'])+" "+str(c['text'])+" "+str(c['correct_response'])+" "+str(c['notes'])+" "+str(c['pos_y'])+" "+str(c['order_within_round'])+" "+str(c['ja_clue_id'])+" "+str(c['media'])
            old = old.strip()
            new = new.strip()
            if old == new:
                #print("Duplicate data for game " + str(c['game_id']) + " clue.id=" + str(c['ja_clue_id']) + " " + c['crtid'] + "; skipping.")
                write_errors(c['game_id'], c['crtid'], "Duplicate data for game " + str(c['game_id']) + " clue.id=" + str(c['ja_clue_id']) + " " + c['crtid'] + "; skipping. [UDF: write_clues]")
                #pause()
            else:
                print("Different data exists for game " + str(c['game_id']) + " clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'] + ".")
                print('game_id','crtid','value','round_id','cat_id','dd','type_id','text','correct_response','notes','pos_y','order_within_round','ja_clue_id','media')
                print("Old:",old)
                print("New:",new)
                #pause()
                write_errors(c['game_id'], c['crtid'], "Different data exists for game " + str(c['game_id']) + " clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'] + ". [UDF: write_clues]\nOld:\n" + old + "\nNew:\n" + new)
            #pause()

def write_clue_responses():
    #print("Entering UDF write_clues()...")
    for c in clue_responses:
        #print(c)
        old = ""
        new = ""
        # validation
        write.execute('SELECT * FROM clue_response WHERE game_id = ? and crtid = ?', (c['game_id'],c['crtid']))
        val = write.fetchone()
        if val == None:
            write.execute('''INSERT INTO clue_response (ja_clue_id, crtid, game_id,
                value, category_id, round_id, dd, clue_notes, response_details) VALUES (?,?,?,?,?,?,?,?,?)
                ''', (c['ja_clue_id'], c['crtid'], c['game_id'], c['value'], c['cat_id'], c['round_id'], c['dd'], c['notes'], c['response_details']))
        else:
            for v in val:
                old += str(v) + " "
            new = str(c['ja_clue_id'])+" "+str(c['crtid'])+" "+str(c['game_id'])+" "+str(c['value'])+" "+str(c['cat_id'])+" "+str(c['round_id'])+" "+str(c['dd'])+" "+str(c['notes'])+" "+str(c['response_details'])+" "
            if old == new:
                print("Duplicate data for clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'] + "; skipping.")
                write_errors(c['game_id'], c['crtid'], "Duplicate data for clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'] + "; skipping. [UDF: write_clues]")
            else:
                print("Different data exists for clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'])
                print("Old / New:")
                print(old)
                print(new)
                #pause()
                write_errors(c['game_id'], c['crtid'], "Different data exists for clue.id=" + str(c['ja_clue_id']) + ", " + c['crtid'] + ". [UDF: write_clues]\nOld:\n" + old + "\nNew:\n" + new)
            #pause()

def write_clue_count(game_id, cs, crs):
    if crs == 0: crs = None
    # validation
    w2.execute('SELECT game_id, clue_count, clue_response_count FROM clue_count WHERE game_id = ' + str(game_id))
    val = w2.fetchone()
    if val == None:
        w2.execute('INSERT INTO clue_count (game_id, clue_count, clue_response_count) VALUES (?,?,?)', (game_id, cs, crs))
    else:
        if cs != None and val[1] != None and cs > int(val[1]):
            print("Parsed more clues for game " + str(game_id) + ". Prev: " + val[1] + ", New: " + str(cs))
            w2.execute('UPDATE clue_count SET clue_count = ? WHERE game_id = ?', (cs, game_id))
        if crs != None and val[2] != None and crs > int(val[2]):
            print("Parsed more clues for game " + str(game_id) + ". Prev: " + val[2] + ", New: " + str(crs))
            w2.execute('UPDATE clue_count SET clue_response_count = ? WHERE game_id = ?', (crs, game_id))

        #x = input("clue_count data exists for game " + str(game_id) + ": " + str(val[1]) + ", " + str(val[2]) + ". Overwrite? ")
        #if x[0] == '1' or x[0].lower() == 'y': w2.execute('UPDATE clue_count SET clue_count = ?, clue_response_count = ? WHERE game_id = ?', (cs,crs,game_id))
    #conn_w2.commit()

def write_errors(game_id, crtid, notes):
    global errors
    filename = "ja_clean_clues.py"

    # save the timestamp
    timestamp = datetime.datetime.now()
    timestamp = timestamp.isoformat(timespec='seconds')
    timestamp = str(timestamp).replace("T", "")
    if crtid == None: crtid = 'n/a'

    write.execute('SELECT distinct game_id, crtid, notes FROM errors WHERE game_id = ? and crtid = ? and notes = ?', (game_id, crtid, notes))
    val = write.fetchone()
    if val == None:
        # new error
        write.execute('INSERT INTO errors (game_id, crtid, timestamp, filename, notes) VALUES (?,?,?,?,?)', (game_id, crtid, timestamp, filename, notes))
        errors['new'] += 1
    elif val[0] != game_id or val[1] != crtid or val[2] != notes:
        # new error
        write.execute('INSERT INTO errors (game_id, crtid, timestamp, filename, notes) VALUES (?,?,?,?,?)', (game_id, crtid, timestamp, filename, notes))
        errors['new'] += 1
    else:
        # error has already been recorded
        print('Error data already exists: ' + str(game_id), notes)
        errors['dupes'] += 1

    conn_write.commit()

def remove_html_tags(html):
    # find & fix erroneous starting tags, ex: </i>text</i>
    if re.search('^</([a-zA-Z])>', html.strip()):
        html = "<" + re.findall('^</([a-zA-Z])>', html.strip())[0] + ">" + html[4:]
    # prep for soupification
    html = html.strip()
    html = "<td>" + str(html) + "</td>"
    soup = BeautifulSoup(html, "html.parser")
    return soup.td.text.strip() #soup returns the text string without formatting tags like <b>, <u>, <i>

def clear_incompletes(cr):
    cr['ts'] = None
    cr['response'] = None
    cr['correct'] = None
    cr['player_id'] = None
    cr['player_score'] = None
    cr['player_score_impact'] = None
    cr['order_within_clue'] = None
    return cr

def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i+=1
    return q[:-1] + ")"

def decode(a):
    a = a.replace("\\'","'")
    return html.unescape(str(a))

def pause(): pz = input("<...>")

i = 0
j = 0
k = 0
gslc = 0
raw = list()
clues = list()
modded = list()
newdivs = list()
players = list()
clue_responses = list()
grc = dict()
cid = dict()
divdata = dict()
errors = {'new': 0, 'dupes': 0}

loop_counter = 0
while loop_counter < total_loops:
    #print("loop_counter:",loop_counter,"total_loops:",total_loops)
    #print('game_id >= ' + str(gmin) + ' and game_id <= ' + str(min(max_game, gmin + per_loop - 1)))
    grc.clear()
    modded.clear()
    newdivs.clear()
    divdata.clear()
    players.clear()
    clues.clear()
    clue_responses.clear()
    # retrieve the gamedata html for this game
    #  'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    read.execute('SELECT game_id, gamedata FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id <= ' + str(min(max_game, gmin + per_loop - 1)) + ' order by game_id asc')
    raw = read.fetchall()

    # header cleanup before processing
    for r in raw:
        # set the game_id
        game_id = r[0]
        #print("Cleaning html for game", str(game_id))
        #print("")

        # store game-round-category data in a local list
        write.execute("SELECT distinct game_id || '-' || round_id || '-' || category_order, category_id FROM game_round_category WHERE game_id = " + str(game_id) + " order by 1,2")
        grc_raw = write.fetchall()

        # if there's no grc data for this game, skip to the next game
        if grc_raw == None or len(grc_raw) < 1: #html data is probably incomplete and didn't have category data
            write_errors(game_id, "n/a", "Game has no game_round_category data")
            continue

        # store category ids for each round and clue position in a local dictionary
        i_g = 0
        while i_g < len(grc_raw):
            grc[grc_raw[i_g][0]] = grc_raw[i_g][1]
            i_g += 1

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
        ##CommBreak(game_id, r)

        # rename soup-breaking tags in the javascript divs
        jsdivs = re.findall('<div.*onclick=.*\'\)\">\n', rah)
        for div in jsdivs:
            og_div = div
            # instead of renaming the headers, let's truncate the div and store it in a dictionary for easy reference later
            div = decode(div).strip()
            # extract the crtid to use as the new id= for this div
            div_id = re.findall('onclick=.*(clue_.*)_stuck.\)', div)[0]
            #div = "<div id=\"" + div_id + "\">" + div_id
            div_id_tag = 'id="' + div_id + '"'
            # add our new div id & class to the beginning, then close the tag
            div = div.replace('<div ', '<div ' + div_id_tag + ' class="cluedata" ')
            div = div + "</div>"
            # save this div in a dictionary to parse later
            divdata[str(game_id) + '-' + div_id] = div

            # replace with a basic div in the overall file
            slimdiv = '<div ' + div_id_tag + ' class="cluedata">'
            newdivs.append([og_div,slimdiv])

        nd = 0
        while nd < len(newdivs):
            rah = rah.replace(newdivs[nd][0], newdivs[nd][1])
            nd += 1
        modded.append((r[0], rah))

    i = 1
    # parse clues for the retrieved games
    for m in modded:
        # set the game_id
        game_id = m[0]
        #print("Parsing clues for game", game_id)

        # soupify the modded html
        soup = BeautifulSoup(m[1], "html.parser")

        # extract the html sections needed for each parsing function
        player_html = soup.find_all("p", class_="contestants")
        scores_html = soup.find_all("table", id="scores")
        cat_html = soup.find_all("td", class_="category")
        fj_html = soup.find_all("table", class_="final_round")
        clues_html = soup.find_all("div", class_="cluedata")

        """
        for ch in clues_html:
            if "clue_value_daily_double" in str(ch):
                crtid = re.findall('id=\"(clue_.*?)\"><', str(ch))[0]
                wager = re.findall('clue_value_daily_double\">(.*?)</td>', str(ch))[0]
                wager = wager.replace('DD','')
                wager = wager.replace(':','')
                wager = wager.replace('$','')
                wager = int(wager.replace(',','').strip())

                write.execute('select id from clue where crtid = ? and game_id = ?', (crtid, game_id))
                clue_id = int(write.fetchall()[0][0])
                write_wager.execute('insert or ignore into wager (game_id, clue_id, crtid, wager) values (?,?,?,?)', (game_id, clue_id, crtid, wager))
        """

        # send the player html to be parsed
        players = identify_players(player_html)
        # get the round results for each player-round and write them to the db
        round_results(scores_html, game_id)
        # parse clue data from each chunk of html
        counts = parse_clues(clues_html, game_id, grc)
        # record the number of clues & clue_responses identified for each game
        write_clue_count(game_id, counts[0], counts[1])

        i += 1 #counter for games
        gslc += 1 #counter for games written since last commit
        print("Finished game", game_id)

    # write clue data to the db
    #write_clues()
    #write_clue_responses()

    # commit db changes at the end of each cycle
    #conn_write.commit()
    #conn_w2.commit()

    """
    print("")
    print("Duplicate errors:", errors['dupes'])
    print("New errors:", errors['new'])
    print("")
    """

    # update boundaries for the next chunk of html gamedata
    gmin = game_id + 1
    gmax = min(max_game, game_id + 1 + per_loop)
    j += 1
    loop_counter += 1
    conn_write_wager.commit()
    if errors['new'] > 150: break

print("")
print("Loops completed:", loop_counter)
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")

#conn_w2.commit()
conn_w2.close()
#conn_write.commit()
conn_write.close()
conn_write_wager.close()
conn_read.close()
quit()
# """
