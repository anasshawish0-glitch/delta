# Copy a recording with the gripper opening wider; how tightly it grips stays the same.
#   python widen_gripper.py <recording> <new name> [factor, default 1.5]
import sys, json, shutil, pathlib
import numpy as np, pyarrow as pa, pyarrow.parquet as pq

src_name, dst_name = sys.argv[1], sys.argv[2]
k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
L = pathlib.Path.home() / ".cache/huggingface/lerobot/local"
src, dst = L / src_name, L / dst_name
if not src.exists(): sys.exit(f"{src_name} not found in {L}")
if dst.exists(): sys.exit(f"{dst_name} already exists, pick another name")

names = json.load(open(src / "meta/info.json"))["features"]["action"]["names"]
if isinstance(names, dict): names = next(iter(names.values()))
g = next(i for i, n in enumerate(names) if "gripper" in n)

shutil.copytree(src, dst)
for p in sorted((dst / "data").glob("*/*.parquet")):
    t = pq.read_table(p)
    col = t.column("action")
    a = np.array(col.to_pylist(), dtype=np.float32)
    v = a[:, g].copy()
    lo, hi, med = np.percentile(v, 2), np.percentile(v, 98), np.median(v)
    closed = lo if (med - lo) < (hi - med) else hi      # it is closed most of the time
    a[:, g] = np.clip(closed + (v - closed) * k, 0, 100)
    i = t.schema.get_field_index("action")
    t2 = t.set_column(i, t.schema.field(i), pa.array(a.tolist(), type=col.type))
    pq.write_table(t2.replace_schema_metadata(t.schema.metadata), p)
    print(f"{p.name}: gripper closed at {closed:.1f}, widest was {v.max() if closed == lo else v.min():.1f}, "
          f"now {a[:, g].max() if closed == lo else a[:, g].min():.1f}  ({len(v)} frames)")
print(f"Done: {dst_name}")
