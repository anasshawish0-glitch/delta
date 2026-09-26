"""Packs every part onto one Bambu Studio plate: all_parts.3mf.

Usage: python3 make_plate.py [template.3mf]   (default: servo_bracket/Servo-U-Bracket.3mf)

Each part keeps the print orientation of its own 3MF. Printer / filament /
process settings come from the template.
"""
import io
import json
import re
import struct
import sys
import uuid
import zipfile

import numpy as np

template = sys.argv[1] if len(sys.argv) > 1 else "servo_bracket/Servo-U-Bracket.3mf"

# (name, stl, orientation, plate x, plate y)
PARTS = [
    ("servo_bracket",   "servo_bracket/servo_bracket.stl",     "on-side", 105, 162),
    ("flange_standoff", "flange_standoff/flange_standoff.stl", None,      160, 162),
    ("motor_bracket",   "motor_bracket/motor_bracket.stl",     "on-side", 105, 100),
    ("fit_test_coin",   "fit_test/fit_test_coin.stl",          None,      160, 100),
]


def load_stl(path):
    data = open(path, "rb").read()
    count = struct.unpack_from("<I", data, 80)[0]
    rec = np.frombuffer(data, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]),
                        count=count, offset=84)
    verts, faces = np.unique(rec["v"].reshape(-1, 3), axis=0, return_inverse=True)
    return verts.astype(np.float64), faces.reshape(-1, 3)


def orient(v, how):
    if how == "on-side":   # +90 deg about X
        v = np.c_[v[:, 0], -v[:, 2], v[:, 1]]
    elif how == "flip":    # 180 deg about X
        v = np.c_[v[:, 0], -v[:, 1], -v[:, 2]]
    lo, hi = v.min(0), v.max(0)
    return v - (lo + hi) / 2, hi - lo


header = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<model unit="millimeter" xml:lang="en-US" '
          'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
          'requiredextensions="p">\n')

