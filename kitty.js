// Shared bits for the twin pages: the animated corner mascot, number parsing that accepts Arabic
// digits, background patterns and the 3D table items. Two looks: "kitty" (pink, Hello-Kitty style)
// and "libra" (black and gold night goat with ram horns and bell eyes); <html data-theme> picks one.

export const theme = document.documentElement.dataset.theme === 'libra' ? 'libra' : 'kitty';

const HEART = 'M50 86C20 64 2 46 2 26C2 12 13 2 27 2C37 2 45 8 50 16C55 8 63 2 73 2C87 2 98 12 98 26C98 46 80 64 50 86Z';

const KITTY_SVG = `
<svg viewBox="-14 -40 148 142" aria-hidden="true">
  <ellipse cx="60" cy="97" rx="36" ry="4" fill="#000" opacity=".35"/>
  <g class="sk-hearts">
    <g class="sk-heart"><path d="${HEART}" transform="translate(6 -8) scale(.17)"/></g>
    <g class="sk-heart"><path d="${HEART}" transform="translate(51 -20) scale(.2)"/></g>
    <g class="sk-heart"><path d="${HEART}" transform="translate(98 -6) scale(.15)"/></g>
  </g>
  <g class="sk-zzz"><text class="sk-z" x="96" y="6">z</text><text class="sk-z" x="108" y="-12">z</text><text class="sk-z" x="120" y="-30">z</text></g>
  <g class="sk-body"><g class="sk-head">
    <path class="sk-ear-l sk-line sk-fur" d="M18 46Q12 12 22 8Q31 6 48 26Z"/>
    <path class="sk-ear-r sk-line sk-fur" d="M102 46Q108 12 98 8Q89 6 72 26Z"/>
    <ellipse class="sk-line sk-fur" cx="60" cy="58" rx="50" ry="36"/>
    <g class="sk-wl sk-line" fill="none" style="stroke-width:3"><path d="M2 55L24 60M0 66L23 67M3 78L24 73"/></g>
    <g class="sk-wr sk-line" fill="none" style="stroke-width:3"><path d="M118 55L96 60M120 66L97 67M117 78L96 73"/></g>
    <ellipse class="sk-blush" cx="29" cy="72" rx="7" ry="4"/>
    <ellipse class="sk-blush" cx="91" cy="72" rx="7" ry="4"/>
    <g class="sk-look">
      <g class="sk-open"><ellipse class="sk-ink" cx="40" cy="60" rx="4.5" ry="6.5"/><ellipse class="sk-ink" cx="80" cy="60" rx="4.5" ry="6.5"/></g>
      <path class="sk-happy" d="M33 63Q40 53 47 63M73 63Q80 53 87 63"/>
      <path class="sk-closed" d="M33 59Q40 66 47 59M73 59Q80 66 87 59"/>
    </g>
    <ellipse class="sk-line" cx="60" cy="69" rx="5.5" ry="4" style="fill:#f5c542;stroke-width:2"/>
    <g class="sk-bow sk-line">
      <ellipse cx="77" cy="18" rx="12" ry="9" transform="rotate(-25 77 18)"/>
      <ellipse cx="101" cy="22" rx="12" ry="9" transform="rotate(25 101 22)"/>
      <circle cx="89" cy="20" r="6"/>
    </g>
    <path class="sk-tear" d="M36 68Q32 76 35 80Q39 83 41 78Q42 74 36 68Z"/>
  </g></g>
</svg>`;

