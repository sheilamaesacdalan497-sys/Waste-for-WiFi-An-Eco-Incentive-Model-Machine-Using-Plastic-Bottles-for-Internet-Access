# script to inspect the SQLite database file used by the app, printing out tables and schemas for debugging purposes
import sys
from pathlib import Path
# ensure repo root is on sys.path so "from app import create_app" works
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import create_app
import os, sqlite3

app = create_app()
db_path = app.config.get('DB_PATH') or app.config.get('DATABASE') or os.path.join(app.instance_path, 'wifi_portal.db')
print('DB path:', db_path)

if not os.path.exists(db_path):
    print('DB file not found.')
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print('Tables:', [r[0] for r in cur.fetchall()])
    print('\nSchemas:')
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
    for name, sql in cur.fetchall():
        print(f'\n-- {name} --\n{sql}')
    conn.close()