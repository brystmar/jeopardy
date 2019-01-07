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
conn = sqlite3.connect('jarchive.sqlite')
cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS seasons_scraped (season_id INTEGER, data BLOB)')

url = dict()
url['season'] = "http://www.j-archive.com/showseason.php?season="
season_id = 35

r = 0
i = 0
remove = list()
remove.append("""<div id="disclaimer">The J! Archive is created by fans, for fans.  The <i><a href="http://www.jeopardy.com">Jeopardy!</a></i> game show and all elements thereof, including but not limited to copyright and trademark thereto, are the property of Jeopardy Productions, Inc. and are protected under law.  This website is not affiliated with, sponsored by, or operated by Jeopardy Productions, Inc.  Join the discussion at <a href="http://jboard.tv">JBoard.tv</a>.</div>""")
remove.append("""<script src="http://www.google-analytics.com/urchin.js" type="text/javascript"></script>""")

while season_id <= 34:
    print("Retrieving season", season_id, "|| loop",i+1)
    # open the URL, get the html/php
    html_s = urlopen(url['season'] + str(season_id)).read()
    #html_s = urlopen(url['season'] + "superjeopardy").read()
    #html_s = urlopen(url['season'] + "trebekpilots").read()
    soup_s = BeautifulSoup(html_s, "html.parser")

    soup_s.find('div', id='navbar').decompose()

    while r < len(remove):
        soup_s = str(soup_s).replace(remove[r],"")
        r += 1

    r = 0
    cur.execute('INSERT INTO seasons_scraped (season_id, data) VALUES (?,?)', (season_id, soup_s))
    season_id += 1
    i += 1

conn.commit()

#print(exists)
print("")

# """
