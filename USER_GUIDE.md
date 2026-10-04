**TapIn user guide**, for TapIn 3

This guide shows how to use TapIn: classes, students, attendance, statistics, settings and the card reader. It is written for teachers, so you need no technical skills. The last chapter is for anyone who builds the reader.

The same guide is inside the app, under Settings → Help & about → User guide.

# Start here

### What TapIn is

TapIn helps you take attendance for the classes you teach and keep a clean record of it.

- You can take attendance by hand, or with an RFID card reader: students tap a card and are marked as they go.
- Everything stays on your computer. There is no account, no login and no server.
- Your data lives in one folder that you choose, as ordinary `.json` and Excel (`.xlsx`) files. You can back it up or move it like any other folder.

The card reader is optional. Every screen works without it.

### Install

| System | File | Notes |
|---|---|---|
| Windows 10 or 11, 64-bit | `TapIn-x.y.z-setup.exe` | Installs for your user. No administrator password is needed. Windows SmartScreen may warn on the first run because the installer is not code-signed: choose More info, then Run anyway. |
| macOS, Apple Silicon (M1 or newer) | `TapIn-x.y.z-macos.zip` | Unzip it, move TapIn to Applications, open it. macOS blocks the first launch because the app is not signed by Apple: open System Settings → Privacy & Security and choose Open Anyway. There is no Intel build yet. |
| Debian or Ubuntu, 64-bit | `tapin_x.y.z_amd64.deb` | Run `sudo apt install ./tapin_*_amd64.deb`. This adds a menu entry and a `tapin` command. |

TapIn 3 opens data folders made by TapIn 2, so an upgrade keeps your classes.

### Your first five minutes

1. Start TapIn and choose where to keep your data (see Your data folder).
2. Create a class: press Ctrl+N, or press New class. Give it a code, a name and a schedule.
3. Add students: type them in, or upload your university's student list.
4. Open the class and press Take attendance. Mark the students, then press Submit.
5. Open Statistics to see how the class is doing.

### The first time TapIn opens

A short tour walks through the main screens. Press Next to move on, or Skip at any time. You can see it again from Settings → Help & about → Show the tour.

After an update, a "What's new" box appears once for that version.

# Your data folder

Your classes, students and attendance live in one folder, which TapIn calls the data folder. Nothing is stored anywhere else.

### The first time

TapIn asks "Where should TapIn keep your data?"

- **Choose a folder** opens a folder picker. Pick an empty folder to start fresh, or an existing TapIn data folder to carry on with its classes.
- **Use ~/TapIn** makes a folder called `TapIn` inside your home folder.

### Every time after that

TapIn opens the folder you used last, and does not ask. You see the launch screen only when no folder is saved yet, or when the saved folder cannot be opened.

### The launch screen

The launch screen is called "Open a data folder". It lists the folders TapIn has opened before.

- A folder that has gone is marked "folder not found".
- A folder that is open somewhere else is marked "In use".
- Pick a folder and press Open, or press Choose another folder…, or Quit.

### When a folder will not open

| What TapIn says | What to do |
|---|---|
| This folder is open on another computer | Close TapIn on that computer first, then try again. Two computers must not write to the same folder. If that computer is off or has crashed, delete the file called `.lock` in the data folder. |
| This folder is already open in another TapIn on this computer | Close the other copy, then try again. TapIn shows its process number. |
| That folder isn't there any more | If it is on a USB stick or a network drive, plug it in or connect, then try again. |
| TapIn can't write to that folder | Choose a folder of your own, or ask for permission to write to it. |

### Switching to another folder

Open Settings → Data and press Choose folder… under "Switch data folder". You can also choose Switch data folder… in the folder menu at the top of the sidebar, or in the command palette (Ctrl+K); both take you to that place. Nothing in the folder you leave is moved or deleted, so you can switch back at any time.

If you are in the middle of taking attendance, TapIn warns you that the scans you have not submitted would be lost.

The top of the sidebar shows the name of the open folder. Click it for Show in folder, Switch data folder… and Data settings.

### Keeping the folder safe

- The files are not encrypted. Anyone who can open the folder can read the students' names, numbers and attendance. Keep the folder where only you can reach it.
- Do not open the same folder on two computers at the same time, and take extra care if it sits in a synced folder such as OneDrive, Dropbox or iCloud. TapIn refuses to open a folder that another computer has open.

