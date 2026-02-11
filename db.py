("""Simple sqlite helpers for the captive portal.

Provides: init_db(app), get_db(), close_db()
""")
import sqlite3
import os
from flask import current_app, g
from datetime import datetime, timezone
import time


def get_db():
	if "db" not in g:
		db_path = current_app.config.get("DB_PATH")
		os.makedirs(os.path.dirname(db_path), exist_ok=True)
		g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
		g.db.row_factory = sqlite3.Row
	return g.db


def close_db(e=None):
	db = g.pop("db", None)
	if db is not None:
		db.close()


def init_db(app=None):
	# if called with app instance, register teardown and create tables
	if app is not None:
		app.teardown_appcontext(close_db)
		with app.app_context():
			_ensure_tables()


def _ensure_tables():
	db = get_db()
	cur = db.cursor()
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS sessions (
			id TEXT PRIMARY KEY,
			ip TEXT,
			mac TEXT,
			status TEXT,
			start_time TIMESTAMP,
			end_time TIMESTAMP,
			duration INTEGER
		)
		"""
	)
	# ensure bottles column exists (add if missing)
	cur.execute("PRAGMA table_info(sessions)")
	cols = [r[1] for r in cur.fetchall()]
	if "bottles" not in cols:
		try:
			cur.execute("ALTER TABLE sessions ADD COLUMN bottles INTEGER DEFAULT 0")
		except Exception:
			pass
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS ratings (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			session_id TEXT,
			rating INTEGER,
			comment TEXT,
			created_at TIMESTAMP
		)
		"""
	)
	db.commit()


def create_session(session_id, ip, mac=None, status="waiting", duration=None):
	db = get_db()
	db.execute(
		"INSERT OR REPLACE INTO sessions (id, ip, mac, status, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?, ?, ?)",
		(session_id, ip, mac, status, None, None, duration),
	)
	db.commit()


def update_session_start(session_id, start_time, duration):
	db = get_db()
	db.execute(
		"UPDATE sessions SET status = ?, start_time = ?, end_time = ?, duration = ? WHERE id = ?",
		("active", start_time, start_time + duration, duration, session_id),
	)
	db.commit()


def revoke_session(session_id, end_time=None):
	db = get_db()
	db.execute(
		"UPDATE sessions SET status = ?, end_time = ? WHERE id = ?",
		("expired", int(end_time if end_time is not None else time.time()), session_id),
	)
	db.commit()


def get_session(session_id):
	db = get_db()
	cur = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
	return cur.fetchone()


def add_rating(session_id, rating, comment=None):
	db = get_db()
	db.execute(
		"INSERT INTO ratings (session_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
		(session_id, rating, comment, int(time.time())),
	)
	db.commit()


def extend_session(session_id, extra_seconds):
	db = get_db()
	cur = db.execute("SELECT end_time, bottles FROM sessions WHERE id = ?", (session_id,))
	row = cur.fetchone()
	now = int(time.time())
	if row is None:
		return None
	end = row[0] or now
	try:
		end = int(end)
	except Exception:
		end = now
	new_end = end + int(extra_seconds)
	bottles = (row[1] or 0) + 1
	db.execute("UPDATE sessions SET end_time = ?, bottles = ? WHERE id = ?", (new_end, bottles, session_id))
	db.commit()
	return {"end": new_end, "bottles": bottles}


def migrate(app=None):
	"""Run migrations to ensure schema compatibility.

	If `app` is provided, run within its app_context so `get_db()` works.
	"""
	if app is not None:
		with app.app_context():
			_ensure_tables()
		return True
	return False

