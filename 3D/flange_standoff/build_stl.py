"""Builds flange_standoff.stl: a solid column with a round flange at each end.

Requires: pip install manifold3d numpy
"""
import struct
import numpy as np
from manifold3d import CrossSection, Manifold, set_circular_segments

set_circular_segments(128)

L        = 55.40  # total length, flange face to flange face
tube_d   = 12.44  # column outer diameter
flange_d = 18.0   # flange diameter
flange_t = 2.86   # flange thickness
screw_d  = 2.6    # 4 screw holes per flange; 2.6 lets an M3 screw tap its own thread (use 3.2 for a clearance hole)
pat      = 14.0   # distance between opposite screw holes

tube = Manifold.cylinder(L, tube_d / 2)
flange = Manifold.cylinder(flange_t, flange_d / 2)
part = tube + flange + flange.translate((0, 0, L - flange_t))

holes = CrossSection()
for (x, y) in [(pat / 2, 0), (-pat / 2, 0), (0, pat / 2), (0, -pat / 2)]:
    holes += CrossSection.circle(screw_d / 2).translate((x, y))
hole_cyl = holes.extrude(flange_t + 2).translate((0, 0, -1))
part = part - hole_cyl - hole_cyl.translate((0, 0, L - flange_t))

m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("flange_standoff.stl", "wb") as fh:
    fh.write(b"Flange standoff".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(),
      "volume mm3:", round(part.volume(), 1),
      "bounds:", np.round(v.min(0), 2).tolist(), np.round(v.max(0), 2).tolist())
