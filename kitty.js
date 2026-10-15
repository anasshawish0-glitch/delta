// Shared bits for the Kitty twin pages: the animated status kitty, number parsing that accepts
// Arabic digits, the kitty patterns, and a 3D kitty head built from simple shapes.

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

const LABELS = {
  idle: 'Kitty is ready', busy: 'Kitty is watching the robot move', sad: "Kitty is sad: the robot can't reach that",
  happy: 'Kitty is happy', sleep: 'Kitty is asleep',
};

// Mounts the corner kitty in `el`. set('idle'|'busy'|'sad') is the lasting mood, cheer() a short
// happy jump with hearts. She falls asleep after 30 s without any input and wakes on the next one.
export function statusKitty(el) {
  el.innerHTML = KITTY_SVG;
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

// faint kitty outlines behind the control rail
export function railPattern(el, color) {
  const k = `<g fill='none' stroke='${color}' stroke-width='3' stroke-linejoin='round' stroke-linecap='round' opacity='0.09'><path d='M18 46Q12 12 22 8Q31 6 48 26M102 46Q108 12 98 8Q89 6 72 26'/><ellipse cx='60' cy='58' rx='50' ry='36'/><ellipse cx='89' cy='20' rx='16' ry='8'/></g>`;
  const tile = `<svg xmlns='http://www.w3.org/2000/svg' width='150' height='150' viewBox='0 0 300 300'><g transform='translate(20 20)'>${k}</g><g transform='translate(170 170) scale(.8)'>${k}</g></svg>`;
  el.style.backgroundImage = `url("data:image/svg+xml,${encodeURIComponent(tile)}")`;
}

// repeating kitty-face texture for floors and tables
export function kittyTile(THREE, bg, line, rx, ry) {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = bg; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = line; g.lineWidth = 4; g.lineJoin = g.lineCap = 'round';
  g.translate(68, 78);
  g.stroke(new Path2D('M18 46Q12 12 22 8Q31 6 48 26M102 46Q108 12 98 8Q89 6 72 26'));
  g.beginPath(); g.ellipse(60, 58, 50, 36, 0, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.ellipse(77, 18, 12, 9, -0.44, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.ellipse(101, 22, 12, 9, 0.44, 0, Math.PI * 2); g.stroke();
  g.fillStyle = line; for (const x of [40, 80]) { g.beginPath(); g.ellipse(x, 60, 4.5, 6.5, 0, 0, Math.PI * 2); g.fill(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

// A kitty head `w` wide (any unit), sitting on z = 0 and facing +X in a Z-up frame.
// Returns the group; group.userData.h is its height without the ears.
export function kittyHead(THREE, w, bow) {
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
