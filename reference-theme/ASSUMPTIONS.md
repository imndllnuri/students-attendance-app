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

My first pass on Settings was wrong. I checked whether its existing widgets were internally
consistent with the token system (they were) and stopped there - I never actually held it up
against the reference screenshots. When you pushed back, I looked at `reference-theme/2026-07-16_
02:45:59.png` (General), `...02:46:38.png` (Edit Profile), `...02:46:47.png` (Security) and the
spec's §16, and the real structure has nothing to do with what was there: a `QTabWidget`-style
General / Edit Profile / Security layout, full page width, one card per logical section - not the
narrow 420px centered form with everything (including the separate Profile page's content) crammed
into one column with `Line` dividers between subsections.

Rebuilt to match:
- **Full-width page** with a "Settings" title + "Manage your preferences and account" subtitle,
  matching every other page's header treatment, replacing the centered-card layout.
- **Segmented pill tab bar** (General / Edit Profile / Security) reusing the exact same
  `variant="segmented"` + `QButtonGroup` pattern already built for Dashboard's filter tabs, driving
  a `settings_stack` `QStackedWidget`.
- **General tab:** four cards - Appearance (Dark Mode), Language & Region (Display Language),
  Session (Auto Logout Timeout + caption), Typography (Font Size) - plus a fifth "Backup &
  Restore" card for Export/Import Settings, which has no reference equivalent (the reference has no
  app-preference backup feature) but needed a home since it's a real, working feature.
- **Dark Mode is now a real toggle-switch look** (a wide pill `QCheckBox::indicator`, accent-filled
  when on) instead of a small square tickbox, matching the reference's switch control - done via
  QSS only, no custom painting.
- **The standalone Profile page is gone.** Its content (Personal Information, Change Password,
  Recent Logins, Download My Data) now lives in Settings' **Edit Profile tab**, exactly where the
  reference puts it. `show_profile()` (still called from the sidebar/topbar) now opens Settings on
  that tab instead of a separate page. The profile page's centered avatar image was dropped - the
  reference's Edit Profile tab doesn't have one either, and the sidebar already shows an avatar.
  `PROFILE_PAGE` is gone from the page-index enum; `stackedWidget` now has 5 pages, not 6.
