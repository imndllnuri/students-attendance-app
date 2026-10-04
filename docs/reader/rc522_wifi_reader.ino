/* RC522 -> ESP32 -> WiFi, as the card-reader backend for the app's
 * "esp8266" (WiFi/TCP) path - services/card_reader.py's ESP8266CardReader.
 * The sibling sketch firmware/rc522_serial_reader is the same reader over
 * a USB cable instead; use that one unless the reader has to be untethered.
 *
 * WHY SoftAP (this board makes its own WiFi network) rather than joining
 * the school's WiFi: the app is the TCP *client* - it dials out to a fixed
 * host:port from .hardware_config.json (see ESP8266CardReader.connect ->
 * socket.create_connection). So this board has to sit at an address the
 * app already knows. On a normal router, DHCP reassigns addresses and that
 * breaks. Running our own AP pins the address permanently at 192.168.4.1
 * (the Arduino-ESP32 SoftAP default), and also dodges the client-isolation
 * setting most institutional networks enable, which would silently block
 * the laptop from reaching this board at all.
 *
 * SETUP, once flashed:
 *   1. On the laptop, join the WiFi network named by AP_SSID below.
 *   2. Write this file next to the app (user_data_dir(), which is the repo
 *      root when running from source) as .hardware_config.json:
 *        {"backend": "esp8266", "host": "192.168.4.1", "port": 8888}
 *   3. Open Take Attendance and press Start. There is no settings UI for
 *      this yet - the JSON file is currently the only way to switch.
 *
 * Wiring is IDENTICAL to firmware/rc522_serial_reader, so the same
 * soldered board runs either sketch:
 *
 *   RC522 pin   ESP32 pin        Other          ESP32 pin
 *   ---------   ---------        -----          ---------
 *   3.3V        3V3              Green LED      GPIO 4
 *   RST         GPIO 21          Yellow LED     GPIO 16
 *   GND         GND              Red LED        GPIO 17
 *   MISO        GPIO 19          White LED      GPIO 26
 *   MOSI        GPIO 23          Buzzer I/O     GPIO 27
 *   SCK         GPIO 18          Buzzer VCC     VIN (5V)
 *   SDA (SS)    GPIO 5           LCD SDA        GPIO 32
 *   IRQ         not connected    LCD SCL        GPIO 22
 *
 * Every LED: GPIO --[220ohm resistor]--> LED anode, cathode -> GND.
 *
 * The white LED is a plain power indicator: it comes on at boot and stays
 * on. There is no on/off GPIO to read, because the on/off switch is a
 * latching switch wired in series with the battery's + wire - it cuts
 * power to the whole board, so "off" is genuinely off rather than a flag
 * the firmware tracks. Nothing here can observe that switch, by design.
 *
 * PROTOCOL (identical text to the serial sketch, just over TCP):
 *   board -> app   "04A3B2C1\n"   a card UID, one per line, per new tap
 *   app -> board   "INVALID\n"    that card isn't registered; go red + beep
 *
 * Card UIDs are the ONLY thing this board ever sends. That is deliberate:
 * the app treats every incoming line as a card ID, so any status chatter
 * mixed into the same stream would be processed as a card and pop up the
 * "register this card" dialog.
 *
 * Lines are also mirrored to USB serial, so a plain Serial Monitor still
 * shows everything while debugging with no laptop-side app running.
 *
 * Nothing blocks waiting for the app's answer. Scanning, the network and
 * the buzzer all keep running; replies are queued and each is held on
 * screen for DISPLAY_HOLD_MS. The earlier version waited 700ms per tap
 * with scanning stopped, so a second student in that window was never
 * read at all - queueing on the app side could not have fixed that.
 *
 * POWER WARNING: WiFi draws in short, sharp bursts. A 9V zinc-chloride
 * battery has high internal resistance and sags under exactly that kind of
 * load, which shows up as random mid-session reboots rather than a clean
 * "battery empty". Use a USB power bank or a 4xAA pack into VIN.
 */

