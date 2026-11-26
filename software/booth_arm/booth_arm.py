# Robot house booth without recordings: teach a few poses per block once, then the program builds and
# takes the house apart the same way every time.
#
#   python booth_arm.py teach            build the house once with the black arm, press Enter at each step
#   python booth_arm.py run              loop: build, show, take apart, rest (Ctrl+C to stop)
#   python booth_arm.py run --once       one build + one unbuild
#   python booth_arm.py test 4           pick block 4, place it, take it back (check one block)
#   python booth_arm.py fix 4 place      re-teach one pose of block 4 (pick_above | pick | place_above | place)
#   python booth_arm.py fix travel       re-teach the high pose it passes through between places (or: fix home)
#
# Between places the arm goes straight up to the taught "travel" height, turns, then comes down, so it never
# sweeps through the stacks. Every block has 4 taught poses: above it in storage (gripper open), gripping it in storage,
# above its spot in the house (holding it), and seated in the house (still holding it).
# Taking the house apart is the same list backwards. The gripper position tells whether a block is really
# held: if a grab misses or a block drops, the arm goes home, beeps and waits for a person.
import argparse, json, math, os, sys, time
from pathlib import Path

# ---------------- settings ----------------
FOLLOWER_PORT, FOLLOWER_ID = "COM11", "white_arm"
LEADER_PORT, LEADER_ID = "COM12", "black_arm"
POSES = Path(__file__).with_name("booth_poses.json")
TRAVEL_SPEED = 45.0     # deg/s for moves between places
SLOW_SPEED = 15.0       # deg/s going down onto a block / lifting off it
SQUEEZE = 10.0          # gripper units closed past where it touched the handle while teaching
MISS_TOL = 6.0          # closed this much further than with a block = nothing in the gripper
RELEASE_OPEN = 0.7      # share of the taught opening used to let go (less = narrower)
RELEASE_WAIT = 1.0      # s the arm stays still after opening, before it lifts
GRIP_WAIT = 0.5         # s after closing, before it lifts
SHOW_PAUSE = 30         # s the finished house stays up
REST_PAUSE = 90         # s rest after taking it apart (torque off, motors cool)
HOME_SPEED = 10.0       # deg/s going home after Ctrl+C
RATE = 50               # commands per second
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
JOINTS = ARM + ["gripper"]
STEPS = ["pick_above", "pick", "place_above", "place"]
HELP = {"pick_above": "ABOVE the block in storage, gripper OPEN",
        "pick": "jaws CLOSED on the block's handle in storage",
        "place_above": "carrying it, ABOVE its spot in the house",
        "place": "block SEATED in the house, jaws still CLOSED",
        "home": "arm FOLDED at rest (home)",
        "travel": "arm RAISED HIGH above the middle of the board, gripper down, well above every stack (travel)"}

# ---------------- keyboard (Windows console; line input elsewhere) ----------------
try:
    import msvcrt
    def key():
        """non-blocking: '\\r', 'b', 'q' ... or None"""
        if not msvcrt.kbhit(): return None
        k = msvcrt.getwch()
        if k in ("\x00", "\xe0"): msvcrt.getwch(); return None
        return {"\x08": "b", "\x1b": "q"}.get(k, k.lower())
except ImportError:
    import select
    def key():
        if not select.select([sys.stdin], [], [], 0)[0]: return None
        s = sys.stdin.readline().strip().lower()
        return s[:1] if s else "\r"
def wait_key(allowed="\rq"):
    while True:
        k = key()
        if k and k in allowed: return k
        time.sleep(0.02)
def beep(n=2):
    for _ in range(n):
        try:
            import winsound; winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception: print("\a", end="", flush=True)
        time.sleep(0.8)

# ---------------- hardware ----------------
def make_follower():
    from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    r = SO101Follower(SO101FollowerConfig(port=FOLLOWER_PORT, id=FOLLOWER_ID))
    r.connect(); return r
def make_leader():
    from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
    t = SO101Leader(SO101LeaderConfig(port=LEADER_PORT, id=LEADER_ID))
    t.connect(); return t
def obs(robot): o = robot.get_observation(); return {j: float(o[f"{j}.pos"]) for j in JOINTS}
def send(robot, pose): robot.send_action({f"{j}.pos": float(pose[j]) for j in JOINTS})

