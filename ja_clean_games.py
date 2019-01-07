"""
1) Verifies that the scraped html for each page was captured & stored properly
2) Extracts data for the following attributes from these 2 tables:
 game: id, show, date, season_id*, type_id, theme_id, tournament_stage_id, tournament_game, pool, notes, incomplete_data
  (omits tournament_id [these haven't been defined yet])
  (*: requires season_id & game_id already be defined in a table called 'season_games')

 game_player: game_id, player_id, player_name, occupation, from, player_position, current_streak_wins, current_streak_winnings, winnings_type, notes
  (omits: none)

gamedata is incomplete for games: []

known games w/incomplete data on JA: [320, 1088, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139, 1150, 1151, 1153, 1165, 1182, 1183, 1218, 1220, 1221, 1385, 1387, 1389, 1434, 1435, 1436, 1437, 1438, 1443, 1444, 1445, 1449, 1665, 1667, 1720, 1721, 1723, 1724, 1725, 1726, 1727, 1728, 1731, 1732, 1733, 1734, 1735, 1736, 1748, 1750, 1752, 3552, 3575, 4246, 4256, 4264, 4271, 4273, 4284, 4757, 4758, 4759, 4760, 4763, 4764, 4765, 4766, 4767, 4960, 4983, 5348, 5361, 5773, 5877]
"""
from bs4 import BeautifulSoup
import sqlite3, re
print("")
print("***** ***** ***** *****")
print("")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite') #much faster using the local db
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

# find the largest game we've already parsed data for
write.execute("SELECT max(id) FROM game")
latest_game = int(write.fetchone()[0])
game_id = latest_game + 1
read.execute("SELECT max(game_id) FROM games_scraped")
max_game = int(read.fetchone()[0])
per_loop = 100
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id + 1,"total.")

i = 0
j = 0
k = 0
p_counter = 0
inc = list()
errors = list()
g_exists = list()
gp_exists = list()
player_id = list()
player_name = list()
player_streak = list()
player_winnings = list()
player_winnings_type = list()
player_occupation = list()
player_hometown = list()
player_position = list()
player_notes = list()

