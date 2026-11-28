# Booth loop for two LeRobot recordings (build, then take apart), with a watchdog.
#
#   python booth_replay.py --build build106 --unbuild build108
#
# It plays the recordings itself (like lerobot-replay) and compares the arm with what it did while you
# recorded. If a block is missing from the gripper, the arm gets stuck, or the connection drops, it stops at
# once, lets go, folds the arm, beeps, waits one minute so someone can put ALL the blocks back in storage,
# and starts again from the build. Ctrl+C folds the arm and quits. A log goes to booth_log.txt.
import argparse, glob, json, os, sys, time
from pathlib import Path
import numpy as np, pyarrow.parquet as pq

LOCAL = Path.home() / ".cache/huggingface/lerobot/local"
LOG = Path(__file__).with_name("booth_log.txt")
SHOW_PAUSE = 30        # s the finished house stays up
REST_PAUSE = 90        # s rest after taking it apart
PROBLEM_WAIT = 60      # s for a person to put the blocks back after a problem
MAX_FAILS = 5          # problems in a row before it waits for Enter
MISS_TOL = 8.0         # gripper units more closed than in the recording = no block in the gripper
SQUEEZE_MIN = 4.0      # recording: commanded this much past where the gripper stopped = it was holding a block
BLOCK_TOL = 25.0       # degrees away from the recording = the arm is stuck
WINDOW = 0.3           # s of timing slack when comparing with the recording
MISS_TIME, BLOCK_TIME = 0.3, 1.0   # how long a difference must last
HOME_SPEED = 15.0      # deg/s when folding after a problem
HEADLESS_WAIT = 300    # s instead of "press Enter" when nobody can type (Raspberry Pi service)

def find_port(port):
    """auto: COM11 on Windows; on Linux the first USB serial device that is not an Arduino"""
    if port != "auto": return port
    if os.name == "nt": return "COM11"
    ids = [p for p in sorted(glob.glob("/dev/serial/by-id/*")) if "arduino" not in p.lower()]
    devs = ids or sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))
    return devs[0] if devs else None

def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")
    except OSError: pass

def beep(n=2):
    for _ in range(n):
        try:
            import winsound; winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception: print("\a", end="", flush=True)
        time.sleep(0.8)

class Problem(Exception): pass

class Recording:
    def __init__(self, name):
        d = LOCAL / name
        if not (d / "meta/info.json").exists(): sys.exit(f"recording {name} not found in {LOCAL}")
        info = json.loads((d / "meta/info.json").read_text())
        self.name, self.fps = name, info.get("fps", 30)
        names = info["features"]["action"]["names"]
        self.names = next(iter(names.values())) if isinstance(names, dict) else list(names)
        t = pq.read_table(sorted((d / "data").glob("*/*.parquet"))[0])
        if "episode_index" in t.column_names:
            keep = np.array(t.column("episode_index").to_pylist()) == 0
            t = t.filter(keep)
        self.act = np.array(t.column("action").to_pylist(), dtype=float)
        self.obs = np.array(t.column("observation.state").to_pylist(), dtype=float) if "observation.state" in t.column_names else self.act.copy()
        self.g = next(i for i, n in enumerate(self.names) if "gripper" in n)
        self.arm = [i for i in range(len(self.names)) if i != self.g]
        self.w = max(1, int(WINDOW * self.fps))
        # where it was holding a block: the command went past where the gripper stopped, for 0.5 s or more
        diff = self.obs[:, self.g] - self.act[:, self.g]
        big = np.abs(diff) > SQUEEZE_MIN
        self.sgn = float(np.sign(np.median(diff[big]))) if big.any() else 0.0
        hold = big & (np.sign(diff) == self.sgn) if self.sgn else np.zeros(len(diff), bool)
        self.hold = np.zeros(len(diff), bool)
        i = 0
        while i < len(hold):
            if hold[i]:
                j = i
                while j < len(hold) and hold[j]: j += 1
                if j - i >= 0.5 * self.fps: self.hold[i + self.w:j - self.w] = True
                i = j
            else: i += 1
        # the gripper's most open position, to let go after a problem
        self.open_g = float(np.percentile(self.act[:, self.g], 98 if self.sgn > 0 else 2)) if self.sgn else None

    def pose(self, i): return {n: float(v) for n, v in zip(self.names, self.act[i])}

class Arm:
    def __init__(self, port, robot_id):
        self.port, self.robot_id, self.robot = port, robot_id, None
    def connect(self):
        while True:
            port = find_port(self.port)
            try:
                if port is None: raise ConnectionError("no USB serial device")
                from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
                self.robot = SO101Follower(SO101FollowerConfig(port=port, id=self.robot_id, max_relative_target=10.0))
                self.robot.connect(); log(f"arm connected on {port}"); return
            except Exception as e:
                log(f"waiting for the arm on {port or self.port} ({type(e).__name__})"); self.robot = None; time.sleep(5)
    def read(self, names):
        o = self.robot.get_observation(); return np.array([float(o[n]) for n in names])
    def send(self, names, values): self.robot.send_action({n: float(v) for n, v in zip(names, values)})
    def rest(self):
        try: self.robot.bus.disable_torque()
        except Exception: pass
    def wake(self, names):
        now = self.read(names); self.send(names, now); self.robot.bus.enable_torque(); return now
    def glide(self, names, start, goal, speed, fps=30, min_t=0.5):
        d = float(np.max(np.abs(goal - start)))
        n = max(1, int(max(min_t, d / speed) * fps)); t0 = time.perf_counter()
        for k in range(1, n + 1):
            s = k / n; s = s * s * (3 - 2 * s)
            self.send(names, start + (goal - start) * s)
            dt = t0 + k / fps - time.perf_counter()
            if dt > 0: time.sleep(dt)
    def close(self):
        try: self.robot.disconnect()
        except Exception: pass

