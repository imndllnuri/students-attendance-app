# TapIn — Complete Feature & Hardware Guide

This document explains, in full detail, everything the TapIn student-attendance
application does — every screen, every button, every setting — and everything
about the physical RFID hardware that goes with it: what it's made of, how it's
wired, how its firmware behaves, and how it talks to the app. It's written to
be usable by a non-technical reader (e.g. handing the whole project to a
teacher) while still being precise enough for anyone who needs to maintain or
extend the code later.

It's split into two parts:

- **Part 1 — Software** walks through every screen of the desktop application.
- **Part 2 — Hardware** covers the RFID reader, the microcontroller, the
  wiring, the LEDs, the firmware, and how it all connects to the app.

---

# Part 1 — Software

## 1. What TapIn is

TapIn is a desktop application that lets an instructor manage classes, keep
a roster of students, and record attendance for each class session — either
automatically, by having students tap an RFID card on a physical reader, or
manually, by clicking through the app. It also produces statistics, charts,
and reports about attendance over time.

TapIn works the way Obsidian does: everything lives in one folder you pick
(the **vault**), stored as plain JSON and Excel files you can open, back up,
or move like any other folder. There is no server, no account, and no login
screen — open the app and you're in. How the vault is organized on disk is
covered in §13.

### 1.1 First launch — choosing where your data lives

The very first time TapIn is opened on a computer, a **"TapIn Vault"**
dialog asks which folder should hold your classes, rosters, and attendance
records. **"Open Folder as Vault"** opens a folder picker (defaulting to a
`TapIn` folder in your home directory) — pick an empty folder for a fresh
start, or an existing TapIn vault to reconnect to its data. If the folder
you pick has files in it but none of TapIn's own, the app warns you before
starting a fresh vault there, in case you picked the wrong folder.

Closing the dialog without choosing defaults to that same `TapIn`
home-directory folder, so the app is never left unusable. The choice isn't
permanent: **Settings → Data Storage** reopens the same dialog any time.
Switching vaults doesn't move or delete anything — it just points the app
at a different folder, so the old vault stays exactly where it was if you
want to switch back. The name of the open vault is always visible at the
top of the sidebar (hover it for the full path).

## 2. The first time the app opens

There is no sign-in screen — the main window opens directly. On a brand-new
install, a short **"How to Use TapIn"** tour walks through Dashboard, My
Classes, Take Attendance, Statistics & Exports, and Data Storage, one screen
at a time — click **Next** to move through it, or **Skip** at any point. It
only shows once; you can bring it back any time from **Settings → Help →
Show Tutorial Again**. If this is instead the first time you're opening a
new *version* of the app, a **"What's New"** popup summarizes what changed
since the last version you used — that one appears once per version, then
won't show again until the next update.

## 3. The Dashboard

The Dashboard is the home screen when the app opens. It has:

- **A greeting** ("Good morning/afternoon/evening") along
  with today's date, so it's immediately obvious the app is showing
  up-to-date information.
- **Summary stat cards**: how many active classes you have, how many are
  pinned, the total count including archived ones, a running total of
  attended sessions across all your active classes with an overall
  attendance rate, and an archived-classes count.
- **Filter tabs**: "All Classes", "Active", "Pinned" — each shows a live
  count and switches which classes are listed below.
- **"Today's Classes"**: any class scheduled to meet on today's weekday,
  each with a one-click **Take Attendance** button that jumps straight into
  a live scanning session for that class.
- **"Recently Viewed"**: the last five classes you opened *this session*
  (this list resets every time you restart the app — it's not saved to
  disk).
- **Class cards**, grouped into Pinned / Active / Archived sections,
  showing each class's name, code, schedule, and attendance rate at a
  glance.
- **"+ Create New Class"** and **"Import Classes"** buttons (see §5 and
  §4.7).

If you have no classes at all yet, the dashboard shows a friendly empty-state
message instead of a blank page.

## 4. My Classes — the full class list

This is a more detailed, more controllable view of your classes than the
Dashboard's cards.

### 4.1 Sorting

A dropdown lets you sort by:
- **Class Name** (alphabetical)
- **Day** (by the earliest day of the week each class meets)
- **Custom Order** — switches the whole list into a drag-and-drop mode where
  you manually reorder classes by dragging rows; your order is remembered
  for next time.

Pinned classes always float to the top regardless of which sort mode you
pick.

### 4.2 Archived classes

A **"Show Archived"** checkbox switches the list to show only archived
classes (classes you've hidden from your main list, but not deleted — see
§4.5). From there, each archived class has an **Unarchive** button (bring it
back) and a **Delete Permanently** button (irreversible — this actually
erases the class and its attendance history).