- **Security tab:** Security Questions card kept as this app's real 2-question flow (the reference
  shows only one question+answer - a simplified mockup - but the actual backend requires two
  distinct questions, an established deviation already recorded in §1). "Active Sessions" (only
  meaningful for the networked/multi-device backend this app doesn't have, per §1/§20.1) is
  replaced with a **Danger Zone card** (Delete Account) instead, since that's a real feature that
  needs a home and Security is the most sensible tab for it.
- Also fixed while rebuilding: `export_settings_btn`/`import_settings_btn` had **no styling at all**
  (bare native buttons) **and were never wired to a click handler**, despite `export_settings()`/
  `import_settings()` already being fully implemented - clicking them did nothing. Wired both up
  with `variant="secondary"` styling. Same fix applied to `export_account_data_btn` ("Download My
  Data"), found while re-screenshotting this pass.
- **Not built:** Font Family switching (Sans/Serif/Mono) and Phone/Bio fields on Edit Profile - both
  shown in the reference, neither backed by anything real yet. Font Family would need the QSS
  generator to accept a font-family token (currently only accepts color/radius/spacing tokens);
  Phone/Bio would need new `Account`/database columns. Flagging both rather than half-building them
  (a dropdown that doesn't change anything, or fields that silently don't save).

### Notifications / Profile popover

Both the notifications-bell menu and the profile-avatar menu are plain `QMenu`s with no styling
applied anywhere in the app - they rendered as bare native OS popups, clashing with every other
floating surface (cards, dialogs) which are themed. Added one generic `QMenu`/`QMenu::item`/
`QMenu::separator` rule set (rounded corners, card background, hover highlight, muted color for
disabled/header items) that styles both menus - and any future one - at once, rather than a
per-screen fix.

## 15. Dark-mode color bugs found from real screenshots (Dashboard/My Classes/Class Detail)

Two concrete "text/background is the wrong color in dark mode" bugs, found from your screenshots
rather than my own testing:

- **`shared/palette.py`'s `qcolor()` helper was hardcoded to the light `PALETTE`, always**,
  regardless of the active theme. `QTableWidgetItem` background/foreground colors are set directly
  in Python (`item.setBackground(qcolor(...))`) rather than through the QSS stylesheet, so unlike
  every other widget, they never picked up dark mode at all - this is exactly the class of bug
  `active_palette()` exists to prevent (it already covers matplotlib charts), but `qcolor()` itself
  was never routed through it. Fixed by having `qcolor()` read `active_palette()[token]` instead of
  `PALETTE[token]`. This was a **single fix affecting two real, screenshotted bugs at once**: the
  Class Detail roster table's "Not Attended Hours" severity-tint cells (shown as a jarring pale
  green/red rectangle in the middle of an otherwise dark table) and Take Attendance's staged-row
  tinting (same root cause, not yet screenshotted but would have shown the identical bug).
- **`import_classes_btn` ("Import Classes From Spreadsheet") had no styling at all** - same bare-
  native-button bug pattern found several times already this pass (Export/Import Settings,
  Download My Data) - rendering as a stark white bar at the bottom of My Classes in dark mode.
  Wired up with `variant="secondary"`.

The PDF export chart's `PALETTE["success"/"warning"/"error"]` (main_window.py, `export_statistics_
pdf`) is the one intentional exception left as-is - it always uses the light palette on purpose so
exported reports stay print-friendly regardless of the app's current theme (documented back in
this file's `render_statistics` note).

## 16. Dark mode removed entirely (per your request)

The light/dark toggle is gone - the app now has one visual theme, always. Removed:

- The sun/moon toggle button on every auth screen and the app's top bar (`theme_toggle_btn`), and
  the Settings General tab's "Appearance" card, which only ever contained the Dark Mode switch -
  once that's gone the card had nothing left in it, so the whole card is gone too.
- `shared/theme.py` (theme preference persistence) - deleted entirely, along with the
  `.theme_preference` file it used.
- `DARK_PALETTE`/`DARK_TAG_COLORS` in `shared/palette.py`, and `active_palette()` - there's only
  one palette now, so the "pick light or dark" indirection was removed rather than kept as a
  no-op; every former `active_palette()` call site now reads `PALETTE` directly.
- `scripts/generate_theme.py` now renders only `theme.qss` (the `theme_dark.qss` output is gone).
- The dark-mode-skips-the-shadow rule in `shared/shadow.py` (§4.4 of the original spec) - shadows
  now always apply.
- "theme" as an Export/Import Settings JSON field.
- Test coverage that only existed to verify dark-mode behavior (`test_theme.py`,
  `test_main_window_dark_mode.py`, `test_main_window_dark_mode_charts.py`) - deleted. Kept the
  parts of `test_theme.py` that were really about the QSS generator's token-substitution logic
  (still applies with a single palette), moved into a new `test_generate_theme.py`.

**What did NOT change:** the sidebar and auth-screens' left panel are still fixed-dark chrome -
that was never the "dark mode" feature (it doesn't toggle; it's the same permanently-dark
navigation surface in what is now the app's only theme), so it's untouched. `PALETTE`'s
`bg_sidebar`/`text_sidebar`/etc. tokens already held these fixed-dark values before this change
and still do.

## 17. Roster add/remove moved from Class Detail into the Edit Class wizard

Per your request: the "Add Student" / "Remove Selected" row that used to sit under Class Detail's
roster table now lives on a new **Roster** step of the Edit Class wizard (opened via Class Detail's
"⚙ Settings" button), between Schedule and Color & Confirm - so the wizard is now Class Info →
Schedule → Roster → Color & Confirm.

- Class Detail keeps the roster **table** (Student Number / Name / Not Attended Hours / Attended
  Hours) for viewing attendance - only the two mutation controls moved, per your wording ("student
  adding and removing").
- The Roster step only appears when **editing an existing class** - a brand-new class has no
  `class_id` yet for `add_student`/`remove_student` to target, so the step is skipped entirely in
  Create and Duplicate mode (its step-dot label is hidden, and Next/Back skip over it). Those two
  modes keep using the Schedule step's spreadsheet bulk-upload, which was always create-only.
  Editing an existing class's roster this way still uses the exact same `ClassManager.add_student`/
  `remove_student`/`get_roster` calls as before, just placed on this new step instead of Class
  Detail.
- Since these mutations now happen immediately against the server as each button is clicked
  (matching the original Class Detail behavior - there's no "unsaved roster changes" concept),
  `ClassWindow._reload_after_edit` now also calls `load_student_list()` after the wizard closes, so
  the roster table reflects any additions/removals made during that Settings session.

## 18. App renamed to "TapIn", with a generated icon

Per your request - a real product name, deliberately not AGU-branded. "TapIn" fits the app's
actual mechanic (an RFID card *tap* to check in), which is why the generated icon is a contactless/
NFC-style radiating-arcs symbol (not a generic checkmark or calendar glyph) - it reads as "tap a
card" rather than just "attendance app #4327."

- `resources/images/app_icon.png` - a 512x512 rounded-square icon, drawn with QPainter (no external
  asset/API needed): the app's own accent gradient (`#7C6EF7` → `#6D8CFA`, the same one every
  primary button already uses) behind three white concentric arcs + a dot, anchored bottom-left.