class Arm:
    def __init__(self, robot, travel=None):
        self.r = robot; self.cmd = obs(robot); self.torque = True; self.T = travel
    def move(self, target, speed=TRAVEL_SPEED, min_t=0.4):
        """smooth move of all joints from the last command to target (dict, missing joints stay)"""
        if not self.torque: self.wake()
        goal = dict(self.cmd); goal.update({j: v for j, v in target.items() if j in JOINTS})
        d = max(abs(goal[j] - self.cmd[j]) for j in ARM)
        T = max(min_t, d / speed, abs(goal["gripper"] - self.cmd["gripper"]) / 120)
        n = max(1, int(T * RATE)); start = dict(self.cmd); t0 = time.perf_counter()
        for i in range(1, n + 1):
            s = i / n; s = s * s * (3 - 2 * s)
            p = {j: start[j] + (goal[j] - start[j]) * s for j in JOINTS}
            send(self.r, p); self.cmd = p
            dt = t0 + i / RATE - time.perf_counter()
            if dt > 0: time.sleep(dt)
        self.cmd = goal
    def go(self, target, speed=TRAVEL_SPEED):
        """to another place: straight up to the travel height, turn, come down (gripper set on the way down)"""
        if not self.T: return self.move(target, speed)
        if not self.torque: self.wake()
        lift = {j: self.T[j] for j in ("shoulder_lift", "elbow_flex", "wrist_flex")}
        self.move(lift, speed)
        self.move({"shoulder_pan": target["shoulder_pan"], "wrist_roll": target["wrist_roll"]}, speed)
        self.move(target, speed)
    def wait(self, sec): time.sleep(sec)
    def grip(self): return obs(self.r)["gripper"]
    def rest(self):
        """torque off: the folded arm rests on itself and cools down"""
        self.r.bus.disable_torque(); self.torque = False
    def wake(self):
        """torque back on without a jump: goal = where it is now"""
        now = obs(self.r); send(self.r, now); self.r.bus.enable_torque(); self.cmd = now; self.torque = True

# ---------------- poses ----------------
def load():
    if not POSES.exists(): sys.exit(f"No poses yet: run  python {Path(__file__).name} teach")
    return json.loads(POSES.read_text())
def save(P): POSES.write_text(json.dumps(P, indent=1)); print(f"saved {POSES.name}")
def grip_info(b, where):
    """closed (touching the handle), open-direction sign and open value for a block at pick or place"""
    closed = b[where]["gripper"]; opened = b["pick_above"]["gripper"]
    sgn = 1.0 if opened >= closed else -1.0
    return closed, sgn, opened

# ---------------- teach ----------------
def sync(robot, leader):
    """bring the white arm slowly to where the black arm is, before it starts following"""
    Arm(robot).move({j: float(v) for j, v in ((k.removesuffix(".pos"), v) for k, v in leader.get_action().items())}, SLOW_SPEED, 1.5)
def teleop_until_key(robot, leader, allowed="\rbq"):
    """the white arm follows the black one until a key; returns (key, pose of the white arm)"""
    while True:
        a = leader.get_action(); robot.send_action(a)
        k = key()
        if k and k in allowed:
            time.sleep(0.25); return k, {j: float(leader.get_action()[f"{j}.pos"]) for j in JOINTS}, obs(robot)
        time.sleep(1 / RATE)
def teach(args):
    robot, leader = make_follower(), make_leader(); sync(robot, leader)
    P = {"home": None, "travel": None, "blocks": []}
    print("\nTEACH: build the house once with the black arm. Enter = save this step, b = redo the last step, q = stop.\n"
          "Start with all blocks in storage and the arm folded.\n")
    seq = [(k, s) for k in range(12) for s in STEPS] + [(None, "home"), (None, "travel")]
    i = 0
    try:
        while i < len(seq):
            k, s = seq[i]
            print(f"  block {k + 1:2d}/12  {HELP[s]}" if k is not None else f"  {HELP[s]}", end=" ... ", flush=True)
            got, cmd, now = teleop_until_key(robot, leader)
            if got == "q": print("stopped"); break
            if got == "b":
                print("back"); i = max(0, i - 1); continue
            pose = dict(cmd); pose["gripper"] = now["gripper"]     # arm: what was sent; gripper: where it really is
            if k is None: P[s] = pose
            else:
                while len(P["blocks"]) <= k: P["blocks"].append({})
                P["blocks"][k][s] = pose
            print("ok"); i += 1
    finally:
        done = [b for b in P["blocks"] if all(s in b for s in STEPS)]
        P["blocks"] = done
        if P["home"] or done: save(P)
        miss = [n for n in ("home", "travel") if not P[n]]
        print(f"{len(done)} blocks taught" + (f" (missing: python booth_arm.py fix {' / fix '.join(miss)})" if miss else ""))
        leader.disconnect(); robot.disconnect()
def fix(args):
    P = load(); robot, leader = make_follower(), make_leader(); sync(robot, leader)
    try:
        named = args.block in ("home", "travel")
        name = HELP[args.block] if named else f"block {args.block}: {HELP[args.step]}"
        print(f"Move to: {name}  then Enter (q = cancel)")
        got, cmd, now = teleop_until_key(robot, leader, "\rq")
        if got == "\r":
            pose = dict(cmd); pose["gripper"] = now["gripper"]
            if named: P[args.block] = pose
            else: P["blocks"][int(args.block) - 1][args.step] = pose
            save(P)
    finally:
        leader.disconnect(); robot.disconnect()