# Getting around

### The sidebar and the top bar

The sidebar has Dashboard, Classes, Statistics, History and Settings, and a Quit button. A button on it collapses it to icons.

The top bar has the search box and the bell for notifications.

### Keyboard shortcuts

On a Mac, use ⌘ in place of Ctrl.

| Keys | What it does |
|---|---|
| Ctrl+1 | Dashboard |
| Ctrl+2 | Classes |
| Ctrl+3 | Statistics |
| Ctrl+4 | Settings |
| Ctrl+N | New class |
| Ctrl+F | Go to the search box |
| Ctrl+K | Command palette: type a class name or a command |

History has no shortcut. The keys for Take attendance are listed in that chapter.

### Search

Type in the search box and press Enter. TapIn looks at class codes, class names, student names and student numbers. Results can show Active or Archived classes, and each result says what matched.

### Notifications

The bell shows a number when there is news. It lists:

- Students who have become at risk in a class.
- Attendance that could not be saved at the time and has now been saved.
- A student list file that TapIn could not read.
- A new TapIn version, if you turned update checks on.

The list lasts only while TapIn is open. Press Clear all to empty it.

### Leaving TapIn

Press Quit in the sidebar, or close the window. If you have scans that are not submitted, TapIn asks first.

TapIn can also close itself after a while without use. This protects a shared computer. Shortly before it closes, a box asks "Still there?" and counts down. Press Stay open to carry on. TapIn never closes by itself while scans are waiting to be submitted. You choose the time in Settings → General.

# Dashboard

The Dashboard is the home screen.

- **A greeting and today's date.**
- **New class** and **Import classes** buttons.
- **Four tiles:** Active classes (with how many are pinned and archived), Attendance rate across your active classes, Records attended (present and late), and Students at risk. Press Review on that tile to see who they are.
- **Today:** every class that meets on today's weekday. Each shows "Not taken yet" or "Taken", with how many students are recorded. A class that is on right now has a Now tag. Press Take attendance to start, or Open to see the class. A class with no students offers Add students.
- **Recently viewed:** the last five classes you opened. The list starts empty again each time TapIn starts.
- **Your classes:** cards in three groups, Pinned, Active and Archived. Use All, Active or Pinned to filter. Each card has a pin and a menu with Open, Take attendance, Statistics, Details, Duplicate and Archive.

With no classes yet, the Dashboard shows a short message and a button to make your first one.

# Classes

The Classes page lists all your classes in one place.

### The list

- **Active or Archived** switches between the two lists.
- **Sort by** Class code, Class name, Day, or Custom order.
- **Compact view** shows each class on one line.
- Each row shows the class name, section, schedule, and its attendance rate. The rate is red when it is under the class's policy, amber when it is within 10 points above the policy, and green otherwise.
- The pin keeps a class at the top of the list.
- Tick several rows to Archive them together.

### Custom order

Drag the handle of a row to move it. To use the keyboard instead, press Space or Enter on the handle to pick the class up, use the arrow keys to move it, Space or Enter to drop it, and Escape to cancel. Pinned classes always stay on top. Archived classes are sorted by class code.

### Archiving and deleting

**Archive** moves a class to the Archived list. Its students and attendance are kept. Use it when you have finished teaching a class for now. You can bring it back with Unarchive.

**Delete permanently** erases the class's settings, students and all its attendance. It cannot be undone. To stop accidents, TapIn asks you to type the class name before it deletes anything. You find it in the Archived list, in the row menu, and in the class editor's Danger zone.

### Import classes

You can create many classes at once from a spreadsheet (`.xlsx`, `.xls` or `.csv`). The first row must name these columns:

- `class_code`
- `class_name`
- `section`
- `attendance_policy`
- `late_threshold`
- `total_weeks`
- `total_hours`
- `weekly_hours`

A `term` column is optional. Other columns are ignored. The file made by Export list also works, so you can export, edit and import again.

TapIn first shows a preview. Every row says Ready or "Can't be imported" and gives the reason. Rows with problems are skipped, and the rest are created. Fix the file and import it again to add the skipped ones.

Only the classes are imported. Schedules and students are not, so set each class's days and times in its editor, then add its students.

### Export list

