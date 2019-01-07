"""
Parse html from game data to fill a temp table, which will be used to create the category table and define category_ids.
From there, we can fill the category and game_round_category tables.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html
print("")
print("***** ***** ***** *****")
missing_data = [320, 1088, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1150, 1151, 1153, 1165, 1182, 1183, 1218, 1220, 1221, 1385, 1387, 1389, 1434, 1435, 1436, 1437, 1438, 1443, 1444, 1445, 1449, 1665, 1667, 1720, 1721, 1723, 1724, 1725, 1726, 1727, 1728, 1731, 1732, 1733, 1734, 1735, 1736, 1748, 1750, 1752, 3552, 3575, 4246, 4256, 4264, 4271, 4273, 4284, 4757, 4758, 4759, 4760, 4763, 4764, 4765, 4766, 4767, 4960, 4983, 5348, 5361, 5773, 5877]

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive_decoded.sqlite') #much faster using the local db
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
read = #REMOVE_THIS conn_read.cursor()
write = conn_write.cursor()

# find the largest game we've already parsed data for
write.execute('SELECT max(game_id) FROM cat')
try: latest_game = int(write.fetchone()[0])
except: latest_game = 1
game_id = latest_game
read.execute('SELECT max(game_id) FROM games_scraped')
max_game = int(read.fetchone()[0])
#game_id = 5700
#max_game = 4591
per_loop = 20
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id + 1, "total.")
print("")
if max_game < game_id:
    print("Max game_id must be higher than the current game_id")
    quit()

def parse_cat(cats, data, game_id):
    global errors
    cat_order = 1
    i = 0
    name = None
    comm = None

    for d in data:
        # skip if there's a div w/javascript.  no divs for normal category formatting
        if '<div' in str(d):
            if 'clue_' not in str(d):
                print("Found an errant div")
                print(str(d))
                continue
            else: continue
        # find the round placeholder we inserted earlier
        if 'id=\"round\"' in str(d):
            r = int(re.findall('id=\"round\">.*R(\d)<',str(d))[0])
            cat_order = 1 #when we find it, reset the category counter since we're starting a new round
            continue
        name = None
        comm = None
        # get the text from the tags
        name = d.find("td", class_="category_name").text.strip()
        comm = d.find("td", class_="category_comments")

        # create the textual category identifier used in the JA html to organize cats & clues. format: clue_[J|DJ]_[cat_order]_[clue_order]
        #  Ex: clue_J_2_5 is in the first (J) round, from the 2nd category, and the 5th clue down in that category
        #  Ex: clue_DJ_3_1 is in the second (DJ) round, from the 3rd category, and the 1st clue down in that category
        if r == 1: crtid = "clue_J_" + str(cat_order)
        if r == 2: crtid = "clue_DJ_" + str(cat_order)

        # set empty comments = None (instead of a blank string)
        if comm == None or len(comm) < 1: comm = None
        else: comm = comm.text.strip()

        # if the category has link(s), append those to comm
        for link in d.find_all('a'):
            if comm == None: comm = link.get('href')
            else: comm = comm + "\n" + link.get('href')
        # program was originally run w/o link extraction.  if the category notes are now different, update the db
        #if comm != None and "http" in comm:
        #    update_comms_with_links(comm, game_id, crtid)
        if comm != None: comm = notes_cleanup(comm, game_id)

        #print(i,cat_order,"Name:",name, "crtid:", crtid, "comm:", comm)
        #if i == 6: print(d)
        # append data to our list
        cats.append([game_id, r, crtid, cat_order, name, comm])
        i += 1
        cat_order += 1

    #print("")
    #print("***** ***** ***** *****")
    return cats

def notes_cleanup(comm, game_id):
    comm = comm.replace("Alex:  ", "Alex: ")
    if comm == comm.upper() and game_id in(222,223,1401,1402,1403):
        # these games have Norweigan translations as the comment for each category
        return None

    if re.search('^\(Alex: ',comm) and not re.search('^\(Alex: .*\(.*',comm) and not re.search('^\(Alex: .*\).*\)',comm) and "Crockett" not in comm:
        comm = comm.replace("(Alex: ","")
        comm = comm.replace(")","")

    return comm

def update_comms_with_links(comm, game_id, crtid):
    # program was originally run w/o link extraction.  if the category notes are now different, update the db
    write.execute('SELECT notes FROM cat WHERE game_id = ? and crtid = ?', (game_id, crtid))
    val = write.fetchone()[0]
    if val != comm:
        write.execute('UPDATE cat SET notes = ? WHERE game_id = ? and crtid = ?', (comm, game_id, crtid))
        conn_write.commit()
        print("Updated comm for game " + str(game_id) + ", clue:",crtid,"comm:",comm)

def parse_cat_fj(cats, data, game_id):
    global errors
    # extract the Final Jeopardy category (and tiebreaker, if necessary)
    if data == None:
        errors.append([game_id,"FJ category - len(data) = None"])
        return cats
    elif len(data) not in(1,2):
        errors.append([game_id,"FJ category - len(data) out of bounds"])
        return cats
    r=3
    for mo in data:
        name = None
        comm = None

        # set the round number
        if r == 3: crtid = "clue_FJ" #final jeopardy = round 3
        elif r == 4: crtid = "clue_TB" #tiebreaker = round 4

        # get the text from the tags
        name = mo.find("td", class_="category_name").text.strip()
        comm = mo.find("td", class_="category_comments")

        # set empty comments = None (instead of a blank string)
        if comm == None or len(comm) < 1: comm = None
        else: comm = comm.text.strip()

        # if the category has link(s), append those to comm
        for link in mo.find_all('a'):
            if comm == None: comm = link.get('href')
            else: comm = comm + "\n" + link.get('href')

        # send for cleanup
        if comm != None: comm = notes_cleanup(comm, game_id)
        #print(r, "Name:",name,"crtid:",crtid)
        cats.append([game_id, r, crtid, 0, name, comm])
        r+=1
    #print(i,cat_order,"Name:",name, "crtid:", crtid)
    #cats.append([game_id, r, crtid, None, name, comm])
    return cats

def write_cats(cats):
    i = 0
    #val = list()
    #print(len(cats))
    #x = input("Cats len ^^^")
    for abc in cats:
        #if i>=80:
        #    errors.append([abc[0],"i >= 80 in the write_cats loop"])
        #    continue
        # validate against dupes
        write.execute('SELECT distinct game_id, round_id, crtid, pos_y, name, notes FROM cat WHERE game_id = ? and crtid = ?',(abc[0],abc[2]))
        try: val = write.fetchall()[0]
        except: val = None
        if val == None or val[0] == None:
            write.execute('INSERT INTO cat (game_id, round_id, crtid, pos_y, name, notes) VALUES (?,?,?,?,?,?)',(abc[0],abc[1],abc[2],abc[3],abc[4],abc[5]))
            conn_write.commit()
            #print(i,"Wrote new data for game " + str(abc[0]) + ", clue " + abc[2])
            continue
        else:
            print(i,"Data already exists for game", str(abc[0]) + ", clue", abc[2])
            continue

        #elif val[0] != cat[0] or val[1] != abc[1] or val[2] != abc[2] or val[3] != abc[3] or val[4] != abc[4] or val[5] != abc[5]:
            #write.execute('update cat SET game_id = ?, round_id = ?, crtid = ?, pos_y = ?, name = ?, notes = ? WHERE game_id = ? and crtid = ?',(abc[0],abc[1],abc[2],abc[3],abc[4],abc[5],abc[0],abc[2]))
            #conn_write.commit()
            #print("Updated data for game " + str(game_id) + ", clue " + abc[2])
        i += 1

    conn_write.commit()

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
cats = list()
errors = list()
modded = list()
newdivs = list()

while gmin <= max_game:
    cats.clear()
    raw.clear()
    modded.clear()
    newdivs.clear()
    # retrieve the gamedata html for this game
    #  'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    read.execute('SELECT game_id, gamedata FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id <= ' + str(gmax) + ' order by game_id asc')
    raw = read.fetchall()

    # header cleanup before processing
    for r in raw:
        game_id = r[0]
        # insert a placeholder <td> tag before each round for easier category sorting in the UDF
        rah = r[1].replace('<div id="jeopardy_round">', '<div id="jeopardy_round"> <td class="category" id="round">CAT_R1</td> <td class="clue" id="round">CLUE_R1</td>')
        rah = rah.replace('<div id="double_jeopardy_round">', '<div id="double_jeopardy_round"> <td class="category" id="round">CAT_R2</td> <td class="clue" id="round">CLUE_R2</td>')
        rah = rah.replace('<em class="underline">', '')
        rah = rah.replace('</em>', '')
        # clean up tags in the javascript divs that are breaking soup
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
    # parse categories for the retrieved games
    for m in modded:
        game_id = m[0]
        print("Reading game",game_id)
        # soupify the modded html
        soup = BeautifulSoup(m[1], "html.parser")

        # extract the html sections needed for each parsing function
        categories = soup.find_all("td", class_="category")
        fj = soup.find_all("table", class_="final_round")
        #clues = soup.find_all("td", class_="category") #soup.find_all("td", class_="clue")

        #try:
        cats = parse_cat(cats, categories, game_id)
        #except: errors.append([game_id,"Error w/regular categories"])
        try: cats = parse_cat_fj(cats, fj, game_id)
        except: errors.append([game_id,"FJ categories"])

        #print("Reg len:",len(categories))
        #print("FJ len:",len(fj))
        #print(fj[0])
        #print("")
        i += 1 #counter for gamedata html lines

    if j % per_loop == 0: print("Writing",game_id,"...")
    j += 1

    # send this chunk of data to be written before getting the next block of html to parse
    write_cats(cats)

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
    print(len(errors),"Errors:",errors)
else: print("No errors!")
print("")

conn_write.commit()
conn_write.close()
conn_read.close()
quit()
# """
