# SO-101 assembled, with McKibben "Power Mode" muscle

Whole follower arm in place (not for printing), to see what the finished arm looks like.

- `so101_assembly.stl` — one file, in mm. Import into Onshape: Part Studio → Import → pick the file (units: millimeter).
- `so101_assembly.glb` — coloured version (red = muscles, blue = printed crossbars and outrigger, black = STS3215 motors).
- `preview.png` — side and 3/4 view.

The arm parts and motors come from TheRobotStudio/SO-ARM100 (Simulation/SO101, Apache-2.0, see LICENSE).
Muscle layout (placeholders, 18 mm muscles): two McKibben muscles, one each side of the upper arm,
from a bolt through the back of the upper arm near the elbow down to a printed outrigger behind the
base. The outrigger is fixed to the part that turns with the shoulder, so the muscles turn with the arm.
In this pose the muscle is about 200 mm long and acts about 80 mm from the shoulder axis.

Official editable CAD (Onshape, by TheRobotStudio):
https://cad.onshape.com/documents/7715cc284bb430fe6dab4ffd/w/4fd0791b683777b02f8d975a/e/826c553ede3b7592eb9ca800

Rebuild: `python3 build_assembly.py <path to SO-ARM100/Simulation/SO101>`