Export list saves your classes to a `.csv` file: code, name, section, policy, late threshold, weeks, hours and schedule. It exports the list you are looking at, Active or Archived.

### The class editor

New class, Edit class and Duplicate all open the same editor. It has four steps: Details, Schedule, Students, and Colour & review. The step bar at the top shows where you are.

**Details**

| Field | Meaning |
|---|---|
| Class code | A short code such as COMP101. It cannot be changed after the class is created. |
| Class name | The full name. |
| Section | The section letter or number. |
| Term | Optional, for example Fall 2026. Two classes can share a code if their terms differ. |
| Attendance policy | The lowest attendance percentage a student needs, from 0 to 100. |
| Late after | How many minutes after a session starts a student still counts as Present. A whole number, 0 or more. |
| Weeks | How many weeks the class runs. A whole number, 1 or more. |
| Total hours | The hours for the whole class. Above 0. |
| Weekly hours | The hours in a normal week. Above 0. |

A class code must be unique for its term. If it is not, TapIn says so under the field.

**Schedule**

Switch on each day the class meets, from Monday to Sunday, then set the times. Press Add time to add a second slot on the same day. An end time must be after its start time, and two slots on one day cannot overlap. You can leave the schedule empty and add it later.

**Students**

Add students one at a time with their student number and their name and surname, or press Upload student list…. TapIn reads three kinds of file:

- Your university's student list report, exactly as the university gives it.
- A roster exported from TapIn.
- Any sheet whose first two columns are headed "Student Number" and "Name Surname".

Before anything is added, TapIn shows a preview: who will be added, who is already on the roster and is skipped, and any student number that appears more than once (only the first row of each is used).

- When you create a new class, the students are saved together with the class when you press Create class.
- When you edit an existing class, a change to the students is saved right away. Removing a student also deletes their attendance in this class, and TapIn warns you first.

**Colour & review**

Pick Automatic, one of nine colours, or Custom colour…. A review panel lists everything you set, with Edit buttons to jump back to a step. Press Create class, or Save changes when editing.

**Duplicate**

Duplicate copies a class's details, term, schedule and colour into the editor. You must give the copy its own code. It starts with no students.

**Danger zone**

When you edit a class, the Danger zone at the bottom has Archive class (or Restore class) and Delete permanently….

If you leave the editor with changes that are not saved, TapIn asks whether to discard them.

# A class page

Open a class by pressing its name anywhere in the app.

### The top of the page

- A back button to Classes, and the class name and section.
- **Edit class** and **Take attendance** buttons, and a **More** menu.
- A strip with the class's settings: Policy, Late after, Weeks, Total hours and Weekly hours.
- The class attendance rate, as a bar and as "attended / total sessions". It appears after the first session.

### Students at risk

When students are getting close to the limit, a panel says how many are at risk and lists them, worst first. Press Show to open the list.

The limit is worked out from the class's Total hours and its Attendance policy:

```
failing limit = Total hours × (100 − policy) ÷ 100, rounded up
at risk from  = half of the limit
```

TapIn counts each missed session as one against this limit. For example, with 42 total hours and a 70% policy, the limit is 13 missed sessions, and a student is at risk from 7.

In the table, the Missed number is coloured: green is safe, amber is at risk, red is failing risk.

### The roster and attendance table

One row for each student. The columns are Number, Name, Missed, Attended, and then one column for each session held. A session cell shows a tick for Present, a clock for Late, a cross for Absent, and is empty when nothing was recorded.

To correct a record, double-click its cell, or select it and press Enter. Choose Present, Late or Absent and press Save. Choosing Absent removes the record. That session still counts as missed.

Right-click a cell, or press Shift+F10, for a menu with Student details and Correct attendance….

You can move around the table with the arrow keys, Home and End, and PageUp and PageDown.

### Student details

Student details shows the student's card (or "No card"), how many sessions they attended and missed, their rate, and every session they were in. Press Export CSV to save that history. Press Remove card if the card is lost: it then stops working in every class that student is in. Attendance already recorded is not touched.

### Schedule and notes

The Schedule card shows the weekly times, with a button to add them if there are none.

Notes is a free text box for the class: room changes, exam dates, anything to remember. It saves as you type.

### The More menu

