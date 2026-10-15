# Kitty twin: SO-101 arm and hexapod in the browser

Two black-and-pink pages that share one theme. The site is live at
https://anasshawish0-glitch.github.io/delta/

**Arm (`index.html`)**: the SO-101 follower arm in 3D. Drag the heart gizmo to move the gripper
(IK), preview the move as a pink ghost, run it with the heart button, or let the arm pick a kitty
into the tray. Simulation only for now; a Python service on the Raspberry Pi will later stream
real joint angles and camera frames.

**Hexapod (`hexapod.html`)**: an 18-servo hexapod with a tripod walk, driven with the heart
joystick or W A S D / Q E. It can stand, sit, wave and dance, and it talks to the real robot over
USB (Web Serial, so Chrome or Edge on a computer). Trims and reversed servos are set on the page
and saved in the browser.

The default model is a look-alike of the Hexapod Spider Robot by Emre Kalem (MG996R servos).
Its sizes were measured from the print files: hip bearings 116 mm out at ±29.4° and ±150.6° and
106 mm out at ±90°, coxa 38 mm, femur 86.3 mm, knee to claw tip 163 mm. The original files are
not in this repo because their license does not allow sharing them; the 3D look-alike is drawn
from simple shapes. Other layouts (round or long body, any leg sizes) can be picked on the page.

With long claws the femur would pass 180° if the body simply dropped, so sitting steps the feet
out first and then lowers the body; standing up rises first and then steps the feet back in.

Files:
- `kitty.css`, `kitty.js`: shared theme, the animated corner mascot, patterns and 3D table items
- `theme.js`: the look switch. "Kitty" is the pink Hello-Kitty style; "Libra" is black, bone and
  gold with an original ram-horned night goat (bell eyes, a mask, gold flecks) that goes mad
  instead of sad (a flame spiral burns on its mask, fire rises from its head), golden bell items,
  a flame-spiral Run button and ram horns on the hexapod. Pick it with the Kitty / Libra buttons
  or `?theme=libra`; the choice is remembered in the browser
- `libra.js`: the Libra world behind the 3D view, all painted in code: a burning swirling sky, a
  far burnt tree with yellow fire and a fireball bursting from its crown throwing sparks, and a
  ring of broken, burning buildings with fires and rising embers. On the hexapod page the floor
  fades out behind the robot so this world shows beyond it
- `kin.js`: arm forward kinematics + damped least-squares IK (also runs in Node)
- `robot.json`, `meshes.json`: arm model built from the official URDF by `build_meshes.py`
- `hexapod.js`: hexapod leg IK and tripod gait (also runs in Node)
- `hexapod_serial/hexapod_serial.ino`: Arduino sketch; drives the servos through two PCA9685
  boards ("Adafruit PWM Servo Driver Library") or straight from Arduino Mega pins (`USE_PCA9685 0`)
- `hexapod_check/hexapod_check.ino`: moves one servo at a time and prints which leg, joint,
  board and channel it should be, to check the channel map on the real robot

Hexapod serial protocol (115200 baud, one line each):
`S` + 18 comma-separated angles in degrees in the robot's own leg order (Leg 1 coxa, femur,
tibia, Leg 2 …, Leg 6), `R` to relax all servos, `?` to get `HEXAPOD v1` back. The sketch eases
each servo toward its angle (at most 4° per 20 ms) and powers them up two at a time.

Calibration: the page starts from the robot's working standing pose (the angles from its old
code). The median femur and tibia angles give the stance height and spread, and each servo's
difference from them becomes its trim, so the page's stand pose sends exactly those angles.
Defaults for this robot: Arduino UNO, PCA9685 boards at 0x40 and 0x41 with the channel map from
CHANNELS.md, legs numbered round the body (1-3 right side front to back, 4-6 left side back to
front, so legs 1 and 6 are the front pair), tibia servos turning opposite to the femurs. A Rug
setting raises the step to 50 mm and slows the cadence to 1.2 s per cycle.

Rebuild arm assets: `python3 build_meshes.py <path to SO-ARM100/Simulation/SO101>`
Preview locally: `python3 -m http.server` in this folder, then open http://localhost:8000

Website: the `gh-pages` branch holds a copy of this folder's web files (everything except
`build_meshes.py` and this README) and GitHub Pages serves it. After changing a page, copy those
files onto `gh-pages` and push.
