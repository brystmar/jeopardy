"""
Python for Everyone Capstone
Clean & organize game data scraped from j-archive.org

Note: Since season data isn't included on the game page, this program assumes
the season_id for each game_id resides in a table called season_games.
"""
from bs4 import BeautifulSoup
import sqlite3, re
print("")
print("***** ****** ***** *****")
print("")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite') #much faster using the local db
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

game_id = 1001
max_game = 10
i = 0
errors = list()
error_data = list()

start = 1
limit = 5883 - game_id
j=0
read.execute('SELECT game_id, gamedata FROM games_scraped WHERE game_id >= ' + str(game_id) + ' order by game_id limit ' + str(limit))
html = read.fetchall()
while i < len(html):
    if i % 300 == 0: print("Analyzing", game_id)
    soup = BeautifulSoup(html[i][1], "html.parser")
    ss = str(soup).strip()
    l = len(ss)
    ss_end = ss[l-1200:]
    #print(game_id, ss_end)
    if not "Combined Coryat" in ss_end:
        errors.append(game_id)
        error_data.append(ss_end)
        print("Incomplete game:",game_id)
    i += 1
    game_id += 1
    #print(ss.find("Combined Coryat"), l, l-ss.find("Combined Coryat"))

print("")
print(i,"loops complete.")
print("Errors:",len(errors))
print(419, errors)
#while j < len(errors):
    #print(errors[j])
    #print(error_data[j])
    #j += 1

quit()

while game_id <= max_game:
    # game already exists?
    write.execute('SELECT id FROM game WHERE id = ' + str(game_id))
    try:
        exists = write.fetchone()[0]
        # data must already exist for this game; skip it
        print("Data already exists for game",season)
        game_id += 1
        continue
    except: pass

    # initialize variables
    season_id = None
    show = None
    date = None
    notes = None
    game_type = None
    t_id = None
    t_round_id = None
    t_game = None
    t_pool = None
    incomplete = None

    # retrieve the page's html from db
    read.execute('SELECT gamedata FROM games_scraped WHERE game_id = ' + str(game_id))
       # 'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    # read the html blob
    html = read.fetchone()[0]
    # soup-ify the html
    soup = BeautifulSoup(html, "html.parser")

    notes = soup.find(id="game_comments").text.strip()
    print("GC:",gcom)
    quit()

    # get known data for each game
    write.execute('SELECT season_id, show, aired, game_notes FROM season_games WHERE game_id = ' + str(game_id))
    gamedata = write.fetchall()
    season_id = int(gamedata[0][0])
    show = int(gamedata[0][1])
    date = gamedata[0][2]
    notes = "" #gamedata[0][3]

    # everything beyond here is based on notes, so skip if there aren't any
    if len(notes) < 1:
        # assume it's a regular game if there aren't any notes about the game
        game_type = 1
        # assume the data is complete
        incomplete = 0
    else:
        # write the game types to a local dictionary
        #write.execute('SELECT id, name FROM game_type ORDER BY id')
        #game_types = write.fetchall()

        #### GAME TYPE #### (1 = standard, 2 = tourney, 3 = exhibition)
        # pilot episodes are considered exhibition matches
        if season_id == 0: game_type = 3
        # if notes for a game match a game_type, set that value
        elif "tournament " in notes.lower() and "alex announces" not in notes.lower(): game_type = 2
        elif "championship" in notes.lower(): game_type = 2
        # adding an exception for the 2009 Celebrity Invitational, which is a tourney
        # ...unlike the 1998 Celebrity Invitational, which was a series of regular games
        elif "celebrity invitational" in notes.lower() and "final" in notes.lower(): game_type = 2
        # catch-all for errors
        else: game_type = 4

        #### INCOMPLETE GAMES ####
        if re.findall('*missing*round*', notes.lower()) or re.findall('*missing*clue*', notes.lower()): incomplete = 1
        else: incomplete = 0

        # begin tournament-specific stuff
        if game_type == 2:
            # write the tourney names to a local dictionary
            write.execute('SELECT id, name FROM tournament ORDER BY id')
            tourneys = write.fetchall()

            # if notes for a game match the tourney name, use that tourney_id
            for t in tourneys:
                if t[1].lower() in notes.lower(): t_id = int(t[0])
            # the 2001 int'l tourney was called the _championship_ in 2001; they belong under the same t_id
            if "international championship" in notes.lower(): t_id = 5
            quit()

            # write the tourney rounds to a local dictionary
            write.execute('SELECT id, name FROM tournament_round ORDER BY id')
            tourney_rounds = write.fetchall()


            if t_id != None: game_type = 2
            if "5" in notes: quit()


    trtags = soup.find_all('tr')
    for tr in trtags:
        # capture the notes field
        notes = str(tr.find(id="game_comments").text).strip()

        # capture the text blob of the players
        cc = tr.find_all(valign="top")
        players = cc[1].text.strip()

        # get all the link tags to iterate through them
        linktags = tr.find_all('a')
        for tag in linktags:
            # ignore random links that aren't to games
            if '/showgame.php?game_id=' not in str(tag):
                print("no game tag")
                continue
            if i > 500: break
            try:
                game_id = int(re.findall('game_id=(\d+)', str(tag))[0])
                show = int(re.findall('>.*#(\d+),', str(tag))[0])
                aired = str(re.findall('\w+?ed.(\S+)<', str(tag))[0])

                write.execute('INSERT OR IGNORE INTO season_games (season_id, game_id, show, aired, game_players, game_notes) VALUES (?,?,?,?,?,?)', (season, game_id, show, aired, players, notes))
                print("Wrote:", season_name, "(s" + str(season) + ")", game_id, show, aired, players, notes)
            except:
                print("Exception: Season", season_name, "(s" + str(season) + "), loop#:", i, "notes:",notes)
                print("Tag:",tag)
                errors.append("Exception: Season" + season_name + "(s" + str(season) + "), loop#:" + str(i) + "notes:" + notes)
        i += 1
    #conn_write.commit()
    i=0
    game_id += 1

# commit changes, close connections
#conn_write.commit()
conn_write.close()
conn_read.close()

print("")
print("Errors:",len(errors))
print(errors)
print("")
# """
