# Feature Backlog

Tracks the 30 feature ideas proposed for this app, numbered as originally
presented. Checked items are implemented (each as its own commit); items
marked "not selected" were intentionally left out of this batch.

## Login & Account
- [x] 1. Password strength indicator on password-creation fields
- [ ] 2. Email verification step on signup (not selected)
- [x] 3. Session timeout / auto-logout after inactivity
- [x] 4. "Recent logins" log on the Profile page

## Dashboard / My Classes / Search
- [x] 5. "Today's Classes" widget with a quick Take Attendance shortcut
- [x] 6. Sort/filter classes (by code, name, day)
- [x] 7. Color tag per class card
- [x] 8. Archive a class instead of hard delete
- [x] 9. "Duplicate Class" (copy settings into a new class)
- [x] 10. Search by student name, not just class name/code

## Class Detail & Roster
- [x] 11. "Edit Class" (was previously create-only)
- [x] 12. Add/remove individual roster students after class creation
- [x] 13. "Export Report" button (wires the existing unused export button)
- [ ] 14. Student photo/avatar in roster (not selected)
- [x] 15. Correct/edit a past attendance record
- [x] 16. Visual weekly schedule grid (replacing plain text)

## Take Attendance
- [x] 17. Manual attendance mode (mark by clicking, no RFID needed)
- [x] 18. "Mark All Present" bulk action
- [x] 19. "Undo Last Scan"
- [ ] 20. Audio feedback on successful scan (not selected)
- [ ] 21. QR code as an RFID alternative (not selected)
- [x] 22. Live "X/Y students recorded" counter

## Statistics
- [x] 23. Per-student detail statistics
- [x] 24. "At-Risk Students" list
- [x] 25. Attendance trend over time (line chart)
- [x] 26. Export chart as PNG/PDF

## Settings & Profile
- [x] 27. Dark mode
- [x] 28. Language selector (English/Turkish) - infrastructure + partial
      string coverage; see note below

## Cross-cutting
- [x] 29. Notification/activity feed
- [x] 30. Keyboard shortcuts (Ctrl+N new class, Ctrl+F search, ...)

## Also implemented (not in the original 30, explicitly requested)
- [x] Show-password checkbox on the login screen

## Batch 2 (from ideas.md)
- [x] 13. CSV export of the class list
- [x] 16. Roster CSV/Excel re-export
- [x] 5. Export/download your own account data as JSON
- [x] 38. Type-your-email confirmation before permanent account deletion
- [x] 28. Confirm closing Take Attendance with unsubmitted records
- [x] 26. Session countdown/timer display
- [x] 25. Duplicate-card warning
- [x] 17. Duplicate student-number detection on roster upload
- [x] 24. Bulk "Mark Selected Absent" for cancelled sessions
- [x] 36. Configurable session-timeout duration
- [x] 19. Class notes/memo field
- [x] 20. Manual class tag color override
- [x] 21. Copy roster from another class
- [x] 18. Merge student tool
- [x] 7. Drag-and-drop reordering of class cards (Custom Order sort mode)
- [x] 8. Pin/favorite classes
- [x] 11. Class list density toggle (comfortable vs compact)
- [x] 10. "Recently Viewed Classes" quick-access list
- [x] 12. "Jump to Class" command-palette shortcut (Ctrl+K)
- [x] 9. Bulk actions on the class list (multi-select archive)
- [x] 14. Import multiple classes from one spreadsheet
- [x] 22. Attendance session templates (time slot + late-threshold override)
- [x] 23. Offline queueing for attendance submission
- [x] 29. Cross-class attendance comparison view
- [x] 32. Attendance heatmap by day/time-slot
- [x] 31. Downloadable PDF statistics report
- [x] 35. Font size / accessibility scaling
- [x] 37. Export/import app settings as JSON
- [x] 40. What's New changelog dialog
- [x] 43. Server connectivity health indicator
- [x] 34. Per-student attendance CSV export
- [x] 42. Admin audit log (account deletion, class archive/unarchive/delete,
      student merges, attendance corrections)
