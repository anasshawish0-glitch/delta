# MG996R servo bracket

The Servo U-Bracket (`Servo-U-Bracket.3mf`) with a window for an MG996R servo cut
into its base. Everything else – size, thickness, leg holes – is unchanged from
the U-bracket. The servo drops through the window and its ears are screwed to
the base.

| File | Purpose |
|------|---------|
| `servo_bracket.3mf` | Bambu Studio project (Bambu Lab A1), laid on its side so the layers run around the bends |
| `servo_bracket.stl` | Ready to print / import (units: mm) |
| `Servo-U-Bracket.3mf` | Source U-bracket (also used as the Bambu settings template) |
| `build_stl.py` | Generates the STL (`pip install manifold3d numpy`) |
| `preview.png` | Render preview |

Rebuild the 3MF with `python3 ../make_3mf.py servo_bracket.stl Servo-U-Bracket.3mf --on-side`.

## Changes to the U-bracket base (mm)

| Parameter | Value | Source |
|-----------|-------|--------|
| Servo window | 41 × 20.5 | servo body measured 40.43 × 20.02, plus clearance |
| Ear screw holes | 4 × Ø3.2, 48 × 10 | MG996R ear holes (slotted, so a little play is fine) |
| Leg center holes | Ø8.6, widened from Ø8 | an 8.25 mm bushing slides in |
