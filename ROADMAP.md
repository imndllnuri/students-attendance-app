# Roadmap

A living document — check items off as they land, and add new ones as scope
becomes clearer. Phases are ordered because later ones build on earlier
ones (notably: the design report in Phase 4 depends on Phases 2-3 settling
first, to avoid rewriting large sections twice).

## Phase 1 — Foundation: hygiene, docs, critical fixes, test/CI scaffolding

- [x] Remove untracked legacy/sensitive files (`accounts.json`, `data/`,
      `IoT.zip`, `server/attendance.db`) from local disk; confirm none were
      ever in git history.
- [x] Full doc set: this file, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
      `DEVELOPMENT.md`, `TESTING.md`, `CHANGELOG.md`, `.github/` PR/issue
      templates + CI workflow.
- [x] Centralize email/password/security-question validation into
      `shared/validation.py` (was duplicated and had drifted out of sync
      across three views).
- [x] Fix the RFID re-scan dedup bug (`views/take_attendance_window.py`) —
      scanning an already-recorded card no longer inserts a duplicate row.
- [x] Catch malformed (non-UTF-8) serial reads instead of crashing.
- [x] Fix "new class doesn't appear without navigating away and back" via a
      `class_created` signal.
- [x] Route `class_window.py`/`take_attendance_window.py` through
      `ClassManager` instead of instantiating `ApiClient` directly.
- [x] Move the inline-styled delete-class button into `theme.qss`.
- [x] Rename inconsistent `.ui` root widget classes (`Form` → real names).
- [x] Add basic `logging` setup, replacing stray `print()`s.
- [x] `tests/` scaffold: pytest + pytest-qt, mocked serial + throwaway
      SQLite fixtures, mock data module, GitHub Actions CI.
- [x] `scripts/seed_mock_data.py` for populating a fresh dev DB without
      hand-entering data or needing RFID hardware.

## Phase 2 — Offline / local-storage backend

Goal: run the whole app with **zero Flask server involvement**, per-class
attendance stored in `.xlsx` files.

- [x] Design a `LocalStorageClient` implementing the same method surface as
      `ApiClient` (`authenticate`, `create_class`, `get_roster`,
      `submit_attendance`, etc.) so `AccountManager`/`ClassManager` don't
      need to change — only which client they're constructed with.
      (`services/local_storage_client.py`)
- [x] Accounts/classes stored as local files (JSON: `accounts.json`,
      `login_history.json`, `classes/<class_id>.json` — the class-metadata
      shape matches `server/app.py`'s `class_row_to_dict()`, not the older
      pre-server `data/<instructor>/<class>/class_info.json` layout
      `server/migrate_legacy_data.py` reads, since that legacy format
      stored plaintext passwords/answers, which this backend deliberately
      does not); attendance per class as one `.xlsx` per class via
      `openpyxl`/`pandas` (`classes/<class_id>.xlsx`, "Roster" +
      "Attendance" sheets — see `ARCHITECTURE.md`).
- [x] A config flag to choose backend (`ApiClient` vs `LocalStorageClient`)
      — `.backend_config.json` via `shared/backend_config.py`'s
      `create_client()`, defaulting to the server backend so behavior is
      unchanged unless explicitly configured (same convention as
      `shared/hardware_config.py`). Also the point where `ApiClient`'s
      `base_url` is now configurable, instead of hardcoded.
- [x] Test suite mirroring `tests/test_server_routes.py` but against the
      local adapter (`tests/test_local_storage_client.py`,
      `tests/test_backend_config.py`), reusing the CI harness from Phase 1.
- [x] Document the file/folder naming convention chosen. See
      `services/local_storage_client.py`'s module docstring and
      `ARCHITECTURE.md`.

## Phase 3 — Remaining GUI/architecture fixes

- [x] Replace `ClassWindow(QMainWindow)` being embedded as a
      `QStackedWidget` page (unsupported pattern — a `QMainWindow` isn't
      meant to be a non-top-level child widget) with a proper widget-based
      page. **Already done** by the time this item was revisited —
      `views/class_window.py`'s `ClassWindow` is a plain `QWidget` (and
      `ui/class_window.ui`'s root is `QWidget`), added to
      `MainWindow.stackedWidget` via `addWidget()` like every other page.
      Must have landed during an earlier redesign pass in this same
      project without the checkbox being updated.