### 4.3 Compact view

A **"Compact View"** checkbox tightens up the row spacing (hides the small
schedule caption under each class name) if you have a lot of classes and want
to see more at once without scrolling.

### 4.4 Each class row shows

- A colored accent bar (either a color you picked for that class, or one
  automatically generated from its class code, so classes are visually easy
  to tell apart)
- A checkbox (for bulk actions — see §4.6)
- The class name (click to open it)
- Its weekly schedule, in short form
- The class code as a small tag/pill
- Attendance rate as a percentage, color-coded: red if it's below the
  class's required attendance policy, yellow if it's close (within 10
  percentage points above), green if it's comfortably above
- A pin toggle (☆/★) to pin/unpin
- An expandable "Properties" panel with more detail (see §4.5)

### 4.5 The expandable "Properties" panel

Clicking the small arrow on a class row expands a panel showing: section,
full schedule, total sessions held, sessions attended, sessions missed, and
whether it's archived — plus two buttons:

- **Duplicate**: opens the class-creation wizard pre-filled with this
  class's schedule and settings (but not its roster — see §5.9), so you can
  quickly set up a new section without re-entering everything.
- **Archive / Unarchive**: hides the class from your main list without
  deleting anything. A confirmation dialog explains that its data is kept
  and it can be restored later. Archiving is meant for "I'm done teaching
  this for now" — not deletion.

### 4.6 Bulk actions and export

Checking the box on multiple rows lets you **"Archive Selected"** in one
action (with a confirmation showing how many classes will be archived).

**"Export Class List"** saves every class's key details (code, name,
section, attendance policy, late threshold, weeks, hours, schedule) to a CSV
file you choose — useful for record-keeping outside the app.

### 4.7 Importing classes from a spreadsheet

The **"Import Classes"** button lets you bulk-create classes from a
spreadsheet, provided it has exactly these column headers: `class_code`,
`class_name`, `section`, `attendance_policy`, `late_threshold`,
`total_weeks`, `total_hours`, `weekly_hours`. Note this only creates the
classes themselves — schedules and rosters aren't imported this way and need
to be added afterward per class. If any row fails (e.g. a duplicate class
code), you get a clear report of which ones failed and why, without losing
the ones that succeeded.

## 5. Creating, editing, and duplicating a class

Clicking **"+ Create New Class"** (or "Edit"/"Duplicate" from elsewhere in
the app) opens a step-by-step wizard.

### 5.1 Step 1 — Class Info

- Class code (e.g. "COMP101") — must be unique among your own classes (two
  different instructors *can* use the same code, since it's checked per
  instructor, not globally)
- Class name
- Section
- Attendance policy — the minimum attendance percentage required to pass
  (e.g. 70%)
- Late threshold — how many minutes after a session's start time a scan
  still counts, but as "Late" instead of "Present"
- Number of weeks, total hours, and weekly hours for the term
- An optional custom color for the class (via a color picker), or you can
  reset it back to an automatic color derived from the class code

### 5.2 Step 2 — Schedule

