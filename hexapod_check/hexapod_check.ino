// Kitty Hexapod channel check: moves one servo at a time so you can see which joint is on which
// board and channel. Put the robot on a box with the legs free first.
//
// Open the Serial Monitor at 115200 baud (line ending: Newline), then type and press Enter:
//   n        next servo (Leg 1 coxa, Leg 1 femur, Leg 1 tibia, Leg 2 coxa ... Leg 6 tibia)
//   1-18     jump to that servo
// The chosen servo goes to its standing angle and swings ±10° three times; every other servo is
// switched off. The Serial Monitor prints which joint should be moving.
//
// Uploading this replaces the program on the Arduino, so keep a backup of your old one.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// same values as hexapod_serial.ino (and your old code)
const uint16_t SERVOMIN = 150;
const uint16_t SERVOMAX = 600;
const long OSC_FREQ = 27000000;

Adafruit_PWMServoDriver board[2] = { Adafruit_PWMServoDriver(0x40), Adafruit_PWMServoDriver(0x41) };

const uint8_t MB[6][3] = { { 1, 1, 1 }, { 1, 1, 1 }, { 1, 1, 1 }, { 1, 2, 2 }, { 2, 2, 2 }, { 2, 2, 2 } };
const uint8_t MC[6][3] = { { 10, 9, 11 }, { 7, 6, 5 }, { 0, 1, 2 }, { 15, 1, 3 }, { 13, 10, 8 }, { 7, 6, 5 } };
const uint8_t STAND[6][3] = { { 55, 105, 60 }, { 60, 110, 95 }, { 65, 110, 80 }, { 60, 120, 155 }, { 40, 95, 60 }, { 40, 95, 60 } };
const char *const JOINT[3] = { "coxa (hip, in the body)", "femur (thigh, in the bracket)", "tibia (knee, at the claw)" };
const char *const PLACE[6] = { "front right", "middle right", "back right", "back left", "middle left", "front left" };

char line[8];
uint8_t len = 0;

void setAngle(uint8_t leg, uint8_t j, int deg) {
  deg = constrain(deg, 0, 180);
  board[MB[leg][j] - 1].setPWM(MC[leg][j], 0, SERVOMIN + (uint32_t)deg * (SERVOMAX - SERVOMIN) / 180);
}
void allOff() {
  for (uint8_t leg = 0; leg < 6; leg++)
    for (uint8_t j = 0; j < 3; j++) board[MB[leg][j] - 1].setPWM(MC[leg][j], 0, 4096);
}

void show(uint8_t i) {  // i = 0..17
  uint8_t leg = i / 3, j = i % 3;
  allOff();
  Serial.print(F("Servo ")); Serial.print(i + 1); Serial.print(F(": Leg ")); Serial.print(leg + 1);
  Serial.print(F(" ")); Serial.print(JOINT[j]); Serial.print(F(", ")); Serial.print(PLACE[leg]);
  Serial.print(F(" -> board ")); Serial.print(MB[leg][j]); Serial.print(MB[leg][j] == 1 ? F(" (0x40)") : F(" (0x41)"));
  Serial.print(F(" channel ")); Serial.println(MC[leg][j]);
  int s = STAND[leg][j];
  setAngle(leg, j, s);
  delay(400);
  for (uint8_t k = 0; k < 3; k++) {
    for (int d = 0; d <= 10; d++) { setAngle(leg, j, s + d); delay(15); }
    for (int d = 10; d >= -10; d--) { setAngle(leg, j, s + d); delay(15); }
    for (int d = -10; d <= 0; d++) { setAngle(leg, j, s + d); delay(15); }
  }
}

uint8_t current = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  for (Adafruit_PWMServoDriver &b : board) {
    b.begin();
    b.setOscillatorFrequency(OSC_FREQ);
    b.setPWMFreq(50);
  }
  allOff();
  Serial.println(F("Channel check. Type n for the next servo, or 1-18."));
  show(current);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c != '\n' && c != '\r') { if (len < sizeof(line) - 1) line[len++] = c; continue; }
    line[len] = 0; len = 0;
    int n = atoi(line);
    if (n >= 1 && n <= 18) current = n - 1;
    else if (line[0] == 'n' || line[0] == 'N') current = (current + 1) % 18;
    else continue;
    show(current);
  }
}
