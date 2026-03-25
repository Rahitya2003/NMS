# init_db.py
import sqlite3

conn = sqlite3.connect('notes_app.db')
with open('schema.sql') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print("SQLite database created!")