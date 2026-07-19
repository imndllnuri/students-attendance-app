# Deployment

This document describes how to run the TapIn server as a standing,
always-on service on a dedicated Linux machine, so it can be reached over a
LAN by multiple instructor GUI clients — instead of the single-machine dev
setup in `README.md`'s "Running it" section, where server and GUI run
together on one laptop.

For a fully spelled-out, step-by-step walkthrough (including RFID hardware
wiring and an end-to-end testing checklist), see `old-pc-server.md`. This
document is the terser reference version, in the same style as
`ARCHITECTURE.md`/`TESTING.md`.

## When to use this

A single spare Linux machine running the server continuously, with one or
more instructor laptops running the GUI and pointing at it over the LAN.
Not a public-internet-facing deployment — see "Known limitations" in
`ARCHITECTURE.md`, which this setup narrows but does not eliminate.

## 1. Install on the server machine

```
sudo mkdir -p /opt/tapin
sudo chown "$USER":"$USER" /opt/tapin
git clone <repo-url> /opt/tapin
cd /opt/tapin

sudo useradd --system --home /var/lib/tapin --create-home --shell /usr/sbin/nologin tapin
sudo mkdir -p /var/lib/tapin/backups
sudo chown -R tapin:tapin /var/lib/tapin

python3 -m venv /opt/tapin/.venv
/opt/tapin/.venv/bin/pip install -r /opt/tapin/requirements-server.txt
```

`requirements-server.txt` installs only `Flask` + `gunicorn` — none of the
GUI's dependencies (PyQt5, pandas, matplotlib, ...) are needed on this
machine.

## 2. Configure

Environment files live outside the repo clone, so they're never touched by
`git pull` or accidentally committed:

```
sudo mkdir -p /etc/tapin
sudo cp deploy/tapin.env.example /etc/tapin/tapin.env
sudo nano /etc/tapin/tapin.env      # set TAPIN_DB_PATH and a real TAPIN_API_KEY
sudo chmod 600 /etc/tapin/tapin.env
```

Generate a real API key:

```
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Every GUI client will need this exact value (see step 5).

## 3. systemd

```
sudo cp deploy/tapin.service /etc/systemd/system/tapin.service
sudo systemctl daemon-reload
sudo systemctl enable --now tapin
sudo systemctl status tapin
```

`deploy/tapin.service` runs `gunicorn --workers 1 --threads 4 --bind
0.0.0.0:5000 server.wsgi:app`. One worker is deliberate: SQLite is a
single-writer file and `server/app.py`'s periodic-backup timer is meant to
fire once per process, not once per worker.

`server/wsgi.py` (not `server/app.py`'s `__main__` block) is the entry
point gunicorn uses — importing it is what triggers `init_db()` and the
backup scheduler in production, keeping `python -m server.app`'s dev path
unchanged.

## 4. Firewall

```
sudo ufw allow from <your-LAN-subnet> to any port 5000 proto tcp
sudo ufw allow ssh
sudo ufw enable
```

Scope the rule to your LAN subnet specifically — don't open port 5000
unscoped. The API key is defense in depth, not a substitute for not being
reachable from the internet at all.

## 5. Point a GUI client at it

On each instructor's machine, install the full app (`pip install -r
requirements.txt`, includes the GUI dependencies) and launch it. On the
login screen, click the gear icon next to the "TapIn" wordmark (or, once
logged in, go to **Settings → General → Server Connection**) and enter:

- **Server URL**: `http://<server-LAN-ip>:5000`
- **API Key**: the value generated in step 2

Click **Test Connection** to verify before saving.

## 6. Verify

```
curl http://<server-LAN-ip>:5000/health
curl http://<server-LAN-ip>:5000/classes?instructor_id=x            # -> 401, no key
curl -H "X-API-Key: <key>" http://<server-LAN-ip>:5000/classes?instructor_id=x   # -> 200
```

Then complete a real login → create class → take attendance flow from a
GUI client.

## Restoring from backup

There is no restore *tooling* — `server/db.py`'s `backup_database()` keeps
the last 10 timestamped copies in `<TAPIN_DB_PATH's directory>/backups/`,
but restoring is a manual file copy:

```
sudo systemctl stop tapin
sudo cp /var/lib/tapin/backups/attendance-<timestamp>.db /var/lib/tapin/attendance.db
sudo chown tapin:tapin /var/lib/tapin/attendance.db
sudo systemctl start tapin
```

## Updating

```
cd /opt/tapin
sudo -u tapin git pull
sudo -u tapin /opt/tapin/.venv/bin/pip install -r requirements-server.txt
sudo systemctl restart tapin
```
