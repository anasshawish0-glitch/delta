# Flange standoff

Solid column with a round flange at each end: a printable copy of the aluminium standoff.

| File | Purpose |
|------|---------|
| `flange_standoff.3mf` | Bambu Studio project (Bambu Lab A1), standing upright, centered on the plate |
| `flange_standoff.stl` | Ready to print / import (units: mm) |
| `flange_standoff.scad` | Parametric OpenSCAD source |
| `build_stl.py` | Generates the STL (`pip install manifold3d numpy`) |
| `preview.png` | Render preview |

Rebuild the 3MF with `python3 ../make_3mf.py flange_standoff.stl <template.3mf>`.

## Dimensions (mm)

| Parameter | Value | Source |
|-----------|-------|--------|
| Total length | 55.40 | caliper |
| Column diameter | 12.44 | caliper |
| Flange diameter | 18 | estimated from photo |
| Flange thickness | 4 | estimated from photo |
| Screw holes | 4 per flange, "+" pattern, 14 between opposite holes | same as the motor bracket |
| Screw hole diameter | 2.6 | M3 screws tap their own thread in the plastic |
