
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "arena.db"

def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT NOT NULL,
                player_x TEXT NOT NULL,
                player_o TEXT NOT NULL,
                result TEXT NOT NULL,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

def save_match(room_code, player_x, player_o, result):
    with connect() as db:
        db.execute(
            """INSERT INTO matches
               (room_code, player_x, player_o, result)
               VALUES (?, ?, ?, ?)""",
            (room_code, player_x, player_o, result),
        )

def get_stats():
    with connect() as db:
        rows = db.execute("""
            SELECT result, COUNT(*) AS total
            FROM matches GROUP BY result
        """).fetchall()
    return {row["result"]: row["total"] for row in rows}

def get_recent_matches(limit=20):
    with connect() as db:
        rows = db.execute("""
            SELECT room_code, player_x, player_o, result, played_at
            FROM matches ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    return [dict(row) for row in rows]

init_db()
