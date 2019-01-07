"""
Python for Everyone Capstone
Clean & organize player data scraped from j-archive.org
Ignore the 'stats' data for now
"""
from bs4 import BeautifulSoup
import sqlite3, re
print("")

player_name = None
i = 0
j = 0
k = 0
xyz = 1
userlist = list()
aliases = list()
a_list = list()
user = None

# open & initialize the db
#conn_read = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn_read = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite') #much faster using the local db
#conn_write = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jdata.sqlite')
conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
read = conn_read.cursor()
write = conn_write.cursor()

# find where we left off last time
write.execute('SELECT max(id) FROM player')
starting_point = write.fetchone()
for item in starting_point:
    if j > 0: break
    if item == None:
        player_id = 1
        j += 1
        break
    player_id = int(item)
    j += 1

# find the max player_id we've scraped
read.execute('SELECT max(player_id) FROM players_scraped')
starting_point = read.fetchone()
for item in starting_point:
    if k > 0: break
    if item == None:
        max_player = 11811
        k += 1
        break
    max_player = int(item)
    break
    k += 1

print("***************************")
print("Range:",player_id,max_player)
print("***************************")

while player_id <= max_player:
    # retrieve player data html
    read.execute('SELECT data FROM players_scraped WHERE player_id = ?',(player_id,))
    # read the html blob
    line = read.fetchone()[0]
    # soup-ify the html
    soup = BeautifulSoup(line, "html.parser")

    player_name = soup.find_all('p','player_full_name')[0].text.strip()
    o_and_h = soup.find_all('p','player_occupation_and_origin')[0].text.strip()
    notes = soup.find_all('p','text')[0].text.strip()
    if re.search('[u|U]ser.*?[n|N]ame:[ \t\f\r\v](.+)',notes):
        userlist.append(re.findall('[u|U]ser.*?[n|N]ame:[ \t\f\r\v](.+)', notes))
        for u in userlist: user = u[0].strip()

    print(player_id, player_name, end=' ')

    # raw occupation & hometown
    occupation = o_and_h.rpartition(' from ')[0]
    hometown = o_and_h.rpartition(' from ')[2] #[hometown.index(' from ')+6:]

    # clean up occupation
    if occupation.endswith(' originally'):
        occupation = occupation[:-11]
    if occupation[0:1].lower() == 'a':
        fs = occupation.index(' ')
        occupation = occupation[fs+1].upper() + occupation[fs+2:]
    # clean up hometown
    hometown = hometown.replace('...','')

    # write player data
    write.execute('SELECT id FROM player WHERE id = ' + str(player_id))
    if write.fetchone() == None:
        #print(player_id, player_name, "already exists.  Skipping.")
        write.execute('INSERT OR IGNORE INTO player (id, name, occupation, hometown, username, notes, ja_player_id) VALUES (?,?,?,?,?,?,?)', (player_id, player_name, occupation, hometown, user, notes, player_id))
        #print("Wrote:", season_id, season_name, ja_game_id, show, aired)
    else: print("already exists. Skipping.", end=' ')

    # find aliases
    aliaslinks = str(soup.find_all('td','top_padded'))
    aliases = re.findall('showplayer\.php\?player_id=(\d+)"', aliaslinks)
    # write aliases
    for alias in aliases:
        alias_id = int(alias)
        tup1 = (player_id,alias_id)
        tup2 = (alias_id,player_id)

        # determine if the (player,alias) tuple already exists
        write.execute('SELECT player_id, alias_id from player_alias WHERE player_id in(?,?)', tup1)
        #print("before:",a_list)
        a_list = write.fetchall()
        #print("after:",a_list)
        #write.execute('SELECT * from player_alias')
        #print(write.fetchall())

        if a_list.count(tup1) > 0:
            print("- Alias for", tup1, "already exists.", end=' ')
            continue
        if a_list.count(tup2) > 0:
            print("- Alias for", tup2, "already exists.", end=' ')
            continue

        # save this new alias
        write.execute('INSERT OR IGNORE INTO player_alias (player_id, alias_id, notes) VALUES (?,?,?)',(player_id, alias_id, "From " + str(player_id) + " http://www.j-archive.com/showplayer.php?player_id=" + str(player_id)))
        conn_write.commit()
        print("New alias:",str(tup1)+".",end=' ')

    player_id += 1
    user = None
    i = 0
    if i % 150 == 0: conn_write.commit()
    print("")

# commit changes, close connections
conn_write.commit()
conn_write.close()
conn_read.close()

print("")
# """
