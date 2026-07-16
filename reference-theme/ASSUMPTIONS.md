# AttendU Redesign — Assumptions & Decisions Log

This file records every decision I made that the spec (`student-attendance-app-redesign-prompt.md`)
left open, or where I deliberately diverged from it. Written as I went; check this against the
open questions in the spec's §20 and flag anything you want changed.

## Scope of this pass

Per your instruction, this pass covers the spec through **§14 (Add/Edit Class Modal)** and stops
before **§15 (Statistics)**. That means Statistics, Settings, and the Notifications popover keep
their previous ("Kintsugi") visual language for now — they are not touched by this pass and will
look inconsistent with the rest of the app until a follow-up pass restyles them. Everything else
(auth screens, shell/sidebar/topbar, Dashboard, My Classes, Class Detail, Take Attendance, Add/Edit
Class) is fully redone.

## 1. Local vs. networked backend (§2, §20.1)

The app already has a real local backend: `services/api_client.py` talks to
`http://127.0.0.1:5000` (a Flask-style server the user runs locally via `python -m server.app`).
This was already true before this redesign — I did not change it. Given that, I'm treating this as
the **local, single-instructor tool** path the spec recommends for exactly this situation:

- Settings → Security → Active Sessions is **not built** this pass (Settings isn't in scope this
  pass anyway — see above). When Settings is redesigned in a later pass, recommend simplifying
  Active Sessions to "this device" only, per the spec's own suggestion, rather than building a
  fake multi-device list.
- "Remember me for 30 days" (Login screen) is implemented as a local, non-secret flag using this
  app's existing preference-file convention (`shared/theme.py`'s pattern of a small flat file per
  preference — e.g. `.remember_me` / a remembered-email file), **not** `QSettings` and **not**
  `keyring`. The existing codebase never uses `QSettings` anywhere (it has its own established
  flat-file-per-preference convention across `shared/theme.py`, `shared/font_scale.py`,
  `shared/session_timeout.py`, etc.) so I matched that existing convention instead of introducing
  a second, competing persistence mechanism. No password/credential is stored — only "was the box
  checked" and "last email used," exactly the non-secret half the spec describes as the safe
  minimum.
- The marketing stats on the auth screens' left panel (98% Uptime / 12k+ Students / 450+
  Instructors) are **kept as literal placeholder copy** for now, visually matching the reference
  exactly. The spec flags these as something to swap for real figures or feature bullets before
  shipping (§2, §20.6) — that's a product decision for you, not something I should silently invent
  real numbers or bullet copy for. Left as-is, clearly marked here so it isn't forgotten.

## 2. Demo shortcut (§2, §20.5)

The reference shows "Demo: click Sign In without credentials to enter the app." I did **not**
implement this shortcut. The existing app has real, working authentication already
(`AccountManager`/`ApiClient.authenticate`); adding a credential-bypass path — even gated — is a
real auth-security decision I shouldn't make silently. If you want it (e.g. for demos/screenshots),
tell me and I'll add it behind an explicit debug flag.

## 3. PyQt version

Already PyQt5 throughout the existing codebase (confirmed from imports). Kept as PyQt5 — no
migration to PyQt6. Alignment enums etc. stay in the PyQt5 style (`Qt.AlignCenter`) already used
everywhere.

## 4. Theme system architecture

The existing app already had almost exactly the architecture §4.6 recommends: `shared/palette.py`
holds `PALETTE`/`DARK_PALETTE` token dicts, `resources/styles/theme.qss.tmpl` is a single template
with `{{token}}` placeholders, and `scripts/generate_theme.py` renders it into real
`theme.qss`/`theme_dark.qss` files applied at the `QApplication` level. I kept this pipeline as-is
and rewrote its *contents* for the new AttendU tokens (colors, radii, spacing, gradient buttons)
rather than inventing a parallel system — it already does what §4.6 asks for.

New token values (light/dark) were taken directly from the reference screenshots' visible colors,
matching §4.1's table. Where the table gave a token but a specific pixel-level value wasn't visible
in any screenshot, I used the exact hex the spec's table already provided.

## 5. Sidebar and auth left-panel are NOT theme-reactive

Confirmed directly from the reference screenshots (light-mode Dashboard/Settings screenshots still
show a dark sidebar, and the auth screens' left panel stays dark in both the light- and dark-mode
right-panel screenshots). I implemented this as: the sidebar and the auth screens' left brand panel
always use the dark-mode surface/accent tokens regardless of the app's light/dark setting, exactly
matching what's shown. This is a real, confirmed detail from the screenshots, not a guess.

