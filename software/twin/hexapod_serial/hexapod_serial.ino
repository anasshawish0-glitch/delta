// Kitty Hexapod: drives 18 servos on two PCA9685 boards from the Kitty Twin web page over USB.
//
// The page sends one line per frame at 115200 baud:
//   S90,90,90,...   18 angles in degrees (0-180), in this order:
//                   R1 coxa, femur, tibia, R2 ..., R3 ..., L1 ..., L2 ..., L3 ...
//                   (R = right, L = left, 1 = front, 2 = middle, 3 = back)
//   R               relax: switch every servo off
//   ?               the sketch answers "HEXAPOD v1"
//
// Needs the "Adafruit PWM Servo Driver Library" (Arduino IDE: Tools > Manage Libraries).
// Power the servos from their own 5-6 V supply on the PCA9685 V+ terminal, never from the
// Arduino 5 V pin, and connect the grounds together.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver boardA(0x40);  // right legs
Adafruit_PWMServoDriver boardB(0x41);  // left legs (solder the A0 jumper on this board)

// Where each servo is plugged in, in the order the page sends them.
// 0-15 = channel on board A, 16-31 = channel 0-15 on board B. Change these to match your wiring.
const uint8_t CHANNEL[18] = {
  0, 1, 2,     // R1 coxa, femur, tibia
  4, 5, 6,     // R2
  8, 9, 10,    // R3
  16, 17, 18,  // L1
  20, 21, 22,  // L2
  24, 25, 26,  // L3
};

// Pulse width for 0 and 180 degrees. Most hobby servos use 500-2500 us; some use 1000-2000.
const uint16_t MIN_US = 500;
const uint16_t MAX_US = 2500;

char line[100];
uint8_t len = 0;

Adafruit_PWMServoDriver &boardFor(uint8_t ch) { return ch < 16 ? boardA : boardB; }

void writeServo(uint8_t i, int deg) {
  deg = constrain(deg, 0, 180);
  uint16_t us = map(deg, 0, 180, MIN_US, MAX_US);
  boardFor(CHANNEL[i]).writeMicroseconds(CHANNEL[i] & 15, us);
}

void relaxAll() {
  for (uint8_t i = 0; i < 18; i++) boardFor(CHANNEL[i]).setPWM(CHANNEL[i] & 15, 0, 4096);  // full off
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
    if (n == 18) for (uint8_t i = 0; i < 18; i++) writeServo(i, deg[i]);
  } else if (s[0] == 'R') {
    relaxAll();
  } else if (s[0] == '?') {
    Serial.println(F("HEXAPOD v1"));
  }
}

void startBoard(Adafruit_PWMServoDriver &b) {
  b.begin();
  b.setOscillatorFrequency(27000000);
  b.setPWMFreq(50);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  startBoard(boardA);
  startBoard(boardB);
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
}
