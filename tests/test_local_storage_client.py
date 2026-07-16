"""Mirrors tests/test_server_routes.py's scenarios, but against
LocalStorageClient directly instead of an HTTP Flask test client - same
behavior, zero server process. Audit-log/backup scenarios aren't repeated
here since ApiClient (and therefore LocalStorageClient, which matches its
method surface) doesn't expose those - they're server-admin routes, not
part of the client-facing surface AccountManager/ClassManager depend on.
"""

import pytest

from services.api_client import ApiError
from services.local_storage_client import LocalStorageClient
from tests.mock_data import SAMPLE_INSTRUCTOR, sample_class_payload


@pytest.fixture
def client(tmp_path):
    return LocalStorageClient(data_dir=tmp_path / "local_data")


def create_instructor(client):
    return client.create_account(SAMPLE_INSTRUCTOR)["user_id"]


def test_health_check(client):
    assert client.check_health() == {"status": "ok"}


def test_create_account_then_duplicate_email_conflicts(client):
    created = client.create_account(SAMPLE_INSTRUCTOR)
    assert created["email"] == SAMPLE_INSTRUCTOR["email"]

    with pytest.raises(ApiError) as exc_info:
        client.create_account(SAMPLE_INSTRUCTOR)
    assert exc_info.value.status_code == 409


def test_create_account_rejects_two_identical_security_questions(client):
    payload = dict(SAMPLE_INSTRUCTOR)
    payload["security_question_2"] = payload["security_question_1"]

    with pytest.raises(ApiError) as exc_info:
        client.create_account(payload)
    assert exc_info.value.status_code == 400


def test_authenticate_success_and_failure(client):
    create_instructor(client)

    ok = client.authenticate(SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["password"])
    assert ok["email"] == SAMPLE_INSTRUCTOR["email"]

    with pytest.raises(ApiError) as exc_info:
        client.authenticate(SAMPLE_INSTRUCTOR["email"], "wrong")
    assert exc_info.value.status_code == 401


def test_login_history_records_successful_logins_only(client):
    user_id = create_instructor(client)

    client.authenticate(SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["password"])
    with pytest.raises(ApiError):
        client.authenticate(SAMPLE_INSTRUCTOR["email"], "wrong")
    client.authenticate(SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["password"])

    assert len(client.get_login_history(user_id)) == 2


def test_security_questions_endpoint_returns_both_questions(client):
    create_instructor(client)

    questions = client.get_security_questions(SAMPLE_INSTRUCTOR["email"])["security_questions"]
    assert questions == [
        SAMPLE_INSTRUCTOR["security_question_1"], SAMPLE_INSTRUCTOR["security_question_2"],
    ]


def test_reset_password_requires_both_answers_to_be_correct(client):
    create_instructor(client)

    with pytest.raises(ApiError):
        client.reset_password(
            SAMPLE_INSTRUCTOR["email"], "wrong", SAMPLE_INSTRUCTOR["answer_2"], "NewPassword123"
        )
    with pytest.raises(ApiError):
        client.reset_password(
            SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["answer_1"], "wrong", "NewPassword123"
        )

    client.reset_password(
        SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["answer_1"], SAMPLE_INSTRUCTOR["answer_2"],
        "NewPassword123",
    )
    reauth = client.authenticate(SAMPLE_INSTRUCTOR["email"], "NewPassword123")
    assert reauth["email"] == SAMPLE_INSTRUCTOR["email"]


def test_update_security_questions_requires_current_password_and_distinct_questions(client):
    user_id = create_instructor(client)

    with pytest.raises(ApiError) as wrong_password:
        client.update_security_questions(user_id, "wrong", "New Q1", "a1", "New Q2", "a2")
    assert wrong_password.value.status_code == 401

    with pytest.raises(ApiError) as same_question:
        client.update_security_questions(
            user_id, SAMPLE_INSTRUCTOR["password"], "New Q1", "a1", "New Q1", "a2"
        )
    assert same_question.value.status_code == 400

    client.update_security_questions(
        user_id, SAMPLE_INSTRUCTOR["password"],
        "New Q1", "new-answer-1", "New Q2", "new-answer-2",
    )
    questions = client.get_security_questions(SAMPLE_INSTRUCTOR["email"])["security_questions"]
    assert questions == ["New Q1", "New Q2"]

    client.reset_password(SAMPLE_INSTRUCTOR["email"], "new-answer-1", "new-answer-2", "AnotherPass123")
    assert client.authenticate(SAMPLE_INSTRUCTOR["email"], "AnotherPass123")


