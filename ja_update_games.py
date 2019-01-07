"""
Fix some data in the 'game' table regarding the Battle of the Decades tourney
"""
import sqlite3, re
print("")
print("***** ***** ***** *****")
print("")

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
write = conn.cursor()

# find the games to edit
write.execute('select id, notes from game where structure_id = 2 and tournament_id is null order by notes')
games = write.fetchall()

# write the tourneys to a local dictionary
write.execute('SELECT id, name FROM tournament ORDER BY id')
tourneys = write.fetchall()

i=0

for g in games:
    game_id = int(g[0])
    tid = None
    notes = g[1][:4] + g[1][6:]

    #if "battle of the decades: the" in g[1].lower():
        #stage_id = 2
        #pool = re.findall('Decades: (The \d\d\d\ds)', g[1])[0].strip()

    # tourney stage (aka round)
    for t in tourneys:
        if notes.startswith(t[1]):
            tid = int(t[0])
            break
    #print(game_id, stage_id, game, pool, g[1])

    # write to the db
    conn.execute('UPDATE game SET tournament_id = ? WHERE id = ?', (tid, g[0]))
    conn.commit()
    print(game_id, tid)
    #if i > 50: quit()
    i+=1

print("")

conn.commit()
conn.close()
quit()
#"""

write.execute('SELECT id FROM game WHERE lower(notes) like "%teen%" and id <> 3970 ORDER BY id')
#games = write.fetchall()

for g in games:
    #conn.execute('UPDATE game SET theme_id = 7 WHERE id = ' + str(g[0]))
    print(g[0])

#conn.commit()
conn.close()
quit()