- [x] Consistent modal-vs-non-modal rule across dialogs. **Already
      resolved**, as a side effect of a different change rather than a
      dedicated fix: Login, Create Account, and Reset Password used to be
      described as separate windows with inconsistent modality, but they've
      since been consolidated into a single non-modal `LoginWindow`
      (`QWidget`, shown once via `.show()`) with an internal `auth_stack`
      `QStackedWidget` switching between sign-in/sign-up/reset pages. Every
      other top-level window (`MainWindow`, `AddNewClassWindow`,
      `TakeAttendance`) is likewise always shown via `.show()`, never
      `.exec_()` — the only `.exec_()` calls in the app are on small,
      correctly-modal sub-dialogs (`ChoiceDialog`, `DetailDialog`, the
      inline Mark Selected Absent picker), which is the right call for a
      confirm/pick popup, not the inconsistency this item was about.
- [x] Remaining `.ui` widget-naming-convention cleanup. Renamed the last 3
      outliers to match the dominant `snake_case_combo` convention already
      used by the other 7 combo boxes in the app:
      `security_question_ComboBox`/`security_question_2_ComboBox` →
      `security_question_combo`/`security_question_2_combo`
      (`ui/login_window.ui`, `views/login_window.py`), `hours_comboBox` →
      `hours_combo` (`ui/take_attendance_window.ui`,
      `views/take_attendance_window.py`), plus their test references.
- [ ] ~~Introduce a formal `Session`/`AppState` object~~ **Assessed, not
      pursued.** This item's own stated precondition (the `ClassWindow`
      navigation rework above) turned out to already be satisfied, so it
      was fair to revisit - but today's user/manager threading is already
      small and direct: `MainWindow(user)` holds the one `Account`;
      `ClassWindow`/`TakeAttendance`/`AddNewClassWindow` each take exactly
      2-4 constructor args (`class_obj`, a `main_window` or `class_window`
      back-reference, `class_manager`) rather than a long threaded chain.
      There's no evidence of the kind of tangled global-state problem a
      `Session`/`AppState` singleton is meant to fix - introducing one now
      would just relocate the same 2-3 objects behind a new indirection
      layer for a single-user desktop app. Left undone deliberately;
      revisit only if a concrete pain point (hard-to-test coupling,
      multi-window state desync) actually shows up.

## Phase 4 — Software design/architecture report

- [ ] Write a professional report (architecture, data model, GUI, offline
      mode, API) in LaTeX, compiled to PDF, with a pandoc-generated `.docx`
      alongside it.
- [ ] Source material: `ARCHITECTURE.md`, kept in sync incrementally through
      Phases 1-3, so this is largely a transcription/formatting pass rather
      than fresh technical writing.

## Phase 5 — Hardware tutorial + mocked-hardware-in-the-loop testing

- [ ] RFID RC522 + ESP32 wiring and firmware tutorial (the hardware side of
      this project), written as a learning document.
- [ ] Extend the Phase 1 `FakeSerial` test pattern into a fuller
      hardware-in-the-loop test mode, so GUI changes can be validated
      without physical hardware attached, and real hardware can be swapped
      in for final validation.

## Possible future additions (not yet scoped into a phase)

- Packaging/distribution (e.g. PyInstaller) — would justify adding
  `BUILDING.md`, `VERSIONING.md`, and `RELEASE_PROCESS.md`, intentionally
  skipped in Phase 1 since there's currently no compiled/packaged release
  process to document.
- Turkish (or other) language support — no i18n infrastructure exists today;
  every string is hardcoded English in both `.ui` files and Python
  (`QMessageBox` text, f-strings). Two options when this becomes a priority:
  Qt's built-in translation workflow (`pylupdate5` → `.ts` → `.qm` →
  `QTranslator`, the standard/maintainable Qt approach) or a lighter
  dict-based runtime language switch. Not started — revisit if/when needed.