def test_update_account_rejects_email_already_used_by_another_account(client):
    user_id = create_instructor(client)
    other = client.create_account({**SAMPLE_INSTRUCTOR, "email": "other@example.edu"})

    with pytest.raises(ApiError) as exc_info:
        client.update_account(other["user_id"], email=SAMPLE_INSTRUCTOR["email"])
    assert exc_info.value.status_code == 409

    updated = client.update_account(user_id, name="Grace")
    assert updated == {
        "user_id": user_id, "email": SAMPLE_INSTRUCTOR["email"],
        "name": "Grace", "surname": SAMPLE_INSTRUCTOR["surname"],
    }


def test_change_password_requires_current_password(client):
    user_id = create_instructor(client)

    with pytest.raises(ApiError):
        client.change_password(user_id, "wrong", "NewPassword123")

    client.change_password(user_id, SAMPLE_INSTRUCTOR["password"], "NewPassword123")
    assert client.authenticate(SAMPLE_INSTRUCTOR["email"], "NewPassword123")


def test_delete_account_requires_no_owned_classes(client):
    user_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(user_id))["class_id"]

    with pytest.raises(ApiError) as exc_info:
        client.delete_account(user_id)
    assert exc_info.value.status_code == 409

    client.delete_class(class_id)
    client.delete_account(user_id)
    with pytest.raises(ApiError):
        client.authenticate(SAMPLE_INSTRUCTOR["email"], SAMPLE_INSTRUCTOR["password"])


def test_create_class_then_duplicate_code_conflicts(client):
    instructor_id = create_instructor(client)
    payload = sample_class_payload(instructor_id)

    created = client.create_class(payload)
    assert created["class_code"] == payload["class_code"]
    assert "Monday" in created["schedule"]

    with pytest.raises(ApiError) as exc_info:
        client.create_class(payload)
    assert exc_info.value.status_code == 409


def test_archiving_a_class_hides_it_from_the_default_listing(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]

    patched = client.update_class(class_id, {"archived": True})
    assert patched["archived"] is True

    assert client.list_classes(instructor_id) == []
    everything = client.list_classes(instructor_id, include_archived=True)
    assert len(everything) == 1
    assert everything[0]["archived"] is True

    unarchived = client.update_class(class_id, {"archived": False})
    assert unarchived["archived"] is False
    assert len(client.list_classes(instructor_id)) == 1


def test_update_class_edits_fields_and_schedule(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]

    updated = client.update_class(
        class_id,
        {
            "class_name": "Advanced Programming",
            "late_threshold": 20,
            "schedule": {"Friday": [{"start_time": "10:00", "end_time": "11:50", "selected": True}]},
        },
    )
    assert updated["class_name"] == "Advanced Programming"
    assert updated["late_threshold"] == 20
    assert updated["schedule"] == {
        "Friday": [{"start_time": "10:00", "end_time": "11:50", "selected": True}]
    }


def test_new_class_starts_with_empty_notes_and_can_be_updated(client):
    instructor_id = create_instructor(client)
    created = client.create_class(sample_class_payload(instructor_id))
    assert created["notes"] == ""

    updated = client.update_class(created["class_id"], {"notes": "TA covers Thursdays."})
    assert updated["notes"] == "TA covers Thursdays."


def test_class_color_defaults_to_none_and_can_be_set_at_creation_or_after(client):
    instructor_id = create_instructor(client)
    created = client.create_class(sample_class_payload(instructor_id))
    assert created["color"] is None

    updated = client.update_class(created["class_id"], {"color": "#FF0000"})
    assert updated["color"] == "#FF0000"

    payload = sample_class_payload(instructor_id, class_code="COMP102")
    payload["color"] = "#00FF00"
    assert client.create_class(payload)["color"] == "#00FF00"


