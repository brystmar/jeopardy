"""
Config file for MySQL, et all
user: 'py4e'@'localhost'
pass: 'zjc5^Jkv9u_TFeo2'
"""

import mysql.connector

cnx = mysql.connector.connect(user='py4e', password='zjc5^Jkv9u_TFeo2', host='localhost', database='Jeopardy')
cur = cnx.cursor()

cur.execute('SELECT * FROM jeopardy.clue_type')
val = cur.fetchall()

for v in val:
    print(v)

cnx.close()