| Item | What it does |
|---|---|
| Add student… | Adds one student, and can scan their card straight away. |
| Edit card… | Gives a student a new card, or replaces a lost one. |
| Merge students… | Joins two entries for the same person. |
| Copy roster from another class… | Brings the students of another class into this one. |
| Export roster… | Saves the student numbers and names as an Excel file. |
| Export attendance grid… | Saves the whole table, every student and every session, as an Excel file. |
| Export certificate… | Makes a one-page PDF for one student. |
| Refresh | Reads the class files again. |

**Add student.** Type the number and name. Leave "Scan their card now" ticked and press Add student; TapIn then asks you to tap the card on the reader. The student is added first, so if the scan fails they stay on the roster without a card. You can add the card later with Edit card. A student number that is already on the roster is refused. If the card belongs to someone else, TapIn tells you who.

**Edit card.** Pick the student, press Scan card, then tap the new card. If the student already has a card, the button says Replace card and TapIn asks you to confirm, because the old card stops working in every class once the new one is saved.

**Merge students.** For a person who is on the roster twice. Choose the entry to keep and the entry to remove. All the attendance of the removed entry moves to the kept one. If both have a record for the same session, the record of the kept entry stays. The removed entry is then deleted.

**Copy roster.** Choose another class, including an archived one. TapIn shows how many students will be copied and skips anyone already on this roster.

**Export certificate.** Choose a student and see a preview. The certificate says the student was enrolled in the class, how many sessions they attended out of the total with their rate, and whether they meet the attendance policy. Press Save PDF… to keep it.

# Take attendance

Open a class and press Take attendance. This screen records one session.

### Set up the session

- **Session date.** It starts on today. The calendar marks days that already have a saved session.
- **Time slot.** The slots the class has on that weekday. If there are none, the screen says "No session" for that day. Pick another date, or press Edit class: it opens the class page with the schedule step of the editor ready, and when you come back to Take attendance the new slot is there.
- **Time remaining** counts down to the end of the slot.
- **Late after.** A student who is recorded more than this many minutes after the slot starts is marked Late. Type another number to change it for this session only. Press Save as default to keep the time slot and the late value for next time.
- **The reader.** A small tag shows USB, Wi-Fi, Bluetooth or No reader.

If the date is not today, TapIn tells you. On another day the clock time means nothing, so every card tap counts as Present.

### Taking attendance with the reader

1. Press **Start scanning**, or press Space.
2. Students tap their cards. Each one appears in the list as it happens.
3. Press **Stop scanning** (or Space) to pause. Pressing Start again carries on.

If the reader is not found, the screen says so, and Set up reader opens the reader settings. You can still take attendance by hand.

### What happens when a card is tapped

| The card… | What happens |
|---|---|
| Belongs to a student in this class | The student is recorded as Present or Late. The reader shows their number and name, and its green light comes on. |
| Belongs to a student who is already recorded | Nothing new is recorded. TapIn says they were already recorded. |
| Belongs to a student who is not in this class | TapIn refuses it and says who the card belongs to and in which class. The reader's red light comes on and it beeps. |
| Is registered to a student in another class, and that student is also in this class | TapIn recognises the card, links it to this class, and records the student. A card works in every class its owner is in. |
| Is not registered to anyone, and some students here have no card | The "Register this card" box opens. Choose the student and press Register and record. Press Not now to skip it. |
| Is not registered, and every student here already has a card | TapIn refuses it as an unknown card. The reader goes red and beeps. |

If you register a card to a student who already has a different card, TapIn asks you to confirm the replacement first. The new card replaces the old one in every class.

While a box is open, further taps wait in line ("2 more taps are waiting") and run afterwards. If the day has no session, or the class has no students, TapIn says so and records nothing.

### Taking attendance by hand

- **Manual entry** (or press M): choose a student and a status, then press Record.
- **Mark all present:** marks everyone who is not recorded yet as Present.
- **Mark absent…:** tick the students who are not here, then confirm. Each one gets an Absent record.
- **Undo** (or Ctrl+Z): removes the most recent record.

The roster panel shows who is recorded and who is still waiting. You can filter it by All, Waiting or Recorded. If the class has no students yet, it offers Add students, which opens the class page with the students step of the editor ready.

### Keys on this screen

| Keys | What it does |
|---|---|
| Space | Start or stop scanning |
| M | Open Manual entry |
| Ctrl+Z | Undo the last record |
| Ctrl+Enter | Submit |

