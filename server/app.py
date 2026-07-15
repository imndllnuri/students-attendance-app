import uuid
from collections import defaultdict
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from server.db import get_connection, init_db

app = Flask(__name__)


def class_row_to_dict(conn, row):
    slots = conn.execute(
        "SELECT day, start_time, end_time, selected FROM schedule_slots WHERE class_id = ?",
        (row["class_id"],),
    ).fetchall()
    schedule = defaultdict(list)
    for s in slots:
        schedule[s["day"]].append(
            {
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "selected": bool(s["selected"]),
            }
        )
    return {
        "class_id": row["class_id"],
        "class_code": row["class_code"],
        "class_name": row["class_name"],
        "instructor_id": row["instructor_id"],
        "section": row["section"],
        "attendance_policy": row["attendance_policy"],
        "late_threshold": row["late_threshold"],
        "total_weeks": row["total_weeks"],
        "total_hours": row["total_hours"],
        "weekly_hours": row["weekly_hours"],
        "schedule": dict(schedule),
    }


@app.post("/accounts")
def create_account():
    data = request.get_json()
    conn = get_connection()
    existing = conn.execute(
        "SELECT 1 FROM accounts WHERE email = ?", (data["email"],)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already exists"}), 409

    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO accounts (user_id, email, password_hash, name, surname, "
        "security_question, answer_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            data["email"],
            generate_password_hash(data["password"]),
            data["name"],
            data["surname"],
            data["security_question"],
            generate_password_hash(data["answer"]),
        ),
    )
    conn.commit()
    conn.close()
    return jsonify(
        {
            "user_id": user_id,
            "email": data["email"],
            "name": data["name"],
            "surname": data["surname"],
        }
    ), 201


