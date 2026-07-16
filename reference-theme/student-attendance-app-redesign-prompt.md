# {{APP_NAME}} — Full Redesign & Feature Specification (v2 — PyQt)

**A prompt document for restyling the student attendance app to match the "AttendU" reference theme, and for building the new pages/features described below.**

> **What changed in this revision:** the stack is now confirmed as **PyQt** (a Python desktop app), not a web framework — every "how to implement" note below has been rewritten for that. This revision also folds in exact details now visible in the newer reference screenshots: the finished login/signup/reset-password flow, the finished Class Detail screen, and the finished Take Attendance screen. Where those screenshots showed something more specific (or different) than the first draft of this document guessed at, the screenshot wins and the text below has been corrected to match it.

---

## 1. Purpose of This Document

This document is written to be handed, in full, to whoever (or whatever — including an AI coding assistant such as Claude Code) implements the work, **alongside the reference screenshots** it is based on. It has three jobs:

1. Extract a complete, reusable **design system** from the reference screenshots (colors, type, spacing, components, layout shell) so every new screen looks like it shipped from the same team as the old ones.
2. Specify, screen by screen, exactly what should be **built, restyled, or extended**.
3. Provide a **data model and interaction spec**, plus **PyQt-specific implementation notes**, detailed enough that no implementer has to guess at edge cases (merging duplicate students, what happens when the hardware scanner disconnects, what "Remember me for 30 days" actually persists, how to fake CSS-variable theming and toast notifications in a framework that doesn't have either, etc.).

Replace `{{APP_NAME}}` everywhere with the product's real name (the reference screenshots use "AttendU" as a placeholder brand).

---

## 2. Tech Stack & Assumptions

- **Stack: PyQt** (PyQt5 or PyQt6 — confirm which; the notes below apply to either, but syntax for enums like `Qt.AlignCenter` vs `Qt.AlignmentFlag.AlignCenter` differs between the two, so pick one and stay consistent throughout the codebase). All layout, styling, and navigation guidance below is written in Qt terms — QWidget/QLayout hierarchies, QSS instead of CSS, `QStackedWidget` instead of routes, signals/slots instead of `onClick`.
- **The person signing in is an instructor**, and "students" are roster records the instructor manages rather than separate account holders who log into {{APP_NAME}} themselves. Nothing in the new screenshots contradicts this.
- **Local vs. networked backend — flag this explicitly, it changes real architecture:** the reference's Security → Active Sessions list (a MacBook Pro, an iPhone 16, and a Windows PC, each in a different city) and the auth screens' marketing stats ("12k+ Students," "450+ Instructors," "98% Uptime") both imply a networked, multi-tenant service with a real backend and multiple client platforms. A PyQt app is normally a single-machine desktop tool. Decide which of these you're actually building before implementing Settings → Security and "Remember me":
  - **If this is a local, single-instructor tool:** back it with a local SQLite database, simplify "Active Sessions" to show only the current machine (or drop the section entirely), and implement "Remember me" as a plain local flag (see §9.4a) — no server, no tokens.
  - **If this is genuinely a networked multi-device product:** you need a real auth backend issuing sessions/tokens that the PyQt client talks to over HTTP, and the Active Sessions list becomes real data from that backend rather than a static reference layout.
  - Everything below is written to work either way, but §9.4a gives the concrete simpler version, since that's the far more likely fit for a PyQt instructor tool.
- **The demo shortcut currently on the login screen** ("Demo: click Sign In without credentials to enter the app.") is presumably a development convenience. Gate it behind a debug/dev-mode build flag so it can't ship to a real instructor's build by accident.
- **The auth screens' marketing stats** (98% Uptime / 12k+ Students / 450+ Instructors) read as placeholder template copy rather than real figures for a personal or small-deployment tool. Worth swapping for something honest before shipping — three feature bullets instead of three fake numbers is an easy, harmless fix (see §9.1).

---

## 3. Brand & Visual Identity

- **Logo lockup:** a small rounded-square icon (graduation-cap glyph) in the accent color, next to the bold wordmark. Confirmed present, unchanged, on every auth screen and the sidebar.
- **Voice:** plain and direct — "Good morning, Aiden 👋", "Session not started", "No attendance recorded yet. Start session or mark all present." Buttons are named for the action they perform ("Save Notes," "Start Attendance," "Submit Attendance") and the confirmation/empty-state text keeps using that same verb. Section 18 expands on this with the newly-confirmed exact copy.
- **Personality knobs exposed to the end user:** Dark Mode toggle, font family (DM Sans / Serif / Mono), font size (Small / Medium / Large) in Settings → General. These need to be runtime-swappable, not just build-time choices — see §4.6.

---

## 4. Design Tokens

### 4.1 Color

| Token | Light mode | Dark mode | Used for |
|---|---|---|---|
| `bg` | `#EEF0F5` (reference value) | `#0B0E14` (reference value) | Window/page background |
| `surface` | `#FFFFFF` | `#161A24` (reference value) | Cards, dialogs, sidebar |
| `surface_raised` | `#FFFFFF` + soft shadow | `#1B202C` (reference value) | Dropdowns, popovers, dialogs-over-dialogs |
| `border` | `#E4E7ED` (reference value) | `#262B38` (reference value) | Card borders, dividers, input outlines |
| `text_primary` | `#1B1E2B` (reference value) | `#F1F2F6` (reference value) | Headings, primary copy |
| `text_muted` | `#8A93A7` (reference value) | `#8790A6` (reference value) | Labels, timestamps, captions, "Session not started" |
| `accent` | `#7C6EF7` (confirmed via the Add-Class "Class Color" swatch) | `#8B7CF9` (reference value) | Primary buttons, active nav item, links, selected calendar day, focus rings |
| `accent_gradient` | `qlineargradient` from `#7C6EF7` -> a blue tone | same | "Start Attendance," "Sign In," "Create Account," "Submit Attendance" — every primary CTA uses the same purple-to-blue gradient, confirmed across the new screenshots |
| `success` | `#16A34A` text / `#DCFCE7` bg | `#4ADE80` text / `#123722` bg | "Present," "ACTIVE" pill |
| `warning` | `#B45309` text / `#FEF3C7` bg | `#FBBF24` text / `#3A2E0F` bg | "Late," attendance approaching the class minimum |
| `danger` | `#DC2626` text / `#FEE2E2` bg | `#F87171` text / `#3A1414` bg | "Absent," attendance below the class minimum, destructive actions, the scanner-disconnected banner |
| `neutral_pill` | `#F1F2F6` bg / `#6B7280` text | `#232838` bg / `#9AA1B4` text | "INACTIVE" pill, tag chips |

**Two status-display conventions, both now confirmed in the screenshots — keep both, don't merge them:**
- **Filled pill** (colored background + colored text): used for class/session-level state — "ACTIVE"/"INACTIVE," session status.
- **Plain colored text, no background:** used for per-student attendance status inside tables — "Late," "Absent," "Present" in both the Class Detail roster table and the Take Attendance session table render as colored text only.

**Attendance color-tier logic** (unchanged recommendation): danger if current % is below the class's configured minimum; warning if at/above the minimum but within 10 points of it; success if 10+ points above it.

### 4.2 Typography

DM Sans as the default, Serif and Mono as user-selectable alternates, exactly as in Settings -> General -> Typography. Font size (Small/Medium/Large) scales the whole type ramp, not just body text.

| Role | Size (Medium) | Weight | Example |
|---|---|---|---|
| Display / page greeting | 28-30px | Bold | "Good morning, Aiden" |
| Page title | 22-24px | Bold | "Take Attendance," "Database Systems" |
| Card title | 16-17px | Semibold | "Class Details," "Roster & Attendance" |
| Body | 14-15px | Regular | Field labels, table cells |
| Small / caption | 12-13px | Medium | Timestamps, "Session not started," tag chips |
| Stat number | 26-32px | Bold | Dashboard/Statistics big numbers |

### 4.3 Spacing & Radius

Base unit 4px on a 4/8/12/16/20/24/32px scale. Card padding 20-24px, gap between cards 16-24px. Card radius 16px. Control radius (inputs/buttons) 10-12px. Pills fully rounded.

### 4.4 Elevation

Light mode: a soft drop shadow plus a 1px border. Dark mode: skip the shadow, rely on the border + a slightly-lighter-than-background surface color.

### 4.5 Iconography

Outline style, ~1.5px stroke. Rather than hand-maintaining individual SVG files, consider the **`qtawesome`** package (installable via pip), which gives Font-Awesome/Material-style icons as `QIcon` objects with a couple of lines — much less friction inside a PyQt project than sourcing and importing dozens of individual SVGs.

### 4.6 Implementing These Tokens in PyQt

QSS (Qt Style Sheets) is a CSS-like subset: `background-color`, `color`, `border`, `border-radius`, `padding`, `margin`, `font-family`/`font-size`/`font-weight` all work, and gradients are supported via `qlineargradient(...)`. It does **not** support CSS variables, `box-shadow`, transitions, or flexbox/grid. Work around each of those:

- **No CSS variables ->** keep one Python module (e.g. `theme.py`) with `LIGHT` and `DARK` dicts mapping token name to value, and a function that renders the *entire* app stylesheet as an f-string from the active dict, applied once at the `QApplication` level so it cascades everywhere:

  ```python
  def build_stylesheet(tokens: dict, font: dict) -> str:
      return f"""
      QWidget {{ background-color: {tokens['bg']}; color: {tokens['text_primary']};
                 font-family: '{font['family']}'; font-size: {font['base_px']}px; }}
      QFrame#card {{ background-color: {tokens['surface']}; border: 1px solid {tokens['border']};
                     border-radius: 16px; }}
      QPushButton#primary {{ border-radius: 10px; padding: 8px 18px; color: white;
          background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                      stop:0 {tokens['accent']}, stop:1 {tokens['accent_end']}); }}
      QPushButton#primary:disabled {{ background: {tokens['border']}; color: {tokens['text_muted']}; }}
      """

  app.setStyleSheet(build_stylesheet(DARK if dark_mode else LIGHT, font_settings))
  ```
  Re-call this (and re-apply) whenever the user flips Dark Mode or changes the font settings in Settings -> General.

- **No box-shadow ->** apply a `QGraphicsDropShadowEffect` object programmatically to any widget that needs the light-mode card shadow: `frame.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=24, xOffset=0, yOffset=8, color=QColor(16,24,40,25)))`.

- **Tier-based coloring (success/warning/danger) that changes at runtime** — QSS selectors can match on a *dynamic property*, which is the idiomatic way to do this:

  ```python
  bar.setProperty("tier", "danger")
  bar.style().unpolish(bar); bar.style().polish(bar)   # forces QSS to re-evaluate -- easy to forget
  ```
  ```css
  QProgressBar[tier="danger"]::chunk { background-color: #DC2626; }
  QProgressBar[tier="warning"]::chunk { background-color: #B45309; }
  QProgressBar[tier="success"]::chunk { background-color: #16A34A; }
  ```

- **Persisting theme/font/window preferences and "Remember me"** -> use `QSettings`, Qt's built-in cross-platform key-value store (backed by the registry on Windows, plist on macOS, an ini file on Linux) — this is the direct equivalent of what "local storage" would be on the web, and it's what should back Settings -> General and the "Remember me" flag (see §9.4a).

---

## 5. Global Application Shell

- **Top-level window:** a single `QMainWindow` containing one `QStackedWidget` as its central widget, with (at minimum) two top-level pages: the **auth stack** (login/signup/forgot-password, itself a nested `QStackedWidget`) and the **app shell** (sidebar + topbar + content). Swapping from "logged out" to "logged in" is just changing the outer stack's current index — this avoids opening/closing separate windows and keeps size/position stable.
- **Sidebar** (`QWidget`, fixed width ~220-240px, `QVBoxLayout`): logo lockup, current user block (initials avatar + name + role/program subtext), then the nav list — Dashboard / Classes / Statistics / Settings — as checkable `QPushButton`s in a `QButtonGroup` (exclusive selection gives you the "active item" state for free), then a bottom-pinned Sign Out button.
- **Topbar** (`QWidget`, `QHBoxLayout`): search `QLineEdit`, then right-aligned: connectivity pill, theme toggle button, notification bell (`QToolButton` + unread-count badge, drawn as a small colored `QLabel` overlaid or via a custom paintEvent), avatar button opening a `QMenu` (Edit Profile / Settings / Sign Out).
- **Content area:** another `QStackedWidget`, one page per top-level screen (Dashboard, Classes, Statistics, Settings), navigated by connecting each sidebar button's `clicked` signal to `content_stack.setCurrentIndex(n)`. The Class Detail and Take Attendance screens are pushed onto this same stack (or a `QStackedWidget` nested one level deeper) when a class is opened, with the "<- My Classes" / "<- {{Class Name}}" back buttons simply calling `setCurrentIndex` back down.
- **Window resizing:** PyQt doesn't have CSS breakpoints; instead, give layouts sensible `QSizePolicy` and minimum widths, and — if you want the 3-column card grids to reflow to 2 or 1 columns — recompute the grid's column count inside a `resizeEvent` override based on the available width, rather than trying to fake `@media` queries.

---

## 6. Component Library — Web Concept to PyQt Widget Mapping

| Component | Anatomy | PyQt approach |
|---|---|---|
| **StatCard** | icon, big number, label | `QFrame` (`objectName="card"`) + `QVBoxLayout` of `QLabel`s |
| **ClassCard / ClassListRow** | colored accent bar, name, instructor, progress bar, pills | `QFrame` with a `border-left`/`border-top` QSS rule keyed to a per-instance dynamic property or per-instance stylesheet string for the class color |
| **ProgressBar** | tier-colored fill | `QProgressBar`, styled via the dynamic-property pattern in §4.6 |
| **StatusPill** | small filled rounded badge | `QLabel` styled with `border-radius: <h/2>px; padding: 2px 10px;` |
| **Plain colored status text** (table rows) | colored text, no background | `QLabel`/table-cell foreground color set directly (or a tiny `QStyledItemDelegate` for `QTableWidget`/`QTableView` cells) |
| **TagChip** | neutral rounded badge | Same as StatusPill, neutral palette |
| **SegmentedTabs** | pill tab group | `QTabBar`/`QTabWidget` restyled via QSS, or a `QButtonGroup` of checkable flat `QPushButton`s if you want the exact pill look; skip trying to animate a sliding indicator — a static checked/unchecked style is much less effort and reads fine |
| **ModalWizard** (Add/Edit Class) | numbered steps, Back/Next/Submit footer | `QDialog` containing a `QStackedWidget` (one page per step) + a small row of `QLabel`/`QFrame` step-dots + footer `QHBoxLayout` |
| **IconButton** | icon-only button | `QToolButton` with `setIcon(...)`, `setAutoRaise(True)` for the "flat until hovered" look |
| **Toast/Snackbar** | transient confirmation | Qt has no built-in equivalent — implement as a frameless `QWidget` (`Qt.FramelessWindowHint \| Qt.WindowStaysOnTopHint` or a plain child overlay positioned with `move()`), fade in/out with a `QPropertyAnimation` on `windowOpacity`, auto-hide via `QTimer.singleShot(4000, self.close)` |
| **ConfirmDialog** | Cancel + destructive confirm | `QMessageBox.question(...)` for simple cases; a custom `QDialog` for anything with a data preview (e.g. the Merge Students summary) |
| **Alert/Banner** | icon + message + optional action | `QFrame` + `QHBoxLayout` of an icon `QLabel`, a message `QLabel`, and an optional `QPushButton` |
| **Calendar grid** | custom-styled month grid | A hand-built `QGridLayout` of checkable `QPushButton`s (one per day) rather than the native `QCalendarWidget`, which is very difficult to restyle to this degree — the existing screenshots' calendar look is consistent with a hand-built grid already |
| **Roster/session table** | sortable rows, status coloring | `QTableWidget` (simplest) or `QTableView` + `QStandardItemModel` (better for larger rosters); color cells with `setForeground`/`setBackground` or a `QStyledItemDelegate` |
| **Per-row actions** (mark present/absent, edit, note, view details, remove) | — | Rather than embedding a row of icon-button widgets in each table cell (heavy in Qt), use a **right-click context menu**: `table.setContextMenuPolicy(Qt.CustomContextMenu)`, connect `customContextMenuRequested` to build a `QMenu` with the relevant actions for the clicked row, and use **double-click** on a row to open the Student Detail dialog. This is the idiomatic desktop pattern and is much less work than the icon-per-row approach a web version would use. |
| **Password visibility toggle** | eye icon inside the field | `QLineEdit` supports embedded actions natively: `action = line_edit.addAction(QIcon(eye_svg), QLineEdit.TrailingPosition)`, then toggle `line_edit.setEchoMode(QLineEdit.Password / QLineEdit.Normal)` on `action.triggered` |
| **Leading icon in a field** (mail/lock icons in the login form) | icon inside the field, left side | Same mechanism, `QLineEdit.LeadingPosition` |

```python
# Right-click row actions -- the pattern to reuse for the roster table
table.setContextMenuPolicy(Qt.CustomContextMenu)
table.customContextMenuRequested.connect(self._show_row_menu)

def _show_row_menu(self, pos):
    row = table.rowAt(pos.y())
    if row < 0:
        return
    menu = QMenu(self)
    menu.addAction("Mark Present", lambda: self.mark(row, "present"))
    menu.addAction("Mark Absent", lambda: self.mark(row, "absent"))
    menu.addAction("Add Note...", lambda: self.add_note(row))
    menu.addSeparator()
    menu.addAction("View Details...", lambda: self.view_details(row))
    menu.addAction("Edit...", lambda: self.edit_student(row))
    menu.addAction("Remove from Roster", lambda: self.remove(row))
    menu.exec(table.viewport().mapToGlobal(pos))
```

---

## 7. Screen & Window Inventory

| Screen | Container | Purpose |
|---|---|---|
| Login | Page in the auth `QStackedWidget` | Sign in |
| Sign Up | Page in the auth `QStackedWidget` | Create account |
| Reset Password (request) | Page in the auth `QStackedWidget` | Request a reset link |
| Reset Password (sent confirmation) | Page in the auth `QStackedWidget` | "Check your email" state |
| Reset Password (set new password) | Page in the auth `QStackedWidget`, reached via a token/link | Choose a new password |
| Dashboard | Page in the app content `QStackedWidget` | Overview |
| My Classes | Page in the app content `QStackedWidget` | Full class list |
| Class Detail | Pushed onto the content stack when a class is opened | Details, notes, roster |
| Take Attendance | Pushed onto the content stack from Class Detail's "Take Attendance" button | Calendar + live session + manual/scanned entry |
| Statistics | Page in the app content `QStackedWidget` | Personal analytics |
| Settings | Page in the app content `QStackedWidget`, with an internal `QTabWidget` for General/Edit Profile/Security | Preferences and account |
| Add/Edit Class | `QDialog` | 3-step wizard, opened from "+ Add Class" or a class's "Settings" button |
| Add Student | Inline row (confirmed — not a modal; see §12.5) | Add a student to the current class's roster |
| Merge Students | `QDialog` | Reconcile duplicate roster entries |
| Student Detail | `QDialog` | Cross-class history for one student |

---

## 8. Data Model Reference

Unchanged by the framework switch — this is the shape the data layer needs regardless of whether it's SQLite-via-`sqlite3`/SQLAlchemy locally or a networked API (see §2's local-vs-networked flag).

