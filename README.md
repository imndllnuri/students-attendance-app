# Student Attendance App

A desktop application for teachers to manage classes and take student attendance, built with PyQt5.

## Features

- Account creation / login (with security question recovery)
- Create and manage classes, add/remove students
- Take attendance per class session
- Data persisted as JSON (`accounts.json`, `data/`)

## Tech stack

- Python, PyQt5 (UI, `.ui` files compiled via `views/` + `ui/`)
- pandas / openpyxl / numpy for data handling and export

## Layout

```
main.py     # entry point, launches LoginWindow
models/     # Account, Class, Student data models (JSON-backed)
views/      # PyQt5 window controllers (login, class, attendance, etc.)
ui/         # Qt Designer .ui files
resources/  # images / icons
```

## Status

Functional desktop prototype; supersedes an earlier version of this app.