@app.post("/authenticate")
def authenticate():
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE email = ?", (data["email"],)
    ).fetchone()
    if account and check_password_hash(account["password_hash"], data["password"]):
        conn.execute(
            "INSERT INTO login_history (user_id, logged_in_at) VALUES (?, ?)",
            (account["user_id"], datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        return jsonify(
            {
                "user_id": account["user_id"],
                "email": account["email"],
                "name": account["name"],
                "surname": account["surname"],
            }
        )
    conn.close()
    return jsonify({"error": "Incorrect email or password"}), 401


@app.get("/accounts/<user_id>/login-history")
def login_history(user_id):
    limit = request.args.get("limit", default=10, type=int)
    conn = get_connection()
    rows = conn.execute(
        "SELECT logged_in_at FROM login_history WHERE user_id = ? "
        "ORDER BY logged_in_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return jsonify([row["logged_in_at"] for row in rows])


@app.post("/security-question")
def security_question():
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT security_question FROM accounts WHERE email = ?", (data["email"],)
    ).fetchone()
    conn.close()
    if not account:
        return jsonify({"error": "No account found with this email"}), 404
    return jsonify({"security_question": account["security_question"]})


@app.post("/reset-password")
def reset_password():
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE email = ?", (data["email"],)
    ).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "No account found with this email"}), 404
    if not check_password_hash(account["answer_hash"], data["answer"]):
        conn.close()
        return jsonify({"error": "Incorrect security answer"}), 401
    conn.execute(
        "UPDATE accounts SET password_hash = ? WHERE email = ?",
        (generate_password_hash(data["new_password"]), data["email"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"email": account["email"]})


@app.patch("/accounts/<user_id>")
def update_account(user_id):
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    new_email = data.get("email", account["email"])
    new_name = data.get("name", account["name"])
    new_surname = data.get("surname", account["surname"])

    existing = conn.execute(
        "SELECT 1 FROM accounts WHERE email = ? AND user_id != ?",
        (new_email, user_id),
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already exists"}), 409

    conn.execute(
        "UPDATE accounts SET email = ?, name = ?, surname = ? WHERE user_id = ?",
        (new_email, new_name, new_surname, user_id),
    )
    conn.commit()
    conn.close()
    return jsonify(
        {"user_id": user_id, "email": new_email, "name": new_name, "surname": new_surname}
    )


@app.post("/accounts/<user_id>/change-password")
def change_password(user_id):
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404
    if not check_password_hash(account["password_hash"], data["current_password"]):
        conn.close()
        return jsonify({"error": "Current password is incorrect"}), 401

    conn.execute(
        "UPDATE accounts SET password_hash = ? WHERE user_id = ?",
        (generate_password_hash(data["new_password"]), user_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"user_id": user_id})


@app.post("/accounts/<user_id>/security-question")
def update_security_question(user_id):
    data = request.get_json()
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404
    if not check_password_hash(account["password_hash"], data["current_password"]):
        conn.close()
        return jsonify({"error": "Current password is incorrect"}), 401

    conn.execute(
        "UPDATE accounts SET security_question = ?, answer_hash = ? WHERE user_id = ?",
        (data["security_question"], generate_password_hash(data["answer"]), user_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"user_id": user_id})


@app.delete("/accounts/<user_id>")
def delete_account(user_id):
    conn = get_connection()
    account = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    owned_classes = conn.execute(
        "SELECT COUNT(*) AS n FROM classes WHERE instructor_id = ?", (user_id,)
    ).fetchone()["n"]
    if owned_classes > 0:
        conn.close()
        return jsonify(
            {"error": "Delete or transfer your classes before deleting your account."}
        ), 409

    conn.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return "", 204


@app.get("/classes")
def list_classes():
    instructor_id = request.args.get("instructor_id")
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM classes WHERE instructor_id = ?", (instructor_id,)
    ).fetchall()
    result = [class_row_to_dict(conn, row) for row in rows]
    conn.close()
    return jsonify(result)


@app.post("/classes")
def create_class():
    data = request.get_json()
    conn = get_connection()
    existing = conn.execute(
        "SELECT 1 FROM classes WHERE class_code = ? AND instructor_id = ?",
        (data["class_code"], data["instructor_id"]),
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Class code already exists"}), 409

    class_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO classes (class_id, class_code, class_name, instructor_id, "
        "section, attendance_policy, late_threshold, total_weeks, total_hours, "
        "weekly_hours) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            class_id,
            data["class_code"],
            data["class_name"],
            data["instructor_id"],
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
                "INSERT INTO schedule_slots (class_id, day, start_time, end_time, "
                "selected) VALUES (?, ?, ?, ?, ?)",
                (class_id, day, slot["start_time"], slot["end_time"], int(slot["selected"])),
            )
    for student in data.get("students", []):
        conn.execute(
            "INSERT INTO students (class_id, student_number, name_surname, card_id) "
            "VALUES (?, ?, ?, NULL)",
            (class_id, student["student_number"], student["name_surname"]),
        )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM classes WHERE class_id = ?", (class_id,)
    ).fetchone()
    result = class_row_to_dict(conn, row)
    conn.close()
    return jsonify(result), 201


@app.delete("/classes/<class_id>")
def delete_class(class_id):
    conn = get_connection()
    conn.execute("DELETE FROM classes WHERE class_id = ?", (class_id,))
    conn.commit()
    conn.close()
    return "", 204


@app.get("/roster")
def get_roster():
    class_id = request.args.get("class_id")
    conn = get_connection()
    rows = conn.execute(
        "SELECT student_id, student_number, name_surname, card_id FROM students "
        "WHERE class_id = ? ORDER BY student_number",
        (class_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/roster/<int:student_id>/card")
def register_card(student_id):
    data = request.get_json()
    conn = get_connection()
    conn.execute(
        "UPDATE students SET card_id = ? WHERE student_id = ?",
        (data["card_id"], student_id),
    )
    conn.commit()
    conn.close()
    return "", 204


@app.get("/students")
def get_student_table():
    """Returns the roster + attendance history as a column/row table,
    mirroring the previous student_list.xlsx layout the GUI already knows
    how to render."""
    class_id = request.args.get("class_id")
    conn = get_connection()
    students = conn.execute(
        "SELECT student_id, student_number, name_surname FROM students "
        "WHERE class_id = ? ORDER BY student_number",
        (class_id,),
    ).fetchall()
    records = conn.execute(
        "SELECT student_id, date, time_slot, status FROM attendance_records "
        "WHERE class_id = ?",
        (class_id,),
    ).fetchall()
    conn.close()

    session_columns = sorted({f"{r['date']} - {r['time_slot']}" for r in records})
    by_student = defaultdict(dict)
    for r in records:
        by_student[r["student_id"]][f"{r['date']} - {r['time_slot']}"] = r["status"]

    columns = ["Student Number", "Student Name Surname", "Not Attended Hours",
               "Attended Hours"] + session_columns
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

    return jsonify({"columns": columns, "rows": rows})


@app.post("/attend")
def submit_attendance():
    data = request.get_json()
    class_id = data["class_id"]
    conn = get_connection()
    for record in data["records"]:
        conn.execute(
            "INSERT INTO attendance_records (class_id, student_id, date, "
            "time_slot, time, status) VALUES (?, ?, ?, ?, ?, ?)",
            (
                class_id,
                record["student_id"],
                record["date"],
                record["time_slot"],
                record["time"],
                record["status"],
            ),
        )
    conn.commit()
    conn.close()
    return "", 204


@app.get("/attendance_sheet")
def attendance_sheet():
    class_id = request.args.get("class_id")
    date = request.args.get("date")
    conn = get_connection()
    rows = conn.execute(
        "SELECT ar.time_slot, ar.time, ar.status, s.student_number, s.name_surname "
        "FROM attendance_records ar JOIN students s ON s.student_id = ar.student_id "
        "WHERE ar.class_id = ? AND ar.date = ?",
        (class_id, date),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.get("/statistics")
def statistics():
    class_id = request.args.get("class_id")
    conn = get_connection()
    num_students = conn.execute(
        "SELECT COUNT(*) AS n FROM students WHERE class_id = ?", (class_id,)
    ).fetchone()["n"]
    num_sessions = conn.execute(
        "SELECT COUNT(DISTINCT date || '|' || time_slot) AS n FROM attendance_records "
        "WHERE class_id = ?",
        (class_id,),
    ).fetchone()["n"]
    status_counts = conn.execute(
        "SELECT status, COUNT(*) AS n FROM attendance_records WHERE class_id = ? "
        "GROUP BY status",
        (class_id,),
    ).fetchall()
    conn.close()

    counts = {"Present": 0, "Late": 0}
    for row in status_counts:
        counts[row["status"]] = row["n"]

    expected = num_students * num_sessions
    absent = max(expected - counts["Present"] - counts["Late"], 0)

    return jsonify(
        {
            "present": counts["Present"],
            "late": counts["Late"],
            "absent": absent,
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