const HORN_L = 'M47 24C33 -2 2 4 4 32C6 50 28 52 30 38C31 29 20 27 17 35';
const HORN_R = 'M73 24C87 -2 118 4 116 32C114 50 92 52 90 38C89 29 100 27 103 35';
const FLECK = 'M0 -7L5 0L0 7L-5 0Z';
const bellEye = (x, y, side) => `<g class="lb-bell lb-bell-${side}"><circle cx="${x}" cy="${y}" r="10" fill="url(#lb-orb)" stroke="#120e0a" stroke-width="2"/><rect x="${x - 7}" y="${y - 2.5}" width="14" height="5" rx="2.5" fill="#120e0a"/></g>`;
const LIBRA_SVG = `
<svg viewBox="-14 -40 148 142" aria-hidden="true">
  <ellipse cx="60" cy="99" rx="34" ry="4" fill="#000" opacity=".4"/>
  <g class="sk-hearts">
    <g class="sk-heart"><path d="${FLECK}" transform="translate(14 -10) scale(1.1)" fill="#f2b929"/></g>
    <g class="sk-heart"><path d="${FLECK}" transform="translate(60 -24) scale(1.4)" fill="#ffe38a"/></g>
    <g class="sk-heart"><path d="${FLECK}" transform="translate(104 -8)" fill="#f2b929"/></g>
  </g>
  <g class="sk-zzz"><text class="sk-z" x="96" y="6">z</text><text class="sk-z" x="108" y="-12">z</text><text class="sk-z" x="120" y="-30">z</text></g>
  <g class="sk-body"><g class="sk-head">
    <g fill="none" stroke-linecap="round">
      <path d="${HORN_L}" stroke="#120e0a" stroke-width="12"/><path d="${HORN_L}" stroke="#bfa86c" stroke-width="8"/>
      <path d="${HORN_R}" stroke="#120e0a" stroke-width="12"/><path d="${HORN_R}" stroke="#bfa86c" stroke-width="8"/>
    </g>
    ${bellEye(17, 34, 'l')}${bellEye(103, 34, 'r')}
    <g fill="#1f1a15" stroke="#0b0907" stroke-width="2" stroke-linejoin="round">
      <path class="sk-ear-l" d="M40 34L24 39L39 45Z"/><path class="sk-ear-r" d="M80 34L96 39L81 45Z"/>
      <path d="M60 16C75 16 84 27 83 42C82 57 73 72 66 86L60 96L54 86C47 72 38 57 37 42C36 27 45 16 60 16Z"/>
      <g class="sk-wl"><path d="M38 46L28 50L36 52L27 58L37 58" stroke-width="1.5"/></g>
      <g class="sk-wr"><path d="M82 46L92 50L84 52L93 58L83 58" stroke-width="1.5"/></g>
      <path d="M55 92L60 104L65 92Z" stroke-width="1.5"/>
    </g>
    <path d="M60 25C69 25 73 34 71.5 47C70 61 65.5 74 60 82C54.5 74 50 61 48.5 47C47 34 51 25 60 25Z" fill="#ebe1cd" stroke="#0b0907" stroke-width="1.5"/>
    <g class="sk-look">
      <g class="sk-open"><path class="lb-slit" d="M53 40H67M52 47H68M54 54H66" fill="none" stroke="#1f1a15" stroke-width="2.4" stroke-linecap="round"/></g>
      <path class="sk-happy" d="M53 45Q60 38 67 45M53 53Q60 46 67 53"/>
      <path class="sk-closed" d="M53 47H67"/>
    </g>
    <path d="M57 77h.01M63 77h.01" stroke="#1f1a15" stroke-width="2.6" stroke-linecap="round"/>
    <g class="sk-blush"><circle cx="42" cy="56" r="7" opacity=".4"/><circle cx="78" cy="56" r="7" opacity=".4"/></g>
    <g stroke="#0b0907" stroke-width="1">
      <ellipse class="lb-eye" cx="42" cy="56" rx="3.4" ry="2.3" fill="#f2b929"/><ellipse class="lb-eye" cx="78" cy="56" rx="3.4" ry="2.3" fill="#f2b929"/>
      <ellipse class="lb-eye" cx="45" cy="68" rx="2.7" ry="1.9" fill="#f2b929"/><ellipse class="lb-eye" cx="75" cy="68" rx="2.7" ry="1.9" fill="#f2b929"/>
    </g>
    <g class="sk-tear"><path d="M71 -1Q75 3 71 7M81 -1Q77 3 81 7M72 -2Q76 2 80 -2M72 8Q76 4 80 8" fill="none" stroke="#ff5a36" stroke-width="2.6" stroke-linecap="round"/></g>
  </g></g>
</svg>`;

