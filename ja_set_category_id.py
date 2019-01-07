"""
Set category_ids
"""

import sqlite3, re, html
print("")
print("***** ***** ***** *****")

# open & initialize the db
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jtemp.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

i = 0
j = 0

read.execute('SELECT distinct name, count(*) as num FROM cat group by 1 ORDER BY num desc, name')
catlist = read.fetchall()

for cl in catlist:
    write.execute('SELECT id FROM category WHERE name = ?',(cl[0],))
    try: val = write.fetchone()[0]
    except: val = None
    if val == None:
        write.execute('INSERT INTO category (name) VALUES (?)',(cl[0],))
        conn_write.commit()
        j += 1
    else:
        print(i,"Category already exists: id=" + str(val),cl[0])
    if i % 500 == 0: print(i)
    i += 1

conn_write.commit()
conn_write.close()
conn_read.close()

print("Committed",j,"changes")
# """
