# SO-101 assembled, with McKibben "Power Mode" muscle

Whole follower arm in place (not for printing), to see what the finished arm looks like.

- `so101_assembly.stl` — one file, in mm. Import into Onshape: Part Studio → Import → pick the file (units: millimeter).
- `so101_assembly.glb` — coloured version (red = muscle, blue = printed mast, black = STS3215 motors).
- `preview.png` — side and 3/4 view.

The arm parts and motors come from TheRobotStudio/SO-ARM100 (Simulation/SO101, Apache-2.0, see LICENSE).
The mast and muscle are simple placeholders: a 12 mm square post behind the shoulder, 10 cm above the
shoulder axis, and an 18 mm muscle from its top to the upper arm, 3 cm from the shoulder axis.

Official editable CAD (Onshape, by TheRobotStudio):
https://cad.onshape.com/documents/7715cc284bb430fe6dab4ffd/w/4fd0791b683777b02f8d975a/e/826c553ede3b7592eb9ca800

Rebuild: `python3 build_assembly.py <path to SO-ARM100/Simulation/SO101>`
