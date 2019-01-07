"""
Write data to the game_round_category table from the temp table we created in the temp db
"""

import sqlite3
print("")
print("***** ***** ***** *****")

# open & initialize the db
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

data = list()
i = 0
j = 0

"""
# write the cat_id to the jtemp db for easier mapping & transfer back
read.execute('select distinct name FROM cat WHERE cat_id is null order by 1')
data = read.fetchall()

for d in data:
    #print(i)
    write.execute('select id FROM category WHERE name = ?',(d[0],))
    cat_id = write.fetchone()[0]
    #print(d[0], "cat_id:",cat_id)

    read.execute('update cat SET cat_id = ? WHERE name = ?',(cat_id, d[0]))
    if i % 250 == 0:
        print(i,"Commit")
        conn_read.commit()
    i += 1

print("Updated",i,"categories")
print("")
"""

# get the game, round, and position data from the jtemp db
read.execute('select distinct game_id, round_id, cat_id, pos_y, notes FROM cat order by 1,2,3,4,5')
data = read.fetchall()

for d in data:
    # validation
    print(i,j)
    write.execute('SELECT game_id, round_id, category_id, category_order FROM game_round_category WHERE game_id = ? and round_id = ? and category_id = ? and category_order = ?', (d[0],d[1],d[2],d[3]))
    val = write.fetchone()
    if val == None or len(val) < 1:
        write.execute('INSERT INTO game_round_category (game_id, round_id, category_id, category_order, notes) VALUES (?,?,?,?,?)', (d[0],d[1],d[2],d[3],d[4]))
        j += 1
    else:
        print("Data exists for",d[0],d[1],d[2],d[3])

    if i % 250 == 0:
        print(i,"Commit")
        conn_write.commit()
    i += 1

print("Inserted",j,"rows on",i,"attempts")
print("")

conn_write.commit()
conn_write.close()
#conn_read.commit()
conn_read.close()
quit()
# """