For each weekday (Monday through Friday — weekends aren't supported), you can
enable that day and add one or more time slots (start and end time). A class
can meet more than once on the same day if needed (e.g. a morning and an
afternoon section).

### 5.3 Step 3 — Roster (only when editing an existing class)

When creating a brand-new class, there's no roster step — instead you can
optionally upload a spreadsheet of students right there in Steps 1–2 (see
§5.4), since a new class doesn't have a saved ID yet to attach students
to individually.

When *editing* an existing class, a Roster step appears where you can add
students one at a time (student number + name) or remove a selected student
(which also deletes their attendance history for this class — you're warned
before this happens).

### 5.4 Uploading a roster spreadsheet (only when creating a new class)

You can load a `.csv`, `.xlsx`, `.xls`, or `.ods` file. This parser expects a
specific institutional template format (it skips the first 8 rows as a
header block, then reads specific columns for student number and name) — if
your spreadsheet doesn't match that shape, you may need to add students
individually instead, or reformat the file. If the same student number
appears twice, you're warned and asked whether to continue anyway.

### 5.5 Finishing up

The last step has a **"Create Class"** (or **"Save Changes"** when editing)
button. Every field is validated before submission — you can't submit with a
missing field, and numeric fields (attendance policy, hours, threshold,
weeks) must actually be valid numbers.

### 5.6 The "Danger Zone" (editing an existing class only)

At the bottom of the edit wizard:

- **Archive Class** — same as the archive action described in §4.5.
- **Delete Class Permanently** — this is deliberately hard to trigger by
  accident: you must type the exact class name to confirm before anything
  is deleted. This erases the class and every attendance record tied to it,
  with no way to undo it afterward.

## 6. The Class Detail page

Opening a class (by clicking its name anywhere in the app) brings you to its
detail page, which has several sections.

### 6.1 Class Details card

Shows the class name, code, section, attendance policy, late threshold,
number of weeks, total/weekly hours, and a visual grid of the weekly
schedule.

### 6.2 Roster & Attendance table

This is the main spreadsheet-style table: one row per student, with columns
for their student number, name, total hours not attended, total hours
attended, and then one additional column for every past session that's been
held.

Each session column shows a small colored checkbox rather than plain text:
- **Green, checked** = Present
- **Yellow, checked** = Late
- **Red, unchecked** = Absent

The "Not Attended Hours" column itself is also color-tinted per student —
green if they're comfortably fine, yellow once they're getting close to the
attendance-policy failure point, red once they've reached or passed it —
giving you an at-a-glance sense of who's at risk without reading numbers.

An **"At-Risk"** panel automatically lists any student who's crossed that
yellow/red threshold, sorted worst-first, so you don't have to scan the
whole table to notice.

A summary strip at the top shows your overall class attendance rate as both
a percentage and a progress bar.

**Double-clicking** a cell does one of two things depending on which column:
- Double-clicking a student's number, name, or hours cell opens a detail
  popup for that one student: the card bound to them, their full attendance
  history session by session, an "Export CSV" option to save just that
  history to a file, and a "Remove Card" button if they have a card (§6.9).
- Double-clicking one of the session (checkbox) columns opens a small dialog
  letting you **correct** that specific attendance record — useful if a scan
  was marked wrong during a live session and needs fixing afterward. You
  pick the corrected status (Present/Late/Absent) from a dropdown.

### 6.3 Class Notes

A free-text notes box tied to the class, with a **Save Notes** button. Use
this for anything you want to remember about the class that doesn't fit
anywhere else structured.

### 6.4 Merge Students

If a student accidentally got added to the roster twice (e.g. with two
different cards, or a typo'd name creating a duplicate entry), **"Merge
Students"** lets you pick which entry to keep and which to remove — all
attendance history from the removed entry is moved onto the kept one before
the duplicate is deleted, so no history is lost.

### 6.5 Copy Roster From Class

Rather than duplicating an entire class, **"Copy Roster From Class"** lets
you pull just the student list from one of your *other* classes (including
archived ones) into this one — useful when the same group of students is
also in a second class.

### 6.6 Export Roster

Saves just the student number + name list (not attendance history) to an
Excel or CSV file.

### 6.6a Export Attendance Grid

Saves the entire Roster & Attendance table exactly as shown on screen
(§6.2) — every student, every session, and their Present/Late/Absent
status — to an Excel or CSV file. Use this instead of Export Roster when
you need the full attendance picture, not just the class list: for
handing to a department office, archiving a semester's records outside
the app, or double-checking totals in a spreadsheet.

### 6.7 Edit Card Binding

This is the proper way to (re)assign a physical RFID card to a specific
student **outside** of a live attendance session. You'd use this when:

- A student loses their card and gets a new one
- A card was accidentally bound to the wrong student and needs correcting
- You're setting up cards ahead of time, before the first attendance session

How it works: pick the student from a list, and if they already have a card
registered, you're asked to confirm you want to replace it. Then the app
shows "Tap the new card on the reader now..." and waits (with a Cancel
button available) for you to physically tap the card. Once it reads a card,
it checks that this exact card isn't already registered to a *different*
student in the class (if it is, it refuses and tells you who has it, so you
don't accidentally give two students the same card) — then saves the new
binding.

This matters because of a related behavior in Take Attendance, explained
next: once *every* student in a class has a card, tapping an unrecognized
card during a live session is now treated as an **invalid card**, not an
invitation to register a new student (see §7.4). So after initial setup,
the card actions on this screen (§6.7–§6.9) are the only places to change
a card assignment.

Whichever reader you have set up is the one used here. If you are on the
WiFi reader (`.hardware_config.json`, see §11), the scan talks to it over
WiFi — you do not need a USB cable plugged in.

### 6.8 Add Student

**"Add Student"** adds one student to the roster and binds their card in
the same pass — the flow for a student standing at the reader right now.
(For a whole class list at once, use the roster import in the Edit Class
wizard instead.)

Fill in the student number and name, leave **"Scan a card for this student
now"** ticked, and press OK. The app adds the student, then asks you to
tap their card.

**The student is added before the reader is ever touched**, so anything
that goes wrong with the scan still leaves them on the roster:

| What happens | Result |
|---|---|
| You tap a fresh card | Student added, card bound |
| You press Cancel at the scan prompt | Student added, no card |
| The card already belongs to someone else | Student added, no card — the app names who has it |
| No reader is connected | Student added, no card |

In every one of those cases the message says the student is on the roster
without a card, and you can bind one later with Edit Card Binding. Nothing
is silently undone.

A student number already on this class's roster is refused before anything
is added — two rows sharing a number would give one card two students to
resolve to, and the reader only ever sends the card.

### 6.9 Removing a Card Binding

Double-click a student's **number or name** in the roster table to open
their detail view (§6.2). It shows the card currently bound to them, and
a red **"Remove Card"** button when there is one.

Use it when a card is lost or stolen. After you confirm:

- The card stops being recognised **in every class that student is
  enrolled in**, not just this one. That is the point — a card is bound to
  a person, so a lost card left working anywhere is a lost card that still
  works.
- **Attendance already recorded is not touched.** Removing a binding
  changes who can tap in from now on, nothing in the past.
- The card is freed, so it can be given to a different student afterwards.

The button only appears when the student actually has a card, so there is
never a confirmation for a delete that would do nothing.

## 7. Take Attendance — the live scanning session

Clicking **"Take Attendance"** on a class opens a dedicated screen for
recording that day's attendance.

### 7.1 Starting a session

The screen tries to connect to the RFID reader as soon as it opens. Click
**"Start Attendance"** to begin actively listening for card taps. If the
reader can't be found or connected to, you'll see a clear error message, but
manual entry (§7.6) still works even without hardware connected.

### 7.2 The scan status indicator

A status card at the top of the screen shows what's currently happening:
a plain dot while idle, a checkmark when a scan succeeds, an exclamation
mark for a warning (like "already recorded"), or an X for an error (like an
invalid card). Each new event also does a brief fade animation so it's
noticeable even if you're mostly watching students instead of the screen.

### 7.3 What happens when a recognized card is tapped

The app looks up the card against the roster. If it matches a student, their
attendance is recorded immediately: the app compares the current time
against the session's scheduled start time (plus the late threshold — see
§7.5) to decide automatically whether they're "Present" or "Late", and adds
a row to the on-screen table.

### 7.4 What happens when an unrecognized card is tapped

Two different things can happen, depending on the state of the roster:

- **If some students in this class still don't have a card assigned yet**,
  the app treats this as "a new student's first tap" — it asks you to pick
  which student this card belongs to from a list, and binds it going
  forward. If that student already had a *different* card bound, you're
  asked to confirm before overwriting it.
- **If every student already has a card assigned**, the app treats an
  unrecognized card as **invalid** — it does *not* offer to register it to
  anyone. This is deliberate: once your roster is fully set up, a stray
  unrecognized card almost certainly means a lost/foreign card or a bad
  read, not a new student who needs registering. The screen shows an error
  message naming the unrecognized card ID, and — if you have the RGB LED
  hardware described in Part 2 — the reader itself lights up red to give
  immediate physical feedback, without you needing to look at the screen at
  all.

If you need to bind a card after this point, use Edit Card Binding on the
class's roster page (§6.7) instead.

### 7.5 Late threshold override

By default, a scan counts as "Late" once more minutes have passed since the
session's scheduled start than the class's configured late threshold. You
can override this just for the current session by typing a different number
of minutes into a field on this screen — handy for a one-off situation (e.g.
"give everyone an extra 5 minutes today because of a fire drill") without
permanently changing the class's settings.

### 7.6 If the reader isn't working — manual entry options

- **Manual Attendance Entry**: pick a student from a dropdown, then pick
  their status (Present/Late/Absent) from another dropdown. This works
  identically to a card scan but doesn't require any hardware.
- **Mark All Present**: instantly marks every student who hasn't been
  recorded yet in this session as Present, all at once — useful for very
  small classes or quick sessions.
- **Mark Selected Absent**: opens a list of not-yet-recorded students where
  you can multi-select several at once and mark them all Absent in one
  step — for example, if you know in advance which students told you
  they'd be missing.
- **Undo Last Scan**: removes the single most recent entry, in case of a
  mis-tap or mis-click.

### 7.7 Session templates

If you always use the same time slot and late-threshold override for a
class, you can click **"Save as Template"** once, and the app will
automatically pre-fill those same settings every time you open Take
Attendance for that class going forward — saving you from re-selecting them
every session.

### 7.8 Submitting the session

Nothing is permanently saved until you click **"Submit Attendance"**. Up
until then, everything is "staged" — visible in the on-screen table, but not
yet written to the vault, so you can freely undo/correct mistakes.

If the save fails when you submit (e.g. the class's Excel workbook is open
in another program, or a disk error), your records aren't lost — they're
kept in a small local queue file and saved automatically the next time you
start the app. You'll see a clear "Saved For Retry" message explaining this
at the time.

If you try to leave the Take Attendance screen with unsubmitted records
still staged, the app stops you and asks to confirm before discarding them.

### 7.9 Exporting

**"Export to Excel"** on this screen exports the *already-submitted* session
for the currently selected date (not the in-progress unsubmitted table) —
useful for printing or emailing a record of a specific day's attendance.

## 8. Statistics

The Statistics page turns raw attendance records into charts.

- **Pick a class** from a dropdown to see its default view: a pie chart of
  Present/Late/Absent counts, next to a line chart showing the attendance
  rate trend over time, session by session.
- **Compare Classes**: a bar chart comparing overall attendance rate across
  every one of your classes side by side.
- **Attendance Heatmap**: for one class, a grid showing average attendance
  rate broken down by day-of-week and time slot — useful for spotting
  patterns like "Friday afternoon sessions always have worse attendance."
- **Export Chart**: saves whatever chart is currently on screen as an image
  (PNG) or PDF.
- **Export PDF Report**: generates a complete one-page PDF combining the
  class's key numbers, both charts, and the list of at-risk students — a
  ready-to-share summary document.

## 9. Settings

Settings has three tabs.

### 9.1 General

- **Language**: English or Turkish. Changing this requires restarting the
  app for it to fully take effect everywhere (some parts of the app are
  translated; a restart applies the change consistently).
- **Session timeout**: how many minutes of inactivity (no mouse movement,
  clicks, or key presses anywhere in the app) before you're automatically
  logged out, for security if you walk away from the computer. Options are
  5, 15, 30 minutes, or "Never."
- **Font size**: Small, Normal, Large, or Extra Large — applies instantly
  across the whole app, useful for readability on a projector or for
  accessibility.
- **Export/Import Settings**: saves your current preferences (language,
  timeout, list density, font size) to a file, or loads them back from one —
  handy for copying your setup to a different computer.
- **Data Storage**: shows which folder is the current vault, with a
  button that reopens the vault picker from first launch (§1.1) — switch
  to a different vault any time, without losing existing data in either
  folder.
- **Updates**: a **Check for New Versions** switch, **off by default**.
  Left off, TapIn opens no internet connection at all. Turned on, it asks
  github.com once each time it starts for the version number of the newest
  release, and adds a line to Notifications (§10) if yours is older. That
  request sends no student data, no vault path and no identifier — it reads
  the same public page anyone can open in a browser. Nothing is downloaded
  or installed either way; you decide whether to fetch the new installer.
- **Help**: a **Show Tutorial Again** button that reopens the "How to Use
  TapIn" tour from §2.4 any time you want a refresher.

## 10. Notifications

A bell icon shows a small number badge whenever there's something worth
knowing about — students who've become "at risk" of failing the attendance
policy, roster-import problems, or a report that offline-queued attendance
records were just successfully resubmitted. Clicking the bell shows the full
list, newest first, with a "Clear All" option. Notifications only exist for
the current app session — they're not saved between restarts, and there's no
email or text-message integration; it's purely an in-app feed.

## 11. Search

Typing into the search bar (or pressing Ctrl+F) and hitting Enter searches
across class names, class codes, and every roster student's name across all
your classes — so you can quickly jump to a class by remembering a student's
name, not just the class name itself.

## 12. Guardrails against accidents

Beyond the configurable inactivity timeout (§9.1, which simply closes the
app after N idle minutes), every action that could cause real damage —
deleting a class, merging students, permanently removing a roster entry —
requires an explicit confirmation step with the confirming button styled
red, and the most destructive one (deleting a class) requires you to type
the exact class name rather than just clicking "Yes," specifically so it's
very hard to trigger by an accidental click.

## 13. How and where your data is actually stored

Everything TapIn knows lives in the vault — the one folder you picked at
first launch (§1.1). There is no database and no server process; the vault
is plain files, understandable even outside the app.

**What's in the vault.**

- `README.txt` — a plain-language explanation of everything below, written
  automatically the first time the folder is used, so it's understandable
  even if someone opens the folder outside the app.
- `_index.json` and `_meta.json` — small internal bookkeeping files (which
  class maps to which file name, and a running student-ID counter). You
  shouldn't need to touch these.
- `classes/` — one `.json` file (class settings) and one `.xlsx` file
  (roster + attendance) per class, named after the class code (e.g.
  `comp101.xlsx`) rather than an unreadable internal ID. The `.xlsx` file
  can be opened directly in Excel any time you want to look at the raw
  data — its "Roster" sheet lists students and their RFID cards, and its
  "Attendance" sheet lists every recorded scan. Avoid editing it by hand
  while TapIn is running, since a save from the app could overwrite
  changes made outside it.
- `.lock` — marks the vault as "currently open," so a second copy of TapIn
  (or the same synced folder opened on two computers at once) can't
  silently race the first one's saves. It's removed automatically when
  TapIn closes normally; if TapIn ever says the vault is already open but
  nothing is actually running (e.g. after a crash), it's safe to delete
  this one file by hand.

**Moving or backing up your data.** Because it's all plain files, the whole
vault can be copied, zipped up, or moved like any other folder — that's
your backup. If you move it, tell TapIn its new location afterward from
**Settings → Data Storage** (§9.1), so it can find it again; moving the
folder without updating this setting just means TapIn creates a fresh,
empty vault in the old location instead of seeing your existing data.

If a submitted attendance session can't be saved right away (e.g. the
class's workbook is open in Excel), it's automatically kept in a small
queue file and saved the next time the app starts — you never have to
manually retry a failed submission.

---

# Part 2 — Hardware

This section explains the physical RFID card-reading hardware: what it is,
how it's wired, what its status LEDs mean, how its firmware behaves, and
exactly how it communicates with the software described in Part 1.

## 14. What the hardware is made of

Two small boards, connected together, plus three LEDs:

1. **An RC522 RFID reader module** — a small board with a Mifare RC522 chip
   on it, which can read the unique ID ("UID") off a 13.56MHz RFID card or
   keyfob when it's held close (a few centimeters) to the board's antenna
   coil.
2. **An ESP32 development board** — a small microcontroller board (in this
   project's case, a "DevKitC"-style ESP32-32 board with 4MB flash) that
   runs a small program (the "firmware") controlling the RC522 and talking
   to the computer over a USB cable.
3. **Three LEDs (green, yellow, red)**, each wired through its own
   resistor, used as a simple traffic-light-style status indicator so you
   can tell what's happening without needing to look at a screen.

The ESP32 connects to the computer with a standard USB cable, and the
computer sees it as a serial (COM-port-style) device — this project's board
uses a "CP2102 USB to UART Bridge Controller" chip internally to make that
work, which is why it shows up with that name if you look at connected
devices.

## 15. Wiring — RC522 to ESP32

The RC522 talks to the ESP32 over a protocol called SPI (a common
short-distance chip-to-chip communication standard). Here's exactly which
pin connects to which:

| RC522 pin  | ESP32 pin | Notes |
|------------|-----------|-------|
| 3.3V       | 3V3       | **Not 5V** — the RC522 chip is 3.3V-only and can be damaged by 5V |
| RST        | GPIO 21   | Reset line |
| GND        | GND       | Ground — shared reference, required |
| MISO       | GPIO 19   | Data: RC522 → ESP32 |
| MOSI       | GPIO 23   | Data: ESP32 → RC522 |
| SCK        | GPIO 18   | Clock signal |
| SDA (SS)   | GPIO 5    | Chip-select line |
| IRQ        | *(not connected)* | Not used by this project's firmware |

## 16. Wiring — the status LEDs

Each LED is wired the same way: its long leg (the **anode**, the `+` side)
goes through a resistor to a GPIO pin on the ESP32; its short leg (the
**cathode**, the `-` side) goes to GND.

| LED color | ESP32 pin | Resistor |
|-----------|-----------|----------|
| Green     | GPIO 4    | 220–330Ω |
| Yellow    | GPIO 16   | 220–330Ω |
| Red       | GPIO 17   | 220–330Ω |

The resistor is required on every LED — without it, too much current flows
through the LED and it can burn out or damage the GPIO pin. All three LEDs
can share a single ground connection back to the ESP32's GND pin (they don't
each need their own separate wire to GND — a shared ground rail on a
breadboard works fine, since the whole rail is one electrically connected
strip).

If an LED doesn't light up when you'd expect it to, it's almost always
simply plugged in backwards (reversed anode/cathode) — pulling it out and
flipping it around is completely safe and usually fixes it.

## 17. What each LED means

- **Yellow (solid, when nothing else is happening)**: idle — the reader is
  powered on and actively listening for a card, but nothing is currently in
  range.
- **Green**: a card was successfully read, *and* the software confirmed it
  belongs to a student in the currently active class — attendance was
  recorded.
- **Red**: one of two situations —
  1. A card was detected but the reader failed to complete a clean read of
     it (for example, it was pulled away too quickly, or there was a
     collision from two cards being too close together at once); or
  2. The card was read successfully, but the software rejected it as
     **invalid** — meaning it doesn't belong to any student in this class
     and every student already has a card assigned (see §7.4 in Part 1).

Every green or red result stays lit for about 0.7 seconds so it's actually
visible, rather than flashing by too quickly to notice. On every scan, the
LED briefly shows green first (confirming the physical read itself
succeeded), and only switches to red afterward if the software specifically
rejects the card — so seeing a very brief green flash before red is normal
and expected, not a malfunction.

## 18. How the firmware behaves, step by step

The firmware is a small program (an "Arduino sketch," written in C++) that
runs continuously on the ESP32. Its source file is
`firmware/rc522_serial_reader/rc522_serial_reader.ino` in this repository.
Here's what it does, in order, every time it's powered on:

1. **On startup**: it starts a serial connection to the computer at 9600
   baud (a specific communication speed both sides need to agree on), turns
   on the yellow "idle" LED, and initializes the RC522 chip.
2. **Self-test**: it reads a special "version" register from the RC522 chip
   over SPI. A real, correctly-wired RC522 always replies with `0x91` or
   `0x92`. If it instead reads `0x00` or `0xFF`, that's a strong sign the
   SPI wiring is wrong or loose — even if both boards' power lights are on
   (those only confirm 3.3V power is present, not that the data lines are
   actually working). This result is printed over the serial connection so
   it can be seen from a computer, and also determines nothing about the
   LEDs directly — it's just a diagnostic message for troubleshooting.
3. **Main loop, repeating forever**:
   - If no card is currently in range: show yellow, wait briefly, check
     again. (This also clears its memory of "the last card seen," which
     matters for step 5 below.)
   - If something is in range but the read doesn't complete cleanly: show
     red, and hold that for about 0.7 seconds before checking again.
   - If a card is read successfully: show green, and if this is a genuinely
     new tap (see step 5), send its unique ID to the computer as a line of
     text, then continue to step 4.
4. **Waiting for the computer's verdict**: after sending a new card's ID,
   the firmware waits up to about 0.7 seconds to see if the computer sends
   back the exact text `INVALID`. If it does, the LED switches from green
   to red for the remainder of that window. If nothing comes back in time
   (or anything other than exactly `INVALID` arrives), the LED just stays
   green. This is what lets the *software's* decision (recognized vs.
   unrecognized-and-rejected) control the *hardware's* red/green result,
   not just whether the RC522 could physically read the card.
5. **Not spamming the same card twice**: if the *exact same* card is still
   sitting on the reader continuously, the firmware won't send its ID again
   and again — it remembers the last card it saw and skips re-sending while
   that same card stays in place. But the moment the card is actually lifted
   off the reader (even briefly), that memory is cleared, so tapping the
   *same* card again later is always treated as a fresh, independent tap
   that gets its own fresh green-then-maybe-red evaluation. This distinction
   matters: without it, a card that was rejected once would incorrectly show
   green forever afterward, even on repeat taps.

The firmware is intentionally designed to work fine completely on its own —
if you power it up without the TapIn software running at all (for example,
just to test it), it will still light up green on every successful read,
since nothing ever tells it otherwise. The "wait for INVALID" behavior only
changes the outcome when the software is actually connected and actively
disagreeing with a read.

## 19. How the app and the hardware talk to each other

This is a simple one-line-at-a-time text protocol over the serial (USB)
connection, running at 9600 baud:

- **Hardware → software**: every time a new card is tapped, the ESP32 sends
  one line of plain text: the card's unique ID, written as hexadecimal
  digits with no spaces or separators (for example, `8A9BD106`), followed by
  a newline character.
- **Software → hardware**: if the software determines that ID doesn't
  belong to any student and the whole roster is already fully assigned, it
  writes back the exact text `INVALID` followed by a newline, within about
  0.7 seconds of receiving the card's ID. Otherwise, it sends nothing back
  at all for that scan.

That's the entire protocol — it's deliberately minimal. The software side of
this lives in `views/take_attendance_window.py` (specifically the
`check_rfid()` and `process_card()` methods) and `services/card_reader.py`;
the hardware side lives entirely in the one firmware file mentioned above.

### The two "backend" options in software

The software actually supports two different ways of receiving card scans,
selected via a small configuration file (`.hardware_config.json`) — not
currently exposed as a visible toggle in the app's own Settings screen:

- **`"serial"` (the default, and what this project's hardware uses)**: a
  wired USB connection exactly as described above.
- **`"esp8266"`**: an alternate, WiFi-based option where a different piece
  of hardware (an ESP8266 board) connects over the network instead of a USB
  cable, and sends card IDs the same way but over a TCP network connection
  instead of serial. This project's actual physical hardware (RC522 +
  ESP32) uses the serial option; the WiFi option exists in the software as a
  working alternative, but the ESP8266 hardware side of it isn't part of
  this specific build.

## 20. Compiling and flashing the firmware

You don't need the full Arduino IDE desktop application to work with this
firmware — everything can be done from the command line using a tool called
`arduino-cli`, and this project also includes a small wrapper script,
`arduino-flash`, that's already installed and makes the common commands
short and easy to remember from anywhere on the computer:

```bash
# Build only (check for compile errors, don't touch the board)
arduino-flash compile /path/to/firmware/rc522_serial_reader

# Build and upload to the board over USB
arduino-flash upload /path/to/firmware/rc522_serial_reader

# Watch what the board is printing over its serial connection
# (useful for troubleshooting — shows the self-test result and any
# card IDs / INVALID responses live)
arduino-flash monitor
```

If you're already sitting inside the firmware's own folder
(`firmware/rc522_serial_reader/`), you can drop the path argument entirely
and just run `arduino-flash upload`. The board defaults are `/dev/ttyUSB0`
for the port and 9600 baud for the monitor, both of which can be overridden
with `--port` and `--baud` flags if needed.

If the Arduino IDE (the graphical application) is used instead: the same
`.ino` file can simply be opened in it directly, with the board type set to
an ESP32 Dev Module and the correct USB port selected — but be sure the
Serial Monitor's own baud-rate dropdown is manually set to match (9600), as
it doesn't automatically pick this up from the code and defaults to a
different speed, which will show garbled text if left mismatched.

## 21. Testing the hardware without touching real hardware

This project also has a ready-to-use setup file
(`firmware/rc522_serial_reader/diagram.json`) for **Wokwi**, a free
browser-based circuit simulator that can run this exact firmware against a
fully simulated ESP32, RC522 reader, and all three LEDs — including a
clickable "scan" button on the simulated RC522 to test a virtual card tap —
without needing any of the physical parts connected, or even present. This
is useful for confirming firmware behavior changes are correct before
touching the real board, or for a teacher/reviewer to see the whole thing
working without needing physical hardware in front of them at all.

## 22. Troubleshooting checklist

- **Board doesn't show up at all when plugged in**: try a different USB
  cable first — some cables only carry power, not data, and those will show
  zero response whatsoever, which looks identical to "nothing plugged in"
  from the computer's point of view. A working data cable will make the
  board appear as a new device immediately.
- **Both boards' power lights are on, but nothing seems to work**: a lit
  power LED only confirms 3.3V is reaching the board — it says nothing
  about whether the SPI data wiring (MISO/MOSI/SCK/SDA/RST) is actually
  correct. Check the self-test message described in §18 step 2 — if it
  reports `0x00` or `0xFF` instead of `0x91`/`0x92`, the wiring needs
  rechecking, most commonly a loose breadboard connection.
- **Text looks garbled when watching the board's output**: almost always a
  baud-rate mismatch — make sure whatever you're using to view the output
  (Arduino IDE's Serial Monitor, or `arduino-flash monitor`) is set to 9600,
  matching the firmware. A short burst of odd characters right when the
  board powers on or resets is normal (it's the board's own low-level boot
  message, sent at a different fixed speed before the firmware itself takes
  over) and can be ignored.
- **The same card sometimes shows green, sometimes doesn't get a red result
  when it should be rejected**: make sure the firmware is up to date — this
  exact behavior was a bug that's since been fixed (see §18 step 5); if
  it's still happening, the board may be running an older firmware version
  and should be reflashed.
- **Tapping a card seems to register against the wrong class entirely**:
  only one class's Take Attendance session can actively be listening to the
  hardware at a time — if you had a different class's Take Attendance
  screen open earlier and didn't fully close it, the app now automatically
  stops that older session's connection the moment a new one takes over, so
  this shouldn't happen with current versions of the software; if it does,
  it likely indicates the software needs updating.
