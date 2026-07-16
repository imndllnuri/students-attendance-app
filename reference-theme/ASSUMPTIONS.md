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

### 7a. Take Attendance implementation details

- "Today's Summary" (Present/Late/Absent/Total) is a single condensed caption line
  (`todays_summary_lbl`) inside the control strip, not 4 separate stat-card widgets — matches the
  "slim control strip" intent instead of competing with the roster table for visual weight.
- The spec's separate "Session state" caption (e.g. "Session not started") was **not** added as its
  own label. The existing `scan_status_card`/`scan_status_text_lbl` already communicates this exact
  information ("Press Start Attendance to begin scanning." → "Listening for scans...") — a second,
  parallel status indicator would just be redundant chrome.
- Fixed a real bug found while building this: connecting the calendar popover's auto-collapse via a
  `lambda: self.date_toggle_btn.setChecked(False)` created a Python reference cycle
  (window → calendarWidget → lambda closure → window) that kept the whole dialog alive past its
  local scope in tests, long enough for `qtbot`'s teardown to call the real (unmocked)
  `.close()` → a blocking `QMessageBox.question` under the offscreen test platform → a full test-
  suite hang. Fixed by using a plain bound method instead of a lambda, matching the rest of the
  file's existing connect-a-method pattern.
- Fixed a second, cosmetic-but-real dark-mode bug also present (independently) on Class Detail: both
  `ClassWindow` and `TakeAttendanceWindow` lay their cards out with generous outer margins rather
  than filling edge-to-edge, and neither root widget had an explicit background rule in the QSS, so
  Qt's default (light) palette showed through as a jarring light strip around the cards in dark
  mode, with page titles rendered in a light dark-mode text color on top of it (nearly unreadable).
  Added `QWidget#ClassWindow, QWidget#TakeAttendanceWindow { background-color: {{bg_app}}; }` to fix
  both. Screens that fill edge-to-edge (Login, Dashboard, My Classes) don't have this problem since a
  themed child widget already covers the full window. The Add/Edit Class wizard (§8 below) has the
  same margin-around-cards shape, so its root got the same `background-color: {{bg_app}}` treatment
  proactively, before it ever showed up as a screenshot bug.

## 8. Add/Edit Class — wizard dialog

Rebuilt as a real 3-step `QDialog` wizard (`QStackedWidget` of 3 pages + step-dot indicator +
Back/Next/Submit footer) matching §14, replacing the old single dense-form page:

- **Step 1 (Class Info):** name/code/section/weeks/hours/policy/threshold, in a 2-column card.
- **Step 2 (Schedule):** the 5 weekday selectors, restyled from `QGroupBox` to plain `QFrame` cards
  (objectNames unchanged - `mondayGroupBox` etc - so the existing `add_time_slot`/`remove_time_slot`
  logic needed zero changes), plus the spreadsheet-upload row (create/duplicate mode only, hidden
  when editing - unchanged from before).
