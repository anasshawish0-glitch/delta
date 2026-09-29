"""Packs parts onto Bambu Studio plates.

    python3 make_plate.py            -> all_parts.3mf (every part of this repo, one plate)

`write_project()` is also used by so101/build_plates.py for multi-plate projects.
Printer / filament / process settings come from a Bambu Studio template 3MF.
"""
import io
import json
import re
import struct
import uuid
import zipfile

import numpy as np

TEMPLATE = "servo_bracket/Servo-U-Bracket.3mf"
PLATE_STRIDE = 256 * 1.2  # Bambu lays plates out in a grid, one bed width + 20 % apart

HEADER = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<model unit="millimeter" xml:lang="en-US" '
          'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
          'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
          'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
          'requiredextensions="p">\n')


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
    elif how == "rot90":   # 90 deg about Z
        v = np.c_[-v[:, 1], v[:, 0], v[:, 2]]
    lo, hi = v.min(0), v.max(0)
    return v - (lo + hi) / 2, hi - lo


def _thumb(tri, lo, hi, px):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    s = 0.3 + 0.6 * np.clip(n @ np.array([0.3, -0.4, 0.85]), 0, 1)
    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.add_collection3d(Poly3DCollection(tri, facecolors=np.c_[s, s, s, np.ones_like(s)], edgecolor="none"))
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(0, 2 * r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(40, -60); ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


def write_project(parts, out_path, template=TEMPLATE, extruder=1, overrides=None, title=None):
    """parts: list of dicts {name, verts (centered), faces, x, y, plate (1-based)}.
    x, y are positions on that plate's bed; z is set so the part sits on the bed."""
    zin = zipfile.ZipFile(template)
    n_plates = max(p["plate"] for p in parts)
    cols = int(np.ceil(np.sqrt(n_plates)))

    def offset(plate):
        i = plate - 1
        return (i % cols) * PLATE_STRIDE, -(i // cols) * PLATE_STRIDE

    files, objects, items, rels, cfg_objs, assemble = {}, [], [], [], [], []
    per_plate = {k: {"inst": [], "bbox": [], "tri": []} for k in range(1, n_plates + 1)}
    for i, p in enumerate(parts):
        sub_id, obj_id = 2 * i + 1, 2 * i + 2
        v, f = p["verts"], p["faces"]
        size = v.max(0) - v.min(0)
        ox, oy = offset(p["plate"])
        wx, wy, wz = p["x"] + ox, p["y"] + oy, -v[:, 2].min()
        vtx = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in v)
        tris = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
        fname = f"3D/Objects/object_{i + 1}.model"
        files[fname] = (HEADER + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                        f'  <object id="{sub_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
                        f'   <mesh>\n    <vertices>\n{vtx}\n    </vertices>\n'
                        f'    <triangles>\n{tris}\n    </triangles>\n   </mesh>\n'
                        '  </object>\n </resources>\n <build/>\n</model>\n').encode()
        rels.append(f' <Relationship Target="/{fname}" Id="rel-{i + 1}" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        objects.append(f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                       f'    <component p:path="/{fname}" objectid="{sub_id}" p:UUID="{uuid.uuid4()}" '
                       'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>')
        tf = f"1 0 0 0 1 0 0 0 1 {wx:g} {wy:g} {wz:g}"
        items.append(f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" transform="{tf}" printable="1"/>')
        cfg_objs.append(f'''  <object id="{obj_id}">
    <metadata key="name" value="{p['name']}"/>
    <metadata key="extruder" value="{extruder}"/>
    <metadata face_count="{len(f)}"/>
    <part id="{sub_id}" subtype="normal_part">
      <metadata key="name" value="{p['name']}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="{p['name']}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="0"/>
      <metadata key="source_offset_y" value="0"/>
      <metadata key="source_offset_z" value="0"/>
      <mesh_stat face_count="{len(f)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>''')
        pp = per_plate[p["plate"]]
        pp["inst"].append(f'''    <model_instance>
      <metadata key="object_id" value="{obj_id}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{100 + i}"/>
    </model_instance>''')
        assemble.append(f'   <assemble_item object_id="{obj_id}" instance_id="0" transform="{tf}" offset="0 0 0" />')
        bb = [p["x"] - size[0] / 2, p["y"] - size[1] / 2, p["x"] + size[0] / 2, p["y"] + size[1] / 2]
        assert bb[0] >= 0 and bb[1] >= 0 and bb[2] <= 256 and bb[3] <= 256, f"{p['name']} is off the bed"
        pp["bbox"].append({"area": float(size[0] * size[1]), "bbox": bb, "id": 100 + i,
                           "layer_height": 0.2, "name": p["name"]})
        pp["tri"].append(v[f] + np.array([p["x"], p["y"], wz]))

    for k, pp in per_plate.items():  # 2 mm gap between parts on a plate
        bbs = pp["bbox"]
        for a in range(len(bbs)):
            for b in range(a + 1, len(bbs)):
                A, B = bbs[a]["bbox"], bbs[b]["bbox"]
                assert A[2] + 2 <= B[0] or B[2] + 2 <= A[0] or A[3] + 2 <= B[1] or B[3] + 2 <= A[1], \
                    f"plate {k}: {bbs[a]['name']} overlaps {bbs[b]['name']}"

    main = zin.read("3D/3dmodel.model").decode()
    main = re.sub(r"<resources>.*</resources>", "<resources>\n" + "\n".join(objects) + "\n </resources>",
                  main, flags=re.S)
    main = re.sub(r"(<build[^>]*>).*</build>", lambda m: m.group(1) + "\n" + "\n".join(items) + "\n </build>",
                  main, flags=re.S)
    main = re.sub(r'<metadata name="Title">[^<]*</metadata>',
                  f'<metadata name="Title">{title or out_path[:-4]}</metadata>', main)
    files["3D/3dmodel.model"] = main.encode()
    files["3D/_rels/3dmodel.model.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + "\n</Relationships>").encode()

    cfg = zin.read("Metadata/model_settings.config").decode()
    plate_tpl = re.search(r"  <plate>.*?</plate>\n", cfg, flags=re.S).group(0)
    plate_tpl = re.sub(r"    <model_instance>.*</model_instance>\n", "{INST}", plate_tpl, flags=re.S)
    plates_xml = ""
    for k, pp in per_plate.items():
        blk = plate_tpl.replace("{INST}", "\n".join(pp["inst"]) + "\n")
        blk = re.sub(r'(key="plater_id" value=")\d+', rf"\g<1>{k}", blk)
        blk = blk.replace("plate_1", f"plate_{k}").replace("plate_no_light_1", f"plate_no_light_{k}") \
                 .replace("top_1", f"top_{k}").replace("pick_1", f"pick_{k}")
        plates_xml += blk
    cfg = re.sub(r"  <object id=.*?</object>\n", lambda m: "\n".join(cfg_objs) + "\n", cfg, count=1, flags=re.S)
    cfg = re.sub(r"  <plate>.*</plate>\n", lambda m: plates_xml, cfg, flags=re.S)
    cfg = re.sub(r"<assemble>.*</assemble>", lambda m: "<assemble>\n" + "\n".join(assemble) + "\n  </assemble>",
                 cfg, flags=re.S)
    files["Metadata/model_settings.config"] = cfg.encode()
    files["Metadata/cut_information.xml"] = ('<?xml version="1.0" encoding="utf-8"?>\n<objects>\n' + "".join(
        f' <object id="{2 * i + 1}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>\n'
        for i in range(len(parts))) + "</objects>").encode()
    files["Metadata/filament_sequence.json"] = json.dumps(
        {f"plate_{k}": {"nozzle_sequence": [], "optimal_assignment": [], "sequence": []} for k in per_plate}).encode()

    settings = json.loads(zin.read("Metadata/project_settings.config"))
    if overrides:
        settings.update(overrides)
        diff = settings["different_settings_to_system"]
        keys = set(filter(None, diff[0].split(";"))) | set(overrides)
        diff[0] = ";".join(sorted(keys))
    files["Metadata/project_settings.config"] = json.dumps(settings, indent=4).encode()

    plate_json = json.loads(zin.read("Metadata/plate_1.json"))
    for k, pp in per_plate.items():
        allb = np.array([b["bbox"] for b in pp["bbox"]])
        pj = dict(plate_json, bbox_all=[allb[:, 0].min(), allb[:, 1].min(), allb[:, 2].max(), allb[:, 3].max()],
                  bbox_objects=pp["bbox"])
        files[f"Metadata/plate_{k}.json"] = json.dumps(pj).encode()
        tri = np.concatenate(pp["tri"])
        lo, hi = tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)
        big, small = _thumb(tri, lo, hi, 512), _thumb(tri, lo, hi, 128)
        for name in (f"plate_{k}.png", f"plate_no_light_{k}.png", f"top_{k}.png", f"pick_{k}.png"):
            files["Metadata/" + name] = big
        files[f"Metadata/plate_{k}_small.png"] = small

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        done = set()
        for item in zin.infolist():
            if item.filename.startswith("3D/Objects/"):
                continue
            zout.writestr(item.filename, files.get(item.filename, zin.read(item.filename)))
            done.add(item.filename)
        for k, data in files.items():
            if k not in done:
                zout.writestr(k, data)
    print(f"{out_path}: {len(parts)} parts on {n_plates} plate(s)")


# (name, stl, orientation, plate x, plate y)
PARTS = [
    ("servo_bracket",      "servo_bracket/servo_bracket.stl",           "on-side",  95, 190),
    ("u_bracket",          "u_bracket/u_bracket.stl",                   "on-side", 160, 190),
    ("servo_base_bracket", "servo_base_bracket/servo_base_bracket.stl", "on-side",  95, 110),
    ("motor_bracket",      "motor_bracket/motor_bracket.stl",           "on-side", 160, 115),
    ("flange_standoff",    "flange_standoff/flange_standoff.stl",       None,      210, 115),
]

if __name__ == "__main__":
    parts = []
    for name, path, how, x, y in PARTS:
        v, f = load_stl(path)
        v, _ = orient(v, how)
        parts.append(dict(name=name, verts=v, faces=f, x=x, y=y, plate=1))
    write_project(parts, "all_parts.3mf", title="all_parts")