#include <SPI.h>
#include <Wire.h>
#include <WiFi.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>

// Rename freely, but WPA2 refuses to start the AP if the password is
// shorter than 8 characters - the board would silently come up as an open
// network instead.
#define AP_SSID     "TapIn-Reader"
#define AP_PASSWORD "tapin12345"
#define TCP_PORT    8888

#define RST_PIN 21
#define SS_PIN  5

#define LED_GREEN  4
#define LED_YELLOW 16
#define LED_RED    17
#define LED_WHITE  26

#define BUZZER_PIN 27
// A pattern, not one long tone. This module is a weak passive disc, so
// volume is not available to us - but the ear notices CHANGE far more than
// steady sound, so three short pulses read as an alert where a single
// quiet tone of the same length goes unnoticed. Three pulses take 480ms,
// which still finishes inside the post-tap hold below.
#define BEEP_FREQ    4500  // measured: a 3000-6000Hz sweep on this actual
                           // module peaked here. Piezo output falls off
                           // sharply either side of resonance, so this
                           // number is doing real work - a "sensible"
                           // 2000Hz is barely audible on this part.
#define BEEP_ON_MS   90
#define BEEP_GAP_MS  70
#define BEEP_PULSES  3
// This module is printed "Buzzer Module Low Level Trigger" (低电平触发): it
// sounds on LOW and is silent on HIGH, the opposite way round to a bare
// buzzer. Driving it the ordinary way leaves it sounding whenever the pin
// rests at its default LOW - which is not an obvious fault, just a
// permanent weak drone that makes the real beep impossible to pick out.
#define BUZZER_ON  LOW
#define BUZZER_OFF HIGH

#define LCD_SDA 32
#define LCD_SCL 22
#define LCD_ADDR 0x27 // try 0x3F instead if the screen stays blank
// The screen is the slowest thing the reader does: at the library's default 100 kHz, writing a
// message takes ~45 ms, during which nothing else runs. The PCF8574 chip on the backpack is rated
// for 400 kHz, which makes that ~12 ms. Tried on this project's board (4 Oct 2026): clean text on
// every message of a live test. If YOUR wiring is long or loose and the text turns to garbage,
// put 100000 here.
#ifndef LCD_I2C_HZ
#define LCD_I2C_HZ 400000
#endif


MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::Uid lastUid;
bool haveLastUid = false;

LiquidCrystal_I2C lcd(LCD_ADDR, 16, 2);
bool lcdShowingIdle = false;

WiFiServer server(TCP_PORT);
WiFiClient client;
bool clientWasConnected = false; // so connect/disconnect is logged once, not every loop

int beepPulsesLeft = 0;      // pulses still owed in the current pattern
bool beepSounding = false;   // is the tone on right now
unsigned long beepNextChange = 0;

// The beep has to be non-blocking. It fires from inside the post-tap hold
// loop, so a delay() here would nest one blocking wait inside another and
// make every rejected card feel sluggish.
void startBeep() {
  beepPulsesLeft = BEEP_PULSES;
  beepSounding = false;
  beepNextChange = 0; // 0 = act on the very next updateBeep() call
}

// Steps the pattern along without ever blocking: it is called from inside
// the post-tap hold loop, so any delay() here would stall card reading.
void updateBeep() {
  if (beepPulsesLeft <= 0 && !beepSounding) return;
  if (millis() < beepNextChange) return;

  if (beepSounding) {
    noTone(BUZZER_PIN);
    digitalWrite(BUZZER_PIN, BUZZER_OFF);
    beepSounding = false;
    beepPulsesLeft--;
    beepNextChange = millis() + BEEP_GAP_MS;
    return;
  }

  // A passive disc makes no sustained sound from steady DC - it only moves
  // when the voltage across it changes - so this drives a square wave
  // rather than holding the pin at BUZZER_ON.
  tone(BUZZER_PIN, BEEP_FREQ);
  beepSounding = true;
  beepNextChange = millis() + BEEP_ON_MS;
}


