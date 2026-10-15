// Kitty Hexapod: drives the 18 servos of the hexapod from the Kitty Twin web page over USB.
//
// The page sends one line per frame at 115200 baud:
//   S55,105,60,...  18 angles in degrees (0-180) in the robot's own leg order:
//                   Leg 1 coxa, femur, tibia, Leg 2 ..., Leg 6
//   R               relax: switch every servo off
//   ?               the sketch answers "HEXAPOD v1"
//
// Servos move toward each new angle by at most MAX_STEP degrees every 20 ms and switch on two at
// a time, so a jump in the commands never becomes a current spike through all 18 at once.
//
// Wiring (CHANNELS.md): Arduino UNO, two PCA9685 boards, B1 = 0x40, B2 = 0x41 (A0 bridged).
// Servo power goes from the regulator straight to each board's green terminal, never through the
// Arduino or the header pins, with the grounds shared.

#define USE_PCA9685 1

const float MAX_STEP = 4;  // degrees per 20 ms (200°/s); an MG996R tops out near 350°/s

#if USE_PCA9685
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Angle -> PCA9685 ticks. Use the same three numbers as your hexapod_walk_final.ino, so that an
// angle means the same horn position there and here (these are Adafruit's example values).
const uint16_t SERVOMIN = 150;   // ticks at 0°
const uint16_t SERVOMAX = 600;   // ticks at 180°
const long OSC_FREQ = 27000000;  // what your code passes to setOscillatorFrequency (library default 25000000)

Adafruit_PWMServoDriver board[2] = { Adafruit_PWMServoDriver(0x40), Adafruit_PWMServoDriver(0x41) };

// Board (1 or 2) and channel of every joint, by leg: { coxa, femur, tibia }
const uint8_t MB[6][3] = {
  { 1, 1, 1 },  // Leg 1
  { 1, 1, 1 },  // Leg 2
  { 1, 1, 1 },  // Leg 3
  { 1, 2, 2 },  // Leg 4
  { 2, 2, 2 },  // Leg 5
  { 2, 2, 2 },  // Leg 6
};
const uint8_t MC[6][3] = {
  { 10, 9, 11 },  // Leg 1
  { 7, 6, 5 },    // Leg 2
  { 0, 1, 2 },    // Leg 3
  { 15, 1, 3 },   // Leg 4
  { 13, 10, 8 },  // Leg 5
  { 7, 6, 5 },    // Leg 6
};

void startServos() {
  Wire.begin();
  Wire.setClock(400000);
  for (Adafruit_PWMServoDriver &b : board) {
    b.begin();
    b.setOscillatorFrequency(OSC_FREQ);
    b.setPWMFreq(50);
  }
}
void writeAngle(uint8_t i, float deg) {
  uint16_t ticks = SERVOMIN + (uint16_t)(deg * (SERVOMAX - SERVOMIN) / 180 + 0.5);
  board[MB[i / 3][i % 3] - 1].setPWM(MC[i / 3][i % 3], 0, ticks);
}
void relaxOne(uint8_t i) { board[MB[i / 3][i % 3] - 1].setPWM(MC[i / 3][i % 3], 0, 4096); }  // full off

#else
#include <Servo.h>

// For servos plugged straight into an Arduino Mega: pulse width at 0° and 180°, and the pin of
// every joint by leg { coxa, femur, tibia }.
const uint16_t MIN_US = 500;
const uint16_t MAX_US = 2500;
const uint8_t PIN[6][3] = {
  { 22, 23, 24 }, { 25, 26, 27 }, { 28, 29, 30 }, { 31, 32, 33 }, { 34, 35, 36 }, { 37, 38, 39 },
};
Servo servo[18];

void startServos() {}
void writeAngle(uint8_t i, float deg) {
  if (!servo[i].attached()) servo[i].attach(PIN[i / 3][i % 3], MIN_US, MAX_US);
  servo[i].writeMicroseconds(MIN_US + (uint16_t)(deg * (MAX_US - MIN_US) / 180 + 0.5));
}
void relaxOne(uint8_t i) { servo[i].detach(); }
#endif

float target[18], cur[18];
bool wanted[18], live[18];  // has a target / is powered and at cur
unsigned long lastTick = 0;
char line[100];
uint8_t len = 0;

void relaxAll() {
  for (uint8_t i = 0; i < 18; i++) { relaxOne(i); wanted[i] = live[i] = false; }
}

void handle(char *s) {
  if (s[0] == 'S') {
    int deg[18];
    uint8_t n = 0;
    char *p = s + 1;
    while (n < 18) {
      deg[n++] = atoi(p);
      p = strchr(p, ',');
      if (!p) break;
      p++;
    }
    if (n == 18) for (uint8_t i = 0; i < 18; i++) { target[i] = constrain(deg[i], 0, 180); wanted[i] = true; }
  } else if (s[0] == 'R') {
    relaxAll();
  } else if (s[0] == '?') {
    Serial.println(F("HEXAPOD v1"));
  }
}

// every 20 ms: switch on up to two waiting servos, ease the others toward their targets
void tick() {
  uint8_t woke = 0;
  for (uint8_t i = 0; i < 18; i++) {
    if (!wanted[i]) continue;
    if (!live[i]) {
      if (woke == 2) continue;
      cur[i] = target[i]; live[i] = true; woke++;
      writeAngle(i, cur[i]);
      continue;
    }
    float d = constrain(target[i] - cur[i], -MAX_STEP, MAX_STEP);
    if (d != 0) { cur[i] += d; writeAngle(i, cur[i]); }
  }
}

void setup() {
  Serial.begin(115200);
  startServos();
  relaxAll();  // servos stay limp until the page sends the first pose
  Serial.println(F("HEXAPOD v1"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (len) { line[len] = 0; handle(line); len = 0; }
    } else if (len < sizeof(line) - 1) {
      line[len++] = c;
    } else {
      len = 0;  // line too long: drop it
    }
  }
  if (millis() - lastTick >= 20) { lastTick = millis(); tick(); }
}
