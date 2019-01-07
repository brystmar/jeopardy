import sqlite3
print("")

def pause():
    programPause = input("<...>")#input("Press the <ENTER> key to continue...")
    programPause.strip()

#conn_write = sqlite3.connect('/users/tberg/documents/python/PY4E/Jeopardy/jdata.sqlite')
conn_read = sqlite3.connect('jdata.sqlite')
read = conn_read.cursor()

conn_write = sqlite3.connect('divdata.sqlite')
write = conn_write.cursor()

read.execute('select game_id, crtid, html, cr_notes, c_notes from clue_div order by 1,2')
#read.execute('select game_id, crtid, html from clue_div where html not like "%<td id%>" order by 1,2')
html = read.fetchall()

print(len(html), "read")

i=0
for h in html:
    cresp_html = h[2].replace('<td class="right"', '<td id="name" class="right"')
    cresp_html = cresp_html.replace('<td class="wrong"', '<td id="name" class="wrong"')
    cresp_html = cresp_html.replace('<td rowspan="2" valign="top"', '<td id="response"') #unnecessary; only applies to FJ
    cresp_html = cresp_html.replace('</tr><tr><td>', '<td id="wager">$') #consolidate rows, add id tag, normalize score display; only FJ
    cresp_html = cresp_html.replace('<td id="wager">$$', '<td id="wager">$') #remove double $s; only FJ

    write.execute('insert into cdiv (game_id, crtid, html, cr_notes, c_notes) values (?,?,?,?,?)', (h[0],h[1],cresp_html,h[3],h[4]))

    if i % 1000 == 0: print(i, "parsing row")
    if i % 10000 == 0:
        conn_write.commit()
        print(i, "COMMIT")
        
    i += 1

print("Wrote",i,"rows")
conn_write.commit()
conn_write.close()
#"""
