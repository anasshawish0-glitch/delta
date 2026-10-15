// Kitty Hexapod kinematics: 6 legs x 3 servos (coxa, femur, tibia) and a tripod gait.
// Plain math, no three.js, so it runs in Node too. Units: millimetres, radians, seconds.
// Body frame: x forward, y left, z up, origin at the body centre on the height of the femur axes.
//
// Joint zero for every leg: coxa pointing straight out from the body, femur level and the tibia
// tip straight below the knee. Servo angle = 90 + sign * joint (deg) + trim.

export const JOINTS = ['coxa', 'femur', 'tibia'];
export const LAYOUTS = {
  kalem: 'Hexapod Spider Robot (Emre Kalem, MG996R)',
  'hex-flat': 'Round body, two legs in front',
  'hex-point': 'Round body, one leg in front',
  rect: 'Long body, three legs per side',
};
// Measured from the Hexapod Spider Robot print files: coxa axis to femur axis 38 mm, femur axis
// to knee 86.3 mm, knee to claw tip 163 mm; coxa bearings 116 mm out at ±29.4° and ±150.6°,
// 106 mm out at ±90°.
export const KALEM = { coxa: 38, femur: 86.3, tibia: 163 };
export const DEFAULT_DIMS = { layout: 'kalem', ...KALEM, radius: 110, length: 140, width: 120 };
const TRIPOD = [0, 1, 0, 1, 0, 1]; // legs 0, 2, 4 step together, then 1, 3, 5
const DEG = Math.PI / 180;

// Leg order is the servo order on the wire. Each layout keeps the tripods alternating around the body.
export function legNames(d) {
  return d.layout === 'hex-point'
    ? { codes: ['F', 'FR', 'BR', 'FL', 'BL', 'B'], names: ['Front', 'Front right', 'Back right', 'Front left', 'Back left', 'Back'] }
    : { codes: ['R1', 'R2', 'R3', 'L1', 'L2', 'L3'], names: ['Right front', 'Right middle', 'Right back', 'Left front', 'Left middle', 'Left back'] };
}

export function legMounts(d) {
  if (d.layout === 'kalem') {
    return [[101, -57], [0, -106], [-101, -57], [101, 57], [0, 106], [-101, 57]].map(([x, y]) => ({ x, y, a: Math.atan2(y, x) }));
  }
  if (d.layout === 'rect') {
    const fx = d.length / 2, my = d.width / 2, cy = my * 0.75, q = Math.PI / 4;
    return [
      { x: fx, y: -cy, a: -q }, { x: 0, y: -my, a: -2 * q }, { x: -fx, y: -cy, a: -3 * q },
      { x: fx, y: cy, a: q }, { x: 0, y: my, a: 2 * q }, { x: -fx, y: cy, a: 3 * q },
    ];
  }
  const angles = d.layout === 'hex-flat' ? [-30, -90, -150, 30, 90, 150] : [0, -60, -120, 60, 120, 180];
  return angles.map(a => ({ x: d.radius * Math.cos(a * DEG), y: d.radius * Math.sin(a * DEG), a: a * DEG }));
}

// where each foot rests on the ground, relative to the point under the body centre;
// spread is the foot's distance out from the femur axis, in % of femur + tibia
export function homeFeet(d, spread) {
  const r = d.coxa + spread / 100 * (d.femur + d.tibia);
  return legMounts(d).map(m => [m.x + r * Math.cos(m.a), m.y + r * Math.sin(m.a)]);
}

const acosc = v => Math.acos(Math.max(-1, Math.min(1, v)));

// foot position in the body frame -> joint angles; ok is false when the foot is out of reach
export function legIK(d, m, p) {
  const vx = p[0] - m.x, vy = p[1] - m.y, c = Math.cos(m.a), s = Math.sin(m.a);
  const lx = c * vx + s * vy, ly = -s * vx + c * vy, lz = p[2];
  const coxa = Math.atan2(ly, lx);
  const r = Math.hypot(lx, ly) - d.coxa;
  const max = d.femur + d.tibia - 0.5, min = Math.abs(d.femur - d.tibia) + 0.5;
  let dist = Math.hypot(r, lz);
  const ok = dist <= max && dist >= min;
  dist = Math.min(max, Math.max(min, dist));
  const femur = Math.atan2(lz, r) + acosc((d.femur ** 2 + dist ** 2 - d.tibia ** 2) / (2 * d.femur * dist));
  const knee = acosc((d.femur ** 2 + d.tibia ** 2 - dist ** 2) / (2 * d.femur * d.tibia));
  return { q: [coxa, femur, knee - Math.PI / 2], ok };
}

// joint angles -> foot position in the body frame (used by the tests)
export function legFK(d, m, q) {
  const ang = m.a + q[0], t = q[1] + q[2] - Math.PI / 2;
  const r = d.coxa + d.femur * Math.cos(q[1]) + d.tibia * Math.cos(t);
  const z = d.femur * Math.sin(q[1]) + d.tibia * Math.sin(t);
  return [m.x + r * Math.cos(ang), m.y + r * Math.sin(ang), z];
}

