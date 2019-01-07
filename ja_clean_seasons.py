"""
Python for Everyone Capstone
Clean & organize season data scraped from j-archive.org
Ignores the 'pilot' season.  The 'Super Jeopardy' season is considered Season 7.
"""
from bs4 import BeautifulSoup
import sqlite3, re
print("")
print("***** ****** ***** *****")
print("")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite') #much faster using the local db
#conn_write = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jdata.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

season_id = 7
max_season = 7
season_name = None
i = 0
errors = list()

while season_id <= max_season:
    season = season_id #Trebek pilots are s0
    if season_id == 0: season = 7 #Super Jeopardy is grouped with s7

    # already have season data?
    write.execute('SELECT * FROM season_games WHERE season_id = ?',(season,))
    try:
        exists = write.fetchone()[0]
        # data must already exist for this season; skip it
        print("Data already exists for Season",season)
        #season_id += 1
        #continue
    except: pass

    read.execute('SELECT data FROM seasons_scraped WHERE season_id = ?',(season_id,))
    # read the html blob
    line = read.fetchone()[0]
    # soup-ify the html
    soup = BeautifulSoup(line, "html.parser")
    # grab the season name (it's the only thing inside an h2 tag on this page)
    season_name = soup.h2.string
    # collect all the <tr> tags
    trtags = soup.find_all('tr')

    for tr in trtags:
        # capture the notes field
        notes = str(tr.find(class_="left_padded").text).strip()

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
    conn_write.commit()
    i=0
    season_id += 1

# commit changes, close connections
conn_write.commit()
conn_write.close()
conn_read.close()

print("")
print("Errors:",len(errors))
print(errors)
print("")
# """
