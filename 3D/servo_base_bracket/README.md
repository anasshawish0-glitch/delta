# MG995 / MG996R / DS3115 base servo bracket

Converted from the supplied SolidWorks STEP (`servo_base_bracket.step`) without
changing the geometry. Size 58 × 25 × 37 mm.

| File | Purpose |
|------|---------|
| `servo_base_bracket.3mf` | Bambu Studio project (Bambu Lab A1), large plate flat on the bed, no supports needed |
| `servo_base_bracket.stl` | Mesh (units: mm) |
| `servo_base_bracket.step` | Original CAD |
| `reference.png` | Original preview image |

The STEP was meshed with gmsh (`pip install gmsh`); the 3MF was built with
`python3 ../make_3mf.py servo_base_bracket.stl ../servo_bracket/Servo-U-Bracket.3mf --on-side`.
