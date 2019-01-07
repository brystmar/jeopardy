"""
Python for Everyone Capstone
Capture season start & end dates from a text file copied from: http://www.j-archive.com/listseasons.php
"""
import sqlite3
print("")

# open & initialize the db
conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
cur = conn.cursor()

# open & initialize the file
filename = "season_dates.txt"
fh = open(filename)

i = 0
l = list()
d = list()
notes = None
season = None

for line in reversed(list(fh)):
    if len(line) < 3: break

    # clean & split by the delimeter |
    line = line.strip()
    l = line.split("|")
    if l[0] in('Trebek pilots','Super Jeopardy!'): continue

    # load data into vars
    season = int(l[0][7:])
    d = l[1].split(" to ")
    season_start = d[0]
    season_end = d[1]

    # already have season data?
    cur.execute('SELECT id FROM season WHERE id = ?',(season,))
    try:
        exists = cur.fetchone()[0]
        # data must already exist for this season; skip it
        print("Data already exists for Season",season)
        continue
    except: pass

    # add notes about Super Jeopardy being included in s7
    if season == 7:
        notes = "Includes the Super Jeopardy tournament held between Seasons 6 and 7 (1990-06-16 to 1990-09-08)."
    else: notes = None

    # write to the db
    cur.execute('INSERT OR IGNORE INTO season (id, start_date, end_date, notes) VALUES (?,?,?,?)', (season,season_start,season_end,notes))
    print("Wrote data for Season",season)
    i += 1

# commit changes, close connections
conn.commit()
conn.close()

print("")
# """
