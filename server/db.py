import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("TAPIN_DB_PATH", str(Path(__file__).parent / "attendance.db")))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
BACKUP_DIR = DB_PATH.parent / "backups"
BACKUP_RETENTION = 10


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        "ALTER TABLE classes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE accounts ADD COLUMN security_question_1 TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN answer_hash_1 TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN security_question_2 TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE accounts ADD COLUMN answer_hash_2 TEXT NOT NULL DEFAULT ''",
    ):
        try:
            conn.execute(statement)
        except sqlite3.OperationalError:
            pass  # column already exists on a database created before this feature
    conn.commit()
    conn.close()


def backup_database(backup_dir=None, retention=BACKUP_RETENTION):
    """Copies the SQLite database file to a timestamped backup, pruning
    older backups beyond `retention` (#41). Returns the backup path, or
    None if there is no database file yet to back up."""
    backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
    if not DB_PATH.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{DB_PATH.stem}-{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)

    existing = sorted(backup_dir.glob(f"{DB_PATH.stem}-*.db"))
    for stale in existing[:-retention]:
        stale.unlink()

    return backup_path
