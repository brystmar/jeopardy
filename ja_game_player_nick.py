"""
Record the player's score as owr=0 before the DJ and FJ rounds.  We'll grab this data from the player_round_result table.
Also adds the player's nickname to the game_player table for the first time.
"""
import sqlite3, re, datetime
time_start = datetime.datetime.now()
time_start = time_start.isoformat(timespec='seconds')
time_start = str(time_start).replace("T", " ")
print("***** ***** **** ***** *****")
print(" Start:", time_start)
print("***** ***** **** ***** *****")
print("")
filename = "ja_score_history_owr0.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

#ja.execute('SELECT max(game_id) from games_scraped where scores is not null')
#max_game_db = int(ja.fetchone()[0])
max_game_db = 5883

jdata.execute('SELECT coalesce(max(game_id),0) from game_score_hist where round_id = 2 and clue_owr = 0')
next_game = int(jdata.fetchone()[0]) + 1

loop_counter = 0
errors = {'new': 0, 'dupes': 0, 'missing': 0}

i=0
j=0
k=0

def pause(): pz = input("====")
def pp(item):
    print("")
    print(item)
    pause()
def print_list(items):
    for i in items:
        print(i)
    pause()
def print_sortedlist(items):
    newlist = list()
    ditems = set(items)
    for d in ditems:
        newlist.append(d)
    newlist.sort()
    for n in newlist:
        print(items.count(n), n)
    pause()
def print_dict(items):
    #if 'card' not in str(items): return 0
    for i in items:
        print(i, items[i])
    pause()
    print("")

# compare those to the players for each game from the prr table
jdata.execute('SELECT distinct game_id, player_id, nickname FROM player_round_result order by 1,2,3')
pdata = jdata.fetchall()

count = 1
prevgame = 0
for p in pdata: #for each player in each game
    game = p[0]

    if game != prevgame: print("Game", game)
    jdata.execute('UPDATE game_player SET nickname = ? WHERE game_id = ? and player_id = ?', (p[2], p[0], p[1]))

    prevgame = game
    count += 1

conn_jdata.commit()
conn_jdata.close()

time_end = datetime.datetime.now()
time_end = time_end.isoformat(timespec='seconds')
time_end = str(time_end).replace("T", " ")

print("")
print("Start:", time_start)
print("Ended:", time_end)
print("")

quit()
# """