const LABELS = theme === 'libra' ? {
  idle: 'Libra is calm', busy: 'Libra is watching the robot move', sad: "Libra is furious: the robot can't reach that",
  happy: 'Libra is pleased', sleep: 'Libra is asleep',
} : {
  idle: 'Kitty is ready', busy: 'Kitty is watching the robot move', sad: "Kitty is sad: the robot can't reach that",
  happy: 'Kitty is happy', sleep: 'Kitty is asleep',
};

// Mounts the corner kitty in `el`. set('idle'|'busy'|'sad') is the lasting mood, cheer() a short
// happy jump with hearts. She falls asleep after 30 s without any input and wakes on the next one.
export function statusKitty(el) {
  el.innerHTML = theme === 'libra' ? LIBRA_SVG : KITTY_SVG;
  el.setAttribute('role', 'img');
  let mood = 'idle', happy = 0, nap = 0;
  const render = () => {
    const s = happy ? 'happy' : mood;
    el.className = 'status-kitty ' + s;
    el.setAttribute('aria-label', LABELS[s]);
  };
  const restartNap = () => {
    clearTimeout(nap);
    nap = setTimeout(() => { if (mood === 'idle' && !happy) { mood = 'sleep'; render(); } }, 30000);
  };
  const wake = () => { if (mood === 'sleep') { mood = 'idle'; render(); } restartNap(); };
  for (const e of ['pointerdown', 'keydown', 'wheel']) addEventListener(e, wake, { passive: true });
  function cheer() {
    clearTimeout(happy);
    el.className = 'status-kitty'; void el.getBoundingClientRect(); // restart the jump
    happy = setTimeout(() => { happy = 0; render(); }, 1700);
    render();
  }
  el.addEventListener('click', cheer);
  function set(s) {
    if (s === mood || (s === 'idle' && mood === 'sleep')) return;
    mood = s; render(); restartNap();
  }
  render(); restartNap();
  return { set, cheer };
}

// Parses what people type, including Arabic-Indic digits and the Arabic decimal mark.
export function toNum(s) {
  const t = String(s).trim()
    .replace(/[٠-٩]/g, d => d.charCodeAt(0) - 0x660)
    .replace(/[۰-۹]/g, d => d.charCodeAt(0) - 0x6f0)
    .replace(/[٫,]/g, '.').replace(/[−–]/g, '-');
  const v = parseFloat(t);
  return Number.isFinite(v) ? v : NaN;
}

// faint kitty outlines (or horns and eyes) behind the control rail
export function railPattern(el, color) {
  const k = theme === 'libra'
    ? `<g fill='none' stroke='${color}' stroke-width='3' stroke-linejoin='round' stroke-linecap='round' opacity='0.08'><path d='${HORN_L}M${HORN_R.slice(1)}'/><path d='M38 72Q60 50 82 72Q60 94 38 72Z'/><path d='M50 72H70'/></g>`
    : `<g fill='none' stroke='${color}' stroke-width='3' stroke-linejoin='round' stroke-linecap='round' opacity='0.09'><path d='M18 46Q12 12 22 8Q31 6 48 26M102 46Q108 12 98 8Q89 6 72 26'/><ellipse cx='60' cy='58' rx='50' ry='36'/><ellipse cx='89' cy='20' rx='16' ry='8'/></g>`;
  const tile = `<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150' viewBox='0 0 300 300'><g transform='translate(20 20)'>${k}</g><g transform='translate(170 170) scale(.8)'>${k}</g></svg>`;
  el.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent(tile)}")`;
}