while game_id <= max_game:
    # retrieve the gamedata html for this game
    #  'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    read.execute('SELECT game_id, gamedata FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id < ' + str(gmax) + ' order by game_id asc')
    html = read.fetchall()

    i = 0
    while i < len(html):
        # soup-ify the html
        soup = BeautifulSoup(html[i][1], "html.parser")
        # initialize variables
        num_players = 0
        incomplete_data = 0
        game_type = None
        game_theme = None
        game_notes = None
        t_stage_id = None
        t_game_id = None
        pool = None
        t_id = None
        player_id.clear()
        player_name.clear()
        player_streak.clear()
        player_winnings.clear()
        player_winnings_type.clear()
        player_occupation.clear()
        player_hometown.clear()
        player_position.clear()
        player_notes.clear()

        # verify that the html page was fully scraped and retrieved
        ss = str(soup).strip()
        if j % 250 == 0: print("Loop",str(j) + ".","Analyzing game", html[i][0])
        if "Combined Coryat" not in ss: #appears immediately after the FJ data in the html
            if "</html>" in ss:
                # got the entire page, but the source lacks most game data
                inc.append(html[i][0]) #append this game_id to the incomplete list
                incomplete_data = 1
                print("JA data is incomplete for:",html[i][0])
            else:
                # there was an error scraping the page or storing it in our db
                errors.append(html[i][0]) #append this game_id to the errors list
                incomplete_data = 1
                print("Need to re-scrape:",html[i][0])

        # extract and clean the game notes
        game_notes = soup.find(id="game_comments").text.strip()
        if len(game_notes) == 0:
            game_notes = None #set to None if the returned string is empty
        else:
            # more incomplete game stuff
            if re.search('missing.*round', game_notes.lower()):
                incomplete_data = 1
            if re.search('missing.*clue', game_notes.lower()):
                incomplete_data = 1

        # get the season_id from the db
        write.execute('select season_id from season_games where game_id = ' + str(game_id))
        season_id = int(write.fetchone()[0])

        # extract basic game metadata
        title = str(soup.title.text).strip()
        show = int(re.findall('.*#(\d+),', title)[0])
        aired = str(re.findall('\w+?ed.(\S+)', title)[0])

        #### GAME TYPE & THEME ####
        game_type = 'N' #(P: Pilot, N: Normal, T: Tourney, X: Exhibition)
        if game_notes == None: pass
        elif season_id == 0: game_type = 'P' #pilot episodes
        # if notes for a game match a game_type, set that value
        elif "tournament " in game_notes.lower() and "alex announces" not in game_notes.lower() and "drawing" not in game_notes.lower():
            game_type = 'T'
        elif "championship" in game_notes.lower():
            game_type = 'T'
        # adding an exception for the 2009 Celebrity Invitational, which is a tourney
        # ...unlike the 1998 Celebrity Invitational, which was a series of regular games
        elif "celebrity invitational" in game_notes.lower() and "final" in game_notes.lower():
            game_type = 'T'
            game_theme = 1
        elif re.search('ibm challenge.*game', game_notes.lower()):
            game_type = 'X'
            game_theme = 3

        # write the game themes to a local dictionary
        write.execute('SELECT id, name FROM game_theme ORDER BY id')
        themes = write.fetchall()
        for theme in themes:
            if game_notes != None and theme[1].lower() in game_notes.lower():
                game_theme = int(theme[0])
                break

        #### PLAYERS ####
        # <p> headings are only used in two places: one for each player, and one at the
        #   bottom of the page that links to the FJ wagering calculator
        paragraphs = soup.find_all('p')
        # loop through all listed players from this game
        for p in paragraphs:
            if "wageringcalculator.php" in str(p): break
            # store player_id and their podium position
            player_id.append(str(re.findall('showplayer\.php\?player_id=(\d+)', str(p))[0]))
            num_players += 1
            player_position.append(num_players) #adds them in the opposite order desired, so we'll reverse this later

            # grab the full text string, capture their name + notes, then store the rest of the metadata string
            pdata = str(p.text).strip()
            player_name.append(pdata[:pdata.find(",")])
            pdata = pdata[pdata.find(",")+2:]
            # raw occupation & hometown
            occupation = pdata.rpartition(' from ')[0]
            hometown = pdata.rpartition(' from ')[2]
            # clean up occupation
            if occupation.endswith(' originally'):
                occupation = occupation[:-11]
            if occupation[0:1].lower() == 'a':
                fs = occupation.index(' ')
                occupation = occupation[fs+1].upper() + occupation[fs+2:]
            # append the clean occupation
            player_occupation.append(occupation)
            # clean up hometown
            hometown = hometown.replace('...','').strip() #must remove the parenthetical before appending

            # time to deal with parentheticals
            if "(whose" in pdata:
                ntemp = re.findall('\(\whose (\d+.+)\)',pdata)[0].strip()
                ntemp = ntemp.replace("total $","total: $")
                player_notes.append(ntemp)
                # streak
                player_streak.append(int(re.findall('\(\D+(\d+)-',pdata)[0]))
                # winnings
                try: wtemp = re.findall('\(.+\$(\S+)\)',pdata)[0]
                except: wtemp = "0" #missing winnings, ex: "Amy Ellis, a pharmacologist from Rockville, Maryland (whose 1-day cash winnings total $)" [game_id=1668]
                player_winnings.append(int(wtemp.replace(",","").strip()))
                # winnings type = Cash
                player_winnings_type.append("C")
                # remove the hometown parenthetical
                htemp = hometown[:hometown.find(" (")].strip()
                player_hometown.append(htemp)

            elif "(subtotal" in pdata: #indicates a multi-round tournament finals; shows their score from the prev day
                #player_notes.append((pdata[pdata.find("(")+1:-1])[0].upper() + (pdata[pdata.find("(")+2:-1])) #capitalizes the first letter and removes ()
                player_notes.append("Carryover amount: " + pdata[pdata.find("$"):-1])
                # no streaks in tournament play
                player_streak.append(None)
                # winnings
                wtemp = re.findall('\(.+\$(\S+)\)',pdata)[0]
                player_winnings.append(int(wtemp.replace(",","").strip()))
                # winnings type = Tourney$$
                player_winnings_type.append("T")
                game_type = 'T' # in case this wasn't properly set
                # remove the hometown parenthetical
                htemp = hometown[:hometown.find(" (")].strip()
                player_hometown.append(htemp)

            else:
                player_notes.append(None)
                player_streak.append(None)
                player_winnings.append(None)
                player_winnings_type.append(None)
                player_hometown.append(hometown)
                #player_occupation was appended before this IF statement
            p_counter += 1

        # players are introduced right-to-left, but i want to number them left-to-right
        player_position.reverse() #this way, the returning champ is always position = 1.
        # also helps w/scaling (some Super Jeopardy games had 4 players)

        #### TOURNAMENT STUFF ####
        if game_type == 'T': #already validated that game_notes is not null for these games
            # write the tourney types to a local dictionary
            write.execute('SELECT id, name FROM tournament_type ORDER BY id')
            t_types = write.fetchall()
            # write the tourney stages to a local dictionary
            write.execute('SELECT id, name FROM tournament_stage ORDER BY id')
            t_stages = write.fetchall()

            """
            print("Tourney types:",t_types)
            print("")
            print("Tourney stages:",t_stages)
            print("")"""

            # tourney type: if notes for a game include the tourney name, use that type
            for t in t_types:
                if t[1].lower() in game_notes.lower(): tt_id = int(t[0])
            # the 2001 int'l tourney was called the _championship_ in 2001; they belong under the same t_id
            if "international championship" in game_notes.lower(): tt_id = 5

            # tourney stage (aka round)
            for s in t_stages:
                if s[1].lower() + " game" in game_notes.lower():
                    t_stage_id = int(s[0])
                    break #otherwise a semifinal game would be overwritten as a final game
                # slightly different for UToC
                if "ultimate tournament of champions round" in game_notes.lower():
                    t_stage_id = int(re.findall(' round (\d)',game_notes.lower())[0])

            # find the tourney game number
            if re.search('final game (\d+)', game_notes.lower()):
                t_game_id = int(re.findall('final game (\d+)', game_notes.lower())[0])
            # slightly different for UToC
            if "ultimate tournament of champions round" in game_notes.lower():
                t_game_id = int(re.findall('round \d+, game (\d+)', game_notes.lower())[0])

            # set the tourney pool, if applicable
            if re.search('^\d\d\d\d-([AB])', game_notes):
                pool = game_notes[5:6]

        #### WRITE DATA TO THE 'game' TABLE ####
        # program assumes no data exists for the current game
        v = None
        write.execute('SELECT * FROM game WHERE id = ' + str(game_id) + ' LIMIT 5')
        v = write.fetchone()
        if v == None:
            write.execute('''INSERT INTO game
            (id, show, date, season_id, type_id, theme_id, tournament_stage_id, tournament_game, pool, notes, incomplete_data)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (game_id, show, aired, season_id, game_type, game_theme, t_stage_id, t_game_id, pool, game_notes, incomplete_data))
            #print("Wrote data for game_id=" + str(game_id))
        else:
            print("There's already data for game_id=" + str(game_id))
            g_exists.append(game_id)

        #### WRITE DATA TO THE 'game_player' TABLE ####
        # program assumes no data exists for the current game-player pair
        k = 0
        while k < num_players:
            v = None
            write.execute('SELECT * FROM game_player WHERE game_id = ' + str(game_id) + ' and player_id = ' + str(player_id[k]) + ' LIMIT 5')
            v = write.fetchone()
            if v == None:
                write.execute('''INSERT INTO game_player
                    (game_id, player_id, player_name, occupation, 'from', player_position, current_streak_wins, current_streak_winnings, winnings_type, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?)''', (game_id, player_id[k], player_name[k], player_occupation[k], player_hometown[k], player_position[k], player_streak[k], player_winnings[k], player_winnings_type[k], player_notes[k]))
                #print("Wrote data for game_id=" + str(game_id) + ", player_id=" + str(player_id[k]))
            else:
                print("There's already data for game_id=" + str(game_id) + ", player_id=" + str(player_id[k]))
                gp_exists.append(str(game_id) + "-" + str(player_id[k]))
            k += 1

        i += 1 #counter for gamedata html lines
        j += 1 #overall loop counter
        game_id += 1

    # update boundaries for the next chunk of html gamedata
    gmin = game_id
    gmax = min(max_game, game_id + per_loop) + 1

    # commit db changes after each chunk of html is parsed
    conn_write.commit()

print("")
print("***** ***** ***** *****")
print("Scanned",j,"games,",p_counter,"players.")
print("Games which already had data:",len(g_exists),".",g_exists)
print("Game-players which already had data:",len(gp_exists),".",gp_exists)
print("Games to re-scrape:",len(errors),".",errors)
print("")

conn_write.commit()
conn_write.close()
conn_read.close()
quit()
# """
