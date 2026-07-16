"""Offline backend for ROADMAP.md Phase 2: the same method surface as
ApiClient (see services/api_client.py), so AccountManager/ClassManager
don't need to change - only which client they're constructed with (see
shared/backend_config.py). Zero Flask server / HTTP involved.

Storage layout, under a data directory (default "local_data/"):

    accounts.json          - list of account dicts (hashed password/answers,
                              never plaintext - see note below)
    login_history.json     - {user_id: [iso timestamp, ...]}
    _meta.json              - {"next_student_id": N}, a global counter
                              standing in for SQL's autoincrement student_id
                              primary key (global across every class, not
                              per-class, so a bare student_id - as passed to
                              remove_student()/register_card() - unambiguously
                              identifies both the student and their class)
    classes/<class_id>.json - class metadata + schedule, same shape
                              server/app.py's class_row_to_dict() returns
    classes/<class_id>.xlsx - one workbook per class, two sheets:
                              "Roster" (student_id, student_number,
                              name_surname, card_id) and "Attendance"
                              (student_id, date, time_slot, time, status -
                              one row per recorded scan, long/tidy form
                              rather than a pivoted crosstab, so appending a
                              session or correcting a record never needs to
                              add/find a column - get_student_table() and
                              get_statistics() pivot/aggregate this exactly
                              like the SQL versions do, in Python instead of
                              SQL)

The legacy pre-server format this app used before server/app.py existed
(see server/migrate_legacy_data.py) stored *plaintext* passwords/answers in
accounts.json - deliberately not repeated here; passwords and security
answers are hashed immediately with the same werkzeug helpers server/app.py
uses, exactly as if this were a second small server sharing its security
model but not its transport or storage engine.
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash

from services.api_client import ApiError

ROSTER_COLUMNS = ["student_id", "student_number", "name_surname", "card_id"]
ATTENDANCE_COLUMNS = ["student_id", "date", "time_slot", "time", "status"]

_CLASS_UPDATABLE_FIELDS = (
    "class_name", "section", "attendance_policy", "late_threshold",
    "total_weeks", "total_hours", "weekly_hours", "notes", "color",
)


def _normalize_schedule(schedule):
    return {
        day: [
            {
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "selected": bool(slot["selected"]),
            }
            for slot in slots
        ]
        for day, slots in schedule.items()
    }


def _records_with_int_student_id(df):
    records = df.to_dict("records")
    for record in records:
        record["student_id"] = int(record["student_id"])
    return records


class LocalStorageClient:
    def __init__(self, data_dir="local_data"):
        self.data_dir = Path(data_dir)
        self.classes_dir = self.data_dir / "classes"
        self.classes_dir.mkdir(parents=True, exist_ok=True)

    # --- accounts.json / login_history.json / _meta.json ---

    def _accounts_path(self):
        return self.data_dir / "accounts.json"

    def _load_accounts(self):
        path = self._accounts_path()
        if not path.exists():
            return []
        with open(path) as f:
            return json.load(f)

    def _save_accounts(self, accounts):
        with open(self._accounts_path(), "w") as f:
            json.dump(accounts, f, indent=2)

    def _find_account(self, accounts, user_id):
        return next((a for a in accounts if a["user_id"] == user_id), None)

    def _find_account_by_email(self, accounts, email):
        return next((a for a in accounts if a["email"] == email), None)

    def _login_history_path(self):
        return self.data_dir / "login_history.json"

    def _load_login_history(self):
        path = self._login_history_path()
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _save_login_history(self, history):
        with open(self._login_history_path(), "w") as f:
            json.dump(history, f, indent=2)

    def _meta_path(self):
        return self.data_dir / "_meta.json"

    def _next_student_id(self):
        path = self._meta_path()
        meta = {"next_student_id": 1}
        if path.exists():
            with open(path) as f:
                meta = json.load(f)
        next_id = meta.get("next_student_id", 1)
        meta["next_student_id"] = next_id + 1
        with open(path, "w") as f:
            json.dump(meta, f)
        return next_id

    # --- classes/<class_id>.json ---

    def _class_json_path(self, class_id):
        return self.classes_dir / f"{class_id}.json"

    def _load_class(self, class_id):
        path = self._class_json_path(class_id)
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def _save_class(self, class_id, record):
        with open(self._class_json_path(class_id), "w") as f:
            json.dump(record, f, indent=2)

    def _all_class_ids(self):
        return [p.stem for p in self.classes_dir.glob("*.json")]

    def _find_student_class_id(self, student_id):
        """A bare student_id (as passed to remove_student()/register_card())
        doesn't say which class it belongs to, so every roster is checked -
        fine for a single instructor's handful of local class files."""
        for class_id in self._all_class_ids():
            roster_df = self._load_roster_df(class_id)
            if student_id in roster_df["student_id"].values:
                return class_id
        return None

    # --- classes/<class_id>.xlsx ---

    def _class_xlsx_path(self, class_id):
        return self.classes_dir / f"{class_id}.xlsx"

    def _empty_roster_df(self):
        return pd.DataFrame(columns=ROSTER_COLUMNS)

    def _empty_attendance_df(self):
        return pd.DataFrame(columns=ATTENDANCE_COLUMNS)

    def _load_roster_df(self, class_id):
        path = self._class_xlsx_path(class_id)
        if not path.exists():
            return self._empty_roster_df()
        df = pd.read_excel(
            path, sheet_name="Roster", engine="openpyxl",
            dtype={"student_number": str, "name_surname": str},
        )
        df["student_id"] = df["student_id"].astype(int)
        df["card_id"] = df["card_id"].apply(lambda v: None if pd.isna(v) else str(v))
        return df

    def _load_attendance_df(self, class_id):
        path = self._class_xlsx_path(class_id)
        if not path.exists():
            return self._empty_attendance_df()
        df = pd.read_excel(
            path, sheet_name="Attendance", engine="openpyxl",
            dtype={"date": str, "time_slot": str, "time": str, "status": str},
        )
        df["student_id"] = df["student_id"].astype(int)
        return df

    def _save_class_xlsx(self, class_id, roster_df, attendance_df):
        with pd.ExcelWriter(self._class_xlsx_path(class_id), engine="openpyxl") as writer:
            roster_df.to_excel(writer, sheet_name="Roster", index=False)
            attendance_df.to_excel(writer, sheet_name="Attendance", index=False)

    # --- misc ---

    def check_health(self):
        return {"status": "ok"}

    # --- Accounts ---

    def authenticate(self, email, password):
        accounts = self._load_accounts()
        account = self._find_account_by_email(accounts, email)
        if account and check_password_hash(account["password_hash"], password):
            history = self._load_login_history()
            history.setdefault(account["user_id"], []).append(
                datetime.now(timezone.utc).isoformat()
            )
            self._save_login_history(history)
            return {
                "user_id": account["user_id"], "email": account["email"],
                "name": account["name"], "surname": account["surname"],
            }
        raise ApiError("Incorrect email or password", 401)

    def create_account(self, account_data):
        accounts = self._load_accounts()
        if self._find_account_by_email(accounts, account_data["email"]):
            raise ApiError("Email already exists", 409)
        if account_data["security_question_1"] == account_data["security_question_2"]:
            raise ApiError("Please choose two different security questions.", 400)

        user_id = str(uuid.uuid4())
        accounts.append({
            "user_id": user_id,
            "email": account_data["email"],
            "password_hash": generate_password_hash(account_data["password"]),
            "name": account_data["name"],
            "surname": account_data["surname"],
            "security_question_1": account_data["security_question_1"],
            "answer_hash_1": generate_password_hash(account_data["answer_1"]),
            "security_question_2": account_data["security_question_2"],
            "answer_hash_2": generate_password_hash(account_data["answer_2"]),
        })
        self._save_accounts(accounts)
        return {
            "user_id": user_id, "email": account_data["email"],
            "name": account_data["name"], "surname": account_data["surname"],
        }

    def get_security_questions(self, email):
        accounts = self._load_accounts()
        account = self._find_account_by_email(accounts, email)
        if not account:
            raise ApiError("No account found with this email", 404)
        return {
            "security_questions": [account["security_question_1"], account["security_question_2"]]
        }

    def reset_password(self, email, answer_1, answer_2, new_password):
        accounts = self._load_accounts()
        account = self._find_account_by_email(accounts, email)
        if not account:
            raise ApiError("No account found with this email", 404)
        if not check_password_hash(account["answer_hash_1"], answer_1) or not check_password_hash(
            account["answer_hash_2"], answer_2
        ):
            raise ApiError("One or more security answers are incorrect", 401)
        account["password_hash"] = generate_password_hash(new_password)
        self._save_accounts(accounts)
        return {"email": account["email"]}

    def update_account(self, user_id, email=None, name=None, surname=None):
        accounts = self._load_accounts()
        account = self._find_account(accounts, user_id)
        if not account:
            raise ApiError("Account not found", 404)

        new_email = email if email is not None else account["email"]
        new_name = name if name is not None else account["name"]
        new_surname = surname if surname is not None else account["surname"]

        conflict = next(
            (a for a in accounts if a["email"] == new_email and a["user_id"] != user_id), None
        )
        if conflict:
            raise ApiError("Email already exists", 409)

        account["email"] = new_email
        account["name"] = new_name
        account["surname"] = new_surname
        self._save_accounts(accounts)
        return {"user_id": user_id, "email": new_email, "name": new_name, "surname": new_surname}

    def change_password(self, user_id, current_password, new_password):
        accounts = self._load_accounts()
        account = self._find_account(accounts, user_id)
        if not account:
            raise ApiError("Account not found", 404)
        if not check_password_hash(account["password_hash"], current_password):
            raise ApiError("Current password is incorrect", 401)
        account["password_hash"] = generate_password_hash(new_password)
        self._save_accounts(accounts)
        return {"user_id": user_id}

    def update_security_questions(
        self, user_id, current_password,
        security_question_1, answer_1, security_question_2, answer_2,
    ):
        accounts = self._load_accounts()
        account = self._find_account(accounts, user_id)
        if not account:
            raise ApiError("Account not found", 404)
        if not check_password_hash(account["password_hash"], current_password):
            raise ApiError("Current password is incorrect", 401)
        if security_question_1 == security_question_2:
            raise ApiError("Please choose two different security questions.", 400)

        account["security_question_1"] = security_question_1
        account["answer_hash_1"] = generate_password_hash(answer_1)
        account["security_question_2"] = security_question_2
        account["answer_hash_2"] = generate_password_hash(answer_2)
        self._save_accounts(accounts)
        return {"user_id": user_id}

    def delete_account(self, user_id):
        accounts = self._load_accounts()
        account = self._find_account(accounts, user_id)
        if not account:
            raise ApiError("Account not found", 404)

        owned_classes = [
            record for record in (self._load_class(cid) for cid in self._all_class_ids())
            if record and record["instructor_id"] == user_id
        ]
        if owned_classes:
            raise ApiError("Delete or transfer your classes before deleting your account.", 409)

        accounts = [a for a in accounts if a["user_id"] != user_id]
        self._save_accounts(accounts)
        return None

    def get_login_history(self, user_id, limit=10):
        history = self._load_login_history()
        timestamps = history.get(user_id, [])
        return sorted(timestamps, reverse=True)[:limit]

    # --- Classes ---

    def list_classes(self, instructor_id, include_archived=False):
        result = []
        for class_id in self._all_class_ids():
            record = self._load_class(class_id)
            if record is None or record["instructor_id"] != instructor_id:
                continue
            if not include_archived and record["archived"]:
                continue
            result.append(record)
        return result

    def create_class(self, class_data):
        instructor_id = class_data["instructor_id"]
        class_code = class_data["class_code"]
        for class_id in self._all_class_ids():
            existing = self._load_class(class_id)
            if existing and existing["class_code"] == class_code and existing["instructor_id"] == instructor_id:
                raise ApiError("Class code already exists", 409)

        class_id = str(uuid.uuid4())
        record = {
            "class_id": class_id,
            "class_code": class_code,
            "class_name": class_data["class_name"],
            "instructor_id": instructor_id,
            "section": class_data["section"],
            "attendance_policy": class_data["attendance_policy"],
            "late_threshold": class_data["late_threshold"],
            "total_weeks": class_data["total_weeks"],
            "total_hours": class_data["total_hours"],
            "weekly_hours": class_data["weekly_hours"],
            "archived": False,
            "notes": "",
            "color": class_data.get("color"),
            "pinned": False,
            "schedule": _normalize_schedule(class_data.get("schedule", {})),
        }
        self._save_class(class_id, record)

        roster_rows = [
            {
                "student_id": self._next_student_id(),
                "student_number": student["student_number"],
                "name_surname": student["name_surname"],
                "card_id": None,
            }
            for student in class_data.get("students", [])
        ]
        roster_df = pd.DataFrame(roster_rows, columns=ROSTER_COLUMNS)
        self._save_class_xlsx(class_id, roster_df, self._empty_attendance_df())

        return record

    def update_class(self, class_id, fields):
        record = self._load_class(class_id)
        if record is None:
            raise ApiError("Class not found", 404)

        for key in _CLASS_UPDATABLE_FIELDS:
            if key in fields:
                record[key] = fields[key]
        if "archived" in fields:
            record["archived"] = bool(fields["archived"])
        if "pinned" in fields:
            record["pinned"] = bool(fields["pinned"])
        if "schedule" in fields:
            record["schedule"] = _normalize_schedule(fields["schedule"])

        self._save_class(class_id, record)
        return record

    def delete_class(self, class_id):
        self._class_json_path(class_id).unlink(missing_ok=True)
        self._class_xlsx_path(class_id).unlink(missing_ok=True)
        return None

    # --- Roster / students ---

    def get_roster(self, class_id):
        df = self._load_roster_df(class_id)
        if df.empty:
            return []
        return _records_with_int_student_id(df.sort_values("student_number"))

    def add_student(self, class_id, student_number, name_surname):
        if self._load_class(class_id) is None:
            raise ApiError("Class not found", 404)
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)

        new_row = {
            "student_id": self._next_student_id(),
            "student_number": student_number,
            "name_surname": name_surname,
            "card_id": None,
        }
        roster_df = pd.concat([roster_df, pd.DataFrame([new_row])], ignore_index=True)
        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return new_row

    def remove_student(self, student_id):
        class_id = self._find_student_class_id(student_id)
        if class_id is None:
            return None
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        roster_df = roster_df[roster_df["student_id"] != student_id]
        attendance_df = attendance_df[attendance_df["student_id"] != student_id]
        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return None

    def merge_students(self, keep_student_id, remove_student_id):
        """Both students are assumed to be in the same class - the only way
        the GUI ever calls this (see views/class_window.py merge_students()),
        since the pick-a-student dropdowns are populated from one roster."""
        class_id = self._find_student_class_id(keep_student_id)
        if class_id is None:
            return None
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        attendance_df.loc[attendance_df["student_id"] == remove_student_id, "student_id"] = keep_student_id
        roster_df = roster_df[roster_df["student_id"] != remove_student_id]
        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return None

    def register_card(self, student_id, card_id):
        class_id = self._find_student_class_id(student_id)
        if class_id is None:
            return None
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        roster_df.loc[roster_df["student_id"] == student_id, "card_id"] = card_id
        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return None

    def get_student_table(self, class_id):
        """Pivots the long-form Attendance sheet into a column-per-session
        table, mirroring server/app.py's get_student_table() SQL/Python
        logic exactly (same column names, same "1 Status"/0 cell values)."""
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        students = _records_with_int_student_id(roster_df.sort_values("student_number")) if not roster_df.empty else []
        records = attendance_df.to_dict("records")

        session_columns = sorted({f"{r['date']} - {r['time_slot']}" for r in records})
        by_student = defaultdict(dict)
        for r in records:
            by_student[int(r["student_id"])][f"{r['date']} - {r['time_slot']}"] = r["status"]

        columns = ["Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours"] + session_columns
        rows = []
        for s in students:
            history = by_student.get(s["student_id"], {})
            attended = sum(1 for v in history.values() if v in ("Present", "Late"))
            not_attended = len(session_columns) - attended
            row = [s["student_number"], s["name_surname"], not_attended, attended]
            for col in session_columns:
                status = history.get(col)
                row.append(f"1 {status}" if status else 0)
            rows.append(row)

        return {"columns": columns, "rows": rows}

    # --- Attendance ---

    def submit_attendance(self, class_id, records):
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        new_rows = [
            {
                "student_id": record["student_id"],
                "date": record["date"],
                "time_slot": record["time_slot"],
                "time": record["time"],
                "status": record["status"],
            }
            for record in records
        ]
        if new_rows:
            attendance_df = pd.concat([attendance_df, pd.DataFrame(new_rows)], ignore_index=True)
        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return None

    def correct_attendance(self, class_id, student_id, date, time_slot, status):
        """Upsert-by-natural-key, mirroring server/app.py's
        /attend/correct behavior exactly: (class_id, student_id, date,
        time_slot) identifies the record, since the GUI's pivoted student
        table doesn't carry a raw attendance-record id."""
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        mask = (
            (attendance_df["student_id"] == student_id)
            & (attendance_df["date"] == date)
            & (attendance_df["time_slot"] == time_slot)
        )
        exists = bool(mask.any())

        if status == "Absent":
            if exists:
                attendance_df = attendance_df[~mask]
            self._save_class_xlsx(class_id, roster_df, attendance_df)
            return {"deleted": True}

        if exists:
            attendance_df.loc[mask, "status"] = status
        else:
            new_row = {
                "student_id": student_id, "date": date, "time_slot": time_slot,
                "time": "", "status": status,
            }
            attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)

        self._save_class_xlsx(class_id, roster_df, attendance_df)
        return {"deleted": False}

    def get_attendance_sheet(self, class_id, date):
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)
        roster_by_id = {r["student_id"]: r for r in _records_with_int_student_id(roster_df)} if not roster_df.empty else {}

        rows = attendance_df[attendance_df["date"] == date].to_dict("records") if not attendance_df.empty else []
        result = []
        for r in rows:
            student = roster_by_id.get(int(r["student_id"]), {})
            result.append({
                "time_slot": r["time_slot"],
                "time": r["time"],
                "status": r["status"],
                "student_number": student.get("student_number", ""),
                "name_surname": student.get("name_surname", ""),
            })
        return result

    def get_statistics(self, class_id):
        roster_df = self._load_roster_df(class_id)
        attendance_df = self._load_attendance_df(class_id)

        num_students = len(roster_df)
        num_sessions = (
            attendance_df[["date", "time_slot"]].drop_duplicates().shape[0]
            if not attendance_df.empty else 0
        )
        present = int((attendance_df["status"] == "Present").sum()) if not attendance_df.empty else 0
        late = int((attendance_df["status"] == "Late").sum()) if not attendance_df.empty else 0

        expected = num_students * num_sessions
        absent = max(expected - present - late, 0)

        return {"present": present, "late": late, "absent": absent}
