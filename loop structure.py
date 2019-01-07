"""
Parse html from game data to fill data points in the clue, clue_value, game_round_category, and player_round_result tables

"""
from bs4 import BeautifulSoup
import sqlite3, re, html
print("")
print("***** ***** ***** *****")
print("")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive_decoded.sqlite') #much faster using the local db
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

# find the largest game we've already parsed data for
write.execute('SELECT max(game_id) FROM game')
#latest_game = int(write.fetchone()[0])
#game_id = latest_game + 1
read.execute('SELECT max(game_id) FROM games_scraped')
#max_game = int(read.fetchone()[0])
game_id = 5695
max_game = 5695
per_loop = 50
gmin = game_id
gmax = min(max_game, game_id + per_loop)
print("Parsing data for games " + str(game_id) + " to " + str(max_game) + ",", max_game - game_id + 1, "total.")

while game_id <= max_game:
    # retrieve the gamedata html for this game
    #  'games_scraped' has columns: game_id, gamedata (html), responses (html), scores (html)
    read.execute('SELECT gamedata FROM games_scraped WHERE game_id >= ' + str(gmin) + ' and game_id < ' + str(gmax) + ' order by game_id asc')
    raw = read.fetchall()

    for ra in raw:
        # add <td> tags for each round
        ra = ra.replace('<div id="jeopardy_round">', '<div id="jeopardy_round"> <td class="category" id="round">CAT_R1</td> <td class="clue" id="round">CLUE_R1</td>')
        ra = ra.replace('<div id="double_jeopardy_round">', '<div id="double_jeopardy_round"> <td class="category" id="round">CAT_R2</td> <td class="clue" id="round">CLUE_R2</td>')
        modded.append(ra)

    i = 0
    while i < len(modded):
        soup = BeautifulSoup(modded[i], "html.parser")



        i += 1 #counter for gamedata html lines
        j += 1 #overall loop counter
        game_id += 1

    # update boundaries for the next chunk of html gamedata
    gmin = game_id
    gmax = min(max_game, game_id + per_loop) + 1

    # commit db changes after each chunk of html is parsed
    #conn_write.commit()

print("")

#conn_write.commit()
conn_write.close()
conn_read.close()
quit()
# """
