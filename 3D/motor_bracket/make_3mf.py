"""Packs motor_bracket.stl into a Bambu Studio project (motor_bracket.3mf).

Usage: python3 make_3mf.py <template.3mf>

The template is any Bambu Studio project; its printer / filament / process
settings are reused. The bracket is laid on its side (the 25 mm width is the
print height) so the layers run around the bend, and centered on the plate.
"""
import io
import json
import re
import struct
import sys
import zipfile

import numpy as np

template = sys.argv[1]
name = "motor_bracket"

# Read binary STL and rebuild the indexed mesh (vertices are exact duplicates).
data = open(f"{name}.stl", "rb").read()
count = struct.unpack_from("<I", data, 80)[0]
rec = np.frombuffer(data, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]),
                    count=count, offset=84)
tri = rec["v"].reshape(-1, 3)
verts, faces = np.unique(tri, axis=0, return_inverse=True)
faces = faces.reshape(-1, 3)
verts = verts.astype(np.float64)

# Lay on its side: rotate +90 deg about X, (x, y, z) -> (x, -z, y), then center at origin.
verts = np.c_[verts[:, 0], -verts[:, 2], verts[:, 1]]
lo, hi = verts.min(0), verts.max(0)
verts -= (lo + hi) / 2
size = hi - lo

zin = zipfile.ZipFile(template)
settings = json.loads(zin.read("Metadata/project_settings.config"))
area = np.array([[float(c) for c in p.split("x")] for p in settings["printable_area"]])
cx, cy = (area.min(0) + area.max(0)) / 2
cz = size[2] / 2

vtx = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in verts)
tris = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<model unit="millimeter" xml:lang="en-US" '
          'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
          'requiredextensions="p">\n')
object_model = (header +
                ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                '  <object id="1" p:UUID="00010000-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                f'   <mesh>\n    <vertices>\n{vtx}\n    </vertices>\n'
                f'    <triangles>\n{tris}\n    </triangles>\n   </mesh>\n'
                '  </object>\n </resources>\n <build/>\n</model>\n')

main_model = zin.read("3D/3dmodel.model").decode()
main_model = re.sub(r'(<item objectid="2"[^>]*transform=")[^"]*"',
                    rf'\g<1>1 0 0 0 1 0 0 0 1 {cx:g} {cy:g} {cz:g}"', main_model)
main_model = re.sub(r'<metadata name="Title">[^<]*</metadata>',
                    f'<metadata name="Title">{name}</metadata>', main_model)

cfg = zin.read("Metadata/model_settings.config").decode()
cfg = re.sub(r'(<object id="2">\s*<metadata key="name" value=")[^"]*', rf"\g<1>{name}.stl", cfg)
cfg = re.sub(r'(<part id="1"[^>]*>\s*<metadata key="name" value=")[^"]*', rf"\g<1>{name}", cfg)
cfg = re.sub(r'key="source_file" value="[^"]*"', f'key="source_file" value="{name}.stl"', cfg)
cfg = re.sub(r'key="source_offset_(x|y|z)" value="[^"]*"', r'key="source_offset_\1" value="0"', cfg)
cfg = re.sub(r'face_count="\d+"', f'face_count="{len(faces)}"', cfg)
cfg = re.sub(r'(<assemble_item[^>]*transform=")[^"]*"',
             rf'\g<1>1 0 0 0 1 0 0 0 1 0 0 {cz:g}"', cfg)

plate = json.loads(zin.read("Metadata/plate_1.json"))
bbox = [cx - size[0] / 2, cy - size[1] / 2, cx + size[0] / 2, cy + size[1] / 2]
plate["bbox_all"] = bbox
plate["bbox_objects"] = [dict(plate["bbox_objects"][0], bbox=bbox, name=f"{name}.stl",
                              area=float(size[0] * size[1]))]

# Thumbnails: simple shaded render of the part as it sits on the plate.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def thumb(px):
    t = verts[faces]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    s = 0.3 + 0.6 * np.clip(n @ np.array([0.3, -0.4, 0.85]), 0, 1)
    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.add_collection3d(Poly3DCollection(t, facecolors=np.c_[s, s, s, np.ones_like(s)], edgecolor="none"))
    r = size.max() / 2
    ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(-r, r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(35, -60); ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


big, small = thumb(512), thumb(128)
replace = {
    "3D/Objects/object_1.model": object_model.encode(),
    "3D/3dmodel.model": main_model.encode(),
    "Metadata/model_settings.config": cfg.encode(),
    "Metadata/plate_1.json": json.dumps(plate).encode(),
    "Metadata/plate_1.png": big,
    "Metadata/plate_no_light_1.png": big,
    "Metadata/top_1.png": big,
    "Metadata/pick_1.png": big,
    "Metadata/plate_1_small.png": small,
}
with zipfile.ZipFile(f"{name}.3mf", "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        zout.writestr(item.filename, replace.get(item.filename, zin.read(item.filename)))

print(f"{name}.3mf: {len(verts)} verts, {len(faces)} faces, size {np.round(size, 2).tolist()} mm, "
      f"at ({cx:g}, {cy:g}) on {settings['printer_model']}")
