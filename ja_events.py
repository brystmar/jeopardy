"""
Read, clean the events html.  Write to the events table.
"""
from bs4 import BeautifulSoup
import sqlite3, re, html, datetime, itertools
print("")
print("***** ***** ***** *****")
filename = "ja_clue_responses.py"

# open & initialize the db
conn_jdata = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
jdata = conn_jdata.cursor()

# open the html file
filename = 'event_payouts.html'
fh = open(filename, "r", encoding="utf-8")
html = fh.read()

i=0
j=0
k=0
tcount = 0
tlist = list()
errors = {'new': 0, 'dupes': 0, 'missing': 0}

def qmarks(num):
    # returns a string of question marks in the length requested, ex: (?,?,?,?)
    i = 0
    q = "("
    while i < num:
        q += "?,"
        i += 1
    return q[:-1] + ")"
def pause(): pz = input("====")
def write_errors(game_id, crtid, notes):
    global errors
    global filename

    # save the timestamp
    timestamp = datetime.datetime.now()
    timestamp = timestamp.isoformat(timespec='seconds')
    timestamp = str(timestamp).replace("T", " ")

    if crtid == None: crtid = 'n/a'

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
    else:
        # error has already been recorded
        pass

    conn_jdata.commit()
def remove_html_tags(t):
    t = str(t)
    # find & fix erroneous starting tags, ex: </i>text</i>
    if re.search('^</([a-zA-Z])>', t.strip()):
        t = "<" + re.findall('^</([a-zA-Z])>', t.strip())[0] + ">" + t[4:]
    # prep for soupification
    t = t.strip()
    t = "<td>" + str(t) + "</td>"
    soup = BeautifulSoup(t, "html.parser")
    return soup.td.text.strip() #soup returns the text string without formatting tags like <b>, <u>, <i>

# retrieve the list of themes from the db
jdata.execute('SELECT name, id FROM event_theme order by 1')
themes = jdata.fetchall()

# add a div to encapsulate each event
html = html.replace('<h3', '<div id="event">\n<h3')
html = html.replace('</table>', '</table>\n</div>')

# soupify the html
soup = BeautifulSoup(html, "html.parser")
divs = soup.find_all(id='event')
err = list()
for d in divs:
    notes = None
    theme = None
    location = None
    title = d.find_all('h3')[0].text.strip()

    # location
    if "from" in title:
        location = title.split("from")[1]
        location = location[1:-1].strip()
        location = location[0:1].upper() + location[1:]

    if title == None: continue
    tname = re.findall('(\d\d\d\d.*?)\(', title)[0].strip()
    year = int(tname[:4])
    if "2009-2010 Million Dollar Celebrity Invitational" in tname:
        year = 2009
    if "Ultimate Tournament of Champions" in tname:
        tname = "2005 Ultimate Tournament of Champions"
    if tname[4:6] == "-A":
        tname = tname.replace("-A","")
        tname = tname + " (A)"
    elif tname[4:6] == "-B":
        tname = tname.replace("-B","")
        tname = tname + " (B)"
    elif tname[4:6] == "-C":
        tname = tname.replace("-C","")
        tname = tname + " (C)"

    if '<tr><td colspan="2" id="notes">' in str(d):
        notes = d.find_all("td", id="notes")[0].text.strip()

    # determine theme, if any
    for th in themes:
        if th[0] in tname:
            theme = th[1]

    # determine game_type
    if "tournament" in str(d).lower() or "champion" in str(d).lower():
        game_type = 'T'
    elif "2nd place" in str(d).lower():
        game_type = 'X'
    else:
        game_type = 'Unknown'
        err.append(tname)

    # check for dupes, then append
    found = False
    for t in tlist:
        if tname == "2005 Ultimate Tournament of Champions" and tname in t[0]:
            found = True
    if found == False: tlist.append([tname, year, theme, game_type, location, notes])

    """
    print("")
    print(year, tname)
    print(location)
    print(notes)
    """
tlist = sorted(tlist, key=lambda item: item[0])
for t in tlist:
    # validation before writing data
    jdata.execute('SELECT id FROM event WHERE name = ? and year = ?', (t[0],t[1]))
    try: val = jdata.fetchone()[0]
    except: val = jdata.fetchone()
    if val == None:
        jdata.execute('INSERT INTO event (name, year, theme, game_type, location, notes) VALUES ' + qmarks(6), (t[0],t[1],t[2],t[3],t[4],t[5]))
    else:
        print(t[0], '(' + str(t[1]) + ') already exists as event_id', val)

print(len(tlist))
print(err)

#conn_jdata.commit()
conn_jdata.close()
fh.close()
"""
print("")
print("Tourneys imported:", tcount)
print("")
print("Missing:", errors['missing'])
print("Duplicate errors:", errors['dupes'])
print("New errors:", errors['new'])
print("")

# """
