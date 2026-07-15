from tests.mock_data import SAMPLE_INSTRUCTOR, sample_class_payload


def create_instructor(client):
    resp = client.post("/accounts", json=SAMPLE_INSTRUCTOR)
    assert resp.status_code == 201
    return resp.get_json()["user_id"]


def test_create_account_then_duplicate_email_conflicts(client):
    resp = client.post("/accounts", json=SAMPLE_INSTRUCTOR)
    assert resp.status_code == 201
    assert resp.get_json()["email"] == SAMPLE_INSTRUCTOR["email"]

    dup = client.post("/accounts", json=SAMPLE_INSTRUCTOR)
    assert dup.status_code == 409


def test_authenticate_success_and_failure(client):
    create_instructor(client)

    ok = client.post(
        "/authenticate",
        json={"email": SAMPLE_INSTRUCTOR["email"], "password": SAMPLE_INSTRUCTOR["password"]},
    )
    assert ok.status_code == 200
    assert ok.get_json()["email"] == SAMPLE_INSTRUCTOR["email"]

    bad = client.post(
        "/authenticate",
        json={"email": SAMPLE_INSTRUCTOR["email"], "password": "wrong"},
    )
    assert bad.status_code == 401


def test_login_history_records_successful_logins_only(client):
    user_id = create_instructor(client)

    client.post(
        "/authenticate",
        json={"email": SAMPLE_INSTRUCTOR["email"], "password": SAMPLE_INSTRUCTOR["password"]},
    )
    client.post(
        "/authenticate",
        json={"email": SAMPLE_INSTRUCTOR["email"], "password": "wrong"},
    )
    client.post(
        "/authenticate",
        json={"email": SAMPLE_INSTRUCTOR["email"], "password": SAMPLE_INSTRUCTOR["password"]},
    )

    history = client.get(f"/accounts/{user_id}/login-history")
    assert history.status_code == 200
    timestamps = history.get_json()
    assert len(timestamps) == 2


def test_create_class_then_duplicate_code_conflicts(client):
    instructor_id = create_instructor(client)
    payload = sample_class_payload(instructor_id)

    created = client.post("/classes", json=payload)
    assert created.status_code == 201
    body = created.get_json()
    assert body["class_code"] == payload["class_code"]
    assert "Monday" in body["schedule"]

    dup = client.post("/classes", json=payload)
    assert dup.status_code == 409


def test_roster_attend_and_statistics_flow(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]

    roster = client.get("/roster", query_string={"class_id": class_id}).get_json()
    assert len(roster) == 3
    student = roster[0]

    register = client.post(
        f"/roster/{student['student_id']}/card", json={"card_id": "CARD-1"}
    )
    assert register.status_code == 204

    submit = client.post(
        "/attend",
        json={
            "class_id": class_id,
            "records": [
                {
                    "student_id": student["student_id"],
                    "date": "01-09-2025",
                    "time_slot": "09:00-10:50",
                    "time": "09:05",
                    "status": "Present",
                }
            ],
        },
    )
    assert submit.status_code == 204

    stats = client.get("/statistics", query_string={"class_id": class_id}).get_json()
    assert stats["present"] == 1
    assert stats["late"] == 0