# ---------------- run ----------------
class Problem(Exception): pass
def pick(arm, b, src, above):
    closed, sgn, opened = grip_info(b, src)
    arm.go({**b[above], "gripper": opened})
    arm.move({**b[src], "gripper": opened}, SLOW_SPEED)
    arm.move({"gripper": closed - sgn * SQUEEZE}, min_t=0.4); arm.wait(GRIP_WAIT)
    if (arm.grip() - closed) * sgn < -MISS_TOL:                     # closed past the handle: nothing there
        arm.move({"gripper": opened}, min_t=0.3); arm.move(b[above], SLOW_SPEED)
        raise Problem("the gripper closed on nothing")
    arm.move({**b[above], "gripper": closed - sgn * SQUEEZE}, SLOW_SPEED)
def place(arm, b, dst, above):
    closed, sgn, opened = grip_info(b, dst)
    arm.go({**b[above], "gripper": arm.cmd["gripper"]})
    if (arm.grip() - closed) * sgn < -MISS_TOL: raise Problem("the block fell on the way")
    arm.move({**b[dst], "gripper": arm.cmd["gripper"]}, SLOW_SPEED)
    arm.move({"gripper": closed + sgn * RELEASE_OPEN * abs(opened - closed)}, min_t=0.4)
    arm.wait(RELEASE_WAIT)
    arm.move({**b[above], "gripper": arm.cmd["gripper"]}, SLOW_SPEED)
def carry(arm, P, k, build):
    b = P["blocks"][k]
    while True:
        try:
            if build: pick(arm, b, "pick", "pick_above"); place(arm, b, "place", "place_above")
            else: pick(arm, b, "place", "place_above"); place(arm, b, "pick", "pick_above")
            return
        except Problem as e:
            where = "storage" if build else "the house"
            print(f"\n*** PROBLEM with block {k + 1}: {e}.")
            arm.go(P["home"]); arm.rest(); beep()
            print(f"    Put block {k + 1} back in its place in {where}, then press Enter to try again (q = stop).")
            if wait_key() == "q": raise KeyboardInterrupt
def cycle(arm, P, blocks):
    print(time.strftime("%H:%M:%S"), "build"); arm.wake()
    for k in blocks: carry(arm, P, k, True)
    arm.go(P["home"]); arm.rest(); time.sleep(SHOW_PAUSE)
    print(time.strftime("%H:%M:%S"), "take apart"); arm.wake()
    for k in reversed(blocks): carry(arm, P, k, False)
    arm.go(P["home"]); arm.rest()
def run(args):
    P = load()
    if not P.get("home"): sys.exit("No home pose: python booth_arm.py fix home")
    if not P.get("travel"): sys.exit("No travel pose yet: python booth_arm.py fix travel  (arm raised high above the middle)")
    blocks = list(range(len(P["blocks"])))
    robot = make_follower(); arm = Arm(robot, P["travel"]); n = 0
    try:
        arm.move(P["home"], SLOW_SPEED)
        while True:
            cycle(arm, P, blocks); n += 1; print(f"   round {n} done")
            if args.once: break
            time.sleep(REST_PAUSE)
    except KeyboardInterrupt:
        go_home_slowly(arm, P)
    finally:
        robot.disconnect()
def go_home_slowly(arm, P):
    print("\nstopping: going home slowly")
    try:
        if not arm.torque: arm.wake()
        arm.go(P["home"], HOME_SPEED)
    except Exception: pass
def test(args):
    P = load(); k = args.block - 1; robot = make_follower(); arm = Arm(robot, P.get("travel"))
    try:
        arm.go(P["home"], SLOW_SPEED); carry(arm, P, k, True); arm.go(P["home"]); time.sleep(2)
        carry(arm, P, k, False); arm.go(P["home"])
    except KeyboardInterrupt: go_home_slowly(arm, P)
    finally: robot.disconnect()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("teach")
    r = sp.add_parser("run"); r.add_argument("--once", action="store_true")
    t = sp.add_parser("test"); t.add_argument("block", type=int)
    f = sp.add_parser("fix"); f.add_argument("block"); f.add_argument("step", nargs="?", choices=STEPS)
    a = ap.parse_args()
    if a.cmd == "fix" and a.block not in ("home", "travel") and not a.step: ap.error("fix <block> <step>  |  fix home  |  fix travel")
    {"teach": teach, "run": run, "test": test, "fix": fix}[a.cmd](a)
