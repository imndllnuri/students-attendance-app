from tests.mock_data import SAMPLE_INSTRUCTOR, sample_class_payload


def create_instructor(client):
    resp = client.post("/accounts", json=SAMPLE_INSTRUCTOR)
    assert resp.status_code == 201
    return resp.get_json()["user_id"]


def test_health_check_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


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


def test_archiving_a_class_hides_it_from_the_default_listing(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]

    patched = client.patch(f"/classes/{class_id}", json={"archived": True})
    assert patched.status_code == 200
    assert patched.get_json()["archived"] is True

    active = client.get("/classes", query_string={"instructor_id": instructor_id})
    assert active.get_json() == []

    everything = client.get(
        "/classes", query_string={"instructor_id": instructor_id, "include_archived": "true"}
    )
    assert len(everything.get_json()) == 1
    assert everything.get_json()[0]["archived"] is True

    unarchived = client.patch(f"/classes/{class_id}", json={"archived": False})
    assert unarchived.get_json()["archived"] is False
    active_again = client.get("/classes", query_string={"instructor_id": instructor_id})
    assert len(active_again.get_json()) == 1


def test_update_class_edits_fields_and_schedule(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]

    resp = client.patch(
        f"/classes/{class_id}",
        json={
            "class_name": "Advanced Programming",
            "late_threshold": 20,
            "schedule": {"Friday": [{"start_time": "10:00", "end_time": "11:50", "selected": True}]},
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["class_name"] == "Advanced Programming"
    assert body["late_threshold"] == 20
    assert body["schedule"] == {
        "Friday": [{"start_time": "10:00", "end_time": "11:50", "selected": True}]
    }


def test_new_class_starts_with_empty_notes_and_can_be_updated(client):
    instructor_id = create_instructor(client)
    created = client.post("/classes", json=sample_class_payload(instructor_id)).get_json()
    assert created["notes"] == ""

    resp = client.patch(f"/classes/{created['class_id']}", json={"notes": "TA covers Thursdays."})
    assert resp.status_code == 200
    assert resp.get_json()["notes"] == "TA covers Thursdays."

    refetched = client.get(
        "/classes", query_string={"instructor_id": instructor_id}
    ).get_json()[0]
    assert refetched["notes"] == "TA covers Thursdays."


def test_class_color_defaults_to_none_and_can_be_set(client):
    instructor_id = create_instructor(client)
    created = client.post("/classes", json=sample_class_payload(instructor_id)).get_json()
    assert created["color"] is None

    resp = client.patch(f"/classes/{created['class_id']}", json={"color": "#FF0000"})
    assert resp.status_code == 200
    assert resp.get_json()["color"] == "#FF0000"


def test_class_color_can_be_set_at_creation(client):
    instructor_id = create_instructor(client)
    payload = sample_class_payload(instructor_id)
    payload["color"] = "#00FF00"

    created = client.post("/classes", json=payload).get_json()

    assert created["color"] == "#00FF00"


def test_add_and_remove_individual_roster_student(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]

    added = client.post(
        "/roster",
        json={"class_id": class_id, "student_number": "99999999", "name_surname": "New Student"},
    )
    assert added.status_code == 201
    student_id = added.get_json()["student_id"]

    roster = client.get("/roster", query_string={"class_id": class_id}).get_json()
    assert any(s["student_id"] == student_id for s in roster)
    assert len(roster) == 4  # 3 seeded + 1 added

    removed = client.delete(f"/roster/{student_id}")
    assert removed.status_code == 204

    roster_after = client.get("/roster", query_string={"class_id": class_id}).get_json()
    assert len(roster_after) == 3
    assert all(s["student_id"] != student_id for s in roster_after)


def test_merge_students_moves_attendance_and_deletes_duplicate(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]
    roster = client.get("/roster", query_string={"class_id": class_id}).get_json()
    keep_id = roster[0]["student_id"]

    duplicate = client.post(
        "/roster",
        json={"class_id": class_id, "student_number": "99999999", "name_surname": "Duplicate Entry"},
    ).get_json()
    duplicate_id = duplicate["student_id"]

    client.post(
        "/attend",
        json={
            "class_id": class_id,
            "records": [{
                "student_id": duplicate_id, "date": "01-09-2025",
                "time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
            }],
        },
    )

    merged = client.post(
        "/roster/merge", json={"keep_student_id": keep_id, "remove_student_id": duplicate_id}
    )
    assert merged.status_code == 204

    roster_after = client.get("/roster", query_string={"class_id": class_id}).get_json()
    assert all(s["student_id"] != duplicate_id for s in roster_after)

    sheet = client.get(
        "/attendance_sheet", query_string={"class_id": class_id, "date": "01-09-2025"}
    ).get_json()
    assert len(sheet) == 1
    assert sheet[0]["student_number"] == roster[0]["student_number"]


def test_class_pinned_defaults_to_false_and_can_be_toggled(client):
    instructor_id = create_instructor(client)
    created = client.post("/classes", json=sample_class_payload(instructor_id)).get_json()
    assert created["pinned"] is False

    resp = client.patch(f"/classes/{created['class_id']}", json={"pinned": True})
    assert resp.status_code == 200
    assert resp.get_json()["pinned"] is True

    resp2 = client.patch(f"/classes/{created['class_id']}", json={"pinned": False})
    assert resp2.get_json()["pinned"] is False


def test_correct_attendance_upserts_and_deletes_by_natural_key(client):
    instructor_id = create_instructor(client)
    class_id = client.post(
        "/classes", json=sample_class_payload(instructor_id)
    ).get_json()["class_id"]
    student_id = client.get(
        "/roster", query_string={"class_id": class_id}
    ).get_json()[0]["student_id"]

    # No existing record -> correcting to Present inserts a new one.
    resp = client.post(
        "/attend/correct",
        json={
            "class_id": class_id, "student_id": student_id,
            "date": "01-09-2025", "time_slot": "09:00-10:50", "status": "Present",
        },
    )
    assert resp.status_code == 200
    sheet = client.get(
        "/attendance_sheet", query_string={"class_id": class_id, "date": "01-09-2025"}
    ).get_json()
    assert len(sheet) == 1
    assert sheet[0]["status"] == "Present"

    # Existing record -> correcting to Late updates it in place (no duplicate row).
    client.post(
        "/attend/correct",
        json={
            "class_id": class_id, "student_id": student_id,
            "date": "01-09-2025", "time_slot": "09:00-10:50", "status": "Late",
        },
    )
    sheet_after_update = client.get(
        "/attendance_sheet", query_string={"class_id": class_id, "date": "01-09-2025"}
    ).get_json()
    assert len(sheet_after_update) == 1
    assert sheet_after_update[0]["status"] == "Late"

    # Correcting to Absent deletes the record entirely.
    client.post(
        "/attend/correct",
        json={
            "class_id": class_id, "student_id": student_id,
            "date": "01-09-2025", "time_slot": "09:00-10:50", "status": "Absent",
        },
    )
    sheet_after_absent = client.get(
        "/attendance_sheet", query_string={"class_id": class_id, "date": "01-09-2025"}
    ).get_json()
    assert sheet_after_absent == []


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
