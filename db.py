("""Simple sqlite helpers for the captive portal.

Provides: init_db(app), get_db(), close_db()
""")
import sqlite3
import os
from flask import current_app, g
from datetime import datetime, timezone


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
		("expired", end_time or datetime.now(timezone.utc), session_id),
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
		(session_id, rating, comment, datetime.now(timezone.utc)),
	)
	db.commit()