**User** (the instructor account) — `id, firstName, lastName, email, phone, bio/programme, avatarInitials, passwordHash, themePreference, fontFamily, fontSize, autoLogoutMinutes, securityQuestion, securityAnswerHash, createdAt`

**Class** — `id, ownerInstructorId, name, section, code, color, numberOfWeeks, weeklyHours, totalHours (derived), lateThresholdMinutes, minAttendancePercent, scheduleSlots[] (day, startTime, endTime), status, pinned, notes, createdAt, updatedAt`

**Student** (a roster record, scoped to the instructor, not a login) — `id, ownerInstructorId, studentNumber, firstName, lastName, email (optional), createdAt`

**Enrollment** (Student <-> Class) — `id, classId, studentId, enrolledAt, status (active/removed)`

**Session** (one scheduled occurrence of a class) — `id, classId, date, timeSlot, status (not-started/live/ended), lateThresholdOverrideMinutes (nullable), isTemplate`

**AttendanceRecord** — `id, sessionId, studentId, status (present/absent/late), method (scanned/manual), recordedAt, recordedBy`

**Note** (class-level or student-level) — `id, classId, studentId (nullable), authorId, body, updatedAt`

**Notification** — `id, userId, type, title, body, isRead, createdAt`

**ActiveSession** (only relevant if you keep the networked/multi-device path — see §2) — `id, userId, deviceLabel, location, lastActiveAt, isCurrent, rememberMe`

