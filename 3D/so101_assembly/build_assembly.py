"""Builds the assembled SO-101 follower arm with the McKibben "Power Mode" muscle.

Reads the official URDF and meshes from github.com/TheRobotStudio/SO-ARM100
(Simulation/SO101, Apache-2.0), poses the arm, adds a printed muscle mast on the
shoulder and a McKibben muscle from the mast top to the upper arm, then writes:
  so101_assembly.stl  everything in one file
  so101_assembly.glb  coloured, for quick viewing

Run: python3 build_assembly.py <path to SO-ARM100/Simulation/SO101>
"""
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh
from trimesh.transformations import euler_matrix, rotation_matrix, translation_matrix

SRC = sys.argv[1]
POSE = dict(shoulder_pan=0.0, shoulder_lift=0.6, elbow_flex=-0.4, wrist_flex=0.9,
            wrist_roll=0.0, gripper=0.3)  # radians, arm reaching forward to lift
MUSCLE_ATTACH = 0.03  # m from the shoulder axis along the upper arm
COLOURS = dict(sts3215=[40, 40, 40, 255], muscle=[220, 60, 50, 255], mast=[90, 140, 220, 255])
PART_COLOUR = [235, 235, 230, 255]


def origin(el):
    o = el.find("origin")
    xyz = [float(v) for v in o.get("xyz", "0 0 0").split()] if o is not None else [0, 0, 0]
    rpy = [float(v) for v in o.get("rpy", "0 0 0").split()] if o is not None else [0, 0, 0]
    return translation_matrix(xyz) @ euler_matrix(*rpy, "sxyz")


root = ET.parse(os.path.join(SRC, "so101_new_calib.urdf")).getroot()
links = {l.get("name"): l for l in root.findall("link")}
joints = [j for j in root.findall("joint") if j.find("parent") is not None]
world = {"base_link": np.eye(4)}
joint_frames = {}
pending = list(joints)
while pending:
    for j in list(pending):
        parent, child = j.find("parent").get("link"), j.find("child").get("link")
        if parent not in world:
            continue
        frame = world[parent] @ origin(j)
        joint_frames[j.get("name")] = frame
        q = POSE.get(j.get("name"), 0.0)
        axis = [float(v) for v in j.find("axis").get("xyz").split()] if j.find("axis") is not None else [0, 0, 1]
        world[child] = frame @ (rotation_matrix(q, axis) if any(axis) else np.eye(4))
        pending.remove(j)

meshes = []  # (name, mesh)
count = {}
for name, link in links.items():
    for vis in link.findall("visual"):
        fn = vis.find("geometry/mesh").get("filename")
        m = trimesh.load(os.path.join(SRC, fn), force="mesh")
        m.apply_transform(world[name] @ origin(vis))
        base = os.path.splitext(os.path.basename(fn))[0]
        count[base] = count.get(base, 0) + 1
        m.visual.face_colors = COLOURS["sts3215"] if base.startswith("sts3215") else PART_COLOUR
        meshes.append((f"{base}_{count[base]}" if base.startswith("sts3215") else base, m))

# Muscle geometry, in metres (URDF units)
sh = joint_frames["shoulder_lift"]
el = joint_frames["elbow_flex"]
axis_pt, elbow_pt = sh[:3, 3], el[:3, 3]
arm_dir = (elbow_pt - axis_pt) / np.linalg.norm(elbow_pt - axis_pt)
attach = axis_pt + MUSCLE_ATTACH * arm_dir
reach = world["gripper_frame_link"][:3, 3] - axis_pt
back = -reach; back[2] = 0; back /= np.linalg.norm(back)
mast_foot = np.array([*(axis_pt[:2] + back[:2] * 0.06), 0.0])  # behind the shoulder, on the base
mast_top = mast_foot + [0, 0, axis_pt[2] + 0.10]
mast = trimesh.creation.box(extents=[0.012, 0.012, mast_top[2] - mast_foot[2]])
mast.apply_translation((mast_foot + mast_top) / 2)
plate = trimesh.creation.box(extents=[0.04, 0.03, 0.004]); plate.apply_translation(mast_foot + [0, 0, 0.002])
muscle = trimesh.creation.capsule(height=np.linalg.norm(attach - mast_top) - 0.02, radius=0.009, count=[24, 12])
v = attach - mast_top
rot = trimesh.geometry.align_vectors([0, 0, 1], v / np.linalg.norm(v))
muscle.apply_transform(rot); muscle.apply_translation((attach + mast_top) / 2)
for n, m, c in [("muscle_mast", mast, "mast"), ("muscle_mast_plate", plate, "mast"), ("mckibben_muscle", muscle, "muscle")]:
    m.visual.face_colors = COLOURS[c]
    meshes.append((n, m))

out = os.path.dirname(os.path.abspath(__file__))
scene = trimesh.Scene()
for n, m in meshes:
    mm = m.copy(); mm.apply_scale(1000)
    scene.add_geometry(mm, node_name=n)
trimesh.util.concatenate([m for _, m in scene.geometry.items()]).export(os.path.join(out, "so101_assembly.stl"))
scene.export(os.path.join(out, "so101_assembly.glb"))
print(len(meshes), "parts; bounds (mm):", scene.bounds.round(1).tolist())
