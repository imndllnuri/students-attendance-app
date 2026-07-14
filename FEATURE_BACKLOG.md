# Feature Backlog

Tracks the 30 feature ideas proposed for this app, numbered as originally
presented. Checked items are implemented (each as its own commit); items
marked "not selected" were intentionally left out of this batch.

## Login & Account
- [ ] 1. Password strength indicator on password-creation fields
- [ ] 2. Email verification step on signup (not selected)
- [ ] 3. Session timeout / auto-logout after inactivity
- [ ] 4. "Recent logins" log on the Profile page

## Dashboard / My Classes / Search
- [ ] 5. "Today's Classes" widget with a quick Take Attendance shortcut
- [ ] 6. Sort/filter classes (by code, name, day)
- [ ] 7. Color tag per class card
- [ ] 8. Archive a class instead of hard delete
- [ ] 9. "Duplicate Class" (copy settings into a new class)
- [ ] 10. Search by student name, not just class name/code

## Class Detail & Roster
- [ ] 11. "Edit Class" (was previously create-only)
- [ ] 12. Add/remove individual roster students after class creation
- [ ] 13. "Export Report" button (wires the existing unused export button)
- [ ] 14. Student photo/avatar in roster (not selected)
- [ ] 15. Correct/edit a past attendance record
- [ ] 16. Visual weekly schedule grid (replacing plain text)

## Take Attendance
- [ ] 17. Manual attendance mode (mark by clicking, no RFID needed)
- [ ] 18. "Mark All Present" bulk action
- [ ] 19. "Undo Last Scan"
- [ ] 20. Audio feedback on successful scan (not selected)
- [ ] 21. QR code as an RFID alternative (not selected)
- [x] 22. Live "X/Y students recorded" counter

## Statistics
- [ ] 23. Per-student detail statistics
- [ ] 24. "At-Risk Students" list
- [ ] 25. Attendance trend over time (line chart)
- [ ] 26. Export chart as PNG/PDF

## Settings & Profile
- [ ] 27. Dark mode
- [ ] 28. Language selector (English/Turkish) - infrastructure + partial
      string coverage; see note below

## Cross-cutting
- [ ] 29. Notification/activity feed
- [ ] 30. Keyboard shortcuts (Ctrl+N new class, Ctrl+F search, ...)

## Also implemented (not in the original 30, explicitly requested)
- [x] Show-password checkbox on the login screen

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