- Wired in three places: `main.py`'s `QApplication.setWindowIcon()` (title bar / taskbar, covers
  every window since Qt inherits the app-level icon by default), the sidebar's wordmark row
  (`sidebar_icon_lbl`, new), and the auth screens' left-panel wordmark row (`auth_icon_lbl`, new) -
  both scaled down from the one master PNG rather than separate assets.
- Text wordmark changed from "AttendU" to "TapIn" in both of those rows, and both windows'
  `windowTitle` (previously "Student Attendance Tracking" / "...App") is now just "TapIn".
- Left `shared/palette.py`/`views/main_window.py`/`views/class_window.py`'s **code comments** that
  say "AttendU" alone - those refer to the named design-system phase this redesign pass followed
  (like "Kintsugi" was the name of the phase before it), not the live app's displayed brand, so
  they're accurate as historical/internal context and don't need to track the product name.
- `README.md`'s title is now "TapIn" too; left the "originally built for the COMP413 IoT course at
  Abdullah Gül University" line alone - that's true project provenance/history, not branding, and
  erasing it would just be inaccurate.

## 19. Doc cleanup + non-standard dialogs rebuilt as real QDialogs

Per your request to "work on .md files ... fix QDialog rebuild":

- Deleted `.claude/plans/wild-jingling-unicorn.md` (the Kintsugi visual-redesign plan) - it assumed
  dark mode would be redesigned in parallel, which directly contradicts §16's full removal, so it was
  stale rather than something to resume.
- `CHANGELOG.md` hadn't been touched since Phase 1; added a `[0.2.0]` entry summarizing the ~80
  features shipped since (grouped by area, pointing at `FEATURE_BACKLOG.md` for the itemized list)
  and moved dark mode/roster-wizard/TapIn changes into `[Unreleased]`.
- `FEATURE_BACKLOG.md` #27 still claimed dark mode was shipped; corrected to unchecked + a note
  explaining it was removed, cross-referencing §15-16.
- `ARCHITECTURE.md`'s module layout annotated to mention the generated `app_icon.png` and that roster
  add/remove now lives in the Edit Class wizard, not `class_window.py`.
- `shared/widgets.py`'s module docstring (and `tests/test_widgets.py`'s) referenced the
  now-deleted plan file too - reworded, since `make_stat_card`/`make_tag_pill` are just reusable
  widget builders, not exclusively Kintsugi-Info-panel-specific (the Info panel itself never shipped;
  `make_tag_pill` is the one of the two actually used, by class color tags).
- New `shared/dialogs.py`: `ChoiceDialog` (a real `QDialog` - label + `QComboBox` + OK/Cancel) and
  `DetailDialog` (a real `QDialog` - label + Close + an optional extra `ActionRole` button), both
  styled automatically via a new generic `QDialog {}` / `QDialog QPushButton {}` / `QDialog QComboBox
  {}` block added to `theme.qss.tmpl` next to the existing `QMessageBox` block (custom `QDialog`
  subclasses had **no** styling at all before this - a gap, not an intentional omission).
- Rebuilt onto these: `register_card()`'s `QMessageBox()` with a `QComboBox` manually inserted into
  its own layout and **no buttons at all** (`take_attendance_window.py`) → `ChoiceDialog.get_item()` -
  this also fixes a real defect, since there was previously no way to cancel out of registering a card
  to the wrong student; `show_student_detail()`'s `QMessageBox.addButton("Export CSV",
  QMessageBox.ActionRole)` hack (`class_window.py`) → `DetailDialog`; and the `QInputDialog.getItem()`
  calls in `correct_attendance_cell()` and both picks in `merge_students()` → `ChoiceDialog.get_item()`
  (same `(text, ok)` return shape, so the call sites barely changed).
- **Deliberately left alone**: `mark_selected_absent()`'s dialog (`take_attendance_window.py`) was
  already a real `QDialog` with a proper button box, just built inline - no rebuild needed, it now
  also picks up the new generic `QDialog` QSS for free. Also left alone: the serial-port-picker
  `QInputDialog.getItem` (hardware setup, not part of the originally-flagged set),
  `manual_attendance_entry()`'s 2 `getItem` calls, and `copy_roster_from_class()`'s `getItem` call -
  these are standard, correctly-functioning uses of the built-in dialog, not hijacked ones; converting
  them too would be scope creep on already-working code.
- Also found and removed while in `theme.qss.tmpl`: two dead `QPushButton#theme_toggle_btn` selector
  blocks (§16 deleted the widget itself but missed these two QSS rules targeting it).
- New `tests/test_dialogs.py` covers `ChoiceDialog`/`DetailDialog` directly; `tests/test_class_window_merge_students.py`,
  `tests/test_class_window_correct_attendance.py`, `tests/test_class_window_student_detail.py`, and
  `tests/test_take_attendance_duplicate_card.py` updated to patch the new dialog classes instead of
  `QInputDialog`/`QMessageBox` internals.
