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
| Width | 26 |
| Leg length (from outer corner) | 32 |
| Inner bend radius | 2 |
| Center hole | Ø7.5 |
| Screw holes | 4 × Ø3.2 (M3), 16 / 19 mm pattern, rotated 45° |

Everything except the thickness was estimated from a photo. Measure your part
with calipers and update the values at the top of `motor_bracket.scad` or
`build_stl.py`.