- **Step 3 (Color & Confirm):** the color picker, plus - in edit mode only - a "Danger Zone" card
  (Archive/Delete), always-visible rather than collapsed once you're on this step (a 3-step wizard
  page is already a deliberate, low-traffic destination, so an extra expand/collapse click felt like
  friction rather than protection). Archive asks a plain Yes/No; Delete requires typing the exact
  class name to confirm, per spec. Both call `ClassManager.archive_class`/`delete_class` directly
  (already-existing model methods, reused from the My Classes card menu's implementation) and reuse
  the `class_created` signal to tell the caller to reload, same as a normal save.
- Stepping forward/back does **not** validate - the existing `validate_inputs()` still runs once,
  only on the final Create/Save click, to avoid duplicating field-validation logic per step for a
  3-page form that's small enough to fill in a few seconds either way.

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

## 13. Round 2 fixes (post-review corrections)

After the first pass, you flagged several real problems. Fixed as follows:

- **Auth screens consolidated into one window.** Forgot Password and Create One used to open a
  brand-new top-level window/dialog (`CreateAccountWindow`, `ResetPasswordWindow`), duplicating the
  left brand panel each time. `views/login_window.py` now owns all three flows directly - the right
  panel is a `QStackedWidget` (`auth_stack`: sign-in/sign-up/reset pages) that swaps in place, one
  shared left panel, one shared theme toggle. `create_account_window.py`/`reset_password_window.py`
  and their `.ui` files are deleted; every field kept its business logic unchanged, only prefixed
  (`signin_`/`signup_`/`reset_`) where a name collided across the merged pages (`email_le`,
  `answer_le`, `answer_2_le`).
- **Fixed a real layout bug causing huge, uneven gaps between fields** on all three auth pages (your
  screenshots showed "Welcome back." and "Sign in to your account" nearly 150px apart with nothing
  between). Root cause: `QStackedWidget` sizes itself to its **tallest** page by default, not the
  currently-shown one - so the compact Sign In page was being stretched to Sign Up's much taller
  natural height, and that slack space leaked out as gaps between fields. Fixed by pinning each
  stack (`auth_stack` and the reset flow's inner `steps_stack`) to its current page's actual
  `sizeHint()` height on every page switch, plus proper top/bottom `Expanding` spacers around the
  form so it now sits centered rather than stretched top-to-bottom.
- **Removed the Abdullah Gül Üniversitesi logo everywhere** (auth screens' left panel, sidebar) per
  your instruction to genericize the branding. Replaced with a plain text wordmark ("AttendU"),
  same position/rhythm as before. Deleted the now-unused `resources/images/qrc.qrc`,
  `resources/images/qrc.py`, and the logo PNG, and dropped every `from resources.images import qrc`
  import across the codebase.
- **Sidebar's profile block (avatar/name/email, directly above Log Out) is now clickable** and
  opens the Profile page - previously it was decorative only, and the *only* way to reach Profile
  was a top-bar avatar menu, which isn't an obvious place to look for it.
- **Restyled Dashboard's "Today's Classes" / "Recently Viewed" rows.** These were bare, unstyled
  `QWidget`s with a plain label and a native OS-style button - the one part of the Dashboard that
  didn't look like it belonged to the rest of the redesign. Now themed compact cards (soft
  background, rounded corners, a small leading icon, pill action button), matching the visual
  language used everywhere else on the page.

## 14. Continuing past §14: Statistics, Settings, Notifications

Per your latest instruction, the pass now continues onto the screens previously marked out of
scope.

### Statistics

Turned out to need much less than expected: its objectNames (`statistics_title_lbl`,
`statistics_card`, `statistics_empty_lbl`, the 4 action buttons) already matched shared selectors
from earlier phases and were already using the `variant`/card/typography system, and
`active_palette()` was already wired into every chart builder's figure background - so visually it
was already consistent with the rest of the app, contrary to what I'd assumed when I flagged it as
"still old visual language" earlier. What I found and fixed instead: a real dark-mode bug where
`figure.patch.set_facecolor()` only tints the *figure's* background, not each individual `Axes`'
own background - so the pie chart (no visible rectangular background) looked fine, but the
Attendance Trend line chart and the Class Comparison bar chart both showed a stark white plot
rectangle in dark mode, because empty/undrawn space inside an Axes still paints white unless you
also call `axes.set_facecolor(...)`. Added that call to all three chart builders
(`render_statistics`, `show_class_comparison`, `show_attendance_heatmap`) for consistency, even
though the heatmap's `imshow` already covered its own axes rect edge-to-edge.

### Settings

Also turned out to be mostly already covered: the card frame, title, section headers, every
`QLineEdit`/`QComboBox`/`QCheckBox` (all styled by generic type selectors, not per-screen), and
`change_password_btn`/`update_security_question_btn`/`delete_account_btn` (an older but still
coherent solid/tinted button convention, reused as-is rather than migrated to the newer pill
system - not broken, just a smaller radius than the newest screens) were already themed from
earlier phases. The one real problem: `export_settings_btn`/`import_settings_btn` had **no styling
at all** (rendering as bare native OS buttons) **and were never connected to a click handler**,
despite `export_settings()`/`import_settings()` already being fully implemented - clicking them
did nothing. Wired both up and gave them `variant="secondary"` pill styling.

### Notifications / Profile popover

Both the notifications-bell menu and the profile-avatar menu are plain `QMenu`s with no styling
applied anywhere in the app - they rendered as bare native OS popups, clashing with every other
floating surface (cards, dialogs) which are themed. Added one generic `QMenu`/`QMenu::item`/
`QMenu::separator` rule set (rounded corners, card background, hover highlight, muted color for
disabled/header items) that styles both menus - and any future one - at once, rather than a
per-screen fix.
