"""
Python for Everyone Capstone: Scrape Jeopardy data for all games from j-archive.com
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl, sqlite3, re, html
print("")

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# open & initialize the db
conn = sqlite3.connect('jarchive.sqlite')
cur = conn.cursor()

#cur.execute('DROP TABLE games_scraped_soup')
#conn.commit()

#cur.execute('CREATE TABLE IF NOT EXISTS games_scraped (game_id INTEGER, show INTEGER, aired TEXT, gamedata BLOB, responses BLOB, scores BLOB)')
#cur.execute('CREATE TABLE IF NOT EXISTS raw_games_scraped (game_id INTEGER, show INTEGER, aired TEXT, gamedata BLOB, responses BLOB, scores BLOB)')

url = dict()
url['gamedata'] = "http://www.j-archive.com/showgame.php?game_id="
url['responses'] = "http://www.j-archive.com/showgameresponses.php?game_id="
url['scores'] = "http://www.j-archive.com/showscores.php?game_id="
game_id = 1318 = remove_this
max_game = 1400

r = 0
i = 0
remove = list()
remove.append("""<div id="disclaimer">The J! Archive is created by fans, for fans.  The <i><a href="http://www.jeopardy.com">Jeopardy!</a></i> game show and all elements thereof, including but not limited to copyright and trademark thereto, are the property of Jeopardy Productions, Inc. and are protected under law.  This website is not affiliated with, sponsored by, or operated by Jeopardy Productions, Inc.  Join the discussion at <a href="http://jboard.tv">JBoard.tv</a>.</div>""")
remove.append("""<script src="http://www.google-analytics.com/urchin.js" type="text/javascript"></script>""")

while game_id <= max_game:
    # game data already exists?
    cur.execute('SELECT game_id FROM games_scraped WHERE game_id = ' + str(game_id))
    try:
        exists = write.fetchone()[0]
        # data must already exist for this game; skip it
        print("Data already exists for game",season)
        game_id += 1
        continue
    except: pass

    print("Retrieving game", game_id, "|| loop number", i+1)
    # open the URL, get the html/php
    html_g = urlopen(url['gamedata'] + str(game_id)).read()
    html_r = urlopen(url['responses'] + str(game_id)).read()
    html_s = urlopen(url['scores'] + str(game_id)).read()
    # might help to unescape all the encoded HTML tags (mostly from the javascript portions) before using Soup
    soup_g = BeautifulSoup(html.unescape(str(html_g)), "html.parser")
    soup_r = BeautifulSoup(html.unescape(str(html_r)), "html.parser")
    soup_s = BeautifulSoup(html.unescape(str(html_s)), "html.parser")

    """
    # soup-ify the html
    soup_g = BeautifulSoup(html_g, "html.parser")
    soup_r = BeautifulSoup(html_r, "html.parser")
    soup_s = BeautifulSoup(html_s, "html.parser")
    """

    title = soup_g.find_all('title')
    title = str(title).strip()
    try:
        show = re.findall('#(\d+)', title)[0]
        aired = re.findall('aired (\S+)<', title)[0]
    except:
        show = re.findall('#(\d+)', title)[0]
        aired = title.replace("<title>","")
        aired = title.replace("</title>","")

    try:
        show = int(show)
    except:
        show = 0

    # remove the navbar section from each
    soup_g.find('div', id='navbar').decompose()
    #soup_g.find('div', id='disclaimer').decompose()
    soup_r.find('div', id='navbar').decompose()
    #soup_r.find('div', id='disclaimer').decompose()
    soup_s.find('div', id='navbar').decompose()
    #soup_s.find('div', id='disclaimer').decompose()

    while r < len(remove):
        soup_g = str(soup_g).replace(remove[r],"")
        soup_r = str(soup_r).replace(remove[r],"")
        soup_s = str(soup_s).replace(remove[r],"")
        r += 1

    r = 0
    cur.execute('INSERT INTO games_scraped (game_id, show, aired, gamedata, responses, scores) VALUES (?,?,?,?,?,?)',(game_id, show, aired, soup_g, soup_r, soup_s))
    #cur.execute('INSERT INTO raw_games_scraped (game_id, show, aired, gamedata, responses, scores) VALUES (?,?,?,?,?,?)',(game_id, show, aired, html_g, html_r, html_s))

    #else:
    #    cur.execute('INSERT INTO games_scraped (gamedata, responses, scores) VALUES (?,?,?) WHERE game_id = ?',(url['gamedata'], html_g, soup_g, game_id))
    #    cur.execute('INSERT INTO games_scraped_soup (gamedata, responses, scores) VALUES (?,?,?) WHERE game_id = ?',(url['gamedata'], html_g, soup_g, game_id))
    game_id += 1
    i += 1

    if i % 100 == 0:
        conn.commit()

conn.commit()
conn.close()
print("")
# """
