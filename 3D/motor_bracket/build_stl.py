"""Builds motor_bracket.stl (same geometry as motor_bracket.scad).

Requires: pip install manifold3d numpy
"""
import math
import struct
import numpy as np
from manifold3d import CrossSection, Manifold, set_circular_segments

set_circular_segments(96)

t        = 2.60   # sheet thickness
W        = 25.0   # bracket width
L_long   = 37.6   # long leg, measured from the outer corner
L_short  = 29.46  # short leg (has the countersunk hole), measured from the outer corner
ri       = 2.0    # inner bend radius
center_d = 8.0    # center (shaft) hole diameter
screw_d  = 3.0    # screw holes
pat_a    = 14.0   # motor hole spacing A
pat_b    = 14.0   # motor hole spacing B

R  = ri + t       # outer bend radius


def circ(d, x=0.0, y=0.0):
    return CrossSection.circle(d / 2).translate((x, y))


# 1) Plain L-profile (side view, X-Z) swept along the width (Y).
bend = (CrossSection.circle(R) - CrossSection.circle(ri)) ^ \
    CrossSection.square((R, R)).translate((-R, -R))
side = bend.translate((R, R)) \
    + CrossSection.square((L_long - R, t)).translate((R, 0)) \
    + CrossSection.square((t, L_short - R)).translate((0, R))
body = side.extrude(W).rotate((90, 0, 0)).translate((0, W / 2, 0))

# 2) Leg outline (rounded end) + holes, in leg coordinates (u along leg, v across).
def leg_profile(L):
    hc = L - W / 2  # hole center distance from outer corner
    outline = CrossSection.square((hc + 1, W)).translate((-1, -W / 2)) + circ(W, hc)
    holes = circ(center_d, hc)
    for (x, y) in [(pat_a / 2, 0), (-pat_a / 2, 0), (0, pat_b / 2), (0, -pat_b / 2)]:
        holes += circ(screw_d, hc + x, y)  # "+" pattern on the leg axes
    return outline - holes


big = max(L_long, L_short) + 2
horiz_cut = leg_profile(L_long).extrude(R + 1).translate((0, 0, -1))  # z in [-1, R]
vert_cut = leg_profile(L_short).extrude(big).rotate((0, -90, 0)).translate((big - 1, 0, 0))
vert_cut = vert_cut ^ Manifold.cube((big + 2, W + 2, big)).translate((-1, -W / 2 - 1, R))

part = body ^ (horiz_cut + vert_cut)

# 3) Write binary STL.
m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("motor_bracket.stl", "wb") as fh:
    fh.write(b"L-bracket motor mount, t=2.60mm".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(),
      "volume mm3:", round(part.volume(), 1),
      "bounds:", np.round(v.min(0), 2).tolist(), np.round(v.max(0), 2).tolist())
