// Hexapod - المشي + تلويح بالرجلين القدامية + موجة ناعمة + رقص (نسخة أبطأ)
// board 1 = 0x40   |   board 2 = 0x41
// Tripod A : Leg 1,3,5    Tripod B : Leg 2,4,6

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver b1 = Adafruit_PWMServoDriver(0x40);
Adafruit_PWMServoDriver b2 = Adafruit_PWMServoDriver(0x41);

// ======== الإعدادات ========

// وضعية الوقوف
const int COXA_MID   = 55;
const int FEMUR_DOWN = 105;
const int TIBIA_DOWN = 65;

// المشية
const int COXA_SWING = 20;    // طول الخطوة
const int FEMUR_LIFT = 45;    // رفع الرجل - مؤكد بالتجربة
const int TIBIA_LIFT = 0;

// السرعة
const int MS_LIFT  = 360;    // كان 180
const int MS_SWING = 640;    // كان 320

// التوقيت
const int STARTUP_DELAY = 5000;
const int WALK_STEPS    = 4;      // خلّها 0 لو ما تبيه يمشي
const int PAUSE_MS      = 2000;
const int STAND_GAP_MS  = 120;    // بين سيرفو والثاني وقت الوقوف (كان 35)

// التلويح بالرجلين القدامية: Leg 1 (قدام يمين) و Leg 6 (قدام يسار)
const uint8_t WAVE_LEGS[2] = { 0, 5 };
const int WAVE_LIFT    = 60;   // كم ترتفع الرجل
const int WAVE_TIBIA   = -45;  // فرد المخلب لفوق
const int WAVE_SWING   = 25;   // التلويح لبرا ولجوا
const int WAVE_TIMES   = 3;    // كم مرة يلوّح
const int MS_WAVE      = 350;  // سرعة التلويح

// الموجة الناعمة: الفيمر بس، الرجول ترتفع وحدة ورا الثانية حوالين الجسم
const uint8_t RIPPLE_ORDER[6] = { 0, 1, 2, 3, 4, 5 };   // Leg 1 -> 2 -> 3 -> 4 -> 5 -> 6
const int   RIPPLE_LIFT   = 40;     // كم ترتفع كل رجل (لا تعدّي 60)
const int   RIPPLE_ROUNDS = 2;      // كم لفة
const long  RIPPLE_PERIOD = 2400;   // وقت اللفة الوحدة بالملي ثانية (أكبر = أبطأ)
const float RIPPLE_WIDTH  = 0.34;   // كم من اللفة كل رجل تكون فوق (أكبر = رجول أكثر فوق مع بعض)
const long  RIPPLE_EASE   = 700;    // بداية ونهاية بالتدريج

// الرقص
const long DANCE_BEAT  = 600;   // وقت الدقة بالملي ثانية (أصغر = أسرع)
const int  DANCE_BEATS = 18;    // طول الرقصة بالدقات
const int  BOUNCE_LIFT = 30;    // النط: الحامل الثلاثي يطلع وينزل
const int  TWIST_SWING = 20;    // اللف يمين ويسار
const int  TWIST_KICK  = 10;    // نطة صغيرة على كل دقة وقت اللف
const int  ROCK_LIFT   = 35;    // المرجيحة: قدام وورا

// اتجاه الـ coxa   +1 يمين   -1 يسار
const int CDIR[6] = { 1, 1, 1, -1, -1, -1 };

// المعايرة   { coxa , femur , tibia }
const int8_t TRIM[6][3] = {
  {   0,   0,  -5 },   // Leg 1
  {   5,   5,  30 },   // Leg 2
  {  10,   5,  15 },   // Leg 3
  {   5,  15,  90 },   // Leg 4
  { -15, -10,  -5 },   // Leg 5
  { -15, -10,  -5 }    // Leg 6
};

// ===========================

// خريطة اللوحات   0=coxa 1=femur 2=tibia
const uint8_t MB[6][3] = {
  { 1, 1, 1 },
  { 1, 1, 1 },
  { 1, 1, 1 },
  { 1, 2, 2 },
  { 2, 2, 2 },
  { 2, 2, 2 }
};

// خريطة القنوات
const uint8_t MC[6][3] = {
  { 10,  9, 11 },
  {  7,  6,  5 },
  {  0,  1,  2 },
  { 15,  1,  3 },
  { 13, 10,  8 },
  {  7,  6,  5 }
};

const uint8_t TA[3] = { 0, 2, 4 };
const uint8_t TB[3] = { 1, 3, 5 };

int cur[6][3];
int tgt[6][3];

