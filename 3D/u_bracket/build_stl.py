"""Builds u_bracket.stl: the Servo U-Bracket unchanged, except the center hole in
each leg is widened to 8.6 mm so an 8.25 mm bushing slides in.

Requires: pip install manifold3d numpy
"""
import re
import struct
import zipfile
import numpy as np
from manifold3d import Manifold, Mesh, set_circular_segments

set_circular_segments(96)

bore_d = 8.6  # leg center holes, widened from 8

src = zipfile.ZipFile("../servo_bracket/Servo-U-Bracket.3mf").read("3D/Objects/object_1.model").decode()
num = r"([-\d.eE]+)"
v = np.array(re.findall(rf'<vertex x="{num}" y="{num}" z="{num}"', src), np.float32)
f = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', src), np.uint32)
bracket = Manifold(Mesh(vert_properties=v, tri_verts=f))

# Legs at x = +-26.5..28, center hole at y = 0, z = -19.75.
bore = Manifold.cylinder(70, bore_d / 2, center=True).rotate((0, 90, 0)).translate((0, 0, -19.75))
part = bracket - bore

m = part.to_mesh()
v = np.array(m.vert_properties)[:, :3]
f = np.array(m.tri_verts)
v[:, 2] -= v[:, 2].min()
tri = v[f]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
n /= np.linalg.norm(n, axis=1, keepdims=True)
with open("u_bracket.stl", "wb") as fh:
    fh.write(b"Servo U-Bracket, 8.6 mm center holes".ljust(80, b" "))
    fh.write(struct.pack("<I", len(f)))
    for ni, ti in zip(n, tri):
        fh.write(struct.pack("<12fH", *ni, *ti.ravel(), 0))

print("status:", part.status(), "genus:", part.genus(),
      "volume mm3:", round(part.volume(), 1), "size:", np.round(v.max(0) - v.min(0), 2).tolist())
