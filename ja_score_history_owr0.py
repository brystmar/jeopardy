"""
Record the player's score as owr=0 before the DJ and FJ rounds.  We'll grab this data from the player_round_result table.
"""
import sqlite3, re, datetime
time_start = datetime.datetime.now()
time_start = time_start.isoformat(timespec='seconds')
time_start = str(time_start).replace("T", " ")
print("***** ***** ***** ***** ****")
print(" Start:", time_start)
print("***** ***** ***** ***** ****")
print("")
filename = "ja_score_history_owr0.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

jdata.execute('SELECT coalesce(max(game_id),0) from game_score_hist where round_id = 2 and clue_owr = 0')
next_game = int(jdata.fetchone()[0]) + 1

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
    for i in items: print(i)
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

    if crtid == None or crtid == '': crtid = 'n/a'

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

    print("Error:", game_id, notes)
    #conn_jdata.commit()
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
    else: pass # error has already been recorded

    print("Missing data:", game_id, rnd, crtid, typ, type_info, notes)
    #conn_jdata.commit()
def write_owr0(pdata):
    count = 1
    prevgame = 0
    for p in pdata: #for each player's score in each round.  Data: game_id, round_id, player_id, score
        rnd = p[1] + 1 #end of round score = beginning score for the next round
        game = p[0]

        # validation
        jdata.execute('SELECT score FROM game_score_hist WHERE clue_owr = 0 and game_id = ? and round_id = ? and player_id = ?', (p[0], rnd, p[2]))
        try: val = jdata.fetchone()[0]
        except: val = jdata.fetchone()

        #print(type(val), val)
        #pause()

        if val == None:
            if game != prevgame: print("Writing game", game)
            jdata.execute('''INSERT INTO game_score_hist (game_id, round_id, player_id, score, clue_owr)
                VALUES ''' + qmarks(5), (p[0], rnd, p[2], p[3], 0))
        else:
            print("owr=0 exists for game " + str(p[0]) + ", round " + str(rnd) + ", player " + str(p[2]) + ".")
            pause()
            #write_errors(game_id, None, "owr=0 exists for game " + str(game_id) + ", round " + str(rnd) + ", player " + str(player_id) + " (" + nick + ".")

        if count % 6000 == 0:
            print("** COMMIT **")
            conn_jdata.commit()
        prevgame = game
        count += 1

# read data
jdata.execute('SELECT distinct game_id, round_id, player_id, score FROM player_round_result WHERE round_id in(1,2) order by 1,2,3,4')
pdata = jdata.fetchall()

write_owr0(pdata)

conn_jdata.commit()
conn_jdata.close()

time_end = datetime.datetime.now()
time_end = time_end.isoformat(timespec='seconds')
time_end = str(time_end).replace("T", " ")

print("")
print("Missing:", errors['missing'])
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")
print("Start:", time_start)
print("Ended:", time_end)
print("")

quit()
# """