## 6. Font family

The spec calls for DM Sans as default with Serif/Mono alternates (wired in Settings → General,
which is out of scope this pass). DM Sans is not guaranteed to be installed on an arbitrary Linux
desktop. I did **not** bundle a font file this pass (no `.ttf` was provided in `reference-theme/`).
`build_stylesheet()`/the QSS template requests `"DM Sans"` by name; Qt will silently fall back to
the platform default sans-serif if it isn't installed, which is a safe, non-breaking degradation.
If you want pixel-perfect font matching, drop a DM Sans `.ttf` into `resources/fonts/` and tell me
— I'll wire up `QFontDatabase.addApplicationFont()` at startup.

## 7. Class Detail & Take Attendance layout — freely redesigned

Per your explicit direction, these two screens do **not** copy the reference's exact card stack.
Both were rebuilt around the student roster as the dominant element:

- **Class Detail:** a left/right split — the roster table takes the full left column (~65-70%
  width) and is the first thing on the page, with its own toolbar and inline add-student row
  directly attached. The right column is a slim rail stacking Class Details (compact label/value
  list), the attendance-rate strip, Schedule chips, and Notes, in that order — supporting
  information, not the headline. Header (back link, name, Settings/Take Attendance buttons) stays
  a full-width bar on top, matching the reference.
- **Take Attendance:** the session table is the dominant element, full width, placed directly under
  a slim horizontal control strip (date, time slot, late-threshold override, start/submit buttons,
  Today's Summary numbers all condensed into one row/rail above the table) rather than the
  reference's calendar-on-the-left/table-at-the-bottom layout. The full month calendar is
  collapsed behind a small date-picker popover triggered from the control strip (still a custom
  hand-built grid per §6, just not permanently on-screen) so the table gets the space instead.

These are genuinely new layouts, not a re-skin of the reference screenshots — flag anything you
don't like and I'll adjust.

## 8. Add/Edit Class — wizard dialog

Rebuilt as a real 3-step `QDialog` wizard (`QStackedWidget` of 3 pages + step-dot indicator +
Back/Next/Submit footer) matching §14, replacing the old single dense-form page. Edit mode reuses
the same dialog with fields prefilled and a "Danger Zone" (Archive/Delete) added inside Step 3,
collapsed by default, per §14's "Edit mode" note. Delete requires typing the class name to confirm,
per spec.

## 9. Data model — no schema changes

Nothing in this pass required a new backend field (color/notes/schedule/pinned/archived already
existed on `Class`; roster/attendance endpoints already existed). "Copy Roster From Class,"
"Merge Students," and "Student Detail" (§12.5, §12.5.1, §12.5.2) already existed as working features
in the previous design — I carried the existing implementations over into the new layout rather
than rebuilding their logic, since the spec's description of them matches what was already built.

## 10. Icons

Continued using `qtawesome` (already a dependency, already used throughout) rather than sourcing
SVGs, per §4.5's own suggestion.

## 11. Reset Password button copy diverges from the spec on purpose

The spec's Step 1 button reads "Send Reset Link," matching its assumed email-token flow (§9.4).
Since this app's real reset flow is security-question-based (see §1 above) and no email is ever
sent, keeping that literal label would actively mislead the user into expecting an email. I used
"Continue" instead - still matches the spec's "keep buttons named for what they do" voice rule
(§18), just honest about what this app actually does at that step.

## 12. What's explicitly NOT done this pass

- Settings screen restyle (still old visual language)
- Notifications popover restyle (still old visual language)
- Statistics page (explicitly out of scope, per your instruction)
- Reset-password "sent confirmation" and "set new password" states (§9.4 says these "aren't in the
  new screenshots" and can extend naturally later — flagged, not built, since there's no reference
  image to match against and no existing token/link-based reset flow in the backend to hang it on)
- Background `QThread` scanner worker refactor (§13's closing implementation note) — the existing
  serial-read mechanism (`QTimer`-polled, not threaded) was left as-is functionally; only its visual
  presentation changed. Worth a follow-up if scan latency becomes a real problem.
- Toast/Snackbar component (§6) — the app still uses `QMessageBox` for confirmations in most
  places, consistent with what was already there. Introducing a whole new transient-notification
  widget felt like scope creep beyond "restyle to match the reference + reorganize two screens";
  say the word if you want it added.
