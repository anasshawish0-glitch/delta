# L-bracket motor mount

3D model of an L-shaped motor mount bracket, sheet thickness **2.60 mm**.

| File | Purpose |
|------|---------|
| `motor_bracket.stl` | Ready to print / import (units: mm) |
| `motor_bracket.scad` | Parametric OpenSCAD source – change dimensions and re-export |
| `build_stl.py` | Python script that generates the STL (`pip install manifold3d numpy`) |
| `preview.png` | Render preview |

## Dimensions (mm)

| Parameter | Value |
|-----------|-------|
| Thickness | 2.60 |
| Width | 25 |
| Leg length (from outer corner) | 32 |
| Inner bend radius | 2 |
| Center hole | Ø8 |
| Screw holes | 4 × Ø3, 7 mm from center (14 mm between opposite holes), "+" pattern on the leg axes |

Thickness, width and hole sizes are exact (width and holes taken from `Servo-U-Bracket.3mf`);
leg length was estimated from a photo. Measure your part
with calipers and update the values at the top of `motor_bracket.scad` or
`build_stl.py`.