### Submitting

Nothing is saved until you press **Submit**. Until then, the records are only on the screen, so you can undo or fix mistakes. The button shows how many records are ready.

If the class's Excel file is open in another program, or the disk has a problem, TapIn cannot save it. Your records are not lost: TapIn keeps them safely in the data folder and saves them by itself the next time it opens. A box called "Attendance saved for later" tells you so.

**Export submitted** saves the sessions already submitted for the chosen date as an Excel file. It does not include records that are still waiting.

### If something goes wrong during a session

- **You try to leave with unsubmitted records.** TapIn asks "Leave without submitting?". Press Stay to go back.
- **TapIn closes before you submit.** The next time you open that class's session, a box asks "Restore unsubmitted scans?". Restore brings them back. Saved drafts older than a week are deleted.
- **The reader disconnects.** The screen says "Reader disconnected" and keeps your records. Fix the connection and press Reconnect.

# The card reader

The reader is a small box with an RFID card sensor, a screen, coloured lights and a buzzer. Students tap a card on it. It is optional: you can always take attendance by hand.

A card belongs to one student, in every class that student is in. A student registers their card once.

### Three ways to connect

| | USB cable | Wi-Fi | Bluetooth |
|---|---|---|---|
| What you do | Plug it in | Join the reader's own Wi-Fi network | Pair it, then pick its port |
| Where the reader sits | Next to the computer | Anywhere, on a power bank | Anywhere, on a power bank |
| Set-up in TapIn | None | Test connection | Choose the port, Test connection |

Choose the way in Settings → Card reader → Connection. USB and Wi-Fi are the ways to rely on. Bluetooth is new in TapIn 3 and has had less testing than the other two: it has been tried with a real reader on Linux, but not yet on Windows or macOS, so its steps may change. Try it before class, not during.

### USB cable

Nothing to set up. Plug the reader in with a USB cable. TapIn finds it when you open Take attendance. In Settings → Card reader, the USB panel shows what it found, and Check again looks once more.

- Use a cable that carries data. Some cables only charge, and they look the same.
- On Linux, your user must be in the `dialout` group to use a serial port. Run `sudo usermod -aG dialout $USER`, then log out and in again.
- The reader's board usually has a CP2102 or a CH340 USB chip. Most systems already know them. If yours does not show the reader, install the driver from the chip's maker.

### Wi-Fi

The reader makes its own Wi-Fi network. It does not join yours.

1. **Power the reader.** Plug it into a power bank or a USB charger. The white light comes on and the screen says "Ready to scan". It does not have to be plugged into the computer. That is the point of Wi-Fi mode.
2. **Join the reader's network.** In your computer's Wi-Fi menu, connect to `TapIn-Reader` with the password `tapin12345`. This is the step people miss: until you are on that network, the computer cannot reach the reader.
3. **Expect "no internet".** Your computer warns that this network has no internet. That is normal. The reader is not a router. If your computer keeps jumping back to your usual Wi-Fi, turn off "connect automatically" for that network while you take attendance.
4. **Test the connection.** In Settings → Card reader, press Test connection. TapIn tries to reach the reader at `192.168.4.1` on port `8888`. Do this before class.
5. **Take attendance** as usual.

The address and the port are already filled in. Change them only if you changed them in the reader's firmware.

### Bluetooth

1. **Pair the reader.** Switch it on. Its screen says "Waiting for app". Open your computer's Bluetooth settings and pair with `TapIn-Reader`. There is no code to type. If your computer asks you to confirm a number, confirm it: the reader has no screen to compare it with.
2. **Find the port.** Pairing gives the reader a serial port, and this depends on your system.

| System | What to do |
|---|---|
| Windows | Windows makes two COM ports. Open Settings → Bluetooth & devices → More Bluetooth settings → COM Ports and use the one marked Outgoing. |
| macOS | The port appears by itself. Choose `/dev/cu.TapIn-Reader`, not the `/dev/tty` one. |
| Linux | No port appears by itself. Run `sudo rfcomm bind 0 <address>` once, where the address is the reader's Bluetooth address (`bluetoothctl devices` shows it). Then `/dev/rfcomm0` appears. You must do it again after a restart. |

3. **Choose the port and test it.** In Settings → Card reader → Bluetooth, pick the port and press Test connection. Look again refreshes the list.

