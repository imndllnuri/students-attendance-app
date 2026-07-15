# More Feature Ideas

50 additional feature ideas, beyond the original 30 tracked in
`FEATURE_BACKLOG.md`. Nothing here is implemented - it's a list to review
and select from for a future batch, using the same numbering convention
(each selected idea becomes its own commit: `#N: Description`).

## Login & Account (6)

1. Two-factor login via a time-based one-time code (TOTP), for instructors
   who want stronger protection than a password alone.
2. "Trust this device" option so 2FA/security questions aren't re-asked on
   a recognized machine for N days.
3. Account lockout after repeated failed logins, with a cooldown timer
   shown in the UI.
4. Password expiry reminder - a gentle nudge after N months suggesting a
   change, not enforced.
5. Export/download a copy of your own account data (email, name, classes,
   roster) as JSON, for instructors who want a local backup.
6. Multiple security questions (pick 2 of 3) instead of just one, for a
   stronger account-recovery bar.

## Dashboard / My Classes / Search (8)

7. Drag-and-drop reordering of class cards on "My Classes" (persisted
   per-instructor ordering, independent of the sort dropdown).
8. Pin/favorite classes to keep them at the top regardless of sort mode.
9. Bulk actions on the class list (select multiple classes, archive/delete
   together) instead of one at a time.
10. "Recently Viewed Classes" quick-access list, separate from "Today's
    Classes."
11. Class list density toggle (comfortable vs. compact rows), for
    instructors managing many classes at once.
12. Global "Jump to Class" keyboard shortcut (type-ahead command palette)
    instead of only the search page.
13. CSV export of the whole class list (code, name, section, schedule,
    policy) for record-keeping outside the app.
14. Import multiple classes at once from a single spreadsheet (one row per
    class) instead of creating them one by one.

## Class Detail & Roster (7)

15. Bulk roster edit: paste a list of "Number, Name" pairs to add several
    students at once, instead of one-by-one via #12's form.
16. Roster CSV/Excel re-export (download the current roster, not just the
    attendance sheet) for cross-checking against the registrar.
17. Detect and warn about duplicate student numbers within a roster at
    upload time.
18. "Merge student" tool for when the same student was accidentally added
    twice with different card IDs, combining their attendance history.
19. Class notes/memo field (freeform text) for instructor-only reminders
    tied to a class (e.g. "TA covers Thursdays").
20. Configurable color per class (manual override of the auto-assigned
    #7 tag color) for instructors who want to group visually by their own
    system.
21. "Copy roster from another class" as a lighter alternative to full
    class duplication (#9), when only the student list should carry over.

## Take Attendance (7)

22. Attendance session templates - save a set of default settings (time
    slot, late threshold override) to reuse across recurring sessions.
23. Offline queueing: if the server is unreachable mid-session, stage
    scans locally and retry submission instead of failing outright.
24. Bulk "Mark Selected Absent" for a guest-lecture cancellation, mirroring
    #18's "Mark All Present."
25. Duplicate-card warning: alert immediately if a scanned card is already
    registered to a different student than expected.
26. Attendance session countdown/timer display showing time remaining in
    the current time slot.
27. CSV import of a pre-taken paper attendance sheet, for sessions where
    RFID wasn't available and manual entry (#17) would be tedious for a
    whole roster.
28. Confirmation prompt before closing the Take Attendance window with
    unsubmitted staged records, to prevent accidental data loss.

## Statistics (6)

29. Cross-class comparison view - attendance rate side-by-side for all of
    an instructor's classes in one chart.
30. Semester-over-semester trend if historical semesters are tagged,
    showing whether attendance is improving or declining.
31. Downloadable statistics summary as a PDF report (policy, rates,
    at-risk list, trend chart together) rather than exporting the chart
    image alone.
32. Attendance heatmap by day-of-week/time-slot, to spot patterns (e.g.
    consistently low Friday afternoon turnout).
33. Configurable date range filter on the trend chart (this month, this
    semester, custom range) instead of always showing every session.
34. Per-student CSV export of their full attendance history, for handing
    to a student who disputes their record.

## Settings & Profile (6)

35. Font size / accessibility scaling option for readability.
36. Configurable session-timeout duration (#3 currently hardcodes 15
    minutes) - let the instructor pick 5/15/30/never.
37. Export/import app settings (theme, language, sort preference) as a
    small JSON file, useful when reinstalling.
38. Confirmation step (type your email) before permanently deleting your
    account, as extra friction against accidental clicks.
39. Additional UI languages beyond English/Turkish if the instructor body
    is more diverse (structure from #28 already supports adding more).
40. "What's New" changelog dialog shown once after an update, summarizing
    recently shipped features from this exact list.

## Cross-cutting / Infrastructure (10)

41. Automatic database backup on a schedule (copy `attendance.db` to a
    timestamped file), independent of any cloud sync.
42. Audit log of administrative actions (account deleted, class archived,
    attendance corrected) for accountability, separate from the
    instructor-facing notification feed (#29).
43. Health-check indicator in the GUI showing server connectivity status
    at a glance, instead of only surfacing errors on failed requests.
44. Configurable server URL in the GUI (currently hardcoded to
    `127.0.0.1:5000` in `services/api_client.py`), for instructors running
    the server on a different machine.
45. Bulk data migration/export tool to move a whole instructor's data to
    a fresh database file.
46. Rate limiting on `/authenticate` to slow down brute-force attempts
    against the server.
47. Structured request logging on the server (method, path, status,
    duration) for debugging beyond today's plain console logging.
48. A `--dry-run` flag for `server/migrate_legacy_data.py` to preview what
    would be imported before committing it.
49. Automatic reconnect/backoff in `services/api_client.py` when the
    server briefly restarts, instead of surfacing a raw connection error.
50. Plugin-style hook for the RFID capture step, so a real ESP8266 device
    (per the original project's `POST /attend` design) can be wired in
    without touching `take_attendance_window.py`'s core logic.
