"""One-off import of the old JSON/Excel-backed data (accounts.json,
data/<instructor>/<class>/class_info.json + student_list.xlsx) into the
SQLite database used by server/app.py. Run once from the project root:

    python -m server.migrate_legacy_data
"""
import json
import sys
import uuid
from pathlib import Path

import pandas as pd
from werkzeug.security import generate_password_hash

from server.db import get_connection, init_db

ROOT = Path(__file__).parent.parent
ACCOUNTS_JSON = ROOT / "accounts.json"
DATA_DIR = ROOT / "data"


def migrate_accounts(conn):
    if not ACCOUNTS_JSON.exists():
        print("No accounts.json found, skipping account migration.")
        return
    with open(ACCOUNTS_JSON) as f:
        accounts = json.load(f)
    for acc in accounts:
        existing = conn.execute(
            "SELECT 1 FROM accounts WHERE user_id = ?", (acc["user_id"],)
        ).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO accounts (user_id, email, password_hash, name, surname, "
            "security_question, answer_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                acc["user_id"],
                acc["email"],
                generate_password_hash(acc["password"]),
                acc["name"],
                acc["surname"],
                acc["security_question"],
                generate_password_hash(acc["answer"]),
            ),
        )
        print(f"Migrated account: {acc['email']}")


def migrate_classes(conn):
    if not DATA_DIR.exists():
        print("No data/ directory found, skipping class migration.")
        return
    for instructor_dir in DATA_DIR.iterdir():
        if not instructor_dir.is_dir():
            continue
        instructor_id = instructor_dir.name
        for class_dir in instructor_dir.iterdir():
            class_info_path = class_dir / "class_info.json"
            if not class_info_path.exists():
                continue
            with open(class_info_path) as f:
                data = json.load(f)

            class_id = data.get("class_id", str(uuid.uuid4()))
            existing = conn.execute(
                "SELECT 1 FROM classes WHERE class_id = ?", (class_id,)
            ).fetchone()
            if existing:
                continue

            conn.execute(
                "INSERT INTO classes (class_id, class_code, class_name, "
                "instructor_id, section, attendance_policy, late_threshold, "
                "total_weeks, total_hours, weekly_hours) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    class_id,
                    data["class_code"],
                    data["class_name"],
                    instructor_id,
                    data["section"],
                    data["attendance_policy"],
                    data["late_threshold"],
                    data["total_weeks"],
                    data["total_hours"],
                    data["weekly_hours"],
                ),
            )
            for day, slots in data.get("schedule", {}).items():
                for slot in slots:
                    conn.execute(
                        "INSERT INTO schedule_slots (class_id, day, start_time, "
                        "end_time, selected) VALUES (?, ?, ?, ?, ?)",
                        (
                            class_id,
                            day,
                            slot["start_time"],
                            slot["end_time"],
                            int(slot["selected"]),
                        ),
                    )

            roster_path = class_dir / "student_list.xlsx"
            if roster_path.exists():
                df = pd.read_excel(roster_path, engine="openpyxl")
                for _, row in df.iterrows():
                    card_id = row.get("Card ID")
                    card_id = str(card_id) if pd.notna(card_id) else None
                    conn.execute(
                        "INSERT INTO students (class_id, student_number, "
                        "name_surname, card_id) VALUES (?, ?, ?, ?)",
                        (
                            class_id,
                            str(row.get("Student Number", "")),
                            str(row.get("Student Name Surname", "")),
                            card_id,
                        ),
                    )
            print(f"Migrated class: {data['class_code']} ({instructor_id})")


def main():
    init_db()
    conn = get_connection()
    migrate_accounts(conn)
    migrate_classes(conn)
    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    sys.exit(main())
