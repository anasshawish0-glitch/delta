"""Builds the browser assets for the SO-101 digital twin.

Reads the official URDF + meshes (github.com/TheRobotStudio/SO-ARM100, Simulation/SO101,
Apache-2.0) and writes:
  meshes.json        one simplified, coloured mesh per link, in the link's own frame
                     (base64 arrays: float32 positions, int8 normals, uint8 colours, uint32 indices)
  robot.json         the kinematic chain (joint origins, axes, limits) for the web page

Run: python3 build_meshes.py <path to SO-ARM100/Simulation/SO101>
"""
import base64
import json
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from trimesh.transformations import euler_matrix, translation_matrix

SRC = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))
FACES_PER_PART = 3000
MOTOR = [38, 38, 42, 255]
PRINTED = [236, 236, 232, 255]


def vec(el, key, default="0 0 0"):
    return [float(v) for v in (el.get(key, default) if el is not None else default).split()]


def origin(el):
    o = el.find("origin")
    return translation_matrix(vec(o, "xyz")) @ euler_matrix(*vec(o, "rpy"), "sxyz")


root = ET.parse(os.path.join(SRC, "so101_new_calib.urdf")).getroot()
links, packed = [], {}


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


for link in root.findall("link"):
    parts = []
    for vis in link.findall("visual"):
        fn = vis.find("geometry/mesh").get("filename")
        m = trimesh.load(os.path.join(SRC, fn), force="mesh")
        if len(m.faces) > FACES_PER_PART:
            m = m.simplify_quadric_decimation(face_count=FACES_PER_PART)
        m.apply_transform(origin(vis))
        m.visual.face_colors = MOTOR if "sts3215" in fn else PRINTED
        parts.append(m)
    if parts:
        merged = trimesh.util.concatenate(parts)
        packed[link.get("name")] = {
            "pos": b64(merged.vertices.astype(np.float32)),
            "nrm": b64(np.round(merged.vertex_normals * 127).astype(np.int8)),
            "col": b64(merged.visual.vertex_colors[:, :3].astype(np.uint8)),
            "idx": b64(merged.faces.astype(np.uint32)),
        }
        links.append(link.get("name"))

joints = []
for j in root.findall("joint"):
    if j.find("parent") is None:
        continue
    o = j.find("origin")
    lim = j.find("limit")
    joints.append({
        "name": j.get("name"), "type": j.get("type"),
        "parent": j.find("parent").get("link"), "child": j.find("child").get("link"),
        "xyz": vec(o, "xyz"), "rpy": vec(o, "rpy"),
        "axis": vec(j.find("axis"), "xyz", "0 0 1"),
        "lower": float(lim.get("lower")) if lim is not None else 0.0,
        "upper": float(lim.get("upper")) if lim is not None else 0.0,
    })
with open(os.path.join(OUT, "meshes.json"), "w") as f:
    json.dump(packed, f)
with open(os.path.join(OUT, "robot.json"), "w") as f:
    json.dump({"links": links, "joints": joints}, f, indent=1)
print(len(links), "links,", len(joints), "joints")