// repeating texture for floors and tables: kitty faces, or goat eyes and gold flecks
export function kittyTile(THREE, bg, line, rx, ry) {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = line; g.lineWidth = 4; g.lineJoin = g.lineCap = 'round';
  if (theme === 'libra') {
    g.fillStyle = line;
    g.save(); g.translate(24, 30); g.stroke(new Path2D('M0 34Q40 0 80 34Q40 68 0 34Z')); g.beginPath(); g.roundRect(24, 30, 32, 9, 4.5); g.fill(); g.restore();
    g.save(); g.translate(180, 180); g.fill(new Path2D('M0 -22Q3 -3 22 0Q3 3 0 22Q-3 3 -22 0Q-3 -3 0 -22Z')); g.restore();   // a gold fleck
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
    return t;
  }
  g.translate(68, 78);
  g.stroke(new Path2D('M18 46Q12 12 22 8Q31 6 48 26M102 46Q108 12 98 8Q89 6 72 26'));
  g.beginPath(); g.ellipse(60, 58, 50, 36, 0, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.ellipse(77, 18, 12, 9, -0.44, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.ellipse(101, 22, 12, 9, 0.44, 0, Math.PI * 2); g.stroke();
  g.fillStyle = line; for (const x of [40, 80]) { g.beginPath(); g.ellipse(x, 60, 4.5, 6.5, 0, 0, Math.PI * 2); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

// A table item `w` wide (any unit), sitting on z = 0 and facing +X in a Z-up frame: a kitty head
// with a bow, or in the Libra look a golden bell eye. group.userData.h is its height.
export function kittyHead(THREE, w, bow) {
  if (theme === 'libra') return bellItem(THREE, w, bow);
  const g = new THREE.Group();
  const white = new THREE.MeshStandardMaterial({ color: 0xfffafc, roughness: 0.5 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x1a0c12, roughness: 0.4 });
  const nose = new THREE.MeshStandardMaterial({ color: 0xf5c542, roughness: 0.5 });
  const bowM = new THREE.MeshStandardMaterial({ color: bow, roughness: 0.45 });
  const dx = 0.8 * w, h = 0.82 * w, zc = h / 2;
  const part = (geo, mat, [x, y, z], [sx, sy, sz] = [1, 1, 1], rx = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.scale.set(sx, sy, sz); m.rotation.x = rx; g.add(m); return m; };
  const ball = new THREE.SphereGeometry(1, 32, 20);
  part(ball, white, [0, 0, zc], [dx / 2, w / 2, h / 2]);
  for (const s of [1, -1]) {
    part(new THREE.ConeGeometry(0.19 * w, 0.36 * w, 20), white, [0, s * 0.3 * w, zc + 0.5 * h], [1, 1, 1], Math.PI / 2 - s * 0.45);
    part(ball, dark, [dx / 2 * 0.93, s * 0.17 * w, zc + 0.02 * h], [0.02 * w, 0.045 * w, 0.065 * w]);
    for (const k of [-1, 0, 1]) part(new THREE.CylinderGeometry(0.006 * w, 0.006 * w, 0.26 * w, 6), dark, [dx / 2 * 0.72, s * 0.5 * w, zc - 0.08 * h + k * 0.07 * h], [1, 1, 1], s * k * 0.25);
  }
  part(ball, nose, [dx / 2 * 0.97, 0, zc - 0.12 * h], [0.02 * w, 0.055 * w, 0.04 * w]);
  for (const s of [1, -1]) part(ball, bowM, [0.05 * w, 0.28 * w + s * 0.12 * w, zc + 0.58 * h], [0.06 * w, 0.13 * w, 0.09 * w], -s * 0.45);
  part(ball, bowM, [0.06 * w, 0.28 * w, zc + 0.58 * h], [0.055 * w, 0.055 * w, 0.055 * w]);
  g.userData.h = h;
  return g;
}

function bellItem(THREE, w, color) {
  const g = new THREE.Group(), r = w / 2;
  const gold = new THREE.MeshStandardMaterial({ color, metalness: 0.6, roughness: 0.32 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x120e0a, roughness: 0.5 });
  const ball = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 20), gold); ball.position.z = r; g.add(ball);
  const pupil = new THREE.Mesh(new THREE.CapsuleGeometry(r * 0.2, r * 0.85, 6, 12), dark);   // goat pupil across the front
  pupil.scale.x = 0.45; pupil.position.set(r * 0.9, 0, r); g.add(pupil);
  const loop = new THREE.Mesh(new THREE.TorusGeometry(r * 0.26, r * 0.07, 8, 24), gold);
  loop.rotation.y = Math.PI / 2; loop.position.z = 2 * r + r * 0.18; g.add(loop);
  g.userData.h = 2 * r;
  return g;
}

// The arm page's target marker: a small heart, or a golden bell eye in the Libra look.
// `mat` is the material whose colour shows whether the target can be reached.
export function markerShape(THREE, mat) {
  if (theme === 'libra') {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.SphereGeometry(0.011, 24, 16), mat));
    const pupil = new THREE.Mesh(new THREE.CapsuleGeometry(0.0024, 0.009, 4, 8), new THREE.MeshStandardMaterial({ color: 0x120e0a }));
    pupil.scale.x = 0.5; pupil.position.x = 0.0102; g.add(pupil);
    return g;
  }
  const s = new THREE.Shape();
  s.moveTo(0, -0.43); s.bezierCurveTo(-0.3, -0.21, -0.48, -0.03, -0.48, 0.17); s.bezierCurveTo(-0.48, 0.31, -0.37, 0.41, -0.23, 0.41);
  s.bezierCurveTo(-0.13, 0.41, -0.05, 0.35, 0, 0.27); s.bezierCurveTo(0.05, 0.35, 0.13, 0.41, 0.23, 0.41);
  s.bezierCurveTo(0.37, 0.41, 0.48, 0.31, 0.48, 0.17); s.bezierCurveTo(0.48, -0.03, 0.3, -0.21, 0, -0.43);
  const geo = new THREE.ExtrudeGeometry(s, { depth: 0.3, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.06, bevelSegments: 3 });
  geo.translate(0, 0, -0.15); geo.scale(0.022, 0.022, 0.022);
  const hm = new THREE.Mesh(geo, mat); hm.rotation.set(Math.PI / 2, 0, Math.PI / 2, 'ZYX');
  return hm;
}