The reader works over Bluetooth Classic, which only the original ESP32 board has.

### What the reader shows

| What you see | What it means |
|---|---|
| White light | The reader has power. |
| Yellow light, "Ready to scan" | Listening for a card. |
| "Checking card" | The card was read. The reader is waiting for TapIn's answer. |
| Green light, a number and a name | The student was recorded. |
| Red light, "Invalid card", three beeps | The card was refused. |
| Red light, "Read error" | The card was moved too fast. Tap it again. |
| "Waiting for app" | The Wi-Fi or Bluetooth reader is on, but TapIn is not connected to it yet. |

The reader's screen has only 16 letters on each line and no Turkish letters, so TapIn shows names without accents there. The student's name in TapIn itself is not changed.

Without TapIn, the reader still reads cards, but it cannot say whose card it is.

# Statistics and history

### Statistics

Open Statistics to see how your classes are doing. At the top you choose what to show:

- **Overview:** one class. Choose the class from the list.
- **Compare classes:** every class side by side.
- **Heatmap:** one class, by weekday and time.

Archived classes are left out unless you turn on **Include archived**. Open class jumps to the class page.

**Overview** has:

- Tiles for the Present, Late and Absent records, and for the Attendance rate next to the class's policy. Absent counts students who were expected but not recorded as present or late.
- A **Breakdown** ring showing the split.
- An **Attendance trend** line, session by session, with the policy as a line to compare against. A short sentence under it says whether attendance rose or fell.
- The **At-risk students** list, with the rule used.

**Compare classes** shows one bar for each class that has attendance, sorted by class code. A class gets a bar after its first session.

**Heatmap** shows the average attendance for each weekday and time slot. It helps you spot patterns, such as "Friday afternoons are always low".

Each chart also has a written summary and a data table, for screen readers.

**Export chart** saves the view you are looking at as a PNG or SVG picture. Choose Print-friendly light for a version with a white background.

**Download report** saves a PDF report for the class. It shows the class's policy, late threshold, section, term, number of sessions and number of students, then the attendance rate, the breakdown, the trend, and a table of the at-risk students with how many sessions each has missed. It needs a class that has attendance.

### History

History is a calendar. A day with a recorded session is marked. Press a day to see the sessions on it, across all your active classes. Use the arrows to change month, Today to return to now, and "Go to the latest session" to jump to the last one. The page also says how many sessions the month has, and on how many days.

History shows active classes only. Archived classes are not shown.

# Settings

Settings has five sections.

### General

| Setting | What it does |
|---|---|
| Language | English or Turkish. Changes every screen at once. |
| Interface size | Small (90%), Normal (100%), Large (115%) or Extra large (130%). Makes text, buttons and lists larger or smaller together. |
| Theme | Dark, Light or System. System follows your computer and changes while TapIn is open. |
| Reduce transparency | Solid panels instead of glass, which can make text easier to read. |
| Compact class list | Shows each class on one line in Classes. |
| Close TapIn after inactivity | 5, 15 or 30 minutes, or Never. |

### Data

| Setting | What it does |
|---|---|
| Data folder | Shows the open folder. Copy path copies it. Show in folder opens it. |
| Switch data folder | Opens another folder of classes. Nothing is moved or deleted. |
| Backups | When TapIn opens a folder whose files have changed, it saves a zip copy in the `.backups` folder inside it. The newest 5 are kept. Open backups folder shows them. |
| Settings file | Export settings saves your language, interface size, class list and inactivity choices into a file, to load on another computer with Import settings. The file is called `app_settings.json`. |

### Card reader

Connection (USB cable, Wi-Fi or Bluetooth) and the set-up for each. See The card reader.

### Updates

**Check for new versions** is off. See Privacy. When it is on, press Check now at any time. If a newer TapIn exists, Open download page takes you to it. TapIn never downloads or installs anything by itself.

### Help & about

Show the tour, User guide, FAQ, and Privacy & your data. It also shows your TapIn version.

# Your files and backups

### What is in the data folder

```
your-data-folder/
├─ README.txt                 a plain explanation of this folder
├─ classes/
│  ├─ comp101.json            the class's settings and schedule
│  └─ comp101.xlsx            its students and attendance
├─ _index.json                which class is which file
├─ _meta.json                 a counter TapIn uses for its own student IDs
├─ _class_order.json          your custom class order
├─ _session_templates.json    saved Take attendance defaults
├─ _offline_queue.json        attendance waiting to be saved
├─ .lock                      says the folder is open
└─ .backups/                  zip copies, the newest 5
```

