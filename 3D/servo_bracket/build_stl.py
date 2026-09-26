"""Builds servo_bracket.stl: multi-functional U bracket for an MG996R servo.

The servo drops through the rectangular window and its ears are screwed to the
top frame; two legs bend down at the short ends. The long leg has a rounded end
with a center hole and 4 screw holes.

Requires: pip install manifold3d numpy
"""
import math
import struct
import numpy as np
from manifold3d import CrossSection, Manifold, set_circular_segments

set_circular_segments(96)

t        = 2.60   # sheet thickness
W        = 25.0   # bracket width
Lo       = 64.0   # frame outer length (outside of one leg to outside of the other)
ri       = 2.0    # inner bend radius
# Servo window + ear screws (MG996R body measured 40.43 x 20.02)
win_l    = 41.0   # window length
win_w    = 20.5   # window width
ear_dx   = 49.5   # ear screw spacing along the servo
ear_dy   = 10.0   # ear screw spacing across the servo
ear_d    = 3.2    # ear screw hole diameter
# Legs, measured from the top of the frame down to the tip
leg_long  = 64.5  # leg with the rounded end and hole pattern
leg_short = 64.5  # plain leg on the other side
# Hole pattern on the long leg
center_d = 8.0    # center hole
screw_d  = 3.0    # 4 screw holes
pat      = 14.0   # distance between opposite screw holes
pat_rot  = 0.0    # pattern rotation (0 = "+", 45 = "x")

R = ri + t
X = Lo / 2


def circ(d, x=0.0, y=0.0):
    return CrossSection.circle(d / 2).translate((x, y))


def rect(x0, y0, x1, y1):
    return CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))


# 1) Side profile (X-Z): top plate + two bends + two legs, swept along Y.
quad = (CrossSection.circle(R) - CrossSection.circle(ri)) ^ rect(0, 0, R, R)
side = (rect(-X + R, -t, X - R, 0)
        + quad.translate((X - R, -R))
        + quad.rotate(90).translate((-X + R, -R))
        + rect(X - t, -leg_long, X, -R)
        + rect(-X, -leg_short, -X + t, -R))
body = side.extrude(W).rotate((90, 0, 0)).translate((0, W / 2, 0))


# 2) Leg outlines in leg coordinates (u = depth below the top, v = across).
def leg_outline(L):
    return rect(-1, -W / 2, L - W / 2, W / 2) + circ(W, L - W / 2)


pattern = circ(center_d, leg_long - W / 2)
a = math.radians(pat_rot)
for k in range(4):
    th = a + k * math.pi / 2
    pattern += circ(screw_d, leg_long - W / 2 + pat / 2 * math.cos(th), pat / 2 * math.sin(th))

big = Lo + 10


def along_x(cs, x0):
    # (u, v, e) -> (x = x0 + e, y = v, z = -u)
    return cs.extrude(big).rotate((0, 90, 0)).translate((x0, 0, 0))


clip = (Manifold.cube((2 * big, 2 * big, R + 1)).translate((-big, -big, -R))
        + along_x(leg_outline(leg_long) - pattern, 0)
        + along_x(leg_outline(leg_short), -big))

# 3) Window and ear screw holes in the top plate.
top_cut = rect(-win_l / 2, -win_w / 2, win_l / 2, win_w / 2)
for sx in (-1, 1):
    for sy in (-1, 1):
        top_cut += circ(ear_d, sx * ear_dx / 2, sy * ear_dy / 2)
top_cut = top_cut.extrude(t + 2).translate((0, 0, -t - 1))

part = (body ^ clip) - top_cut

m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("servo_bracket.stl", "wb") as fh:
    fh.write(b"MG996R multi-functional servo bracket".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(),
      "volume mm3:", round(part.volume(), 1),
      "bounds:", np.round(v.min(0), 2).tolist(), np.round(v.max(0), 2).tolist())