// Ram horns for the hexapod's dome in the Libra look: two spirals curling outward with a bell eye
// in each curl. `at` is the point between the horns on top of the dome (millimetres, Z up).
export function ramHorns(THREE, at, size = 1) {
  const g = new THREE.Group();
  const horn = new THREE.MeshStandardMaterial({ color: 0xbfa86c, roughness: 0.55 });
  const gold = new THREE.MeshStandardMaterial({ color: 0xf2b929, metalness: 0.6, roughness: 0.3 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x120e0a, roughness: 0.5 });
  for (const s of [1, -1]) {
    // a spiral in the side-to-side plane: up from the dome, over and out, down and back in
    const c = [at[0] - 8 * size, at[1] + s * 40 * size, at[2] + 26 * size], pts = [new THREE.Vector3(at[0], at[1] + s * 12 * size, at[2] - 2)];
    for (let i = 0; i <= 40; i++) {
      const t = i / 40 * 2.1 * Math.PI, r = 30 * size * (1 - t / (2.9 * Math.PI));
      pts.push(new THREE.Vector3(c[0] - t * 3 * size, c[1] - s * Math.cos(t) * r, c[2] + Math.sin(t) * r));
    }
    // the horn tapers: thick rings near the root, thinner toward the tip
    const curve = new THREE.CatmullRomCurve3(pts), tube = new THREE.TubeGeometry(curve, 120, 1, 12), p = tube.attributes.position, n = tube.attributes.normal;
    for (let k = 0; k < p.count; k++) {
      const u = Math.floor(k / 13) / 120, rad = (8.5 - 5 * u) * size, at3 = curve.getPointAt(u);
      p.setXYZ(k, at3.x + n.getX(k) * rad, at3.y + n.getY(k) * rad, at3.z + n.getZ(k) * rad);
    }
    tube.computeVertexNormals();
    g.add(new THREE.Mesh(tube, horn));
    const eye = new THREE.Mesh(new THREE.SphereGeometry(9 * size, 20, 14), gold); eye.position.set(c[0] - 4 * size, c[1], c[2]); g.add(eye);
    const pupil = new THREE.Mesh(new THREE.CapsuleGeometry(2 * size, 8 * size, 4, 8), dark);
    pupil.scale.x = 0.5; pupil.position.set(c[0] - 4 * size + 8.6 * size, c[1], c[2]); g.add(pupil);
  }
  return g;
}
