# MG996R servo bracket

Multi-functional U bracket for an MG996R servo: the servo drops through the
rectangular window and its ears are screwed to the frame; two legs bend down at
the short ends. **First draft** – most dimensions are estimates (see below).

| File | Purpose |
|------|---------|
| `servo_bracket.3mf` | Bambu Studio project (Bambu Lab A1), frame flat on the plate, legs up |
| `servo_bracket.stl` | Ready to print / import (units: mm) |
| `build_stl.py` | Generates the STL (`pip install manifold3d numpy`) |
| `preview.png` | Render preview |

Rebuild the 3MF with `python3 ../make_3mf.py servo_bracket.stl <template.3mf> --flip`.

## Dimensions (mm)

| Parameter | Value | Source |
|-----------|-------|--------|
| Servo window | 41 × 20.5 | servo body measured 40.43 × 20.02, plus clearance |
| Ear screw holes | 4 × Ø3.2, 49.5 × 10 | MG996R datasheet |
| Thickness | 2.60 | assumed same as the motor bracket |
| Width | 26.65 | caliper |
| Frame outer length | 64 | estimated |
| Legs (from top of frame) | 64.5 / 64.5 | same height as `Servo-U-Bracket.3mf` |
| Long-leg holes | Ø8 center + 4 × Ø3, 14 apart, "+" pattern | estimated from photo |