void wr(uint8_t l, uint8_t j, int a) {
  a += TRIM[l][j];
  if (a < 0)   a = 0;
  if (a > 180) a = 180;

  int p = map(a, 0, 180, 150, 600);
  if (MB[l][j] == 1) b1.setPWM(MC[l][j], 0, p);
  else               b2.setPWM(MC[l][j], 0, p);
}

// نفس wr بس بكسور الدرجة، عشان الحركة البطيئة تطلع ناعمة
void wrF(uint8_t l, uint8_t j, float a) {
  a += TRIM[l][j];
  if (a < 0)   a = 0;
  if (a > 180) a = 180;

  int p = 150 + (int)(a * 450.0 / 180.0 + 0.5);
  if (MB[l][j] == 1) b1.setPWM(MC[l][j], 0, p);
  else               b2.setPWM(MC[l][j], 0, p);
}

void moveAll(int ms) {
  int steps = ms / 20;
  if (steps < 1) steps = 1;

  int st[6][3];
  for (uint8_t l = 0; l < 6; l++)
    for (uint8_t j = 0; j < 3; j++)
      st[l][j] = cur[l][j];

  for (int s = 1; s <= steps; s++) {
    long p = (long)s * 1000 / steps;
    long e = (p * p / 1000) * (3000 - 2 * p) / 1000;

    for (uint8_t l = 0; l < 6; l++)
      for (uint8_t j = 0; j < 3; j++)
        wr(l, j, st[l][j] + (int)(((long)(tgt[l][j] - st[l][j]) * e) / 1000));

    delay(20);
  }

  for (uint8_t l = 0; l < 6; l++)
    for (uint8_t j = 0; j < 3; j++)
      cur[l][j] = tgt[l][j];
}

void tStand() {
  for (uint8_t l = 0; l < 6; l++) {
    tgt[l][0] = COXA_MID;
    tgt[l][1] = FEMUR_DOWN;
    tgt[l][2] = TIBIA_DOWN;
  }
}

void tLift(const uint8_t *t, bool up) {
  for (uint8_t i = 0; i < 3; i++) {
    uint8_t l = t[i];
    tgt[l][1] = FEMUR_DOWN + (up ? FEMUR_LIFT : 0);
    tgt[l][2] = TIBIA_DOWN + (up ? TIBIA_LIFT : 0);
  }
}

void tCoxa(const uint8_t *t, int dir) {
  for (uint8_t i = 0; i < 3; i++) {
    uint8_t l = t[i];
    tgt[l][0] = COXA_MID + dir * COXA_SWING * CDIR[l];
  }
}

void standUp() {
  tStand();
  for (uint8_t j = 0; j < 3; j++) {
    for (uint8_t l = 0; l < 6; l++) {
      cur[l][j] = tgt[l][j];
      wr(l, j, tgt[l][j]);
      delay(STAND_GAP_MS);
    }
  }
  Serial.println("STAND");
}

void halfStep(const uint8_t *sw, const uint8_t *sup) {
  tLift(sw, true);
  moveAll(MS_LIFT);

  tCoxa(sw, 1);
  tCoxa(sup, -1);
  moveAll(MS_SWING);

  tLift(sw, false);
  moveAll(MS_LIFT);
}

// ---------- التلويح بالرجلين القدامية ----------
void waveSwing(int dir) {
  for (uint8_t i = 0; i < 2; i++) {
    uint8_t l = WAVE_LEGS[i];
    tgt[l][0] = COXA_MID + dir * WAVE_SWING * CDIR[l];   // مرايا: الثنتين لبرا أو لجوا مع بعض
  }
  moveAll(MS_WAVE);
}

void wave() {
  Serial.println("WAVE");

  // يرفع الرجلين ويفرد المخالب
  tStand();
  for (uint8_t i = 0; i < 2; i++) {
    uint8_t l = WAVE_LEGS[i];
    tgt[l][1] = FEMUR_DOWN + WAVE_LIFT;
    tgt[l][2] = TIBIA_DOWN + WAVE_TIBIA;
  }
  moveAll(700);

  // يلوّح
  for (int i = 0; i < WAVE_TIMES; i++) {
    waveSwing(1);
    waveSwing(-1);
  }

  // يرجّع الرجلين مكانها
  tStand();
  moveAll(700);
}

