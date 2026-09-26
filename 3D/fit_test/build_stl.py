"""Builds fit_test_coin.stl: a small coin with the same holes as the bracket legs,
to check the bushing / screw fit before printing a whole part.

Requires: pip install manifold3d numpy
"""
import struct
import numpy as np
from manifold3d import CrossSection, set_circular_segments

set_circular_segments(128)

coin_d   = 25.0   # coin diameter (same as the rounded leg end)
t        = 2.60   # thickness
center_d = 8.6    # center hole (8.25 mm bushing)
screw_d  = 3.0    # 4 screw holes
pat      = 14.0   # distance between opposite screw holes

shape = CrossSection.circle(coin_d / 2) - CrossSection.circle(center_d / 2)
for (x, y) in [(pat / 2, 0), (-pat / 2, 0), (0, pat / 2), (0, -pat / 2)]:
    shape -= CrossSection.circle(screw_d / 2).translate((x, y))
part = shape.extrude(t)

m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("fit_test_coin.stl", "wb") as fh:
    fh.write(b"Fit test coin".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(), "volume mm3:", round(part.volume(), 1))
