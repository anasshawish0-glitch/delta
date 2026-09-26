# Servo U-Bracket (8.6 mm center holes)

The Servo U-Bracket from `../servo_bracket/Servo-U-Bracket.3mf`, unchanged except
the center hole in each leg is widened from Ø8 to Ø8.6 so an 8.25 mm bushing
slides in.

| File | Purpose |
|------|---------|
| `u_bracket.3mf` | Bambu Studio project (Bambu Lab A1), laid on its side |
| `u_bracket.stl` | Ready to print / import (units: mm) |
| `build_stl.py` | Generates the STL (`pip install manifold3d numpy`) |

Rebuild the 3MF with `python3 ../make_3mf.py u_bracket.stl ../servo_bracket/Servo-U-Bracket.3mf --on-side`.