- [x] 41. Scheduled automatic database backup (daily, retains last 10)
- [x] 50. Plugin-style hook for real RFID/ESP8266 hardware integration
- [x] 6. Multiple security questions (pick 2 of 3) for signup, password
      reset, and updating security questions from Settings

## Notes on scope
- **#29 Notifications**: in-app bell-icon feed only (in-memory, not
  persisted across restarts) - no email/SMTP is configured for this
  project, so the "weekly risk summary email" idea became an at-risk
  summary notification shown when a class's roster is loaded instead.
- **#27 Dark mode**: `theme_dark.qss` is generated from `theme.qss` by
  `scripts/generate_dark_theme.py` (hex-value substitution via
  `shared/palette.py`'s `DARK_PALETTE`) rather than hand-authored - re-run
  the script after editing either file. Preference persists to
  `.theme_preference` and applies live via `QApplication.setStyleSheet()`.
  Dynamic per-cell colors (`qcolor()`, `class_tag_color()`) intentionally
  still use the light `PALETTE` in both themes; the top search bar isn't
  covered either since it has no explicit background rule in either theme.
- **#28 Language selector**: implements the lightweight dict-based
  approach (`shared/i18n.py`) discussed earlier - not Qt's full
  `QTranslator`/`.ts`/`.qm` workflow. Covers navigation, page titles, and
  common actions; not every string in the app is translated yet. Language
  choice applies on next launch (no live re-translation of already-open
  windows). See `ROADMAP.md` for extending coverage.
- **#8 Archive**: adds an `archived` column via a defensive
  `ALTER TABLE ... ADD COLUMN` in `server/db.py:init_db()` (wrapped so it's
  a no-op against a DB that already has the column), rather than a full
  migration framework - consistent with this project's current
  dev-database maturity level.
- **#15 Correct attendance**: implemented as an upsert-by-natural-key
  (class_id, student_id, date, time_slot) rather than exposing raw
  `attendance_records.id` to the client, since the existing pivoted
  student-table view doesn't carry record IDs.
- **#41 Scheduled backup**: a `threading.Timer` loop started only when the
  server is run directly (`server/app.py`'s `__main__` block), copying
  `attendance.db` into `server/backups/` once a day and keeping the last
  10 copies. A `POST /admin/backup` endpoint exposes the same logic
  on-demand (used by the tests, since a real 24h timer isn't practical to
  test). No restore tooling is included - this only covers taking the
  backups, not a UI for restoring from one.
- **#50 RFID/ESP8266 hardware hook**: `services/card_reader.py` defines a
  `CardReader` interface (`connect`/`poll`/`close`) with two
  implementations - `SerialCardReader` (wraps the existing pyserial
  reader, used by default) and `ESP8266CardReader` (a TCP client for a
  WiFi reader that streams newline-delimited card IDs). The backend is
  chosen via `shared/hardware_config.py`'s `.hardware_config.json`
  (defaults to `"serial"`, so behavior is unchanged unless explicitly
  configured for `"esp8266"`). `TakeAttendance.check_rfid()` polls through
  whichever backend is active; no real ESP8266 hardware was available to
  test against, so the TCP transport is verified against a local loopback
  server in `tests/test_card_reader_plugin.py` instead.
- **#6 Two security questions**: `SECURITY_QUESTIONS` now has 3 entries;
  signup, reset-password, and the Settings page's "Update Security
  Question" form each collect two answers from two questions that must
  differ (enforced client-side and again server-side in
  `server/app.py`'s `create_account`/`update_security_questions`).
  `accounts.security_question`/`answer_hash` became
  `security_question_1`/`answer_hash_1`/`security_question_2`/
  `answer_hash_2`; existing dev databases get the new columns via the
  same defensive `ALTER TABLE ... ADD COLUMN` pattern used elsewhere in
  `server/db.py`, defaulting to `''` (no data migration for accounts
  created under the old single-question scheme, consistent with this
  project's dev-database-maturity trade-offs noted elsewhere in this
  file). Resetting a password now requires both answers to be correct.
