// The Libra look's world behind the 3D view: a swirling burning sky, a far-off burnt tree with
// yellow fire climbing it, a fireball bursting from its crown and throwing yellow sparks, and a
// ring of broken, burning ruins on the horizon with embers drifting up. Everything is painted in
// code. It lives in its own scene, seen by a camera at its centre that turns with the main camera
// but tips up and down less, so the horizon stays just above the floor while the main camera looks
// down at the robot.

const FIRE_ELEV = 0.12;   // how high the fireball hangs above the horizon (radians, about 7°)

function rng(seed) { return () => { seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }

const SKY_VERT = `varying vec3 vDir; void main() { vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const SKY_FRAG = `
precision highp float;
varying vec3 vDir; uniform float time; uniform vec3 sunDir;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) { vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + 11.7; a *= 0.5; } return v; }
void main() {
  vec3 d = normalize(vDir); float e = d.y;
  vec2 uv = vec2(atan(d.z, d.x) * 1.7, e * 3.2);
  vec2 q = vec2(fbm(uv + time * 0.018), fbm(uv + vec2(5.2, 1.3) - time * 0.014));
  vec2 r = vec2(fbm(uv + 3.0 * q + vec2(1.7, 9.2) + time * 0.01), fbm(uv + 3.0 * q + vec2(8.3, 2.8)));
  float n = fbm(uv + 3.4 * r);
  vec3 col = mix(vec3(0.06, 0.02, 0.09), vec3(0.34, 0.04, 0.10), smoothstep(0.25, 0.6, n));   // night purple to crimson
  col = mix(col, vec3(0.95, 0.38, 0.06), smoothstep(0.55, 0.82, n) * 0.75);                 // orange streaks
  col = mix(col, vec3(1.0, 0.82, 0.32), smoothstep(0.76, 0.95, n) * 0.55);                  // gold highlights
  float s = max(dot(d, sunDir), 0.0);
  col += vec3(1.0, 0.72, 0.24) * pow(s, 40.0) * 0.6 + vec3(1.0, 0.4, 0.08) * pow(s, 9.0) * 0.22;   // light around the fireball
  col = mix(col, vec3(0.88, 0.33, 0.06), smoothstep(0.16, 0.0, e) * 0.75);                 // the glow of the burning city on the horizon
  if (e < 0.0) col = mix(vec3(0.05, 0.035, 0.03), vec3(0.3, 0.09, 0.035), smoothstep(-0.12, 0.0, e));   // charred ground
  gl_FragColor = vec4(col * 0.85, 1.0);
}`;

// a dead tree with a thick twisted trunk and bare, broken branches spreading from its crown, and
// the yellow fire running up the trunk and licking along the branches. The fireball (a sprite)
// bursts out of the crown, CROWN of the way up.
const CROWN = 0.6;
function paintTree() {
  const S = 1024, [c, g] = canvas(S, S), rnd = rng(7), cy = S * (1 - CROWN), L = [], R = [];
  for (let i = 0; i <= 30; i++) {               // the trunk, flared at the roots
    const t = i / 30, y = S - t * (S - cy), lean = Math.sin(t * 3.1) * 22;
    const half = 32 + 62 * (1 - t) ** 2 + Math.sin(t * 29) * 4;
    L.push([S / 2 + lean - half, y]); R.push([S / 2 + lean + half, y]);
  }
  const top = [(L[30][0] + R[30][0]) / 2, cy];
  g.fillStyle = g.strokeStyle = '#0b0705'; g.lineCap = 'round';
  g.beginPath(); g.moveTo(S / 2 - 160, S); L.forEach(p => g.lineTo(...p)); [...R].reverse().forEach(p => g.lineTo(...p)); g.lineTo(S / 2 + 160, S); g.closePath(); g.fill();
  const tips = [];
  const limb = (x, y, ang, len, w, depth) => {
    const bend = (rnd() - 0.5) * 0.7, x2 = x + Math.sin(ang) * len, y2 = y - Math.cos(ang) * len;
    g.lineWidth = w; g.beginPath(); g.moveTo(x, y);
    g.quadraticCurveTo(x + Math.sin(ang + bend) * len * 0.55, y - Math.cos(ang + bend) * len * 0.55, x2, y2); g.stroke();
    if (depth === 0 || rnd() < 0.1) { tips.push([x2, y2, w]); return; }   // burnt off
    const n = rnd() < 0.3 ? 3 : 2;
    for (let i = 0; i < n; i++) limb(x2, y2, ang + (i - (n - 1) / 2) * (0.45 + rnd() * 0.35) + (rnd() - 0.5) * 0.25, len * (0.6 + rnd() * 0.14), w * 0.6, depth - 1);
  };
  for (const [ang, len] of [[-1.25, 150], [-0.8, 140], [-0.35, 120], [0.1, 110], [0.5, 130], [0.95, 145], [1.3, 150]]) limb(top[0], top[1] + 10, ang, len, 34, 4);
  for (const [t, ang, len] of [[0.45, -1.35, 120], [0.62, 1.4, 110], [0.75, -1.2, 90]]) {   // lower limbs off the trunk
    const p = (ang < 0 ? L : R)[Math.round(t * 30)]; limb(p[0], p[1], ang, len, 18, 3);
  }

  const [f, h] = canvas(S, S);
  h.globalCompositeOperation = 'lighter'; h.lineCap = h.lineJoin = 'round';
  const fire = new Path2D(); R.forEach((p, i) => { const x = (p[0] + L[i][0]) / 2 + (p[0] - L[i][0]) * 0.2 + Math.sin(i * 0.5) * 6; i ? fire.lineTo(x, p[1]) : fire.moveTo(x, p[1]); });
  for (const [w, col, blur] of [[80, 'rgba(255,80,0,.45)', 26], [30, 'rgba(255,186,30,.85)', 9], [10, 'rgba(255,250,205,.95)', 2]]) { h.filter = `blur(${blur}px)`; h.strokeStyle = col; h.lineWidth = w; h.stroke(fire); }
  const flame = (x, y, fh, a) => {
    h.fillStyle = `rgba(255,${150 + rnd() * 90 | 0},20,${a})`;
    h.beginPath(); h.moveTo(x - fh * 0.22, y); h.quadraticCurveTo(x - fh * 0.15, y - fh * 0.6, x + rnd() * 10 - 5, y - fh); h.quadraticCurveTo(x + fh * 0.15, y - fh * 0.6, x + fh * 0.22, y); h.fill();
  };
  h.filter = 'blur(3px)';
  for (let i = 0; i < 40; i++) { const p = (rnd() < 0.7 ? R : L)[Math.floor(rnd() * 31)]; flame(p[0] - 10, p[1], 24 + rnd() * 56, 0.8); }
  for (const [x, y] of tips) if (rnd() < 0.55 && Math.hypot(x - top[0], y - top[1]) < 330) flame(x, y + 6, 18 + rnd() * 36, 0.75);
  return { trunk: c, fire: f, crown: [top[0] / S, CROWN] };
}

function paintGlow(stops) {
  const [c, g] = canvas(256, 256), gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  stops.forEach(([o, col]) => gr.addColorStop(o, col)); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); return c;
}
function paintCorona() {
  const [c, g] = canvas(256, 256), rnd = rng(3);
  g.globalCompositeOperation = 'lighter'; g.translate(128, 128); g.filter = 'blur(2px)';
  for (let i = 0; i < 70; i++) {
    const a = rnd() * Math.PI * 2, len = 52 + rnd() * 40;
    g.strokeStyle = `rgba(255,${150 + rnd() * 90 | 0},30,${0.25 + rnd() * 0.4})`; g.lineWidth = 3 + rnd() * 7;
    g.beginPath(); g.moveTo(Math.cos(a) * 34, Math.sin(a) * 34); g.quadraticCurveTo(Math.cos(a + 0.3) * len * 0.75, Math.sin(a + 0.3) * len * 0.75, Math.cos(a + 0.5) * len, Math.sin(a + 0.5) * len); g.stroke();
  }
  return c;
}
function paintFlame() {
  const [c, g] = canvas(64, 128), gr = g.createLinearGradient(0, 128, 0, 0);
  gr.addColorStop(0, 'rgba(255,90,0,.9)'); gr.addColorStop(0.5, 'rgba(255,190,40,.8)'); gr.addColorStop(1, 'rgba(255,240,180,0)');
  g.filter = 'blur(3px)'; g.fillStyle = gr;
  g.beginPath(); g.moveTo(10, 124); g.quadraticCurveTo(4, 60, 32, 6); g.quadraticCurveTo(60, 60, 54, 124); g.closePath(); g.fill();
  return c;
}

// a 360° strip of broken, burnt buildings: a hazy far row, a black near row, ember windows and fires
function paintRuins() {
  const W = 4096, H = 512, [c, g] = canvas(W, H), rnd = rng(11);
  const near = g.createLinearGradient(0, 0, 0, H); near.addColorStop(0, '#070403'); near.addColorStop(0.75, '#140805'); near.addColorStop(1, '#3a1206');
  for (const [color, scale] of [['#4a1a0d', 0.8], [near, 1]]) {
    g.fillStyle = color; g.beginPath(); g.moveTo(0, H);
    let x = 0;
    while (x < W) {
      const kind = rnd(), h = H * (0.16 + rnd() * 0.36) * scale;
      if (kind < 0.22) {                       // a tower with a shattered top
        const w = 34 + rnd() * 46, th = Math.min(H * 0.92, h * (1.5 + rnd()));
        g.lineTo(x, H - h * 0.5); g.lineTo(x + 3, H - th);
        for (let k = 1; k <= 4; k++) g.lineTo(x + (w * k) / 4, H - th + rnd() * 46 * (k % 2 ? 1 : 0.3));
        g.lineTo(x + w, H - h * 0.5); x += w;
      } else if (kind < 0.36) {                // an arch with a broken span
        const w = 90 + rnd() * 80;
        g.lineTo(x, H - h); g.lineTo(x + w * 0.18, H - h); g.lineTo(x + w * 0.18, H - h * 0.35);
        g.quadraticCurveTo(x + w * 0.5, H - h * 0.95, x + w * 0.62, H - h * 0.6); g.lineTo(x + w * 0.66, H - h * 0.9);
        g.lineTo(x + w, H - h * 0.8); x += w;
      } else {                                 // a wall with crenels and missing chunks
        const w = 60 + rnd() * 170; let k = 0;
        g.lineTo(x, H - h);
        while (k < w) { const step = 10 + rnd() * 14; const drop = rnd() < 0.2 ? rnd() * h * 0.6 : 0; g.lineTo(x + k, H - h - (rnd() < 0.5 ? 9 : 0) + drop); k += step; }
        g.lineTo(x + w, H - h * (0.3 + rnd() * 0.5)); x += w;
      }
    }
    g.lineTo(W, H); g.closePath(); g.fill();
  }
  g.globalCompositeOperation = 'source-atop';  // light only the buildings, never the sky between them
  for (let i = 0; i < 90; i++) {               // embers glowing at the foot of the ruins
    const x = rnd() * W, y = H - rnd() * H * 0.2, r = 18 + rnd() * 60, gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(255,${110 + rnd() * 80 | 0},20,.55)`); gr.addColorStop(1, 'rgba(255,60,0,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  for (let i = 0; i < 140; i++) {              // burning windows
    g.fillStyle = `rgba(255,${130 + rnd() * 90 | 0},30,${0.5 + rnd() * 0.4})`;
    g.fillRect(rnd() * W, H - H * (0.08 + rnd() * 0.3), 3 + rnd() * 5, 6 + rnd() * 10);
  }
  return c;
}

