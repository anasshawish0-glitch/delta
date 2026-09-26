"""Builds servo_bracket.stl: the Servo U-Bracket with a window for an MG996R.

Takes the U-bracket geometry unchanged from Servo-U-Bracket.3mf and cuts the
servo window and the four ear screw holes into its base. The servo drops
through the window and its ears are screwed to the base.

Requires: pip install manifold3d numpy
"""
import re
import struct
import zipfile
import numpy as np
from manifold3d import CrossSection, Manifold, Mesh, set_circular_segments

set_circular_segments(96)

win_l  = 41.0   # window length (servo body measured 40.43)
win_w  = 20.5   # window width  (servo body measured 20.02)
ear_dx = 48.0   # ear screw spacing along the servo
ear_dy = 10.0   # ear screw spacing across the servo
ear_d  = 3.2    # ear screw hole diameter
bore_d = 8.6    # leg center holes, widened from 8 so an 8.25 mm bushing slides in

src = zipfile.ZipFile("Servo-U-Bracket.3mf").read("3D/Objects/object_1.model").decode()
num = r"([-\d.eE]+)"
v = np.array(re.findall(rf'<vertex x="{num}" y="{num}" z="{num}"', src), np.float32)
f = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', src), np.uint32)
bracket = Manifold(Mesh(vert_properties=v, tri_verts=f))

# The base plate is the top of the model (z from 30.75 to 32.25), centered on x = y = 0.
lo, hi = bracket.bounding_box()[2], bracket.bounding_box()[5]
cut = CrossSection.square((win_l, win_w)).translate((-win_l / 2, -win_w / 2))
for sx in (-1, 1):
    for sy in (-1, 1):
        cut += CrossSection.circle(ear_d / 2).translate((sx * ear_dx / 2, sy * ear_dy / 2))
part = bracket - cut.extrude(5).translate((0, 0, hi - 3))

# Widen the center hole in each leg (legs at x = +-26.5..28, hole at y = 0, z = -19.75).
bore = Manifold.cylinder(70, bore_d / 2, center=True).rotate((0, 90, 0)).translate((0, 0, -19.75))
part = part - bore

m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
v[:, 2] -= v[:, 2].min()  # sit the leg tips on z = 0
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("servo_bracket.stl", "wb") as fh:
    fh.write(b"MG996R servo bracket (Servo U-Bracket + window)".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(),
      "volume mm3:", round(part.volume(), 1),
      "size:", np.round(v.max(0) - v.min(0), 2).tolist())