You can open each class's `.xlsx` file in Excel at any time. Its Roster sheet lists the students and their cards, and its Attendance sheet lists every record. Do not edit it while TapIn is running, because TapIn could overwrite your changes, and a file left open in Excel stops TapIn from saving.

### Backups

Copy the folder. That is the whole backup: there is no database or hidden state anywhere else. TapIn also makes its own zip copies in `.backups` (see Settings). To restore one, unzip it somewhere and point TapIn at that folder.

### Moving the folder

Copy or move the folder, then open it from Settings → Data → Switch data folder. There is no licence key, no activation and no link to one computer.

### Where TapIn keeps its own settings

Small settings files hold your language, your chosen data folder, your reader set-up and your recent folders. They hold no student data.

| System | Folder |
|---|---|
| Windows | `%APPDATA%\TapIn` |
| macOS | `~/Library/Application Support/TapIn` |
| Linux | `~/.local/share/TapIn` |

### Privacy

- TapIn has no accounts, no cloud service and no analytics. It sends no usage data and no crash reports.
- Out of the box, the only network connection it makes is to your own card reader, on the reader's own network.
- The one exception is the Check for new versions switch, and it is off. If you turn it on, TapIn asks github.com once at startup for the newest version number. The request carries no student data, no folder path and no identifier.
- TapIn stores each student's number and name, their attendance, and the ID of their card. It asks for nothing else: no email addresses, no photographs, no grades.
- Attendance records are personal data about identifiable students. Your university probably has rules for handling them. TapIn keeps the data on your computer, and keeping it lawfully is up to you.
- To delete data, delete a class, or delete the data folder. There is no other copy.

# Fixing problems

| Problem | What to try |
|---|---|
| "No card reader found" | Check the cable carries data, try another USB port, and press Check again in Settings → Card reader. On Linux, make sure you are in the `dialout` group (see The card reader). You can still take attendance by hand. |
| Wi-Fi test says the computer is not on the reader's network | Join the `TapIn-Reader` network (password `tapin12345`) and test again. The "no internet" warning is expected. |
| Wi-Fi test says nothing is answering | The reader is probably still starting, or it is running the USB firmware instead of the Wi-Fi one. Wait until its screen says "Ready to scan", then test again. |
| Bluetooth test says the port is not on this computer | The reader may have been unpaired. On Linux, `rfcomm bind` is lost when the computer restarts. Pair it again, then pick the port. |
| Bluetooth test cannot open the port | Switch the reader on, bring it within a few metres, and close any other program that uses it. Its screen should say "Waiting for app". |
| "Reader disconnected" during a session | Your records are kept. Fix the connection, then press Reconnect. |
| A card is refused | Read the message. It usually names the real owner, often a student handing over a friend's card. |
| "This folder is open on another computer" | Close TapIn there first. If that computer is off or crashed, delete the `.lock` file in the data folder. |
| "Attendance saved for later" | The class's Excel file is probably open in another program. Close it. TapIn saves the records the next time it opens. |
| "Couldn't load the roster" | Close any program that has the class's `.xlsx` file open, then try again. |
| A class import skips rows | Each skipped row says why. Fix the file and import just those rows. |
| Students marked Late when they were on time | Check the time slot and the "Late after" minutes on the Take attendance screen, and the clock on your computer. |
| TapIn closed by itself | The inactivity timer did it. Change it in Settings → General. |
| Windows SmartScreen warns about the installer | The installer is not code-signed. Choose More info, then Run anyway. |
| macOS will not open TapIn | Open System Settings → Privacy & Security and choose Open Anyway. |

# Building the reader

This chapter is for the person who builds the reader. Teachers do not need it.

### The parts

- An **ESP32 DevKit V1** board (30 pins). Only the original ESP32 can do Bluetooth.
- An **RC522** RFID module, which reads 13.56 MHz cards.
- A **16×2 LCD** with an I²C backpack (a PCF8574 board). It must be the backpack type, not a bare 6-wire screen.
- **Four LEDs** (green, yellow, red, white), each with its own 220 Ω resistor.
- A **buzzer** module.
- For Wi-Fi or Bluetooth: a power bank, or a battery pack, and a latching on/off switch in the battery's plus wire. A push button that springs back will not work.

