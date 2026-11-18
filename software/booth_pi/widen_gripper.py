# Copy a recording with the gripper opening wider; how tightly it grips stays the same.
#   python widen_gripper.py <recording> --list                    list the grasps and how wide each release opens
#   python widen_gripper.py <recording> <new name> --grip 4 [1.5]  wider only when it lets go of the 4th block
#   python widen_gripper.py <recording> <new name> --approach 3 0.6  narrower while it comes down onto the 3rd block
#   python widen_gripper.py <recording> <new name> [1.5]           wider everywhere
import sys, json, shutil, pathlib, argparse
import numpy as np, pyarrow as pa, pyarrow.parquet as pq

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst", nargs="?"); ap.add_argument("factor", nargs="?", type=float, default=1.5)
ap.add_argument("--grip", type=int, help="widen only the opening right after this grasp (1 = first block)")
ap.add_argument("--approach", type=int, help="change only the opening while it comes down onto this block (1 = first)")
ap.add_argument("--list", action="store_true", help="only list the grasps")
ap.add_argument("--secs", type=float, default=None, help="--grip: seconds wider after letting go (1); --approach: seconds before it closes (1.5)")
o = ap.parse_intermixed_args()
if o.secs is None: o.secs = 1.5 if o.approach else 1.0

L = pathlib.Path.home() / ".cache/huggingface/lerobot/local"
src = L / o.src
if not src.exists(): sys.exit(f"{o.src} not found in {L}")
info = json.load(open(src / "meta/info.json"))
fps = info.get("fps", 30)
names = info["features"]["action"]["names"]
if isinstance(names, dict): names = next(iter(names.values()))
g = next(i for i, n in enumerate(names) if "gripper" in n)

def analyse(v):
    lo, hi, med = np.percentile(v, 2), np.percentile(v, 98), np.median(v)
    sign = 1 if (med - lo) < (hi - med) else -1           # it is closed most of the time
    closed = lo if sign == 1 else hi
    s = (v - closed) * sign                               # how far open, >= 0
    amp = max(np.percentile(s, 98), 1e-6)
    op = s > 0.3 * amp
    runs, i = [], 0
    while i < len(op):
        if op[i]:
            j = i
            while j < len(op) and op[j]: j += 1
            if j - i >= 0.15 * fps: runs.append([i, j])
            i = j
        else: i += 1
    return closed, sign, s, amp, runs

def window(s, amp, a, b):      # widen [a, b) out to where the gripper is nearly closed again
    while a > 0 and s[a - 1] > 0.05 * amp: a -= 1
    while b < len(s) and s[b] > 0.05 * amp: b += 1
    return a, b

files = sorted((src / "data").glob("*/*.parquet"))
if o.list:
    for p in files:
        v = np.array(pq.read_table(p).column("action").to_pylist(), dtype=np.float32)[:, g]
        closed, sign, s, amp, runs = analyse(v)
        print(f"{p.name}: gripper closed at {closed:.1f}")
        for n in range(1, len(runs)):
            a, b = runs[n]
            print(f"  grasp {n}: holds {runs[n-1][1] / fps:5.1f}s -> {a / fps:5.1f}s, then opens to {closed + sign * s[a:b].max():.1f}")
    sys.exit()

if not o.dst: sys.exit("give a new name for the copy")
dst = L / o.dst
if dst.exists(): sys.exit(f"{o.dst} already exists, pick another name")
shutil.copytree(src, dst)
for p in sorted((dst / "data").glob("*/*.parquet")):
    t = pq.read_table(p); col = t.column("action")
    act = np.array(col.to_pylist(), dtype=np.float32)
    v = act[:, g].copy()
    closed, sign, s, amp, runs = analyse(v)
    if o.approach:
        if not 1 <= o.approach < len(runs): sys.exit(f"there are only {len(runs) - 1} grasps in {o.src}")
        a0, b = runs[o.approach - 1]
        while b < len(s) and s[b] > 0.05 * amp: b += 1          # through the closing onto the handle
        full = max(a0, runs[o.approach - 1][1] - int(o.secs * fps))
        a = max(a0, full - int(0.5 * fps))
        w = np.ones(b - a); ramp = full - a
        if ramp > 0: x = np.arange(ramp) / ramp; w[:ramp] = x * x * (3 - 2 * x)
        s2 = s.copy(); s2[a:b] *= 1 + (o.factor - 1) * w
        print(f"block {o.approach}: coming down at {a / fps:.1f}s -> {b / fps:.1f}s opens to "
              f"{closed + sign * s2[full:b].max():.1f} instead of {closed + sign * s[full:b].max():.1f}")
    elif o.grip:
        if o.grip >= len(runs): sys.exit(f"there are only {len(runs) - 1} grasps in {o.src}")
        a, b = window(s, amp, *runs[o.grip])
        # wider only while it lets go: o.secs at full width, then back to the recorded opening over 0.5 s,
        # so it reaches the next block exactly as recorded
        n = np.arange(b - a) / fps
        w = np.clip(1 - (n - o.secs) / 0.5, 0, 1)
        w = w * w * (3 - 2 * w)
        s2 = s.copy(); s2[a:b] *= 1 + (o.factor - 1) * w
        b = a + int((o.secs + 0.5) * fps) if a + int((o.secs + 0.5) * fps) < b else b
        print(f"grasp {o.grip}: the release at {a / fps:.1f}s -> {b / fps:.1f}s opens to "
              f"{closed + sign * s2[a:b].max():.1f} instead of {closed + sign * s[a:b].max():.1f}")
    else:
        s2 = s * o.factor
        print(f"every opening x{o.factor}")
    act[:, g] = np.clip(closed + sign * s2, 0, 100)
    i = t.schema.get_field_index("action")
    t2 = t.set_column(i, t.schema.field(i), pa.array(act.tolist(), type=col.type))
    pq.write_table(t2.replace_schema_metadata(t.schema.metadata), p)
print(f"Done: {o.dst}")