zin = zipfile.ZipFile(template)
files, objects, items, rels, cfg_objs, instances, assemble, bboxes, shaded = {}, [], [], [], [], [], [], [], []
for i, (name, path, how, px, py) in enumerate(PARTS):
    sub_id, obj_id = 2 * i + 1, 2 * i + 2
    v, f = load_stl(path)
    v, size = orient(v, how)
    pz = size[2] / 2
    vtx = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
    tris = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    fname = f"3D/Objects/object_{i + 1}.model"
    files[fname] = (header + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                    f'  <object id="{sub_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
                    f'   <mesh>\n    <vertices>\n{vtx}\n    </vertices>\n'
                    f'    <triangles>\n{tris}\n    </triangles>\n   </mesh>\n'
                    '  </object>\n </resources>\n <build/>\n</model>\n').encode()
    rels.append(f' <Relationship Target="/{fname}" Id="rel-{i + 1}" '
                'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
    objects.append(f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                   f'    <component p:path="/{fname}" objectid="{sub_id}" p:UUID="{uuid.uuid4()}" '
                   'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>')
    items.append(f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" '
                 f'transform="1 0 0 0 1 0 0 0 1 {px:g} {py:g} {pz:g}" printable="1"/>')
    cfg_objs.append(f'''  <object id="{obj_id}">
    <metadata key="name" value="{name}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(f)}"/>
    <part id="{sub_id}" subtype="normal_part">
      <metadata key="name" value="{name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="{name}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="0"/>
      <metadata key="source_offset_y" value="0"/>
      <metadata key="source_offset_z" value="0"/>
      <mesh_stat face_count="{len(f)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>''')
    instances.append(f'''    <model_instance>
      <metadata key="object_id" value="{obj_id}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{100 + i}"/>
    </model_instance>''')
    assemble.append(f'   <assemble_item object_id="{obj_id}" instance_id="0" '
                    f'transform="1 0 0 0 1 0 0 0 1 {px:g} {py:g} {pz:g}" offset="0 0 0" />')
    bb = [px - size[0] / 2, py - size[1] / 2, px + size[0] / 2, py + size[1] / 2]
    bboxes.append({"area": float(size[0] * size[1]), "bbox": bb, "id": 100 + i,
                   "layer_height": 0.16, "name": name})
    shaded.append(v[f] + np.array([px, py, pz]))

# Overlap check between footprints (2 mm gap).
for a in range(len(bboxes)):
    for b in range(a + 1, len(bboxes)):
        A, B = bboxes[a]["bbox"], bboxes[b]["bbox"]
        assert A[2] + 2 <= B[0] or B[2] + 2 <= A[0] or A[3] + 2 <= B[1] or B[3] + 2 <= A[1], \
            f"{bboxes[a]['name']} overlaps {bboxes[b]['name']}"

main = zin.read("3D/3dmodel.model").decode()
main = re.sub(r"<resources>.*</resources>", "<resources>\n" + "\n".join(objects) + "\n </resources>",
              main, flags=re.S)
main = re.sub(r"(<build[^>]*>).*</build>", r"\1\n" + "\n".join(items).replace("\\", "\\\\") + "\n </build>",
              main, flags=re.S)
main = re.sub(r'<metadata name="Title">[^<]*</metadata>', '<metadata name="Title">all_parts</metadata>', main)
files["3D/3dmodel.model"] = main.encode()
files["3D/_rels/3dmodel.model.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                                        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                                        + "\n".join(rels) + "\n</Relationships>").encode()

cfg = zin.read("Metadata/model_settings.config").decode()
cfg = re.sub(r"  <object id=.*?</object>\n", "\n".join(cfg_objs) + "\n", cfg, flags=re.S)
cfg = re.sub(r"    <model_instance>.*</model_instance>\n", "\n".join(instances) + "\n", cfg, flags=re.S)
cfg = re.sub(r"<assemble>.*</assemble>", "<assemble>\n" + "\n".join(assemble) + "\n  </assemble>", cfg, flags=re.S)
files["Metadata/model_settings.config"] = cfg.encode()
files["Metadata/cut_information.xml"] = ('<?xml version="1.0" encoding="utf-8"?>\n<objects>\n' + "".join(
    f' <object id="{2 * i + 1}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>\n'
    for i in range(len(PARTS))) + "</objects>").encode()

plate = json.loads(zin.read("Metadata/plate_1.json"))
allb = np.array([b["bbox"] for b in bboxes])
plate["bbox_all"] = [allb[:, 0].min(), allb[:, 1].min(), allb[:, 2].max(), allb[:, 3].max()]
plate["bbox_objects"] = bboxes
files["Metadata/plate_1.json"] = json.dumps(plate).encode()

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

tri = np.concatenate(shaded)


def thumb(px):
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    s = 0.3 + 0.6 * np.clip(n @ np.array([0.3, -0.4, 0.85]), 0, 1)
    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=np.c_[s, s, s, np.ones_like(s)], edgecolor="none"))
    ax.set_xlim(70, 190); ax.set_ylim(70, 190); ax.set_zlim(0, 120)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(40, -60); ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


big, small = thumb(512), thumb(128)
for k in ("plate_1.png", "plate_no_light_1.png", "top_1.png", "pick_1.png"):
    files["Metadata/" + k] = big
files["Metadata/plate_1_small.png"] = small

with zipfile.ZipFile("all_parts.3mf", "w", zipfile.ZIP_DEFLATED) as zout:
    names = set()
    for item in zin.infolist():
        if item.filename.startswith("3D/Objects/"):
            continue
        zout.writestr(item.filename, files.get(item.filename, zin.read(item.filename)))
        names.add(item.filename)
    for k, data in files.items():
        if k not in names:
            zout.writestr(k, data)
print("all_parts.3mf:", ", ".join(p[0] for p in PARTS))