Because `Student` is scoped to the instructor rather than to one class, one student can be enrolled in several of the instructor's classes — this is what makes "Copy Roster From Class" and the cross-class Student Detail view (§12.5.1) meaningful.

---

## 9. Authentication Screens

All three (plus the token-based reset step) now exist as real screenshots and share one confirmed layout: a fixed **split panel**.

### 9.1 Shared shell

- **Left panel (~45% width), always dark** regardless of the app's light/dark setting — this is a fixed brand panel, not theme-reactive:
  - Logo lockup, top-left, sitting in front of a soft purple radial glow.
  - Eyebrow label, uppercase, letter-spaced, muted purple: "STUDENT ATTENDANCE PLATFORM."
  - Two-line headline: first line in white ("Track every"/"session."), second line in the accent color ("Never miss a beat.").
  - One paragraph of supporting copy, muted.
  - Three stat pills in a row (currently "98% Uptime," "12k+ Students," "450+ Instructors" — **replace with real figures or swap for three feature bullets**, per §2).
  - Footer: "© 2026 {{APP_NAME}} - All rights reserved," bottom-left.
  - A second, larger, dimmer glow anchored bottom-right for depth.
- **Right panel:** the actual form, on the standard `bg`/`surface` tokens, theme-reactive (this is what the sun/moon toggle — fixed top-right of the whole window — actually controls; the left panel doesn't change).

### 9.2 Login

- **Heading:** "Welcome back." **Subheading:** "Sign in to your {{APP_NAME}} account."
- **Email Address** field, mail icon leading.
- **Password** field, lock icon leading, eye-toggle trailing; "Forgot password?" link sits inline, right-aligned with the "Password" label.
- **Checkbox:** "Remember me for 30 days" — spell out the duration in the label itself, exactly as shown, rather than a bare "Remember me."
- **Primary button:** "Sign In."
- **Demo banner** (dev-only, see §2): an info-styled banner — "Demo: click Sign In without credentials to enter the app."
- **Footer:** "Don't have an account? Create one."

### 9.3 Sign Up

- **Heading:** "Create account." **Subheading:** "Join {{APP_NAME}} and start tracking attendance."
- **Fields:** First Name / Surname (two-column), Email Address, Password (placeholder "Min. 8 characters," eye-toggle), Confirm Password (placeholder "Repeat password").
- **Primary button:** "Create Account."
- **Footer:** "Already have an account? Sign in."

### 9.4 Reset Password

**Request state:**
- Top-left link: "<- Back to sign in."
- **Heading:** "Reset password." **Subheading:** "Enter your email and we'll send a reset link."
- **Email Address** field (prefilled if arriving from a logged-out state that still remembers the last email — confirmed behavior in the screenshot).
- **Primary button:** "Send Reset Link" — shown in a muted/disabled-looking state until the email field is valid.

**Sent-confirmation and set-new-password states** aren't in the new screenshots but extend naturally from the request state already built — keep the earlier recommendation: a "Check your email" state with a resend cooldown, and a token-gated "Choose a new password" form reusing the same password-field component.

### 9.4a "Remember me" — the simple, local-only version

Given §2's flag, the far more likely real implementation is local-only:

- Unchecked (default): the login screen shows on every launch.
- Checked: on successful login, persist a flag (and, if needed, an encrypted credential — consider the `keyring` package, which stores secrets in the OS's native credential store rather than plain `QSettings`) so the app can skip straight to the Dashboard on next launch.
- `QSettings` is the right place for the non-secret half of this (the "remember me was checked" flag, last-used email for the reset-password prefill, theme/font preferences) — see §4.6.
- If you do keep the networked/Active-Sessions path instead, this is where a server-issued long-lived refresh token would be stored (via `keyring`, never in plaintext `QSettings`), and it's what feeds each row of Settings -> Security -> Active Sessions.

---

## 10. Dashboard

Unchanged from the first draft — restyle only, no structural changes needed:

- Time-aware greeting + date/semester line, "+ Add Class" button.
- 5-card stat row: Active Classes, Pinned Classes, Total Classes, Attended, Archived.
- Filter tabs: All / Active / Pinned.
- Pinned section (expandable "Properties"/"Less" detail grid), Active Classes grid, Inactive section.
- Clicking a card body pushes the Class Detail screen onto the content stack; the pin icon and Properties toggle act in place instead.

---

## 11. My Classes

Unchanged from the first draft:

- Header, enrolled count/semester, "+ Enroll in Class."
- `ClassListRow` per class — colored left border, name/instructor/schedule, tag chips, attendance fraction + %, pin, expand chevron.
- Row click (not the chevron, not the pin) pushes the Class Detail screen.

---

## 12. Class Detail Screen

Now confirmed by a real screenshot — the structure below reflects it, with the couple of corrections called out explicitly.

### 12.1 Header

- Back link: **"<- My Classes"** — a single link, not a two-part breadcrumb (correction from the first draft, which proposed "Classes / {{Class Name}}"; the simpler single back-link is what's actually built, and it's the same pattern reused on the Take Attendance screen's "<- {{Class Name}}").
- **Class Name**, large and bold.
- Subheading, one plain line: **"{{Code}} · {{Schedule}}"** (e.g. "CS · Tue / Thu 11:00") — not separate tag chips, just one muted text line combining code and schedule.
- Top-right: **Settings** (outline button, gear icon) and **Take Attendance** (primary gradient button) — matches the first draft.

### 12.2 Class Details card

Confirmed as a **label/value list**, not a grid of mini-stat-cards: Instructor, Attendance Policy (as a percentage, e.g. "75.0%"), Late Threshold ("10 min"), Number of Weeks, Total Hours, Weekly Hours — one row each, label left / value right, inside a single card.

Directly beneath that list, still inside the same card: an **attendance-rate sub-panel** — a light tinted strip containing the label "Your attendance rate," a progress bar, and the value "79% — 30/38 sessions" right-aligned at the bar's end. (New addition versus the first draft — worth calling out since it's a nice, information-dense detail: the bar communicates the number the instructor most wants at a glance without leaving the page.)

### 12.3 Schedule card

Confirmed layout: **one column per meeting day** (e.g. "Wednesday," "Thursday" as column headers), each column stacking a small pill/chip per time slot on that day (Wednesday shows two stacked chips — "09:00-10:30" and "11:00-12:30" — Thursday shows one). This is a column-of-chips layout, not a single inline text line as the first draft guessed.

### 12.4 Notes card

- Textarea, confirmed empty-state copy: *"No additional notes for this class."*
- **"Save Notes"** button — confirmed **full width**, matching the textarea's width, not a small button off to one side.

### 12.5 Roster & Attendance card

**Toolbar, right-aligned above the table:** three text-style actions plus an unlabeled refresh icon:

- **"Copy Roster From Class"** — correction from the first draft, which assumed this meant "copy to clipboard." The actual label describes a different, more useful feature: **clone the roster from one of the instructor's other classes into this one** — open a picker of the instructor's other classes, let them choose one, and bulk-`Enrollment` every one of that class's students into the current class (creating new `Enrollment` rows; no new `Student` rows needed, since `Student` is already instructor-scoped and shared). This is genuinely useful for an instructor who teaches overlapping sections, and it's the feature to build here — not a clipboard export.
- **"Export Roster"** — downloads a spreadsheet (Student Number, First Name, Last Name, Email, Sessions Attended, Sessions Missed, Attendance %). Share the underlying export function with "Export To Excel" on the Take Attendance screen (§13) — one function, two entry points.
- **"Merge Students"** — enabled once 2+ rows are checked; opens the merge dialog described below.
- Unlabeled circular-arrow icon — **Refresh List**.

**Table columns (confirmed):** a checkbox column, **Student No.**, **Name Surname**, **Last Date** (the student's most recently recorded session date in this class — not just "Date," since this table is an aggregate roster view, not a single session), **Time Slot**, **Status** (plain colored text — Late/Absent/Present — per §4.1's "no background pill" convention for this context).

**Per-row actions:** not shown as visible icons in the screenshot — build these as the right-click context menu described in §6 (Mark Present, Mark Absent, Add Note..., View Details..., Edit..., Remove from Roster), with double-click opening Student Detail directly. This is both the idiomatic Qt pattern and consistent with what a static screenshot of a `QTableWidget` would look like even if the menu exists.

**Bottom toolbar row (confirmed, persistent — not a bulk-bar that appears/disappears):**

- Three inline fields — **Student No.**, **Name**, **Surname** — followed by an **"Add Student"** button. Enable "Add Student" once all three fields are filled; before creating a new `Student` row, check the instructor's whole roster (not just this class) for a matching student number and, if found, offer to enroll the existing student instead of creating a duplicate.
- **"Remove Selected"** button, right-aligned in the same row, disabled/grayed until 1+ row is checked — this replaces the first draft's separate floating "bulk action bar" concept with the simpler always-present-but-conditionally-enabled row that's actually built.

#### 12.5.1 Student Detail dialog

Opened via double-click (or the context menu's "View Details...") on any roster row, anywhere in the app — student-centric, not class-centric:

- Header: Student No., Name Surname, Email.
- One section per class this student is enrolled in across the instructor's whole roster: class name, attendance % there, sessions attended/missed.
- Chronological attendance timeline: date, class, status, time recorded, method.
- All notes involving this student, most recent first, tagged with the class each belongs to.
- Quick actions: "Edit Student Info," and (if opened from a specific class) "Remove from {{that class}}."

#### 12.5.2 Merge Students dialog

Unchanged from the first draft:

1. Selected students shown side by side (number, name, email, attendance-record count), radio button to pick the canonical record.
2. Confirmation copy: "{{N}} attendance records and {{M}} notes will move to {{Canonical Name}}. The other entries will be permanently deleted. This can't be undone."
3. Destructive-styled confirm: "Merge & Delete Duplicates."
4. On success, re-point `Enrollment`/`AttendanceRecord`/`Note` rows to the canonical student, delete the duplicates, toast "Merged 2 students into {{Name}}."

---

## 13. Take Attendance Screen

Now confirmed by a real screenshot; the mapping table from the first draft holds up well — here's the corrected, final version.

- **Back link:** "<- {{Class Name}}" (e.g. "<- Database Systems"), same single-link pattern as Class Detail's back link.
- **Page title:** "Take Attendance."
- **Calendar** (left): month grid, confirmed built as a custom widget (not `QCalendarWidget` — see §6), selected day as a solid accent-filled rounded rectangle, weekend headers (Sun/Sat) in a muted red, prev/next-month days dimmed.
- **Session panel** (right), confirmed contents and exact copy:
  - "Taking attendance for {{Class Name}}" (bold) / "{{Weekday}} — {{DD-MM-YYYY}}" (muted, e.g. "Thu — 16-07-2026").
  - **Time Slot** dropdown (only the slots that actually exist for this weekday, per the class's schedule).
  - Plain caption text under the dropdown for session state — confirmed as plain muted text ("Session not started"), not a colored pill; a colored-pill variant for "Live"/"Ended" would be a reasonable light enhancement but isn't required to match the current build.
  - **Late threshold override (min)** field, placeholder "Leave blank for default."
  - **"Save as Template"** (outline button).
  - **"Export To Excel"** (outline button; the label itself is tinted in the success-green token, a nice small touch tying the action to the success color without needing a full pill).
  - **"Start Attendance"** (primary gradient button, disabled until date + time slot are set).
- **Hardware alert banner:** confirmed final copy is short and plain — **"Couldn't connect to scanner — manual attendance mode active"** — a big simplification from the raw serial-port error text in the legacy screen. A "Retry Connection" button and a collapsed "Show technical details" toggle (surfacing the raw port error for troubleshooting) are still worth adding as light enhancements, but the current short-and-actionable copy is the right baseline — don't regress back to dumping the raw exception text.
- **Action row:** "Mark All Present" / "Undo Last Scan" / "Manual Attendance" / "Mark Selected Absent," with an "{{x}}/{{y}} recorded" counter at the far right.
- **Table columns:** Student Name Surname, Date, Time Slot, Time, Status (plain colored text) — this table is scoped to the single in-progress session, so it's genuinely "Date" here (contrast with Class Detail's roster table, which needed "Last Date" because it's an aggregate view — see §12.5).
- **Empty state, confirmed copy:** *"No attendance recorded yet. Start session or mark all present."* — a good model for every other empty state in the app: it names the situation and hands the user the next action in the same sentence.
- **"Submit Attendance"**, primary gradient, full width, at the bottom.
- **"Today's Summary" card** (new — confirmed in the screenshot, not in the first draft): a small stat list sitting below the session panel, showing running counts — Present / Late / Absent / Total — updating live as attendance is recorded during the session.

**Scanner integration, implementation note:** since the hardware read (the serial-port error confirms a physical card/barcode reader over a serial connection) shouldn't block the Qt event loop, run the serial read in a background `QThread` (or a worker object moved to a `QThread` via `moveToThread`) that emits a `pyqtSignal(str)` per scan event; the main thread's slot appends the row to the table and updates the recorded-counter and Today's Summary. Reconnect attempts (for the "Retry Connection" enhancement above) belong in that same worker.

---

## 14. Add / Edit Class Modal

Confirmed to match the first draft closely — no corrections needed, just the PyQt framing:

- Implement as a `QDialog` with an internal `QStackedWidget` for the 3 steps (Class Info -> Schedule -> Color & Confirm) and a step-indicator row of small `QLabel`/`QFrame` dots.
- **Step 1:** Class Name*, Class Section, Class Code, Instructor; "Hours Configuration" (Number of Weeks, Weekly Hours, auto-computed Total Hours); "Attendance Policy" (Late Threshold dropdown, Min. Attendance Required % dropdown) with a live helper sentence.
- **Step 2:** one card per day (Mon-Sun), checkbox to enable, start/end time pickers, "+ Slot"/"x Slot" for multiple blocks per day.
- **Step 3:** color swatches, live preview chip, Summary recap panel, inline validation blocking submit ("Class Name is required to continue.").
- **Edit mode:** same dialog, all fields prefilled, step indicators pre-checked, Step 3's submit reads "Save Changes," with an added collapsible "Danger Zone" (Archive Class / Delete Class — the latter requiring the class name typed into a confirmation field before the button enables).

---

## 15. Statistics

Unchanged from the first draft — apply the §4.1 tier-coloring everywhere a percentage or bar appears: stat row (Overall Attendance %, Classes Attended, Perfect Months, Active Courses), Monthly Attendance Rate bars, Per-Class Breakdown rows.

---

## 16. Settings

Unchanged from the first draft, implemented as a `QTabWidget` with three tabs:

- **General:** Dark Mode toggle, Display Language dropdown, Auto Logout Timeout dropdown, Typography (Font Family, Font Size).
- **Edit Profile:** Personal Information (First Name, Surname, Email, Phone, Bio/Programme), Change Password (Current/New/Confirm, each with the eye-toggle pattern from §6), Save/Cancel.
- **Security:** Security Question + Answer, Active Sessions (only meaningful if you took the networked path in §2 — otherwise simplify to just "this device"), Save Security Settings.

---

## 17. Notifications Panel

Unchanged from the first draft — no new screenshot of this yet. Bell -> `QMenu`-or-custom-popup list, each item with a type icon, title, optional detail line, relative time, unread dot; "Mark all read" link at the top. Wire the attendance-drop notification type directly to the §4.1 tier logic (fire when a class crosses from success/warning into danger).

---

## 18. Microcopy & Content Voice

The newly-confirmed screens hand us several concrete examples worth treating as the house style going forward:

- **Empty states name the situation and hand over the next action in the same breath:** "No attendance recorded yet. Start session or mark all present." / "No additional notes for this class."
- **Session-state captions are plain and quiet, not alarmed:** "Session not started" — muted gray text, no icon, no color.
- **Hardware/error banners are short, plain-language, and immediately followed by what still works:** "Couldn't connect to scanner — manual attendance mode active." Don't regress toward dumping a raw exception string on the user.
- **Buttons keep their exact verb through the whole flow.** "Start Attendance" -> the session becomes "live"; "Submit Attendance" -> whatever confirmation follows should say "submitted," not "saved" or "recorded."
- **Duration-specific labels beat vague ones:** "Remember me for 30 days," not a bare "Remember me."

---

## 19. Accessibility & Interaction States (Desktop)

- Every interactive widget needs a visible focus state — QSS supports a `:focus` pseudo-state (e.g. `QLineEdit:focus { border: 2px solid ACCENT; }`); make sure tab order (`setTabOrder`) actually follows the visual layout on every form.
- Status is never color-only: every StatusPill and every colored table-status text keeps its label ("Present," "78%") alongside the color, matching what's already built.
- Use Qt's accessibility framework (`QAccessible`, `accessibleName`/`accessibleDescription` properties) on custom widgets (the hand-built calendar buttons in particular) so screen readers get sensible names instead of silence.
- Loading states: a `QMovie`-driven spinner or a simple "Loading..." label for first-load table population; disable-and-spin the specific button for in-flight single actions (e.g. "Save Notes") rather than blocking the whole window.
- Every destructive action (Remove Student, Delete Class, Merge Students) goes through `QMessageBox.question()` or a custom confirm dialog — never fires on a single click.
- There's no "reduced motion" OS signal to hook into the way there is on the web; keep animations (the toast fade, any hover transitions you add via `QPropertyAnimation`) minimal and skippable rather than trying to detect a preference that doesn't reliably exist on desktop.

---

## 20. Open Questions & Recommended Next Decisions

1. **Local-only vs. networked backend** (§2) — this is the biggest one, since it decides whether Settings -> Security -> Active Sessions and a real "Remember me" token are even in scope, or whether they simplify to a single local flag.
2. **Are students ever separate accounts**, or purely roster records the instructor manages? (Assumed the latter throughout.)
3. **Can a class have co-instructors?** The model assumes one `ownerInstructorId` per class.
4. **Should "Merge Students" have a short undo window** before the merge is permanent, given it's otherwise irreversible?
5. **Is the demo "click Sign In without credentials" shortcut meant to ship at all**, even gated — or should it be removed entirely once auth is real?
6. **The auth screens' marketing stats** — real figures, feature bullets instead, or dropped entirely for a single-instructor tool?

---

## 21. Implementation Checklist

- [x] Login, Sign Up, Reset Password (request state) — built, matches spec above
- [ ] Reset Password — sent-confirmation and set-new-password states
- [ ] "Remember me" wired to a real persistence mechanism (§9.4a)
- [ ] Dashboard
- [ ] My Classes
- [x] Class Detail — header, Settings/Take Attendance buttons, Class Details card w/ attendance-rate strip, Schedule card, Notes card — built, matches spec above
- [ ] Class Detail — Roster & Attendance: right-click context menu for per-row actions, Copy-Roster-From-Class picker dialog, Merge Students dialog, Student Detail dialog
- [x] Take Attendance — calendar, session panel, alert banner, action row, table, Today's Summary — built, matches spec above
- [ ] Take Attendance — background `QThread` scanner worker, Retry Connection + collapsible technical-details enhancement
- [ ] Statistics
- [ ] Settings — General / Edit Profile / Security tabs
- [x] Add/Edit Class modal — built, matches spec above; still needs the Danger Zone step for edit mode
- [ ] Shared Export function (Export Roster + Export To Excel call the same code)
- [ ] Central `theme.py` + `build_stylesheet()` wired to Settings -> General, applied at the `QApplication` level
