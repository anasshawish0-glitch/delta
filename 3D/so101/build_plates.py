"""Packs the SO-101 follower arm parts onto Bambu Lab A1 plates: so101_follower.3mf

Source: BambuLabA1mini_Follower_SO101.stl from github.com/TheRobotStudio/SO-ARM100
(Apache-2.0, see LICENSE). The parts are already oriented for printing; this
script only splits them, names them, and lays them out on 256 x 256 plates.
Print settings follow the SO-ARM100 README: PLA, 0.2 mm layers, 15 % infill,
supports on (threshold 45 deg).

Run from this folder: python3 build_plates.py
"""
import sys

import numpy as np
import trimesh

sys.path.insert(0, "..")
from make_plate import write_project  # noqa: E402

# Volume (mm^3) of each part in the source file -> name
NAMES = [
    (122690, "Base"), (117328, "Upper_arm"), (92895, "Under_arm"), (68787, "Rotation_Pitch"),
    (56618, "Wrist_Roll_Follower"), (32299, "Wrist_Roll_Pitch"), (23709, "Base_motor_holder"),
    (20769, "Moving_Jaw"), (13872, "Motor_holder_Wrist"), (13307, "Motor_holder_Base"),
    (9093, "WaveShare_Mounting_Plate"), (76, "Small_strip"),
]
BED, MARGIN, GAP = 256.0, 6.0, 6.0

src = trimesh.load("BambuLabA1mini_Follower_SO101.stl")
pieces = []
for p in src.split(only_watertight=False):
    name = min(NAMES, key=lambda n: abs(n[0] - p.volume))[1]
    v = np.asarray(p.vertices, dtype=np.float64)
    f = np.asarray(p.faces)
    ext = v.max(0) - v.min(0)
    if ext[1] > ext[0]:  # lay long side along X (rotate about Z only, print orientation unchanged)
        v = np.c_[-v[:, 1], v[:, 0], v[:, 2]]
    v -= (v.min(0) + v.max(0)) / 2
    pieces.append(dict(name=name, verts=v, faces=f, size=v.max(0) - v.min(0)))
assert len({p["name"] for p in pieces}) == len(pieces) == len(NAMES)

# Shelf packing, biggest first; open a new plate when a part does not fit.
pieces.sort(key=lambda p: -p["size"][0] * p["size"][1])
plates = []  # each: list of shelves [y0, height, x_cursor]
for p in pieces:
    w, h = p["size"][0], p["size"][1]
    placed = False
    for k, shelves in enumerate(plates, start=1):
        for sh in shelves:
            if sh[2] + w <= BED - MARGIN and h <= sh[1]:
                p.update(x=sh[2] + w / 2, y=sh[0] + h / 2, plate=k)
                sh[2] += w + GAP
                placed = True
                break
        if placed:
            break
        top = shelves[-1][0] + shelves[-1][1] + GAP
        if top + h <= BED - MARGIN:
            shelves.append([top, h, MARGIN + w + GAP])
            p.update(x=MARGIN + w / 2, y=top + h / 2, plate=k)
            placed = True
            break
    if not placed:
        plates.append([[MARGIN, h, MARGIN + w + GAP]])
        p.update(x=MARGIN + w / 2, y=MARGIN + h / 2, plate=len(plates))

for p in pieces:
    print(f"plate {p['plate']}  {p['name']:26s} {np.round(p['size'], 1).tolist()}")

write_project(pieces, "so101_follower.3mf", template="../servo_bracket/Servo-U-Bracket.3mf", extruder=2,
              title="SO-101 follower",
              overrides={"layer_height": "0.2", "sparse_infill_density": "15%", "enable_support": "1",
                         "support_type": "tree(auto)", "support_threshold_angle": "45",
                         "support_on_build_plate_only": "0"})
