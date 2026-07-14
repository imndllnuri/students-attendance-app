# Development

## Prerequisites

- Python 3.11 or 3.12
- On Linux, PyQt5 needs a few system Qt libraries to render (and to run
  headless in CI): `libgl1 libegl1 libxkbcommon0 libdbus-1-3 libxcb-cursor0`
  (Debian/Ubuntu package names — see `.github/workflows/build.yml`).

There is no compiled/packaged build step — this is an interpreted desktop
Python app, run directly from source.

## Running it

Either:

```
./run.sh
```

which creates/reuses `.venv`, installs `requirements.txt`, starts the Flask
server in the background, launches the GUI, and stops the server when the
GUI exits — or run the two processes yourself in separate terminals (useful
when you want server logs and GUI logs in separate windows):

```
python -m server.app   # terminal 1
python main.py          # terminal 2
```

## Seeding sample data

Once the server is running, `scripts/seed_mock_data.py` creates a sample
instructor account + class + roster so you have something to click through
without hand-typing data or having RFID hardware attached:

```
python scripts/seed_mock_data.py
```

## Running tests

```
pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen pytest -q   # offscreen only needed without a display (SSH, CI)
```

See `TESTING.md` for what's covered.

## Project layout

See `ARCHITECTURE.md` for the full module map and how the pieces talk to
each other.

## Version matrix

| Component | Version |
|---|---|
| Python | 3.11 / 3.12 |
| PyQt5 | 5.15.10 |
| Flask | 3.0.3 |

(Pinned versions live in `requirements.txt` — that file is the source of
truth if this table goes stale.)
