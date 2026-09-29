# SO-101 follower arm – Bambu Lab A1 plates

`so101_follower.3mf` holds every printed part of the SO-101 follower arm on two
Bambu Lab A1 plates (256 × 256 mm).

- Source: `BambuLabA1mini_Follower_SO101.stl` from
  [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100),
  Apache-2.0 (see `LICENSE`). Parts are kept exactly as supplied, already
  oriented for printing; they are only split into separate objects and laid out.
- Print settings per the SO-ARM100 README: PLA (filament slot 2), 0.2 mm layers,
  15 % infill, tree supports on everywhere with a 45° threshold. Keep supports out
  of the horizontal screw holes.

| Plate | Parts |
|-------|-------|
| 1 | Under_arm, Upper_arm, Base, Wrist_Roll_Follower, Moving_Jaw, Base_motor_holder, Small_strip |
| 2 | Rotation_Pitch, Wrist_Roll_Pitch, WaveShare_Mounting_Plate, Motor_holder_Base, Motor_holder_Wrist |

Rebuild: `python3 build_plates.py` (needs `trimesh`, `numpy`, `matplotlib`).
