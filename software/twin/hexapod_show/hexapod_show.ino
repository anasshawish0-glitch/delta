// Kitty Hexapod booth show: runs on its own, no computer needed.
//
// The robot hangs on a stand with its legs in the air. Every SHOW_EVERY_S seconds (and once, a
// few seconds after power-up) it wakes up, stretches, walks in the air, does one special move
// (wave, dance or turn, a different one each time) and relaxes again. Between shows every servo
// is switched off, so nothing heats up and almost no current is drawn.
//
// The moves come from the same kinematics as the Kitty Twin page (hexapod.html), baked into
// show_data.h by make_show.mjs, a bit slower and lower than on the page.
//
// It still speaks the page's USB protocol (S / R / ?), so the page can drive the robot with this
// sketch too; a pose from the page pauses the show for a minute. "P" over USB starts a show now.
//
// Wiring is the same as hexapod_serial.ino: Arduino UNO, two PCA9685 boards, B1 = 0x40,
// B2 = 0x41 (A0 bridged); servo power from the regulator straight to each board's green terminal.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <avr/pgmspace.h>
#include "show_data.h"

// ---------- settings ----------
const unsigned long SHOW_EVERY_S = 120;  // seconds from the end of one show to the start of the next
const unsigned long FIRST_SHOW_S = 5;    // first show this long after power-up
const unsigned long WALK_S = 15;         // walking in the air, per show
const unsigned long TURN_S = 8;          // the "turn" special move
const float MAX_STEP = 3;                // degrees per 20 ms (150°/s): gentle on the 5 V regulator
const uint8_t WAKE_PER_TICK = 1;         // servos switched on per 20 ms when waking up

// Optional distance sensor (HC-SR04): start a show when someone comes closer than TRIGGER_CM.
#define USE_SONAR 0
const uint8_t TRIG_PIN = 7, ECHO_PIN = 8;
const uint16_t TRIGGER_CM = 80;
const unsigned long COOLDOWN_S = 20;     // at least this long between sonar-started shows

// ---------- servos (same as hexapod_serial.ino) ----------
const uint16_t SERVOMIN = 150;   // ticks at 0°
const uint16_t SERVOMAX = 600;   // ticks at 180°
Adafruit_PWMServoDriver board[2] = { Adafruit_PWMServoDriver(0x40), Adafruit_PWMServoDriver(0x41) };
// Board (1 or 2) and channel of every joint, by leg: { coxa, femur, tibia }
const uint8_t MB[6][3] = { { 1, 1, 1 }, { 1, 1, 1 }, { 1, 1, 1 }, { 1, 2, 2 }, { 2, 2, 2 }, { 2, 2, 2 } };
const uint8_t MC[6][3] = { { 10, 9, 11 }, { 7, 6, 5 }, { 0, 1, 2 }, { 15, 1, 3 }, { 13, 10, 8 }, { 7, 6, 5 } };

void startServos() {
  Wire.begin();
  Wire.setClock(400000);
  for (Adafruit_PWMServoDriver &b : board) { b.begin(); b.setPWMFreq(50); }
}
void writeAngle(uint8_t i, float deg) {
  uint16_t ticks = SERVOMIN + (uint16_t)(deg * (SERVOMAX - SERVOMIN) / 180);
  board[MB[i / 3][i % 3] - 1].setPWM(MC[i / 3][i % 3], 0, ticks);
}
void relaxOne(uint8_t i) { board[MB[i / 3][i % 3] - 1].setPWM(MC[i / 3][i % 3], 0, 4096); }  // full off

float target[18], cur[18];
bool wanted[18], live[18];
void relaxAll() { for (uint8_t i = 0; i < 18; i++) { relaxOne(i); wanted[i] = live[i] = false; } }
void setTargetsP(const uint8_t *p) { for (uint8_t i = 0; i < 18; i++) { target[i] = pgm_read_byte(p + i); wanted[i] = true; } }
bool reached() {
  for (uint8_t i = 0; i < 18; i++) if (wanted[i] && (!live[i] || fabs(target[i] - cur[i]) > 0.5)) return false;
  return true;
}
// every 20 ms: switch on waiting servos a few at a time, ease the others toward their targets
void tick() {
  uint8_t woke = 0;
  for (uint8_t i = 0; i < 18; i++) {
    if (!wanted[i]) continue;
    if (!live[i]) {
      if (woke == WAKE_PER_TICK) continue;
      cur[i] = target[i]; live[i] = true; woke++;
      writeAngle(i, cur[i]);
      continue;
    }
    float d = constrain(target[i] - cur[i], -MAX_STEP, MAX_STEP);
    if (d != 0) { cur[i] += d; writeAngle(i, cur[i]); }
  }
}

