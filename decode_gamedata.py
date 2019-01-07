"""
Soup decoding test
"""
#from bs4 import BeautifulSoup
import sqlite3, html
import urllib.request, urllib.parse, urllib.error, ssl
print("")
print("***** ***** ***** *****")
print("")

def pause():
    print("")
    programPause = input("Press the <ENTER> key to continue...")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite') #much faster using the local db
conn_readsm = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive_decoded.sqlite')
read = conn_read.cursor()
readsm = conn_readsm.cursor()
write = conn_write.cursor()

write.execute('CREATE TABLE IF NOT EXISTS games_scraped (game_id integer not null, season_id integer not null, gamedata blob, responses blob, scores blob)')
read.execute('SELECT max(game_id) FROM games_scraped')
max_game = int(read.fetchone()[0])

write.execute('SELECT max(game_id) FROM games_scraped')
game_id = int(write.fetchone()[0]) + 1

#game_id = 1
#max_game = 3
per_loop = 50
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + " (" + str(max_game - game_id + 1) + " total).")

i = 0
j = 0
k = 0
decoded = list()
pause()

while game_id <= max_game:
    # store the html in a list
    read.execute('SELECT game_id, gamedata, responses, scores FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id < ' + str(gmax) + ' order by game_id asc')
    gdata = read.fetchall()

    i = 0
    while i < len(gdata):
        # get the season_id
        readsm.execute('SELECT season_id FROM game WHERE id = ' + str(gdata[i][0]))
        season_id = int(readsm.fetchone()[0])
        # clean up the unescaped HTML characters
        decoded_g = html.unescape(gdata[i][1])
        decoded_r = html.unescape(gdata[i][2])
        decoded_s = html.unescape(gdata[i][3])
        # add game_id and season_id below the content div
        decoded_g = decoded_g.replace('<div id="content">', '<div id="content"> \n<div id="game_id">' + str(gdata[i][0]) + '</div> \n<div id="season_id">' + str(season_id) + '</div>')
        decoded_r = decoded_r.replace('<div id="content">', '<div id="content"> \n<div id="game_id">' + str(gdata[i][0]) + '</div> \n<div id="season_id">' + str(season_id) + '</div>')
        decoded_s = decoded_s.replace('<div id="content">', '<div id="content"> \n<div id="game_id">' + str(gdata[i][0]) + '</div> \n<div id="season_id">' + str(season_id) + '</div>')

        print(j,'loop:',i,'game:',gdata[i][0],'season:',season_id)
        """#pause()
        #print(gdata[i][1])
        print(decoded_g)
        pause()
        #print(gdata[i][2])
        print(decoded_r)
        pause()
        #print(gdata[i][3])
        print(decoded_s)"""

        write.execute('INSERT OR IGNORE INTO games_scraped (game_id,season_id,gamedata,responses,scores) VALUES (?,?,?,?,?)', (gdata[i][0], season_id, decoded_g, decoded_r, decoded_s))

        i += 1
        j += 1
        game_id += 1

    #game_id += 1
    k += 1
    # update boundaries for the next chunk of html gamedata
    gmin = game_id
    gmax = min(max_game, game_id + per_loop) + 1

    # commit db changes after each chunk of html is parsed
    conn_write.commit()


print("")
print(j-1,'iterations total;',k-1,'loops total')
print("")

conn_write.commit()
conn_write.close()
conn_read.close()
quit()

# find the largest game we've already parsed data for
write.execute("SELECT max(id) FROM game")
latest_game = int(write.fetchone()[0])
game_id = latest_game + 1
read.execute("SELECT max(game_id) FROM games_scraped")
max_game = int(read.fetchone()[0])
per_loop = 100
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id,"total.")