def test_class_pinned_defaults_to_false_and_can_be_toggled(client):
    instructor_id = create_instructor(client)
    created = client.create_class(sample_class_payload(instructor_id))
    assert created["pinned"] is False

    assert client.update_class(created["class_id"], {"pinned": True})["pinned"] is True
    assert client.update_class(created["class_id"], {"pinned": False})["pinned"] is False


def test_add_and_remove_individual_roster_student(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]

    added = client.add_student(class_id, "99999999", "New Student")
    student_id = added["student_id"]

    roster = client.get_roster(class_id)
    assert any(s["student_id"] == student_id for s in roster)
    assert len(roster) == 4  # 3 seeded + 1 added

    client.remove_student(student_id)

    roster_after = client.get_roster(class_id)
    assert len(roster_after) == 3
    assert all(s["student_id"] != student_id for s in roster_after)


def test_merge_students_moves_attendance_and_deletes_duplicate(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]
    roster = client.get_roster(class_id)
    keep_id = roster[0]["student_id"]

    duplicate = client.add_student(class_id, "99999999", "Duplicate Entry")
    duplicate_id = duplicate["student_id"]

    client.submit_attendance(class_id, [{
        "student_id": duplicate_id, "date": "01-09-2025",
        "time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
    }])

    client.merge_students(keep_id, duplicate_id)

    roster_after = client.get_roster(class_id)
    assert all(s["student_id"] != duplicate_id for s in roster_after)

    sheet = client.get_attendance_sheet(class_id, "01-09-2025")
    assert len(sheet) == 1
    assert sheet[0]["student_number"] == roster[0]["student_number"]


def test_correct_attendance_upserts_and_deletes_by_natural_key(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]
    student_id = client.get_roster(class_id)[0]["student_id"]

    client.correct_attendance(class_id, student_id, "01-09-2025", "09:00-10:50", "Present")
    sheet = client.get_attendance_sheet(class_id, "01-09-2025")
    assert len(sheet) == 1
    assert sheet[0]["status"] == "Present"

    client.correct_attendance(class_id, student_id, "01-09-2025", "09:00-10:50", "Late")
    sheet_after_update = client.get_attendance_sheet(class_id, "01-09-2025")
    assert len(sheet_after_update) == 1
    assert sheet_after_update[0]["status"] == "Late"

    client.correct_attendance(class_id, student_id, "01-09-2025", "09:00-10:50", "Absent")
    assert client.get_attendance_sheet(class_id, "01-09-2025") == []


def test_roster_attend_and_statistics_flow(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]

    roster = client.get_roster(class_id)
    assert len(roster) == 3
    student = roster[0]

    client.register_card(student["student_id"], "CARD-1")
    assert client.get_roster(class_id)[0]["card_id"] == "CARD-1"

    client.submit_attendance(class_id, [{
        "student_id": student["student_id"], "date": "01-09-2025",
        "time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
    }])

    stats = client.get_statistics(class_id)
    assert stats["present"] == 1
    assert stats["late"] == 0


def test_get_student_table_matches_the_pivoted_shape(client):
    instructor_id = create_instructor(client)
    class_id = client.create_class(sample_class_payload(instructor_id))["class_id"]
    student = client.get_roster(class_id)[0]

    client.submit_attendance(class_id, [{
        "student_id": student["student_id"], "date": "01-09-2025",
        "time_slot": "09:00-10:50", "time": "09:05", "status": "Present",
    }])

    table = client.get_student_table(class_id)
    assert table["columns"] == [
        "Student Number", "Student Name Surname", "Not Attended Hours", "Attended Hours",
        "01-09-2025 - 09:00-10:50",
    ]
    row = next(r for r in table["rows"] if r[0] == student["student_number"])
    assert row[2:] == [0, 1, "1 Present"]


def test_roster_survives_a_reload_from_disk(tmp_path):
    """The whole point of this backend: data must persist across process
    restarts, unlike the in-memory FakeApiClient used elsewhere in tests."""
    data_dir = tmp_path / "local_data"
    first = LocalStorageClient(data_dir=data_dir)
    instructor_id = create_instructor(first)
    class_id = first.create_class(sample_class_payload(instructor_id))["class_id"]

    second = LocalStorageClient(data_dir=data_dir)
    assert len(second.get_roster(class_id)) == 3
    assert second.list_classes(instructor_id)[0]["class_code"] == "COMP101"
