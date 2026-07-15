"""Sample instructor/class/student data, reused by tests and by
scripts/seed_mock_data.py so manual GUI exploration and automated tests
exercise the same shapes.
"""

SAMPLE_INSTRUCTOR = {
    "email": "instructor@example.edu",
    "password": "Password123",
    "name": "Ada",
    "surname": "Lovelace",
    "security_question_1": "What was your first pet's name?",
    "answer_1": "Rex",
    "security_question_2": "What city were you born in?",
    "answer_2": "London",
}

SAMPLE_STUDENTS = [
    {"student_number": "20230001", "name_surname": "Grace Hopper"},
    {"student_number": "20230002", "name_surname": "Alan Turing"},
    {"student_number": "20230003", "name_surname": "Katherine Johnson"},
]

SAMPLE_SCHEDULE = {
    "Monday": [{"start_time": "09:00", "end_time": "10:50", "selected": True}],
    "Wednesday": [{"start_time": "13:00", "end_time": "14:50", "selected": True}],
}


def sample_class_payload(instructor_id, class_code="COMP101"):
    return {
        "class_code": class_code,
        "class_name": "Introduction to Programming",
        "instructor_id": instructor_id,
        "section": "1",
        "attendance_policy": 70,
        "late_threshold": 15,
        "total_weeks": 14,
        "total_hours": 42,
        "weekly_hours": 3,
        "schedule": SAMPLE_SCHEDULE,
        "students": SAMPLE_STUDENTS,
    }
