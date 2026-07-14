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

## Notes on scope
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