### Wiring

| ESP32 pin | GPIO | Goes to |
|---|---|---|
| D5 | 5 | RC522 SDA (SS) |
| D18 | 18 | RC522 SCK |
| D23 | 23 | RC522 MOSI |
| D19 | 19 | RC522 MISO |
| D21 | 21 | RC522 RST |
| D32 | 32 | LCD SDA |
| D22 | 22 | LCD SCL |
| D4 | 4 | Green LED, through 220 Ω |
| RX2 | 16 | Yellow LED, through 220 Ω |
| TX2 | 17 | Red LED, through 220 Ω |
| D26 | 26 | White LED, through 220 Ω |
| D27 | 27 | Buzzer I/O |

The RC522's IRQ pin is not connected.

Each LED is wired the same way: the pin, then a resistor, then the long leg of the LED (the anode). The short leg goes to GND. Never connect an LED straight to a pin.

### Power

Two voltages are used, and mixing them up is the most common fault.

| Rail | Feeds |
|---|---|
| 3V3 | The RC522 only. It is damaged by 5 V. |
| VIN (5 V) | The LCD's VCC and the buzzer's VCC. The LCD is dim or blank on 3.3 V. |
| GND | Everything. Use a breadboard rail to share it. |

Two more things trip people up. The LCD's SDA goes to D32, not D21, because D21 is already the RC522's reset line. And the pins printed RX2 and TX2 on the board are GPIO 16 and 17.

If the screen stays blank, the LCD's address may be `0x3F` instead of `0x27`. The address is set at the top of each sketch. The sketches run the screen at 400 kHz, which is four times faster than the usual speed. If the letters come out garbled on your wiring, set `LCD_I2C_HZ` at the top of the sketch to `100000`.

The buzzer is an active-low, passive module. The sketches already drive it correctly, with three short pulses at 4500 Hz.

### The three sketches

Each connection has its own Arduino sketch. The wiring is the same for all three, so one board can run any of them.

| Sketch | Connection |
|---|---|
| `rc522_serial_reader` | USB cable |
| `rc522_wifi_reader` | Its own Wi-Fi network, `TapIn-Reader`, password `tapin12345`, address `192.168.4.1`, port `8888` |
| `rc522_bluetooth_reader` | Bluetooth Classic, name `TapIn-Reader` |

To load one:

1. Install the Arduino IDE, and add the ESP32 board support (Espressif's "esp32" package). The sketches are built and tried with version 3.3.12.
2. Install the libraries **MFRC522** and **LiquidCrystal_I2C** from the Library Manager.
3. Open the sketch, choose the board "DOIT ESP32 DEVKIT V1" (or "ESP32 Dev Module") and the USB port, then press Upload.
4. To watch it, open the Serial Monitor and set it to 9600 baud.

The Bluetooth sketch is large. If the upload says "Sketch too big", choose Tools → Partition Scheme → "Huge APP".

When the board starts, it prints a self-test line over USB: `RC522 version register: 0x91` or `0x92` means the RC522 is wired correctly. `0x00` or `0xFF` means the data wires are wrong or loose, even when the power lights are on. Check MOSI, MISO, SCK, SDA and RST.

### How the reader and TapIn talk

It is a simple text line in each direction, 9600 baud over USB. The Wi-Fi sketch sends the same lines over TCP, and the Bluetooth sketch sends them over the Bluetooth serial port.

```
reader to TapIn   04A3B2C1
TapIn to reader   OK:2111051005|Grace Hopper
TapIn to reader   INVALID
TapIn to reader   MSG:No session|today
```

- The reader sends one line for each new tap: the card's ID, in capital hexadecimal letters, with no spaces. A card that stays on the reader is sent once. Lifting it and tapping again sends it again.
- `OK:` is followed by the student number, a bar, and the name. The reader shows them on its two lines and lights green.
- `INVALID` makes the reader show "Invalid card", light red, and beep.
- `MSG:` shows two lines of text and lights yellow.
- The reader sends card IDs only. Anything else on that line would be taken for a card.
- The reader never waits for an answer. It keeps scanning and queues the answers, so students who tap one after another are all read.
