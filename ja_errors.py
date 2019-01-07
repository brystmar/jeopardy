"""
Write errors to a table in the db instead of a text file
"""
import sqlite3, re, datetime
print("")
print("***** ***** ***** *****")

def decode(a):
    a = a.replace("\\'","'")
    return html.unescape(str(a))

def pause():
    #print("")
    programPause = input("...")#input("Press the <ENTER> key to continue...")

errors = [["4261","clue_J_1_1"],["4261","clue_J_2_1"],["4261","clue_J_5_1"],["4261","clue_J_6_1"],["5773","clue_J_6_2"],["5773","clue_J_1_3"]]
notes = "Null question text"

timestamp = "2018-02-09 13:22:00"
filename = "ja_clean_clues.py"

# open & initialize the db
jdata_conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = jdata_conn.cursor()
#jtemp_conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
#jtemp = jtemp_conn.cursor()

i=0
for e in errors:
    game_id = e[0]
    crtid = e[1]

    jdata.execute('INSERT INTO errors (game_id, crtid, timestamp, notes) VALUES (?,?,?,?)', (game_id, crtid, timestamp, "Null question text"))
    if game_id == "4296" and crtid == "clue_DJ_1_4": continue
    else: jdata.execute('INSERT INTO errors (game_id, crtid, timestamp, notes) VALUES (?,?,?,?)', (game_id, crtid, timestamp, "Null answer text"))

    """jdata.execute('select distinct game_id, notes FROM errors WHERE game_id = ? and notes = ?', (game_id, notes))
    val = jdata.fetchone()
    if val == None:
        jdata.execute('insert INTO errors (game_id, timestamp, filename, notes) VALUES (?,?,?,?)', (game_id, timestamp, filename, notes))
        i += 1
    elif val[0] == game_id and val[1] == notes:
        print('Error data already exists: ' + str(game_id), notes)
        continue
    else:
        jdata.execute('insert INTO errors (game_id, timestamp, filename, notes) VALUES (?,?,?,?)', (game_id, timestamp, filename, notes))
        i += 1"""
    i += 1

print("Wrote", i, "values")

jdata_conn.commit()
jdata_conn.close()
# """
