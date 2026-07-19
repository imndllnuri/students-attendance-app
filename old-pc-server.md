# Setting Up an Old PC as the TapIn Attendance Server

**A complete, follow-along guide** — from unboxing a spare PC to a working RFID card scan landing in the database.

The server-hardening work this guide depends on (`server/wsgi.py`, `requirements-server.txt`, `deploy/tapin.service`, `deploy/tapin.env.example`, and the GUI's "Server Connection" dialog) has landed — see `DEPLOYMENT.md` for the terser reference version of this same setup.

---

## Table of Contents

1. [Architecture at a Glance](#1-architecture-at-a-glance)
2. [What You'll Need](#2-what-youll-need)
3. [Part A — Preparing the Old PC](#part-a--preparing-the-old-pc)
4. [Part B — Installing the TapIn Server](#part-b--installing-the-tapin-server)
5. [Part C — Configuring the Server](#part-c--configuring-the-server)
6. [Part D — Running TapIn as a systemd Service](#part-d--running-tapin-as-a-systemd-service)
7. [Part E — Networking & Firewall](#part-e--networking--firewall)
8. [Part F — Connecting an Instructor GUI Client](#part-f--connecting-an-instructor-gui-client)
9. [Part G — Wiring the RFID Hardware (RC522 + ESP32)](#part-g--wiring-the-rfid-hardware-rc522--esp32)
10. [Part H — Flashing the Firmware](#part-h--flashing-the-firmware)
11. [Part I — Selecting the Hardware Backend in TapIn](#part-i--selecting-the-hardware-backend-in-tapin)
12. [Part J — End-to-End Testing Checklist](#part-j--end-to-end-testing-checklist)
13. [Part K — Troubleshooting](#part-k--troubleshooting)
14. [Part L — Ongoing Maintenance](#part-l--ongoing-maintenance)
15. [Appendix — Quick Reference Commands](#appendix--quick-reference-commands)

---

## 1. Architecture at a Glance

```
┌─────────────────────┐         LAN (Wi-Fi/Ethernet)         ┌──────────────────────────┐
│   Old PC (Linux)    │◄─────────────────────────────────────►│  Instructor's Laptop     │
│                      │            HTTP + X-API-Key           │  (runs the PyQt5 GUI)    │
│  gunicorn            │                                        │                          │
│  server/wsgi:app     │                                        │  services/api_client.py  │
│  (systemd service)   │                                        │  → points at old PC's IP │
│                      │                                        │                          │
│  attendance.db       │                                        │  USB serial cable        │
│  (SQLite)            │                                        │       │                  │
│  + daily backups     │                                        │       ▼                  │
└─────────────────────┘                                        │  ┌─────────────────┐      │
                                                                 │  │ ESP32 + RC522   │      │
                                                                 │  │ RFID reader     │      │
                                                                 │  └─────────────────┘      │
                                                                 └──────────────────────────┘
```

**Two separate machines, two separate roles:**

- The **old PC** runs *only* the Flask server (`server/wsgi.py` under gunicorn) and owns the single source of truth: `attendance.db`. It does **not** need a monitor, keyboard, or GUI once set up — headless is fine, and in fact preferred.
- The **instructor's laptop** runs the PyQt5 GUI and is what the ESP32/RC522 reader plugs into via USB, *not* the server. The GUI reads card scans over that serial cable and calls the server's `/attend` endpoint over the network.

If you have multiple instructors, each of their laptops runs the GUI independently and all of them point at the same old-PC server — that's the whole point of doing this instead of running everything on one machine.

---

## 2. What You'll Need

### Hardware
- An old PC or laptop capable of running Linux — this app's server needs almost nothing: **1 GB RAM and any x86_64 or ARM CPU from the last ~15 years is plenty.** Flask + SQLite have a tiny footprint; the heavier dependencies (PyQt5, pandas, matplotlib) never run on this machine.
- A USB-A cable (for the ESP32).
- An **MFRC522** RFID reader module (the common blue breakout board).
- An **ESP32 dev board** (any variant with exposed SPI pins — e.g. ESP32-DevKitC, NodeMCU-32S).
- Jumper wires (female-to-female if your ESP32 has male header pins).
- A handful of MIFARE Classic RFID cards/keyfobs (usually bundled with the RC522 module) — one per student, or a shared set for testing.

### Software / accounts
- A Linux install image (Ubuntu Server 22.04/24.04 LTS or Debian 12 both work well and are well-documented for headless setups).
- SSH access to the old PC (recommended, so you don't need to keep a monitor attached to it).
- The TapIn repository, cloned or copied to the old PC.
- Arduino IDE (or PlatformIO, if you prefer) on whichever machine you'll use to flash the ESP32 — this can be your regular development machine, not the old PC.

---

## Part A — Preparing the Old PC

### A.1 Install Linux

1. Download **Ubuntu Server** (recommended — no desktop environment, minimal footprint, exactly what a headless service box wants) from ubuntu.com, or Debian 12 netinst from debian.org.
2. Write it to a USB stick (`Rufus` on Windows, `dd`/`balenaEtcher` on macOS/Linux).
3. Boot the old PC from the USB stick and follow the installer. Notable choices:
   - **Enable OpenSSH server** when prompted (Ubuntu Server's installer asks directly) — this is how you'll administer the machine afterward without a monitor.
   - Create a regular user account (e.g. `tapin-admin`) with sudo privileges — you'll create a separate, unprivileged `tapin` service account later in Part D; this first account is just for you to log in and administer the box.
   - Set a static hostname you'll remember, e.g. `tapin-server`.
4. After install, remove the USB stick and reboot.

### A.2 First login and update

From another machine on the same network:

```bash
ssh tapin-admin@tapin-server.local
# or, if mDNS resolution doesn't work on your network, find its IP first
# (see Part E.1) and use that instead: ssh tapin-admin@192.168.1.xxx
```

Update the system:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

### A.3 Install Python and Git

TapIn's server targets **Python 3.11 or 3.12**. Check what's available:

```bash
python3 --version
```

If it's older than 3.11 (common on Debian's default repos), install a newer one via `deadsnakes` (Ubuntu) or use `pyenv`:

```bash
# Ubuntu:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev git
```

Verify:

```bash
python3.12 --version
git --version
```

---

## Part B — Installing the TapIn Server

### B.1 Choose an install location

Following the convention used in `DEPLOYMENT.md`, install to `/opt/tapin`:

```bash
sudo mkdir -p /opt/tapin
sudo chown "$USER":"$USER" /opt/tapin
git clone <your-repo-url> /opt/tapin
cd /opt/tapin
```

*(If you're transferring the repo without a git remote — e.g. via `scp` from your dev machine — just copy the whole directory to `/opt/tapin` instead of cloning.)*

### B.2 Create a virtual environment with server-only dependencies

This is the key benefit of `requirements-server.txt`: it installs **only** `Flask` and `gunicorn` — none of the GUI's heavy dependencies (PyQt5, pandas, numpy, matplotlib) — which keeps the install fast and the footprint small on an old machine.

```bash
python3.12 -m venv /opt/tapin/.venv
/opt/tapin/.venv/bin/pip install --upgrade pip
/opt/tapin/.venv/bin/pip install -r /opt/tapin/requirements-server.txt
```

Confirm it worked:

```bash
/opt/tapin/.venv/bin/python -c "import flask, gunicorn; print('ok')"
```

---

## Part C — Configuring the Server

### C.1 Create a dedicated system user

Running the service as its own unprivileged user (rather than your login account or root) limits the blast radius if anything ever goes wrong:

```bash
sudo useradd --system --home /var/lib/tapin --create-home --shell /usr/sbin/nologin tapin
sudo mkdir -p /var/lib/tapin/backups
sudo chown -R tapin:tapin /var/lib/tapin
```

### C.2 Generate a real API key

Do **not** use the placeholder from `deploy/tapin.env.example`. Generate a genuinely random 64-character hex key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output somewhere safe (a password manager is ideal) — every GUI client machine will need to enter this exact string to talk to the server.

### C.3 Create the environment file

Environment files live **outside** the repo clone, at `/etc/tapin/tapin.env`, so they're never accidentally committed or overwritten by a `git pull`:

```bash
sudo mkdir -p /etc/tapin
sudo cp /opt/tapin/deploy/tapin.env.example /etc/tapin/tapin.env
sudo nano /etc/tapin/tapin.env
```

Fill it in:

```ini
TAPIN_DB_PATH=/var/lib/tapin/attendance.db
TAPIN_API_KEY=<paste the key you generated in C.2>
```

Lock the file down so only root can read it (it contains a secret):

```bash
sudo chmod 600 /etc/tapin/tapin.env
sudo chown root:root /etc/tapin/tapin.env
```

### C.4 Sanity-check the server manually before wiring up systemd

It's much easier to debug a plain foreground process than a systemd unit. Run it by hand first:

```bash
cd /opt/tapin
sudo -u tapin env $(cat /etc/tapin/tapin.env | xargs) \
  /opt/tapin/.venv/bin/gunicorn --workers 1 --threads 4 --bind 127.0.0.1:5000 server.wsgi:app
```

In a second terminal (or from another machine, once you bind to `0.0.0.0` in Part D):

```bash
curl http://127.0.0.1:5000/health
# → {"status": "ok"}

curl http://127.0.0.1:5000/classes?instructor_id=test
# → {"error": "Unauthorized"}   (401 — expected, no API key sent)

curl -H "X-API-Key: <your key>" http://127.0.0.1:5000/classes?instructor_id=test
# → []   (200 — empty list, expected for a brand-new database)
```

Confirm the database file was created:

```bash
ls -la /var/lib/tapin/
# should show attendance.db and a backups/ directory
```

Once all three `curl` checks behave as above, press `Ctrl+C` to stop the manual run and move on to systemd.

---

## Part D — Running TapIn as a systemd Service

### D.1 Install the unit file

```bash
sudo cp /opt/tapin/deploy/tapin.service /etc/systemd/system/tapin.service
```

Open it and confirm the paths match your setup (they should already, if you followed `/opt/tapin` and the `tapin` user above):

```bash
sudo nano /etc/systemd/system/tapin.service
```

It should look like:

```ini
[Unit]
Description=TapIn attendance server
After=network.target

[Service]
Type=simple
User=tapin
Group=tapin
WorkingDirectory=/opt/tapin
EnvironmentFile=/etc/tapin/tapin.env
ExecStart=/opt/tapin/.venv/bin/gunicorn --workers 1 --threads 4 --bind 0.0.0.0:5000 server.wsgi:app
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

Note the bind address changes from `127.0.0.1` (Part C.4's manual test, local-only) to **`0.0.0.0`** here — this is what actually allows other machines on the LAN to reach it. That's an intentional and important difference; don't "fix" it back to `127.0.0.1` or nothing outside this box will ever connect.

### D.2 Enable and start it

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tapin
```

`enable` makes it start automatically on every boot; `--now` also starts it immediately.

### D.3 Verify

```bash
sudo systemctl status tapin
```

You want to see `active (running)` in green. If it says `failed` or `activating (auto-restart)`, jump to [Part K — Troubleshooting](#part-k--troubleshooting).

Watch the logs live:

```bash
sudo journalctl -u tapin -f
```

Re-run the `curl` checks from C.4 against `0.0.0.0` — but note that curling `0.0.0.0` directly from the server itself won't work as a destination; use `127.0.0.1` or the machine's real LAN IP instead:

```bash
curl http://127.0.0.1:5000/health
```

### D.4 Test that it survives a reboot

This matters — the whole point is "always-on":

```bash
sudo reboot
```

Wait about a minute, SSH back in, and check:

```bash
sudo systemctl status tapin
```

It should already be `active (running)` without you doing anything.

### D.5 Test that it recovers from a crash

```bash
sudo systemctl status tapin   # note the current PID
sudo kill -9 <that PID>
sleep 6
sudo systemctl status tapin   # should show a NEW PID, active (running)
```

`Restart=on-failure` + `RestartSec=5` means systemd relaunches it within a few seconds of any crash.

---

## Part E — Networking & Firewall

### E.1 Find the old PC's LAN IP address

```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Note the address (something like `192.168.1.42`). This is what you'll enter into every instructor's GUI client in Part F.

### E.2 Give it a stable/static address

DHCP-assigned addresses can change on reboot, which would break every client's saved configuration. Do **one** of the following:

- **Recommended, easiest:** log into your router's admin page and set a **DHCP reservation** for the old PC's MAC address, so it always receives the same IP.
- **Alternative:** configure a static IP directly on the old PC via Netplan (Ubuntu):

  ```bash
  sudo nano /etc/netplan/50-cloud-init.yaml
  ```

  ```yaml
  network:
    version: 2
    ethernets:
      eth0:              # confirm your interface name with `ip addr`
        dhcp4: no
        addresses: [192.168.1.42/24]
        routes:
          - to: default
            via: 192.168.1.1
        nameservers:
          addresses: [192.168.1.1, 8.8.8.8]
  ```

  ```bash
  sudo netplan apply
  ```

### E.3 Open the firewall port — scoped to your LAN only

```bash
sudo apt install -y ufw
sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp
sudo ufw allow ssh
sudo ufw enable
sudo ufw status
```

Replace `192.168.1.0/24` with your actual LAN subnet (from E.1). **Deliberately do not** `ufw allow 5000` unscoped — that would expose the attendance server to the entire internet if this box is ever behind a router with UPnP or port-forwarding enabled. The API key adds a layer of protection, but "not internet-reachable at all" is a much stronger guarantee than "internet-reachable but password-protected" for a small class-management tool like this.

### E.4 (Optional) Access from outside the classroom LAN

If an instructor ever needs to reach the server from off-site, do **not** port-forward 5000 to the public internet. Instead, set up a lightweight mesh VPN such as **Tailscale** or **WireGuard** on both the old PC and the remote laptop — this gives you a private, encrypted tunnel without exposing the Flask server to the open internet at all. This is out of scope for this guide but flagged here since it's the safe way to do it if the need comes up.

---

## Part F — Connecting an Instructor GUI Client

This happens on the **instructor's laptop**, not the old PC.

### F.1 Install the full app (with GUI dependencies)

```bash
git clone <your-repo-url>
cd student-attendance-app
python3 -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt   # the FULL requirements file — PyQt5 etc. included
```

### F.2 Launch the app and open the Server Connection dialog

```bash
python run.py   # or ./run.sh, per the project's existing quick-start instructions
```

On the **login screen**, click the gear icon next to the TapIn wordmark. (This exists specifically so you can point the app at your server *before* logging in — you don't need an account yet to configure this.)

Alternatively, if you're already logged in on a previously-configured client and just need to repoint it: **Settings → General → Server Connection**.

### F.3 Fill in the connection details

| Field | Value |
|---|---|
| Server URL | `http://<old-PC-LAN-IP>:5000` (e.g. `http://192.168.1.42:5000`) |
| API Key | The key you generated in Part C.2 |

Click **Test Connection**. You should see a green "Connected" confirmation — this calls the server's `/health` endpoint using the exact URL/key you just typed, before anything is saved. If it fails, double check:
- The old PC is powered on and `systemctl status tapin` shows `active`.
- You're on the same network (or VPN, per E.4) as the old PC.
- The IP address hasn't changed since Part E.1 (revisit E.2 if it keeps changing).
- The API key matches exactly (no trailing spaces — a common copy-paste mistake).

Click **OK** to save. This writes the URL and key to `.backend_config.json` on the laptop and immediately reconnects the app's internal client — no restart needed.

### F.4 Create your instructor account and a class

With the connection live, sign up for an account, log in, and create a class as normal — this now writes to `attendance.db` on the old PC, not a local file.

### F.5 Repeat for every additional instructor machine

Each laptop goes through F.1–F.3 independently, using the same server URL and API key. They'll all read/write the same shared database.

---

## Part G — Wiring the RFID Hardware (RC522 + ESP32)

**Important:** the reader plugs into the **instructor's laptop** via USB, not into the old PC. The old PC never talks to the RFID hardware directly.

### G.1 Why an ESP32 in between?

The MFRC522 module communicates over **SPI**, which isn't something a laptop's USB port speaks natively. The ESP32 acts as a bridge: it reads card UIDs from the RC522 over SPI, and reports each scan to the laptop as a plain line of text over USB serial — which is exactly the protocol `services/card_reader.py`'s `SerialCardReader` already expects (`ser.readline()` → decode → strip, one card ID per line).

### G.2 Wiring diagram

⚠️ **The RC522 is a 3.3V device.** Never connect its `VCC` to the ESP32's `5V`/`VIN` pin — most ESP32 boards' logic and the RC522 both run at 3.3V, and 5V will likely damage the module.

| RC522 pin | ESP32 pin | Notes |
|---|---|---|
| `SDA` (also labeled `SS`/`CS`) | `GPIO 5` | Chip select |
| `SCK` | `GPIO 18` | SPI clock (VSPI) |
| `MOSI` | `GPIO 23` | SPI data out |
| `MISO` | `GPIO 19` | SPI data in |
| `IRQ` | *(not connected)* | Unused for polling mode |
| `GND` | `GND` | Common ground |
| `RST` | `GPIO 22` | Reset |
| `3.3V` | `3.3V` | **Not 5V** |

```
   MFRC522                     ESP32
  ┌─────────┐                ┌─────────┐
  │ SDA/SS  ├────────────────┤ GPIO 5  │
  │ SCK     ├────────────────┤ GPIO 18 │
  │ MOSI    ├────────────────┤ GPIO 23 │
  │ MISO    ├────────────────┤ GPIO 19 │
  │ IRQ     │   (unused)     │         │
  │ GND     ├────────────────┤ GND     │
  │ RST     ├────────────────┤ GPIO 22 │
  │ 3.3V    ├────────────────┤ 3.3V    │
  └─────────┘                └─────────┘
```

If your ESP32 board's pin labels differ from a standard DevKitC (some boards silkscreen VSPI pins differently), consult your specific board's pinout diagram — the GPIO *numbers* above are what matter, not physical pin position.

---

## Part H — Flashing the Firmware

### H.1 Install the Arduino IDE and libraries

1. Install the [Arduino IDE](https://www.arduino.cc/en/software) on your dev machine.
2. In **Tools → Board → Boards Manager**, search for and install **"esp32" by Espressif Systems**.
3. In **Sketch → Include Library → Manage Libraries**, install **"MFRC522" by GithubCommunity**.

### H.2 The firmware sketch

This sketch reads a card UID whenever one is presented and prints it as a single line, matching the `9600` baud rate hardcoded in `views/take_attendance_window.py`'s `setup_serial()` and the newline-delimited, whitespace-trimmed format `SerialCardReader.poll()` expects.

```cpp
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5
#define RST_PIN 22

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);   // must match SerialCardReader's baudrate in take_attendance_window.py
  SPI.begin();
  mfrc522.PCD_Init();
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  Serial.println(uid);   // one line per scan, e.g. "A1B2C3D4"

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  delay(1000);            // simple debounce so one tap doesn't register as several scans
}
```

### H.3 Upload it

1. Connect the ESP32 to your dev machine via USB.
2. In the Arduino IDE, select **Tools → Board → ESP32 Dev Module** (or your specific board variant).
3. Select the correct **Port** under **Tools → Port**.
4. Click **Upload**.
5. Open **Tools → Serial Monitor**, set the baud rate to **9600**, and tap a card on the reader — you should see a hex UID printed on its own line each time. If you see this, the hardware side is working correctly and you're ready to move to the instructor's laptop.

---

## Part I — Selecting the Hardware Backend in TapIn

TapIn supports two card-reader backends (`services/card_reader.py`): a direct **serial** connection (what you just built) and an alternate **ESP8266 WiFi** backend for a different hardware setup. For the RC522+ESP32-over-USB setup in this guide, you want the default **serial** backend — most users won't need to change anything here, but it's worth understanding what's configurable.

### I.1 Plug the ESP32 into the instructor's laptop

Connect it via the same USB cable used for flashing.

### I.2 Launch Take Attendance

Open a class in the GUI and start a **Take Attendance** session. On startup, `setup_serial()` scans the system's available serial ports and looks for one whose USB description contains `RFID` or `SCM`.

- Most generic ESP32 boards (using a CP2102 or CH340 USB-to-serial chip) will **not** match this filter automatically — you'll instead see a **port picker dialog** listing all available serial ports (e.g. `/dev/ttyUSB0 (CP2102 USB to UART Bridge Controller)` on Linux, `COM3 (Silicon Labs CP210x)` on Windows). Just select the one corresponding to your ESP32.
- You'll see this dialog every time you start a session unless the port's description happens to match the auto-detect filter — this is expected behavior for this hardware combination, not a bug.

### I.3 Confirm the connection

The scan-status indicator in the Take Attendance view should read **"Reader connected (\<port\>). Press Start to begin scanning."** If it instead shows an error, see [Troubleshooting](#part-k--troubleshooting).

---

## Part J — End-to-End Testing Checklist

Work through this in order. Each step builds on the last — don't skip ahead if an earlier one fails.

- [ ] **Server health (from the old PC itself):** `curl http://127.0.0.1:5000/health` → `{"status": "ok"}`
- [ ] **Server health (from a LAN machine):** `curl http://<old-PC-IP>:5000/health` → same response, confirms firewall/networking is correct
- [ ] **Auth enforced:** `curl http://<old-PC-IP>:5000/classes?instructor_id=x` (no header) → `401 Unauthorized`
- [ ] **Auth accepted:** same request with `-H "X-API-Key: <key>"` → `200`
- [ ] **systemd survives reboot:** per Part D.4
- [ ] **systemd survives crash:** per Part D.5
- [ ] **GUI connects:** Test Connection in the Server Connection dialog shows green/success
- [ ] **Account creation works end-to-end:** sign up a test instructor account from the GUI, confirm it appears in `attendance.db` on the server (`sqlite3 /var/lib/tapin/attendance.db "select email from accounts;"` on the old PC)
- [ ] **Class creation works:** create a test class with a couple of roster entries
- [ ] **Firmware prints UIDs:** confirmed in Arduino Serial Monitor (Part H.3)
- [ ] **GUI detects the reader:** "Reader connected" status shown in Take Attendance
- [ ] **A real scan records attendance:** tap a card, confirm it appears in the session's live list in the GUI
- [ ] **The record persists server-side:** after submitting the session, query the server directly: `sqlite3 /var/lib/tapin/attendance.db "select * from attendance_records order by id desc limit 5;"`
- [ ] **Statistics reflect it:** the class's attendance stats/chart in the GUI update to include the new record
- [ ] **A second laptop sees the same data:** if you have a second instructor machine, connect it to the same server and confirm it can see the class/roster/attendance created from the first machine
- [ ] **Backups are being created:** `ls /var/lib/tapin/backups/` shows a timestamped `.db` file after the server has been running past its first backup cycle (or trigger one manually — see Appendix)

If every box is checked, the deployment is fully working end-to-end.

---

## Part K — Troubleshooting

**`systemctl status tapin` shows `failed`**
Run `sudo journalctl -u tapin -n 50 --no-pager` to see the actual Python traceback. Common causes:
- Wrong path in `ExecStart` (typo, or venv not actually at `/opt/tapin/.venv`)
- `/etc/tapin/tapin.env` missing or unreadable by the `tapin` user — re-check ownership/permissions from C.3
- Port 5000 already in use by something else: `sudo ss -tlnp | grep 5000`

**`curl` from another machine times out / connection refused**
- Confirm the unit's `--bind` is `0.0.0.0`, not `127.0.0.1` (Part D.1)
- Confirm `ufw status` shows the rule for port 5000 (Part E.3)
- Confirm both machines are actually on the same subnet — check with `ip addr` on both ends
- Some routers isolate wireless clients from each other ("AP/client isolation" or "guest network" settings) — check your router's Wi-Fi settings if the old PC is on Wi-Fi and this keeps failing

**GUI's Test Connection fails but `curl` from the same laptop succeeds**
- Double-check the API key was pasted without a trailing newline/space
- Confirm the URL includes `http://` and the port (`:5000`) — a bare IP won't work

**`401 Unauthorized` even with the right-looking key**
- The key is compared byte-for-byte (`hmac.compare_digest`) — re-copy it from `/etc/tapin/tapin.env` on the server, don't retype from memory
- If you regenerated the key at some point, every client needs updating individually (Part F.3) — there's no push mechanism

**No serial ports show up in the port picker**
- On Linux, your user needs to be in the `dialout` group to access `/dev/ttyUSB*`/`/dev/ttyACM*`: `sudo usermod -aG dialout $USER`, then **log out and back in** (group membership doesn't apply retroactively to an already-open session)
- Try a different USB cable — many "charge-only" USB cables have no data lines

**ESP32 shows up but no UID ever prints**
- Re-check every wire against the table in Part G.2, especially that `3.3V` isn't accidentally on `5V`
- Confirm the MFRC522 library initialized correctly — add `Serial.println(mfrc522.PCD_PerformSelfTest() ? "OK" : "FAIL");` temporarily to `setup()` after `PCD_Init()` for a hardware self-test (note: after a self-test you must re-run `PCD_Init()`, since the self-test resets the chip)

**Attendance submits from the GUI but never appears in `attendance_records`**
- Check the GUI's connection is actually pointed at the old PC and not still at `127.0.0.1` (re-verify Part F.3)
- Check `sudo journalctl -u tapin -f` on the server while submitting — a 4xx/5xx there tells you exactly what request failed and why

---

## Part L — Ongoing Maintenance

### Updating the server after code changes

```bash
cd /opt/tapin
sudo -u tapin git pull
sudo -u tapin /opt/tapin/.venv/bin/pip install -r requirements-server.txt
sudo systemctl restart tapin
sudo systemctl status tapin   # confirm it came back up cleanly
```

### Restoring from a backup

If `attendance.db` ever becomes corrupted or you need to roll back:

```bash
sudo systemctl stop tapin
ls -la /var/lib/tapin/backups/                     # find the timestamp you want
sudo cp /var/lib/tapin/backups/attendance-<timestamp>.db /var/lib/tapin/attendance.db
sudo chown tapin:tapin /var/lib/tapin/attendance.db
sudo systemctl start tapin
```

### Monitoring disk space

SQLite backups accumulate (though `backup_database()` automatically prunes to the last 10). Periodically check:

```bash
df -h /var/lib/tapin
du -sh /var/lib/tapin/backups
```

### Rotating the API key

If you ever suspect the key has leaked (e.g. a laptop with it saved was lost):

1. Generate a new key (Part C.2).
2. Update `/etc/tapin/tapin.env` on the server.
3. `sudo systemctl restart tapin`.
4. Update every GUI client's Server Connection dialog with the new key (Part F.3) — old clients will start getting `401`s until updated, which is the correct, intended behavior.

---

## Appendix — Quick Reference Commands

```bash
# Service control
sudo systemctl start|stop|restart|status tapin
sudo journalctl -u tapin -f              # live logs
sudo journalctl -u tapin -n 100          # last 100 lines

# Manual backup trigger (server must be running, key required)
curl -X POST -H "X-API-Key: <key>" http://127.0.0.1:5000/admin/backup

# Inspect the database directly
sqlite3 /var/lib/tapin/attendance.db ".tables"
sqlite3 /var/lib/tapin/attendance.db "select count(*) from attendance_records;"

# Find the server's LAN IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Grant serial port access on a GUI client machine (Linux)
sudo usermod -aG dialout $USER   # then log out/in
```
