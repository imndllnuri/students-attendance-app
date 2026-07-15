from PyQt5.QtCore import QTime

from models.accounts import Account, AccountManager
from models.classes import Class, ClassManager, ScheduleSlot
from services.api_client import ApiError


class FakeApiClient:
    """Records calls and returns canned responses, so managers can be
    tested without a running Flask server."""

    def __init__(self):
        self.calls = []

    def create_account(self, account_data):
        self.calls.append(("create_account", account_data))
        return {"user_id": "u1", **account_data}

    def create_class(self, class_data):
        self.calls.append(("create_class", class_data))
        return {"class_id": "c1"}

    def delete_class(self, class_id):
        self.calls.append(("delete_class", class_id))

    def get_statistics(self, class_id):
        self.calls.append(("get_statistics", class_id))
        return {"present": 2, "late": 1, "absent": 0}

    def get_login_history(self, user_id, limit=10):
        self.calls.append(("get_login_history", user_id, limit))
        return ["2026-07-14T10:00:00+00:00"]


class FailingApiClient(FakeApiClient):
    def create_class(self, class_data):
        raise ApiError("Class code already exists", 409)

    def delete_class(self, class_id):
        raise ApiError("boom")

    def get_login_history(self, user_id, limit=10):
        raise ApiError("boom")


def make_class(class_id=None):
    return Class(
        class_code="COMP101",
        class_name="Intro to Programming",
        instructor_id="instr-1",
        section="1",
        attendance_policy=70,
        late_threshold=15,
        total_weeks=14,
        total_hours=42,
        weekly_hours=3,
        schedule={
            "Monday": [
                ScheduleSlot(
                    day="Monday",
                    start_time=QTime(9, 0),
                    end_time=QTime(10, 50),
                    selected=True,
                )
            ]
        },
        class_id=class_id,
    )


def test_class_to_dict_from_dict_round_trip():
    # to_dict() intentionally omits class_id: it's assigned by the server
    # on creation, not sent as part of the create-class payload.
    original = make_class()
    restored = Class.from_dict(original.to_dict())

    assert restored.class_code == original.class_code
    assert restored.class_id is None
    assert restored.schedule["Monday"][0].start_time.toString("HH:mm") == "09:00"
    assert restored.schedule["Monday"][0].selected is True


def test_account_manager_add_account_wraps_api_client():
    fake = FakeApiClient()
    manager = AccountManager(api_client=fake)
    account = Account("a@b.com", "Password123", "A", "B", "Q?", "answer")

    assert manager.add_account(account) is True
    assert fake.calls == [("create_account", account.to_dict())]


def test_class_manager_add_class_sets_id_and_tracks_it():
    fake = FakeApiClient()
    manager = ClassManager(api_client=fake)
    cls = make_class()

    manager.add_class(cls)

    assert cls.class_id == "c1"
    assert manager.get_class_by_code("COMP101") is cls


def test_class_manager_delete_class_returns_false_on_api_error():
    manager = ClassManager(api_client=FailingApiClient())
    assert manager.delete_class("does-not-matter") is False


def test_account_manager_get_login_history_returns_data():
    fake = FakeApiClient()
    manager = AccountManager(api_client=fake)

    assert manager.get_login_history("u1") == ["2026-07-14T10:00:00+00:00"]
    assert fake.calls == [("get_login_history", "u1", 10)]


def test_account_manager_get_login_history_returns_empty_on_api_error():
    manager = AccountManager(api_client=FailingApiClient())
    assert manager.get_login_history("u1") == []


def test_class_manager_proxies_statistics_without_touching_api_client_directly():
    fake = FakeApiClient()
    manager = ClassManager(api_client=fake)

    stats = manager.get_statistics("c1")

    assert stats == {"present": 2, "late": 1, "absent": 0}
    assert fake.calls == [("get_statistics", "c1")]
