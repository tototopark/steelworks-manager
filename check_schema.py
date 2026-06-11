import sqlite3
import json
conn = sqlite3.connect('f:/pe/public_html/steelworks-manager/data/steelworks.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
rows = cur.execute("SELECT * FROM tb_login WHERE login = 'admin'").fetchall()
print(json.dumps([dict(row) for row in rows], indent=2))
