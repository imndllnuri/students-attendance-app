-- Schema for the attendance server. SQLite, no ORM, matches the
-- "basic yet efficient Flask app" described in the project paper.

CREATE TABLE IF NOT EXISTS accounts (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    security_question TEXT NOT NULL,
    answer_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classes (
    class_id TEXT PRIMARY KEY,
    class_code TEXT NOT NULL,
    class_name TEXT NOT NULL,
    instructor_id TEXT NOT NULL REFERENCES accounts(user_id),
    section TEXT NOT NULL,
    attendance_policy REAL NOT NULL,
    late_threshold INTEGER NOT NULL,
    total_weeks INTEGER NOT NULL,
    total_hours REAL NOT NULL,
    weekly_hours REAL NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    color TEXT,
    pinned INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS schedule_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    selected INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    student_number TEXT NOT NULL,
    name_surname TEXT NOT NULL,
    card_id TEXT
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    time TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES accounts(user_id) ON DELETE CASCADE,
    logged_in_at TEXT NOT NULL
);
