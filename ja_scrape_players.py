"""
Python for Everyone Capstone: Scrape Jeopardy data for all games and players from j-archive.com
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl, sqlite3, re
print("")

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# open & initialize the db
#conn = sqlite3.connect('/Volumes/Public/PY4E/Jeopardy/jarchive.sqlite')
conn = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jarchive.sqlite')
cur = conn.cursor()

#cur.execute('CREATE TABLE IF NOT EXISTS players_scraped (player_id INTEGER, data BLOB, stats BLOB)')

url = dict()
url['player'] = "http://www.j-archive.com/showplayer.php?player_id="
url['pstats'] = "http://www.j-archive.com/showplayerstats.php?player_id="
player_id = 500

r = 0
i = 0
remove = list()
remove.append("""<div id="disclaimer">The J! Archive is created by fans, for fans.  The <i><a href="http://www.jeopardy.com">Jeopardy!</a></i> game show and all elements thereof, including but not limited to copyright and trademark thereto, are the property of Jeopardy Productions, Inc. and are protected under law.  This website is not affiliated with, sponsored by, or operated by Jeopardy Productions, Inc.  Join the discussion at <a href="http://jboard.tv">JBoard.tv</a>.</div>""")
remove.append("""<script src="http://www.google-analytics.com/urchin.js" type="text/javascript"></script>""")

while player_id <= 543:
    print("Retrieving player", player_id, "|| loop", i+1)
    # open the URL, get the html/php
    html_p = urlopen(url['player'] + str(player_id)).read()
    html_s = urlopen(url['pstats'] + str(player_id)).read()
    soup_p = BeautifulSoup(html_p, "html.parser")
    soup_s = BeautifulSoup(html_s, "html.parser")

    """
    #print("*** html_g:",type(html_g))
    #print("")
    #print("*** soup_g:",type(soup_g), str(soup_g))

    asdf = input(continue? )
    if asdf == 0: quit()

    cur.execute(SELECT * FROM players_scraped WHERE player_id = ? LIMIT 1,(player_id,))
    try:
        exists = cur.fetchone()[0]
    except:
        exists = None

    if exists == None:
    """
    try: soup_p.find('div', id='navbar').decompose()
    except: pass

    try: soup_s.find('div', id='navbar').decompose()
    except: pass

    while r < len(remove):
        soup_p = str(soup_p).replace(remove[r],"")
        soup_s = str(soup_s).replace(remove[r],"")
        r += 1

    r = 0
    cur.execute('INSERT OR IGNORE INTO players_scraped (player_id, data, stats) VALUES (?,?,?)',(player_id, soup_p, soup_s))
    player_id += 1
    i += 1

    if i % 100 == 0:
        conn.commit()

conn.commit()
conn.close()
print("")

# """
