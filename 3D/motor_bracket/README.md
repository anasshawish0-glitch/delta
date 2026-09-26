# L-bracket motor mount

3D model of an L-shaped motor mount bracket, sheet thickness **2.60 mm**.

| File | Purpose |
|------|---------|
| `motor_bracket.3mf` | Bambu Studio project (Bambu Lab A1, part laid on its side, centered on the plate) |
| `motor_bracket.stl` | Ready to print / import (units: mm) |
| `motor_bracket.scad` | Parametric OpenSCAD source – change dimensions and re-export |
| `build_stl.py` | Python script that generates the STL (`pip install manifold3d numpy`) |
| `../make_3mf.py` | Packs the STL into a Bambu Studio project: `python3 ../make_3mf.py motor_bracket.stl ../servo_bracket/Servo-U-Bracket.3mf --on-side` |
| `preview.png` | Render preview |

## Dimensions (mm)

| Parameter | Value |
|-----------|-------|
| Thickness | 2.60 |
| Width | 25 |
| Long leg (from outer corner) | 37.60 |
| Short leg (from outer corner) | 29.46 |
| Inner bend radius | 2 |
| Center hole | Ø8.6 (an 8.25 mm bushing slides in) |
| Screw holes | 4 × Ø3, 7 mm from center (14 mm between opposite holes), "+" pattern on the leg axes |

Thickness and leg lengths were measured with calipers; width and hole sizes are taken from
`Servo-U-Bracket.3mf`. To change a dimension, edit the values at the top of
`motor_bracket.scad` or `build_stl.py`.