def play(arm, rec):
    names = rec.names
    now = arm.wake(names)
    arm.glide(names, now, rec.act[0], 30.0)                    # smoothly to where the recording starts
    miss = block = 0
    t0 = time.perf_counter()
    for i in range(len(rec.act)):
        arm.send(names, rec.act[i])
        live = arm.read(names)
        lo, hi = max(0, i - rec.w), min(len(rec.act), i + rec.w + 1)
        win = rec.obs[lo:hi]
        if rec.hold[i]:      # it should be holding a block: is the gripper closed further than with the block?
            more_closed = -rec.sgn * (live[rec.g] - win[:, rec.g])
            miss = miss + 1 if more_closed.min() > MISS_TOL else 0
            if miss >= MISS_TIME * rec.fps: raise Problem(f"no block in the gripper ({rec.name}, {i / rec.fps:.1f}s)")
        else: miss = 0
        away = np.maximum(win[:, rec.arm].min(0) - live[rec.arm], live[rec.arm] - win[:, rec.arm].max(0))
        block = block + 1 if away.max() > BLOCK_TOL else 0
        if block >= BLOCK_TIME * rec.fps: raise Problem(f"the arm is stuck ({rec.name}, {i / rec.fps:.1f}s)")
        dt = t0 + (i + 1) / rec.fps - time.perf_counter()
        if dt > 0: time.sleep(dt)

def fold(arm, rec_home, rec_any):
    """after a problem: hold still, let go, fold slowly to where the build starts, torque off"""
    names = rec_home.names
    try:
        now = arm.read(names); arm.send(names, now); time.sleep(0.5)
        if rec_any.open_g is not None:
            opened = now.copy(); opened[rec_any.g] = rec_any.open_g
            arm.glide(names, now, opened, 200.0, min_t=0.5); now = opened
        arm.glide(names, now, rec_home.act[0], HOME_SPEED)
    except Exception as e: log(f"could not fold the arm ({type(e).__name__})")
    arm.rest()

def wait(sec, msg):
    log(msg)
    for left in range(sec, 0, -1):
        if left % 10 == 0 or left <= 5: print(f"   restarting in {left} s", flush=True)
        if left == 10: beep(1)
        time.sleep(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True); ap.add_argument("--unbuild", required=True)
    ap.add_argument("--port", default="auto", help="auto, COM11, /dev/ttyACM0, ..."); ap.add_argument("--id", default="white_arm")
    ap.add_argument("--wait", type=int, default=PROBLEM_WAIT, help="seconds to put the blocks back after a problem")
    a = ap.parse_args()
    build, unbuild = Recording(a.build), Recording(a.unbuild)
    for r in (build, unbuild):
        log(f"{r.name}: {len(r.act) / r.fps:.0f}s, gripper check on {r.hold.mean() * 100:.0f}% of it")
    arm = Arm(a.port, a.id); arm.connect()
    fails = rounds = 0
    try:
        while True:
            try:
                log("build"); play(arm, build); arm.rest(); time.sleep(SHOW_PAUSE)
                log("take apart"); play(arm, unbuild); arm.rest()
                rounds += 1; fails = 0; log(f"round {rounds} done"); time.sleep(REST_PAUSE)
            except Problem as e:
                fails += 1; log(f"PROBLEM: {e}")
                fold(arm, build, unbuild); beep(2)
                if fails >= MAX_FAILS:
                    if sys.stdin is not None and sys.stdin.isatty():
                        log(f"{fails} problems in a row: put the blocks back and press Enter to start again")
                        input()
                    else:
                        wait(HEADLESS_WAIT, f"{fails} problems in a row: waiting {HEADLESS_WAIT // 60} minutes. Put ALL blocks back in storage.")
                    fails = 0
                else:
                    wait(a.wait, "Put ALL blocks back in storage and leave the arm alone.")
            except (ConnectionError, OSError, RuntimeError) as e:
                fails += 1; log(f"PROBLEM: connection lost ({type(e).__name__}: {str(e).splitlines()[0][:80]})")
                arm.close(); beep(2)
                wait(a.wait, "Put ALL blocks back in storage. Check the arm's USB and power.")
                arm.connect()
    except KeyboardInterrupt:
        log("stopping: folding the arm")
        fold(arm, build, unbuild)
    finally:
        arm.close()

if __name__ == "__main__":
    main()
