// SO-101 kinematics for the digital twin: forward kinematics from robot.json and a
// damped least-squares IK for the gripper tip. Plain math, no three.js, so it can be
// tested in Node and reused by the page. Units: metres and radians (URDF).

export const ARM = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll'];
const IK_JOINTS = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex'];

// 4x4 row-major matrices stored as flat arrays of 16
const mul = (a, b) => {
  const r = new Array(16).fill(0);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) r[i * 4 + j] += a[i * 4 + k] * b[k * 4 + j];
  return r;
};
const fromXyzRpy = ([x, y, z], [r, p, w]) => {
  const cr = Math.cos(r), sr = Math.sin(r), cp = Math.cos(p), sp = Math.sin(p), cy = Math.cos(w), sy = Math.sin(w);
  // R = Rz(yaw) * Ry(pitch) * Rx(roll), the URDF convention
  return [
    cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr, x,
    sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr, y,
    -sp, cp * sr, cp * cr, z,
    0, 0, 0, 1];
};
const axisAngle = ([x, y, z], q) => {
  const n = Math.hypot(x, y, z) || 1; x /= n; y /= n; z /= n;
  const c = Math.cos(q), s = Math.sin(q), t = 1 - c;
  return [
    t * x * x + c, t * x * y - s * z, t * x * z + s * y, 0,
    t * x * y + s * z, t * y * y + c, t * y * z - s * x, 0,
    t * x * z - s * y, t * y * z + s * x, t * z * z + c, 0,
    0, 0, 0, 1];
};
const pos = m => [m[3], m[7], m[11]];

export function makeRobot(desc) {
  const byChild = {};
  for (const j of desc.joints) byChild[j.child] = { ...j, origin: fromXyzRpy(j.xyz, j.rpy) };
  const joint = name => desc.joints.find(j => j.name === name);
  const limits = {};
  for (const j of desc.joints) if (j.type === 'revolute') limits[j.name] = [j.lower, j.upper];

  // world transform of every link for joint angles q (a {name: radians} map)
  function fk(q) {
    const world = { base_link: fromXyzRpy([0, 0, 0], [0, 0, 0]) };
    const solve = link => {
      if (world[link]) return world[link];
      const j = byChild[link];
      const parent = solve(j.parent);
      const rot = j.type === 'revolute' ? axisAngle(j.axis, q[j.name] || 0) : fromXyzRpy([0, 0, 0], [0, 0, 0]);
      return (world[link] = mul(mul(parent, j.origin), rot));
    };
    for (const link of Object.keys(byChild)) solve(link);
    return world;
  }
  const tip = q => pos(fk(q).gripper_frame_link);
  // direction the gripper points: from the wrist joint towards the tip
  const approach = q => {
    const w = fk(q), a = pos(w.wrist_link), b = pos(w.gripper_frame_link);
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], n = Math.hypot(...d);
    return d.map(v => v / n);
  };

  // Damped least squares on 4 joints. mode 'down' points the gripper straight down; when the
  // wrist limit makes that impossible it falls back to 'soft' (mostly down), then 'free'.
  function ik(target, q0, mode = 'free') {
    if (mode === 'down') {
      const d = solve(target, q0, 0.08, true);
      if (d.ok) return d;
      const s = solve(target, d.q, 0.015, false);
      if (s.ok) return s;
      const f = solve(target, s.q, 0, false);
      return f.ok ? f : s;
    }
    return solve(target, q0, 0, false);
  }

  function solve(target, q0, w, strict) {
    const q = { ...q0 };
    const err = qq => {
      const p = tip(qq), e = [target[0] - p[0], target[1] - p[1], target[2] - p[2]];
      if (w) { const a = approach(qq); e.push(w * (0 - a[0]), w * (0 - a[1]), w * (-1 - a[2])); }
      return e;
    };
    let e = err(q);
    for (let it = 0; it < 150; it++) {
      const n = e.length, h = 1e-5;
      const J = IK_JOINTS.map(name => {
        const qq = { ...q, [name]: q[name] + h }, e2 = err(qq);
        return e.map((v, i) => (v - e2[i]) / h); // d(position)/dq, since e = target - f
      });
      // dq = J^T (J J^T + l^2 I)^-1 e, J is n x 4 stored by column in J[k][i]
      const lam = 0.02, A = [];
      for (let i = 0; i < n; i++) { A.push([]); for (let k = 0; k < n; k++) { let s = 0; for (let c = 0; c < 4; c++) s += J[c][i] * J[c][k]; A[i].push(s + (i === k ? lam * lam : 0)); } }
      const y = gauss(A, e.slice());
      IK_JOINTS.forEach((name, c) => {
        let d = 0; for (let i = 0; i < n; i++) d += J[c][i] * y[i];
        const [lo, hi] = limits[name];
        q[name] = Math.min(hi, Math.max(lo, q[name] + Math.max(-0.2, Math.min(0.2, d))));
      });
      e = err(q);
      if (Math.hypot(e[0], e[1], e[2]) < 5e-4 && (!strict || Math.hypot(e[3], e[4], e[5]) < 0.002)) break;
    }
    const p = tip(q);
    const miss = Math.hypot(target[0] - p[0], target[1] - p[1], target[2] - p[2]);
    return { q, miss, ok: miss < 0.005 };
  }

  return { fk, tip, approach, ik, limits, joint };
}

function gauss(A, b) {
  const n = b.length;
  for (let i = 0; i < n; i++) {
    let p = i;
    for (let r = i + 1; r < n; r++) if (Math.abs(A[r][i]) > Math.abs(A[p][i])) p = r;
    [A[i], A[p]] = [A[p], A[i]]; [b[i], b[p]] = [b[p], b[i]];
    for (let r = i + 1; r < n; r++) {
      const f = A[r][i] / A[i][i];
      for (let c = i; c < n; c++) A[r][c] -= f * A[i][c];
      b[r] -= f * b[i];
    }
  }
  const x = new Array(n).fill(0);
  for (let i = n - 1; i >= 0; i--) { let s = b[i]; for (let c = i + 1; c < n; c++) s -= A[i][c] * x[c]; x[i] = s / A[i][i]; }
  return x;
}