// ---------- the show ----------
struct Clip { const uint8_t (*f)[18]; uint16_t n; unsigned long loopMs; };  // loopMs 0 = play once
enum Act : uint8_t { A_STAND, A_SIT, A_HOLD, A_CLIP, A_RELAX, A_END };
struct Step { Act act; uint8_t clip; uint16_t ms; };
Clip clips[] = {
  { WALK, WALK_N, WALK_S * 1000UL },
  { WAVE, WAVE_N, 0 },
  { DANCE, DANCE_N, 0 },
  { TURN, TURN_N, TURN_S * 1000UL },
};
const uint8_t SPECIALS[] = { 1, 2, 3 };  // wave, dance, turn: one per show, in turn
Step plan[] = {
  { A_STAND, 0, 0 }, { A_HOLD, 0, 800 },        // wake up into the stand pose
  { A_SIT, 0, 0 }, { A_STAND, 0, 0 },          // stretch: legs up and down again
  { A_HOLD, 0, 400 }, { A_CLIP, 0, 0 },         // walk in the air
  { A_STAND, 0, 0 }, { A_HOLD, 0, 600 },
  { A_CLIP, 255, 0 },                          // the special move of this show
  { A_STAND, 0, 0 }, { A_HOLD, 0, 800 },
  { A_RELAX, 0, 0 }, { A_END, 0, 0 },
};
bool showing = false;
uint8_t stepNo = 0, phase = 0, special = 0;
uint16_t frame = 0;
unsigned long stepAt = 0, frameAt = 0, showEnd = 0, pcUntil = 0;

void startShow() {
  showing = true; stepNo = 0; phase = 0; stepAt = millis();
  Serial.println(F("show: start"));
}
void nextStep() { stepNo++; phase = 0; stepAt = millis(); }

void runShow() {
  Step &s = plan[stepNo];
  unsigned long now = millis();
  switch (s.act) {
    case A_STAND:
    case A_SIT:
      if (phase == 0) { setTargetsP(s.act == A_STAND ? STAND : SIT); phase = 1; }
      else if (reached()) nextStep();
      break;
    case A_HOLD:
      if (now - stepAt >= s.ms) nextStep();
      break;
    case A_CLIP: {
      Clip &c = clips[s.clip == 255 ? SPECIALS[special] : s.clip];
      if (phase == 0) { setTargetsP(c.f[0]); phase = 1; }                       // ease to the first frame
      else if (phase == 1) { if (reached()) { frame = 0; frameAt = now; stepAt = now; phase = 2; } }
      else if (now - frameAt >= FRAME_MS) {
        frameAt += FRAME_MS;
        if (++frame >= c.n) {
          frame = 0;
          if (c.loopMs == 0 || now - stepAt >= c.loopMs) { nextStep(); break; }  // a looped clip ends on a whole cycle
        }
        setTargetsP(c.f[frame]);
      }
      break;
    }
    case A_RELAX:
      relaxAll(); nextStep();
      break;
    case A_END:
      showing = false; showEnd = now;
      special = (special + 1) % sizeof(SPECIALS);
      Serial.println(F("show: done"));
      break;
  }
}

#if USE_SONAR
uint16_t distanceCm() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10); digitalWrite(TRIG_PIN, LOW);
  unsigned long us = pulseIn(ECHO_PIN, HIGH, 25000UL);
  return us ? us / 58 : 999;
}
#endif

// ---------- USB: the page's protocol, plus P = show now ----------
char line[100];
uint8_t len = 0;
void handle(char *s) {
  if (s[0] == 'S') {
    int deg[18]; uint8_t n = 0; char *p = s + 1;
    while (n < 18) { deg[n++] = atoi(p); p = strchr(p, ','); if (!p) break; p++; }
    if (n == 18) {
      showing = false; pcUntil = millis() + 60000UL;
      for (uint8_t i = 0; i < 18; i++) { target[i] = constrain(deg[i], 0, 180); wanted[i] = true; }
    }
  } else if (s[0] == 'R') {
    showing = false; relaxAll(); showEnd = millis();
  } else if (s[0] == '?') {
    Serial.println(F("HEXAPOD v1"));
  } else if (s[0] == 'P' && !showing) {
    pcUntil = 0; startShow();
  }
}

unsigned long lastTick = 0, lastPing = 0;
void setup() {
  Serial.begin(115200);
  startServos();
  relaxAll();
#if USE_SONAR
  pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT);
#endif
  showEnd = millis() - SHOW_EVERY_S * 1000UL + FIRST_SHOW_S * 1000UL;  // first show soon after power-up
  Serial.println(F("HEXAPOD v1"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (len) { line[len] = 0; handle(line); len = 0; } }
    else if (len < sizeof(line) - 1) line[len++] = c;
    else len = 0;
  }
  unsigned long now = millis();
  bool pc = (long)(pcUntil - now) > 0;
  if (!showing && !pc && now - showEnd >= SHOW_EVERY_S * 1000UL) startShow();
#if USE_SONAR
  if (!showing && !pc && now - showEnd >= COOLDOWN_S * 1000UL && now - lastPing >= 200) {
    lastPing = now;
    if (distanceCm() < TRIGGER_CM) startShow();
  }
#endif
  if (showing) runShow();
  if (now - lastTick >= 20) { lastTick = now; tick(); }
}
