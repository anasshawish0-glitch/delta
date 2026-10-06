"""Builds the assembled SO-101 follower arm with the McKibben "Power Mode" muscle.

Reads the official URDF and meshes from github.com/TheRobotStudio/SO-ARM100
(Simulation/SO101, Apache-2.0), poses the arm, adds two McKibben muscles from the
back of the upper arm to a printed outrigger behind the base, then writes:
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
POSE = dict(shoulder_pan=0.0, shoulder_lift=0.0, elbow_flex=0.0, wrist_flex=0.0,
            wrist_roll=0.0, gripper=0.3)  # radians: upper arm up, forearm forward
UPPER_ANCHOR = 0.10   # m from the shoulder axis along the upper arm (near the elbow)
UPPER_BACK = 0.028    # m back from the arm line: a bolt through the back of the upper arm
LOWER_BACK = 0.16     # m behind the shoulder axis, on the outrigger
LOWER_Z = 0.085       # m above the table (clears the base, top at 70 mm)
MUSCLE_Y = 0.05       # m, one muscle each side of the upper arm
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

# Muscles: two McKibben muscles, one each side of the upper arm, from a crossbar near
# the elbow down to a printed outrigger that turns with the shoulder (so the muscles
# turn with the arm when the base pans). Units: metres (URDF).
sh = joint_frames["shoulder_lift"]
el = joint_frames["elbow_flex"]
axis_pt, elbow_pt = sh[:3, 3], el[:3, 3]
arm_dir = (elbow_pt - axis_pt) / np.linalg.norm(elbow_pt - axis_pt)
reach = world["gripper_frame_link"][:3, 3] - axis_pt
back = -reach; back[2] = 0; back /= np.linalg.norm(back)
side = np.cross([0, 0, 1], back)
upper = axis_pt + UPPER_ANCHOR * arm_dir + UPPER_BACK * back
lower = np.array([*(axis_pt[:2] + LOWER_BACK * back[:2]), LOWER_Z])
arm_mesh = next(m for n, m in meshes if n.startswith("upper_arm"))
centre = side * np.dot(arm_mesh.bounds.mean(0) - upper, side)  # joint origin sits on the motor face, not mid-arm
upper, lower = upper + centre, lower + centre


def rod(a, b, r):
    v = b - a
    c = trimesh.creation.cylinder(radius=r, height=np.linalg.norm(v), sections=24)
    c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / np.linalg.norm(v)))
    c.apply_translation((a + b) / 2)
    return c


def beam(a, b, w):
    v = b - a
    bx = trimesh.creation.box(extents=[w, w, np.linalg.norm(v)])
    bx.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / np.linalg.norm(v)))
    bx.apply_translation((a + b) / 2)
    return bx


extra = [("upper_crossbar", rod(upper - side * (MUSCLE_Y + 0.012), upper + side * (MUSCLE_Y + 0.012), 0.004), "mast"),
         ("lower_crossbar", rod(lower - side * (MUSCLE_Y + 0.012), lower + side * (MUSCLE_Y + 0.012), 0.004), "mast")]
front = np.array([*(axis_pt[:2] + 0.035 * back[:2]), LOWER_Z]) + centre  # outrigger root, on the rotating shoulder part
for k, sgn in enumerate([-1, 1]):
    off = side * sgn * MUSCLE_Y
    m = trimesh.creation.capsule(height=np.linalg.norm(upper - lower) - 0.024, radius=0.009, count=[24, 12])
    v = upper - lower
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / np.linalg.norm(v)))
    m.apply_translation((upper + lower) / 2 + off)
    extra.append((f"mckibben_muscle_{k + 1}", m, "muscle"))
    extra.append((f"outrigger_beam_{k + 1}", beam(front + off * 0.8, lower + off * 0.8, 0.01), "mast"))
for n, m, c in extra:
    m.visual.face_colors = COLOURS[c]
    meshes.append((n, m))
lever = np.linalg.norm(np.cross(upper - axis_pt, (lower - upper) / np.linalg.norm(lower - upper)))
print(f"muscle length {np.linalg.norm(upper - lower) * 1000:.0f} mm, lever about the shoulder {lever * 1000:.0f} mm")

out = os.path.dirname(os.path.abspath(__file__))
scene = trimesh.Scene()
for n, m in meshes:
    mm = m.copy(); mm.apply_scale(1000)
    scene.add_geometry(mm, node_name=n)
trimesh.util.concatenate([m for _, m in scene.geometry.items()]).export(os.path.join(out, "so101_assembly.stl"))
scene.export(os.path.join(out, "so101_assembly.glb"))
print(len(meshes), "parts; bounds (mm):", scene.bounds.round(1).tolist())