// ---------- الموجة الناعمة (الفيمر بس) ----------
void ripple() {
  Serial.println("RIPPLE");
  tStand();
  moveAll(300);

  long total = RIPPLE_PERIOD * RIPPLE_ROUNDS;
  for (long t = 0; t <= total; t += 20) {
    // تكبر بالتدريج في البداية وتصغر بالتدريج في النهاية
    float env = 1.0;
    if (t < RIPPLE_EASE) env = (float)t / RIPPLE_EASE;
    if (total - t < RIPPLE_EASE) env = (float)(total - t) / RIPPLE_EASE;
    env = env * env * (3 - 2 * env);

    for (uint8_t k = 0; k < 6; k++) {
      uint8_t l = RIPPLE_ORDER[k];
      float ph = (float)t / RIPPLE_PERIOD - k / 6.0;
      ph -= floor(ph);                                   // مكان الرجل في الموجة: 0 .. 1
      float lift = 0;
      if (ph < RIPPLE_WIDTH) lift = 0.5 * (1 - cos(2 * PI * ph / RIPPLE_WIDTH));
      wrF(l, 1, FEMUR_DOWN + RIPPLE_LIFT * env * lift);  // الفيمر بس
    }
    delay(20);
  }

  // كل الفيمر رجعت لوقفتها
  for (uint8_t l = 0; l < 6; l++) {
    wr(l, 1, FEMUR_DOWN);
    cur[l][1] = FEMUR_DOWN;
  }
}

// ---------- الرقص ----------
float smooth01(float x) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  return x * x * (3 - 2 * x);
}

// وزن مقطع من الرقصة (بالدقات): يدخل بالتدريج خلال دقة ويطلع بالتدريج خلال دقة
float part(float b, float from, float to) {
  return smooth01(b - from) * smooth01(to - b);
}

void dance() {
  Serial.println("DANCE");
  tStand();
  moveAll(300);

  long total = DANCE_BEAT * DANCE_BEATS;
  for (long t = 0; t <= total; t += 20) {
    float b = (float)t / DANCE_BEAT;             // الوقت بالدقات

    float w1 = part(b, 0, 7);                    // ١) نط
    float w2 = part(b, 6, 13);                   // ٢) لف
    float w3 = part(b, 12, DANCE_BEATS);         // ٣) مرجيحة

    float s2   = sin(2 * PI * b / 2);            // دورة كل دقتين
    float s4   = sin(2 * PI * b / 4);            // دورة كل أربع دقات
    float kick = 0.5 - 0.5 * cos(2 * PI * b);    // نطة على كل دقة

    for (uint8_t l = 0; l < 6; l++) {
      bool A     = (l == 0 || l == 2 || l == 4);   // Leg 1,3,5
      bool front = (l == 0 || l == 5);             // Leg 1,6
      bool back  = (l == 2 || l == 3);             // Leg 3,4

      float femur = 0, coxa = 0;

      // ١) نط: الحامل الثلاثي A يطلع والـ B ينزل، وبالعكس
      femur += BOUNCE_LIFT * w1 * (A ? 0.5 + 0.5 * s2 : 0.5 - 0.5 * s2);

      // ٢) لف: كل الرجول تلف لنفس الجهة، ونطة صغيرة على كل دقة
      coxa  += TWIST_SWING * w2 * s4;
      femur += TWIST_KICK * w2 * kick;

      // ٣) مرجيحة: القدامية تطلع والخلفية تنزل، وبالعكس
      if (front) femur += ROCK_LIFT * w3 * (0.5 + 0.5 * s2);
      if (back)  femur += ROCK_LIFT * w3 * (0.5 - 0.5 * s2);

      wrF(l, 0, COXA_MID + coxa);
      wrF(l, 1, FEMUR_DOWN + femur);
    }
    delay(20);
  }

  // يرجع لوقفته
  for (uint8_t l = 0; l < 6; l++) {
    wr(l, 0, COXA_MID);
    wr(l, 1, FEMUR_DOWN);
    cur[l][0] = COXA_MID;
    cur[l][1] = FEMUR_DOWN;
  }
}

void setup() {
  Serial.begin(9600);
  delay(2000);
  Serial.println("START");

  Wire.begin();
  b1.begin();
  b1.setPWMFreq(50);
  b2.begin();
  b2.setPWMFreq(50);
  delay(200);

  standUp();

  Serial.println("hold the robot");
  delay(STARTUP_DELAY);
  Serial.println("WALKING");
}

void loop() {
  for (int i = 0; i < WALK_STEPS; i++) {
    Serial.print("step ");
    Serial.println(i + 1);
    halfStep(TA, TB);
    halfStep(TB, TA);
  }

  Serial.println("PAUSE");
  tStand();
  moveAll(MS_SWING);
  delay(PAUSE_MS);

  wave();
  delay(PAUSE_MS);

  ripple();
  delay(PAUSE_MS);

  dance();
  delay(PAUSE_MS);
}
