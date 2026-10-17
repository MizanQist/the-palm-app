// Pan/zoom for the design board: drag, wheel, Ctrl+wheel / trackpad pinch, touch pinch, buttons, keys.
// The view is kept in sessionStorage so closing a screen returns to the same spot.
const vp = document.getElementById('vp');
const stage = document.getElementById('stage');
const pct = document.getElementById('pct');
const KEY = 'palm-board-view';
const MIN = 0.05, MAX = 3;
let s = 1, tx = 0, ty = 0;

const clamp = (v) => Math.min(MAX, Math.max(MIN, v));
function apply() {
  stage.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
  pct.value = Math.round(s * 100) + '%';
  try { sessionStorage.setItem(KEY, JSON.stringify({ s, tx, ty })); } catch (e) { /* private mode: view just isn't remembered */ }
}
function zoomAt(factor, cx, cy) {
  const ns = clamp(s * factor);
  tx = cx - (cx - tx) * ns / s;
  ty = cy - (cy - ty) * ns / s;
  s = ns;
  apply();
}
function fit() {
  const w = stage.offsetWidth, h = stage.offsetHeight;
  s = clamp(Math.min((innerWidth - 32) / w, (innerHeight - 120) / h));
  tx = (innerWidth - w * s) / 2;
  ty = Math.max(96, (innerHeight - h * s) / 2);
  apply();
}
const centre = () => [innerWidth / 2, innerHeight / 2];

vp.addEventListener('wheel', (e) => {
  e.preventDefault();
  if (e.ctrlKey) zoomAt(Math.exp(-Math.max(-50, Math.min(50, e.deltaY)) * 0.01), e.clientX, e.clientY);
  else { tx -= e.deltaX; ty -= e.deltaY; apply(); }
}, { passive: false });

// Safari trackpad pinch arrives as gesture events, not ctrl+wheel.
let gestureStart = 1;
vp.addEventListener('gesturestart', (e) => { e.preventDefault(); gestureStart = s; });
vp.addEventListener('gesturechange', (e) => { e.preventDefault(); zoomAt(gestureStart * e.scale / s, e.clientX, e.clientY); });

// Pointers: one finger/mouse pans, two fingers pinch. A press that barely moves opens the screen under it.
const pts = new Map();
let downAt = null, moved = 0, pinch = null;
vp.addEventListener('pointerdown', (e) => {
  vp.setPointerCapture(e.pointerId);
  pts.set(e.pointerId, [e.clientX, e.clientY]);
  if (pts.size === 1) { downAt = e.target.closest('.screen'); moved = 0; vp.classList.add('drag'); }
  if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), m: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2] }; }
});
vp.addEventListener('pointermove', (e) => {
  const prev = pts.get(e.pointerId);
  if (!prev) return;
  pts.set(e.pointerId, [e.clientX, e.clientY]);
  if (pts.size === 1) {
    tx += e.clientX - prev[0]; ty += e.clientY - prev[1];
    moved += Math.abs(e.clientX - prev[0]) + Math.abs(e.clientY - prev[1]);
    apply();
  } else if (pts.size === 2 && pinch) {
    const [a, b] = [...pts.values()];
    const d = Math.hypot(a[0] - b[0], a[1] - b[1]), m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    tx += m[0] - pinch.m[0]; ty += m[1] - pinch.m[1];
    zoomAt(d / pinch.d, m[0], m[1]);
    pinch = { d, m }; moved = Infinity;
  }
});
function release(e) {
  pts.delete(e.pointerId);
  if (pts.size < 2) pinch = null;
  if (pts.size) return;
  vp.classList.remove('drag');
  if (e.type === 'pointerup' && downAt && moved < 6) location.href = downAt.href;
  downAt = null;
}
vp.addEventListener('pointerup', release);
vp.addEventListener('pointercancel', release);
// Mouse clicks are handled on pointerup above; keyboard Enter still follows the link normally.
vp.addEventListener('click', (e) => { if (e.detail > 0) e.preventDefault(); });

document.querySelector('.zoom').addEventListener('click', (e) => {
  const z = e.target.closest('button')?.dataset.zoom;
  if (z === 'in') zoomAt(1.25, ...centre());
  if (z === 'out') zoomAt(0.8, ...centre());
  if (z === 'fit') fit();
});
addEventListener('keydown', (e) => {
  if (e.target.closest('input, textarea')) return;
  const step = 80;
  const keys = {
    '+': () => zoomAt(1.25, ...centre()), '=': () => zoomAt(1.25, ...centre()),
    '-': () => zoomAt(0.8, ...centre()), '0': fit,
    ArrowLeft: () => { tx += step; apply(); }, ArrowRight: () => { tx -= step; apply(); },
    ArrowUp: () => { ty += step; apply(); }, ArrowDown: () => { ty -= step; apply(); },
  };
  if (keys[e.key] && !e.metaKey && !e.ctrlKey) { e.preventDefault(); keys[e.key](); }
});

let saved = null;
try { saved = JSON.parse(sessionStorage.getItem(KEY)); } catch (e) { /* ignore */ }
if (saved && saved.s) { ({ s, tx, ty } = saved); apply(); } else fit();
