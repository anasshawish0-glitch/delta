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
- `kitty.css`, `kitty.js`: shared theme, the animated corner kitty, kitty patterns and 3D heads
- `kin.js`: arm forward kinematics + damped least-squares IK (also runs in Node)
- `robot.json`, `meshes.json`: arm model built from the official URDF by `build_meshes.py`
- `hexapod.js`: hexapod leg IK and tripod gait (also runs in Node)
- `hexapod_serial/hexapod_serial.ino`: Arduino sketch; drives the servos through two PCA9685
  boards ("Adafruit PWM Servo Driver Library") or straight from Arduino Mega pins (`USE_PCA9685 0`)

Hexapod serial protocol (115200 baud, one line each):
`S` + 18 comma-separated angles in degrees (R1 coxa, femur, tibia, R2 …, R3 …, L1 …, L2 …, L3 …),
`R` to relax all servos, `?` to get `HEXAPOD v1` back.

Rebuild arm assets: `python3 build_meshes.py <path to SO-ARM100/Simulation/SO101>`
Preview locally: `python3 -m http.server` in this folder, then open http://localhost:8000

Website: the `gh-pages` branch holds a copy of this folder's web files (everything except
`build_meshes.py` and this README) and GitHub Pages serves it. After changing a page, copy those
files onto `gh-pages` and push.
