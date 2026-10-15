// Look switcher for the twin pages: "kitty" (pink Hello-Kitty style) or "libra" (black and gold
// night goat with ram horns and bell eyes). Runs as a plain script at the end of <body>, before
// the 3D module, so the icons and words change before anything is drawn. The <head> of each page
// already set data-theme on <html> so the colours never flash.
(function () {
  const root = document.documentElement;
  const libra = root.dataset.theme === 'libra';

  document.querySelectorAll('[data-theme-pick]').forEach(b => {
    b.setAttribute('aria-pressed', String(b.dataset.themePick === (libra ? 'libra' : 'kitty')));
    b.addEventListener('click', () => {
      try { localStorage.setItem('twin-theme', b.dataset.themePick); } catch (e) { /* private mode */ }
      const u = new URL(location.href); u.searchParams.set('theme', b.dataset.themePick); location.href = u.href;
    });
  });
  // keep the look when moving between the Arm and Hexapod pages
  document.querySelectorAll('.tabs a').forEach(a => { if (libra) a.href += (a.href.includes('?') ? '&' : '?') + 'theme=libra'; });
  if (!libra) return;

  document.title = document.title.replace('Kitty', 'Libra');
  document.querySelectorAll('[data-libra]').forEach(el => { el.textContent = el.dataset.libra; });
  document.querySelectorAll('[data-libra-label]').forEach(el => { el.setAttribute('aria-label', el.dataset.libraLabel); });
  const icon = document.querySelector('link[rel="icon"]');
  if (icon) icon.href = 'data:image/svg+xml,' + encodeURIComponent("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 90'><circle cx='50' cy='45' r='42' fill='#f2b929' stroke='#120e0a' stroke-width='4'/><rect x='16' y='36' width='68' height='18' rx='9' fill='#120e0a'/></svg>");

  const defs = document.querySelector('svg defs');
  // golden orb shading shared by every bell eye
  defs.insertAdjacentHTML('beforeend', `
    <radialGradient id="lb-orb" cx="36%" cy="30%" r="75%">
      <stop offset="0" stop-color="#fff3b8"/><stop offset=".45" stop-color="#f2b929"/><stop offset="1" stop-color="#9a6a12"/>
    </radialGradient>
    <linearGradient id="lb-horn" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d8c48a"/><stop offset="1" stop-color="#8f7a45"/>
    </linearGradient>`);

  // the goat head replaces the kitty head everywhere it is used (brand, decorations)
  const HORN_L = 'M47 24C33 -2 2 4 4 32C6 50 28 52 30 38C31 29 20 27 17 35';
  const HORN_R = 'M73 24C87 -2 118 4 116 32C114 50 92 52 90 38C89 29 100 27 103 35';
  document.getElementById('kitty').innerHTML = `
    <g stroke-linecap="round" stroke-linejoin="round">
      <path d="${HORN_L}" fill="none" stroke="#120e0a" stroke-width="12"/><path d="${HORN_L}" fill="none" stroke="url(#lb-horn)" stroke-width="8"/>
      <path d="${HORN_R}" fill="none" stroke="#120e0a" stroke-width="12"/><path d="${HORN_R}" fill="none" stroke="url(#lb-horn)" stroke-width="8"/>
      <circle cx="17" cy="34" r="10" fill="url(#lb-orb)" stroke="#120e0a" stroke-width="2"/><rect x="10" y="31.5" width="14" height="5" rx="2.5" fill="#120e0a"/>
      <circle cx="103" cy="34" r="10" fill="url(#lb-orb)" stroke="#120e0a" stroke-width="2"/><rect x="96" y="31.5" width="14" height="5" rx="2.5" fill="#120e0a"/>
      <path d="M40 34L24 39L39 45Z M80 34L96 39L81 45Z" fill="#1f1a15" stroke="#0b0907" stroke-width="2"/>
      <path d="M60 16C75 16 84 27 83 42C82 57 73 72 66 86L60 96L54 86C47 72 38 57 37 42C36 27 45 16 60 16Z" fill="#1f1a15" stroke="#0b0907" stroke-width="2"/>
      <path d="M60 25C69 25 73 34 71.5 47C70 61 65.5 74 60 82C54.5 74 50 61 48.5 47C47 34 51 25 60 25Z" fill="#ebe1cd" stroke="#0b0907" stroke-width="1.5"/>
      <path d="M53 40H67M52 47H68M54 54H66" stroke="#1f1a15" stroke-width="2.4"/>
      <g fill="#f2b929" stroke="#0b0907" stroke-width="1"><ellipse cx="42" cy="56" rx="3.2" ry="2.2"/><ellipse cx="78" cy="56" rx="3.2" ry="2.2"/><ellipse cx="45" cy="68" rx="2.6" ry="1.8"/><ellipse cx="75" cy="68" rx="2.6" ry="1.8"/></g>
    </g>`;
  // the heart (Run button, joystick knob, small decorations) becomes a golden bell eye
  document.getElementById('heart').innerHTML = `
    <circle cx="50" cy="45" r="42" fill="url(#lb-orb)" stroke="#120e0a" stroke-width="3"/>
    <rect x="15" y="34" width="70" height="22" rx="11" fill="#120e0a"/>`;
  // the table items are bells, so their list icons are bell eyes too
  document.querySelectorAll('.obj b svg use').forEach(u => u.setAttribute('href', '#heart'));
})();