// horizon: where the far horizon sits on screen at the start (0 top, 1 bottom), placed just above
// the main scene's floor or table edge. side: where the fireball sits across the screen (-1 left
// edge, 1 right edge), in open sky beside the robot.
export function libraBackdrop(THREE, { horizon = 0.34, side = -0.7 } = {}) {
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(40, 1, 0.5, 400);
  const tex = (c, srgb = true) => { const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; };
  const add = (m, o = {}) => new THREE.SpriteMaterial({ map: tex(m), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, ...o });

  const sky = new THREE.ShaderMaterial({ vertexShader: SKY_VERT, fragmentShader: SKY_FRAG, side: THREE.BackSide, depthWrite: false,
    uniforms: { time: { value: 0 }, sunDir: { value: new THREE.Vector3(0, 0.17, -1).normalize() } } });
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(150, 64, 32), sky));

  const ruins = tex(paintRuins()); ruins.wrapS = THREE.RepeatWrapping; ruins.repeat.x = 3;
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(90, 90, 20, 160, 1, true), new THREE.MeshBasicMaterial({ map: ruins, side: THREE.BackSide, alphaTest: 0.4 }));
  ring.position.y = 4; scene.add(ring);

  // the burning tree, its fireball and the sparks, built straight ahead (-Z) and turned into place
  // on the first frame, when the screen's shape is known. The fireball sits FIRE_ELEV above the horizon.
  const blaze = new THREE.Group(); scene.add(blaze);
  const tree = paintTree(), DIST = 70, u = DIST / 120, BASE = -2.5, fireAt = new THREE.Vector3(0, DIST * Math.tan(FIRE_ELEV), -DIST);
  const TH = (fireAt.y - BASE) / tree.crown[1], TW = TH;
  const trunkAt = new THREE.Vector3(-(tree.crown[0] - 0.5) * TW, BASE + TH / 2, -DIST);
  const trunk = new THREE.Mesh(new THREE.PlaneGeometry(TW, TH), new THREE.MeshBasicMaterial({ map: tex(tree.trunk), alphaTest: 0.5 }));
  trunk.position.copy(trunkAt); blaze.add(trunk);
  const treeFire = new THREE.Mesh(new THREE.PlaneGeometry(TW, TH), new THREE.MeshBasicMaterial({ map: tex(tree.fire), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  treeFire.position.copy(trunkAt).setZ(-DIST + 0.05); blaze.add(treeFire);

  const glow = new THREE.Sprite(add(paintGlow([[0, 'rgba(255,170,40,.45)'], [0.4, 'rgba(255,90,0,.15)'], [1, 'rgba(255,40,0,0)']])));
  const corona = new THREE.Sprite(add(paintCorona())), corona2 = new THREE.Sprite(add(paintCorona()));
  const core = new THREE.Sprite(add(paintGlow([[0, 'rgba(255,250,215,1)'], [0.25, 'rgba(255,214,70,1)'], [0.45, 'rgba(255,150,10,.9)'], [0.62, 'rgba(255,90,0,.35)'], [1, 'rgba(255,40,0,0)']])));
  const GLOW = 34 * u, CORONA = 15 * u, CORE = 9 * u;
  for (const s of [glow, corona, corona2, core]) { s.position.copy(fireAt); blaze.add(s); }

  // sparks thrown from the fireball, and embers rising over the ruins
  const dot = tex(paintGlow([[0, 'rgba(255,255,220,1)'], [0.35, 'rgba(255,200,60,.9)'], [1, 'rgba(255,100,0,0)']]));
  const N = 420, sp = new Float32Array(N * 3), sc = new Float32Array(N * 3), vel = new Float32Array(N * 3), life = new Float32Array(N), age = new Float32Array(N);
  const rnd = Math.random;
  const spawn = i => {
    const z = rnd() * 2 - 1, a = rnd() * Math.PI * 2, s = Math.sqrt(1 - z * z), speed = (4 + rnd() * 11) * u, r = 2 * u;
    sp.set([fireAt.x + s * Math.cos(a) * r, fireAt.y + z * r, fireAt.z + s * Math.sin(a) * r], i * 3);
    vel.set([s * Math.cos(a) * speed, z * speed + 3 * u, s * Math.sin(a) * speed], i * 3);
    life[i] = 1 + rnd() * 2.6; age[i] = 0;
  };
  for (let i = 0; i < N; i++) { spawn(i); age[i] = rnd() * life[i]; }
  const sparkGeo = new THREE.BufferGeometry(); sparkGeo.setAttribute('position', new THREE.BufferAttribute(sp, 3)); sparkGeo.setAttribute('color', new THREE.BufferAttribute(sc, 3));
  blaze.add(new THREE.Points(sparkGeo, new THREE.PointsMaterial({ size: u, map: dot, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })));
  const M = 260, ep = new Float32Array(M * 3), ec = new Float32Array(M * 3), ev = new Float32Array(M);
  for (let i = 0; i < M; i++) { const a = rnd() * Math.PI * 2, r = 40 + rnd() * 45; ep.set([Math.cos(a) * r, -4 + rnd() * 30, Math.sin(a) * r], i * 3); ev[i] = 0.6 + rnd() * 2; }
  const emberGeo = new THREE.BufferGeometry(); emberGeo.setAttribute('position', new THREE.BufferAttribute(ep, 3)); emberGeo.setAttribute('color', new THREE.BufferAttribute(ec, 3));
  scene.add(new THREE.Points(emberGeo, new THREE.PointsMaterial({ size: 0.45, map: dot, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })));

  // fires at the foot of the ruins
  const flameMat = add(paintFlame()), flames = [];
  for (let i = 0; i < 40; i++) {
    const a = rnd() * Math.PI * 2, f = new THREE.Sprite(flameMat), r = 84 + rnd() * 4;
    f.position.set(Math.cos(a) * r, -3, Math.sin(a) * r); f.userData = { h: 2 + rnd() * 4, ph: rnd() * 10 }; scene.add(f); flames.push(f);
  }

  // the backdrop camera turns left and right with the main camera, but tips up and down only a
  // third as much, from a start that puts the horizon at `horizon` on screen
  let t = 0, placed = false, pitch0 = 0, lift0 = 0;
  const v = new THREE.Vector3();
  return {
    render(renderer, mainCam, dt) {
      mainCam.getWorldDirection(v);
      const yaw = Math.atan2(-v.x, -v.z), pitch = Math.asin(Math.max(-1, Math.min(1, v.y)));
      const half = Math.tan(THREE.MathUtils.degToRad(mainCam.fov) / 2);
      if (!placed) {
        placed = true; pitch0 = pitch; lift0 = -Math.atan((1 - 2 * horizon) * half);
        blaze.rotation.y = yaw - Math.atan(side * half * mainCam.aspect);
        sky.uniforms.sunDir.value.copy(fireAt).applyAxisAngle(new THREE.Vector3(0, 1, 0), blaze.rotation.y).normalize();
      }
      t += dt; sky.uniforms.time.value = t;
      const pulse = 1 + 0.06 * Math.sin(t * 5.3) + 0.04 * Math.sin(t * 8.9);
      core.scale.setScalar(CORE * pulse); glow.scale.setScalar(GLOW * (0.95 + 0.05 * Math.sin(t * 2.1)));
      corona.scale.setScalar(CORONA * pulse); corona.material.rotation = t * 0.3; corona2.scale.setScalar(CORONA * 1.15); corona2.material.rotation = -t * 0.21 + 1;
      for (let i = 0; i < N; i++) {
        age[i] += dt; if (age[i] > life[i]) spawn(i);
        const k = i * 3; vel[k + 1] -= 5 * u * dt;
        sp[k] += vel[k] * dt; sp[k + 1] += vel[k + 1] * dt; sp[k + 2] += vel[k + 2] * dt;
        const fade = 1 - age[i] / life[i]; sc[k] = fade; sc[k + 1] = fade * (0.55 + 0.4 * fade); sc[k + 2] = fade * fade * 0.25;
      }
      sparkGeo.attributes.position.needsUpdate = sparkGeo.attributes.color.needsUpdate = true;
      for (let i = 0; i < M; i++) {
        const k = i * 3; ep[k + 1] += ev[i] * dt; if (ep[k + 1] > 26) ep[k + 1] = -4;
        const fl = 0.55 + 0.45 * Math.sin(t * 7 + i * 1.3); ec[k] = fl; ec[k + 1] = fl * 0.45; ec[k + 2] = fl * 0.08;
      }
      emberGeo.attributes.position.needsUpdate = emberGeo.attributes.color.needsUpdate = true;
      for (const f of flames) { const { h, ph } = f.userData; f.scale.set(h * 0.5, h * (0.85 + 0.25 * Math.sin(t * 9 + ph) * Math.sin(t * 5.7 + ph)), 1); f.position.y = -3 + f.scale.y / 2; }
      cam.fov = mainCam.fov; cam.aspect = mainCam.aspect; cam.updateProjectionMatrix();
      cam.rotation.set(Math.max(-0.6, Math.min(0.4, lift0 + (pitch - pitch0) / 3)), yaw, 0, 'YXZ');
      renderer.render(scene, cam);
    },
  };
}