void setStatus(bool green, bool yellow, bool red) {
  digitalWrite(LED_GREEN, green ? HIGH : LOW);
  digitalWrite(LED_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(LED_RED, red ? HIGH : LOW);
}

void lcdShow(const char *line1, const char *line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void lcdShowIdle() {
  if (lcdShowingIdle) return;
  lcdShowingIdle = true;
  // The idle screen doubles as the connection indicator - without it
  // there's no way to tell "app is listening" from "app never connected",
  // and both look identical from the student's side of the reader.
  if (client && client.connected()) {
    lcdShow("Ready to scan", "Tap your card");
  } else {
    lcdShow("Waiting for app", AP_SSID);
  }
}

// ---- one reply line from the app, read without ever waiting -----------------
// A reply ("OK:<number>|<name>") is ~30 bytes, which takes ~30 ms to arrive at 9600 baud.
// readStringUntil() would hold the whole loop - card reads, the screen, the beep - for that
// long on every reply, and for a full second if a line ever stopped short. This reads only
// what has already arrived and returns false until a whole line is there; the rest of a line
// waits in the buffer for the next pass.
#define REPLY_MAX 96 // the longest real reply is 37 characters
char replyBuf[REPLY_MAX];
uint8_t replyLen = 0;
bool replyTooLong = false;

bool readReplyLine(Stream &in, String &line) {
  while (in.available()) {
    char c = (char)in.read();
    if (c == '\r') continue;
    if (c != '\n') {
      if (replyLen < REPLY_MAX - 1) replyBuf[replyLen++] = c;
      else replyTooLong = true;
      continue;
    }
    replyBuf[replyLen] = '\0';
    bool usable = replyLen > 0 && !replyTooLong;
    replyLen = 0;
    replyTooLong = false;
    if (!usable) continue; // empty or too long to be a reply: drop it, try the next line
    line = replyBuf;
    line.trim();
    if (line.length() > 0) return true;
  }
  return false;
}

// Every outgoing line goes to both transports: TCP for the app, USB serial
// so a Serial Monitor still works for debugging with no app connected.
void sendLine(const char *text) {
  Serial.println(text);
  if (client && client.connected()) {
    client.println(text);
  }
}

// Picks up a newly connected app, and notices when one drops. Called every
// loop; cheap when nothing has changed.
void updateClient() {
  // A new connection is checked for FIRST, and always wins. A laptop that
  // slept, lost WiFi, or had the app force-quit never sends a proper
  // disconnect, so client.connected() can keep reporting true on a socket
  // that is actually dead. Returning early whenever `client` looks alive
  // would leave the board holding that corpse forever while the real,
  // reconnecting app waits unaccepted - the reader would look perfectly
  // healthy (LCD still "Ready to scan") while no tap ever reached anyone.
  WiFiClient incoming = server.available();
  if (incoming) {
    if (client) {
      client.stop();
    }
    client = incoming;
    // Send each small line at once. Without this, TCP holds a small packet back until the
    // previous one is acknowledged, and a laptop may wait up to 200 ms to acknowledge.
    client.setNoDelay(true);
    replyLen = 0; // a half line from the last connection must not prefix the first of this one
    replyTooLong = false;
    clientWasConnected = true;
    lcdShowingIdle = false;
    Serial.println("App connected.");
    return;
  }

  if (client && client.connected()) {
    return;
  }

  if (clientWasConnected) {
    clientWasConnected = false;
    lcdShowingIdle = false; // force the idle screen back to "Waiting for app"
    Serial.println("App disconnected.");
  }
}

// The next whole line from the app, if one has arrived. Never waits.
bool readAppLine(String &line) {
  if (!client || !client.connected()) return false;
  return readReplyLine(client, line);
}

// ---- display queue -------------------------------------------------------
// Taps can arrive faster than a person can read a name, so results are
// queued and each is held on screen for DISPLAY_HOLD_MS. The card reader
// itself never waits on this: it keeps scanning while the queue drains,
// which is the whole point - the old blocking hold left the board blind
// for 700ms after every tap, so a second student's card was never read at
// all rather than merely shown late.
#define DISPLAY_HOLD_MS  900
#define CHECKING_HOLD_MS 1200
#define QUEUE_SIZE       8
// Card presence flickers for a few ms right after PICC_HaltA(), which in a
// fast loop reads as a fresh tap. This floor absorbs that. It is kept short
// on purpose: a genuine lift-and-retap must still get through, and that is
// exactly what a rejected student does straight away.
#define REREAD_FLOOR_MS  250

struct ReaderMessage {
  char line1[17];
  char line2[17];
  bool green;
  bool red;
  bool beep;
};

ReaderMessage messageQueue[QUEUE_SIZE];
int queueHead = 0;
int queueCount = 0;
unsigned long displayUntil = 0;
bool showingChecking = false;

MFRC522::Uid lastSentUid;
bool haveSentUid = false;
unsigned long lastSentAt = 0;
unsigned long lastReadErrorAt = 0;

void enqueueMessage(const char *line1, const char *line2, bool green, bool red, bool beep) {
  if (queueCount == QUEUE_SIZE) {
    // Full: drop the OLDEST. Those people have already walked away, so
    // catching the screen up toward the person actually standing there
    // beats faithfully replaying a backlog nobody is waiting on.
    queueHead = (queueHead + 1) % QUEUE_SIZE;
    queueCount--;
  }
  ReaderMessage &slot = messageQueue[(queueHead + queueCount) % QUEUE_SIZE];
  strncpy(slot.line1, line1, 16); slot.line1[16] = '\0';
  strncpy(slot.line2, line2, 16); slot.line2[16] = '\0';
  slot.green = green;
  slot.red = red;
  slot.beep = beep;
  queueCount++;
}

// Splits "<number>|<name>" onto the two screen lines. The board never knows
// who a card belongs to - only the app does - so this text is the only way
// the screen can name a student rather than echo a card serial number.
void enqueuePayload(const String &payload, bool green) {
  int bar = payload.indexOf('|');
  if (bar < 0) {
    enqueueMessage(payload.c_str(), "", green, false, false);
    return;
  }
  enqueueMessage(payload.substring(0, bar).c_str(),
                 payload.substring(bar + 1).c_str(), green, false, false);
}

void updateDisplay() {
  // "Checking" is a placeholder, so a real result may replace it at once
  // rather than waiting out its hold.
  if (queueCount > 0 && (showingChecking || millis() >= displayUntil)) {
    ReaderMessage &m = messageQueue[queueHead];
    lcdShow(m.line1, m.line2);
    setStatus(m.green, !m.green && !m.red, m.red);
    if (m.beep) startBeep();
    displayUntil = millis() + DISPLAY_HOLD_MS;
    showingChecking = false;
    lcdShowingIdle = false;
    queueHead = (queueHead + 1) % QUEUE_SIZE;
    queueCount--;
    return;
  }

  if (millis() < displayUntil) return;

  showingChecking = false;
  setStatus(false, true, false); // yellow: listening
  lcdShowIdle();
}

void readCard() {
  if (!rfid.PICC_IsNewCardPresent()) {
    // Presence-based reset, deliberately not a timer: lifting a card off
    // and tapping it again must be re-checked with the app, and a student
    // who was just rejected does exactly that within a moment.
    haveLastUid = false;
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    // In range but the read did not complete (moved too fast, collision).
    // Rate-limited so a card wobbling on the reader cannot flood the queue
    // and push real results off the end of it.
    if (millis() - lastReadErrorAt > 1000) {
      lastReadErrorAt = millis();
      enqueueMessage("Read error", "Try again", false, true, false);
    }
    return;
  }

  bool stillOnReader = haveLastUid && sameUid(lastUid, rfid.uid);
  bool justSent = haveSentUid && sameUid(lastSentUid, rfid.uid)
                  && (millis() - lastSentAt) < REREAD_FLOOR_MS;

  lastUid = rfid.uid;
  haveLastUid = true;

  if (stillOnReader || justSent) {
    rfid.PICC_HaltA();
    return;
  }

  char uidStr[21]; // up to 10 UID bytes * 2 hex chars + null terminator
  uidToHexString(rfid.uid, uidStr);

  // Sent unconditionally, never gated on queue space. A full display queue
  // costs one person their on-screen confirmation; a dropped UID would cost
  // them their attendance record.
  sendLine(uidStr);

  lastSentUid = rfid.uid;
  haveSentUid = true;
  lastSentAt = millis();
  rfid.PICC_HaltA();

  if (queueCount == 0) {
    // Immediate feedback, so a closed app is distinguishable from a dead
    // reader. Never queued - the real answer replaces it the moment it lands.
    lcdShow("Checking card", "Please wait...");
    lcdShowingIdle = false;
    showingChecking = true;
    displayUntil = millis() + CHECKING_HOLD_MS;
  }
}

void handleAppReply() {
  String reply;
  if (!readAppLine(reply)) return;

  if (reply == "INVALID") {
    enqueueMessage("Invalid card", "Not registered", false, true, true);
  } else if (reply.startsWith("OK:")) {
    enqueuePayload(reply.substring(3), true);
  } else if (reply.startsWith("MSG:")) {
    enqueuePayload(reply.substring(4), false);
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  setStatus(false, true, false); // yellow: listening

  // Set the output latch BEFORE enabling the output, so the pin never
  // spends a moment driving the buzzer on during startup.
  digitalWrite(BUZZER_PIN, BUZZER_OFF);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, BUZZER_OFF);

  // Power indicator: lit for as long as the board has power, which is
  // exactly what the battery switch controls.
  pinMode(LED_WHITE, OUTPUT);
  digitalWrite(LED_WHITE, HIGH);

  Wire.begin(LCD_SDA, LCD_SCL);
  Wire.setClock(LCD_I2C_HZ);
  lcd.init();
  lcd.backlight();
  lcdShow("Starting WiFi", AP_SSID);

  WiFi.softAP(AP_SSID, AP_PASSWORD);
  IPAddress ip = WiFi.softAPIP();
  Serial.print("AP \"" AP_SSID "\" up. Connect the laptop, then point ");
  Serial.print(".hardware_config.json at ");
  Serial.print(ip);
  Serial.print(":");
  Serial.println(TCP_PORT);

  server.begin();
  lcdShowIdle();

  SPI.begin();
  rfid.PCD_Init();

  // A real RC522 answers this with 0x91 or 0x92. 0x00/0xFF means SPI isn't
  // reaching the reader at all (loose wire), even though both power LEDs
  // are lit - those only prove 3.3V is present, not that data flows.
  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  Serial.print("RC522 version register: 0x");
  Serial.println(version, HEX);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("RC522 not responding - check SDA/SCK/MOSI/MISO/RST wiring.");
  } else {
    Serial.println("RC522 OK. Tap a card...");
  }
}

bool sameUid(const MFRC522::Uid &a, const MFRC522::Uid &b) {
  if (a.size != b.size) return false;
  for (byte i = 0; i < a.size; i++) {
    if (a.uidByte[i] != b.uidByte[i]) return false;
  }
  return true;
}

void uidToHexString(const MFRC522::Uid &uid, char *out) {
  for (byte i = 0; i < uid.size; i++) {
    byte b = uid.uidByte[i];
    out[i * 2] = "0123456789ABCDEF"[b >> 4];
    out[i * 2 + 1] = "0123456789ABCDEF"[b & 0x0F];
  }
  out[uid.size * 2] = '\0';
}

void loop() {
  updateClient();
  updateBeep();
  handleAppReply();
  readCard();
  updateDisplay();
  // A pass takes ~23 ms on its own (the RC522 poll waits for a card that is not there), so
  // the SPI bus is never hammered; this short pause only lets the other tasks breathe.
  // Measured on the board: delay(20) made a pass ~43 ms (23 per second); delay(5) makes it
  // ~28 ms (about 36 per second), so a tap is noticed ~15 ms sooner at worst.
  delay(5);
}