// ground-frame point -> body frame, for a body raised by h, shifted by (sx, sy) and tilted by
// roll, pitch, yaw (R = Rz * Ry * Rx)
export function toBody(p, b) {
  const x = p[0] - b.sx, y = p[1] - b.sy, z = p[2] - b.h;
  const cy = Math.cos(b.yaw), sy = Math.sin(b.yaw), cp = Math.cos(b.pitch), sp = Math.sin(b.pitch), cr = Math.cos(b.roll), sr = Math.sin(b.roll);
  const x1 = cy * x + sy * y, y1 = -sy * x + cy * y;          // undo yaw
  const x2 = cp * x1 - sp * z, z2 = sp * x1 + cp * z;          // undo pitch
  return [x2, cr * y1 + sr * z2, -sr * y1 + cr * z2];          // undo roll
}

// servo degrees, clamped to 0-180; out.clipped is true when a servo would need to go further
export function servoAngles(qs, cal) {
  const out = []; out.clipped = false;
  qs.forEach((q, leg) => q.forEach((a, j) => {
    const i = leg * 3 + j;
    const v = 90 + (cal.invert[i] ? -1 : 1) * a / DEG + cal.trim[i];
    if (v < -0.5 || v > 180.5) out.clipped = true;
    out.push(Math.round(Math.min(180, Math.max(0, v))));
  }));
  return out;
}

// True when every leg can hold the feet at this spread for body heights lo..hi with each joint
// at most `margin` degrees short of the servo's 0-180 range.
export function poseFits(d, spread, lo, hi, margin = 10) {
  const mounts = legMounts(d), home = homeFeet(d, spread);
  for (let h = lo; h <= hi + 1e-9; h += Math.max(1, (hi - lo) / 8)) {
    for (let i = 0; i < 6; i++) {
      const r = legIK(d, mounts[i], [home[i][0], home[i][1], -h]);
      if (!r.ok || r.q.some(a => Math.abs(a / DEG) > 90 - margin)) return false;
    }
  }
  return true;
}

// The narrowest spread (in %) that lets the body sit down and stand back up without stepping.
export function sitSpread(d, sitH, standH, from = 30) {
  for (let s = from; s <= 90; s++) if (poseFits(d, s, sitH, standH, 15)) return s;
  return 90;
}

// Tripod gait. step(dt, cmd, home, cfg) moves the feet; feet() returns them in the ground frame.
// cmd = {vx, vy, wz} in mm/s and rad/s, cfg = {period, lift}. Feet on the ground move exactly
// opposite to the body so they stay planted; feet in the air swing to the next foothold.
export function makeGait() {
  const off = Array.from({ length: 6 }, () => [0, 0]);
  const from = Array.from({ length: 6 }, () => [0, 0]);
  const z = new Array(6).fill(0);
  const pose = { x: 0, y: 0, yaw: 0 };
  let t = 0, active = false;

  function step(dt, cmd, home, cfg) {
    const want = Math.hypot(cmd.vx, cmd.vy) > 1 || Math.abs(cmd.wz) > 0.01;
    if (!active) {
      if (!want && off.every(o => Math.hypot(o[0], o[1]) < 1)) return false;
      active = true; off.forEach((o, i) => { from[i] = [...o]; });
    }
    const prev = t;
    t = (t + dt / cfg.period) % 1;
    const half = cfg.period / 2;
    for (let i = 0; i < 6; i++) {
      const h = home[i], ux = cmd.vx - cmd.wz * h[1], uy = cmd.vy + cmd.wz * h[0];
      const lp = (t - TRIPOD[i] * 0.5 + 1) % 1, lp0 = (prev - TRIPOD[i] * 0.5 + 1) % 1;
      if (lp < 0.5) {
        if (lp0 >= 0.5 || lp0 > lp) from[i] = [...off[i]];          // this foot just lifted
        const p = lp / 0.5, e = p * p * (3 - 2 * p), tx = ux * half / 2, ty = uy * half / 2;
        off[i] = [from[i][0] + (tx - from[i][0]) * e, from[i][1] + (ty - from[i][1]) * e];
        z[i] = cfg.lift * Math.sin(Math.PI * p);
      } else {
        // a planted foot moves against the body: -(v + w x p) at its current position p
        const px = h[0] + off[i][0], py = h[1] + off[i][1];
        off[i][0] -= (cmd.vx - cmd.wz * py) * dt; off[i][1] -= (cmd.vy + cmd.wz * px) * dt; z[i] = 0;
      }
    }
    pose.yaw += cmd.wz * dt;
    pose.x += (cmd.vx * Math.cos(pose.yaw) - cmd.vy * Math.sin(pose.yaw)) * dt;
    pose.y += (cmd.vx * Math.sin(pose.yaw) + cmd.vy * Math.cos(pose.yaw)) * dt;
    // rest at the next half-cycle boundary once nothing is asked and every foot is home
    const crossed = Math.floor(prev * 2) !== Math.floor(t * 2) || t < prev;
    if (crossed && !want && off.every(o => Math.hypot(o[0], o[1]) < 1)) {
      active = false; t = Math.round(t * 2) / 2 % 1; z.fill(0); off.forEach(o => { o[0] = 0; o[1] = 0; });
    }
    return true;
  }
  // the rest positions moved (new spread or leg sizes): keep the feet where they are and let the
  // next steps carry them to the new rest positions
  function rebase(oldHome, newHome) {
    for (let i = 0; i < 6; i++) for (const k of [0, 1]) { const dk = oldHome[i][k] - newHome[i][k]; off[i][k] += dk; from[i][k] += dk; }
  }
  const feet = home => home.map((h, i) => [h[0] + off[i][0], h[1] + off[i][1], z[i]]);
  return { step, feet, rebase, pose, get active() { return active; } };
}
