# Testing

```
pip install -r requirements-dev.txt
pytest -q
```

Set `QT_QPA_PLATFORM=offscreen` if running without a real display (SSH, CI —
already set in `.github/workflows/build.yml`).

## What's covered

- **Server routes** (`tests/test_server_routes.py`) — account creation +
  duplicate-email conflict, authenticate success/failure, class creation +
  duplicate-code conflict, and the roster → register-card → submit-attendance
  → statistics flow. Runs against a real Flask test client and a throwaway
  SQLite file per test (`tests/conftest.py` monkeypatches `server.db.DB_PATH`
  and re-initializes the schema — no production code changes needed for
  this).
- **Models/managers** (`tests/test_models_managers.py`) — `AccountManager`/
  `ClassManager` against a fake `ApiClient` (no HTTP, no server needed), plus
  `Class.to_dict()`/`from_dict()` round-tripping.
- **Validation rules** (`tests/test_validation.py`) — `is_valid_email`/
  `is_valid_password` from `shared/validation.py`.
- **RFID widget behavior** (`tests/test_take_attendance_widget.py`) — a
  `pytest-qt` test driving `TakeAttendance` against a `FakeSerial` fixture
  (`tests/conftest.py`) and a fake `ClassManager`. Covers the two bugs fixed
  in this phase: rescanning a card that's already been recorded this session
  must not insert a duplicate row, and malformed (non-UTF-8) serial bytes
  must not crash `check_rfid`.

## What's not covered yet

- No end-to-end test drives the full GUI navigation flow (login → main
  window → class window → take attendance) as a user would click through
  it — only individual dialogs are instantiated directly in tests.
- No test exercises real serial hardware — `FakeSerial` stands in for it.
  See `ROADMAP.md` Phase 5 for extending this into a fuller
  hardware-in-the-loop test mode.
- The offline/local-storage backend (`ROADMAP.md` Phase 2) doesn't exist
  yet, so there's nothing to test there.

## Manual QA checklist

Run through this before considering a GUI-touching change done — the
automated suite instantiates dialogs directly and doesn't drive the app's
navigation the way a user would:

- [ ] Log in with a valid account; confirm a wrong password is rejected.
- [ ] Create a new account; confirm a duplicate email is rejected.
- [ ] Reset a password via "Forgot password"; confirm the new password must
      contain both a letter and a digit (not just meet a length minimum).
- [ ] Create a class, including a spreadsheet roster upload; confirm it
      appears in "My Classes" **without navigating away and back**.
- [ ] Open "Take Attendance"; scan (or simulate) card A, then card B, then
      card A again — confirm only one row for A appears, not two.
- [ ] Submit attendance and confirm the class's student table updates.
- [ ] Delete a class from "My Classes" or "Search" — confirm the red
      delete button still renders correctly (now styled via `theme.qss`)
      and the class disappears after confirming.
- [ ] Settings: change password, update security question, edit profile —
      confirm each succeeds and errors show inline, not just via
      `QMessageBox`.
- [ ] View Statistics for a class with and without recorded attendance.
