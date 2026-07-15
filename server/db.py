import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "attendance.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    for statement in (
        "ALTER TABLE classes ADD COLUMN archived INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE classes ADD COLUMN notes TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE classes ADD COLUMN color TEXT",
    ):
        try:
            conn.execute(statement)
        except sqlite3.OperationalError:
            pass  # column already exists on a database created before this feature
    conn.commit()
    conn.close()
