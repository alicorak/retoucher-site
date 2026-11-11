// Docs demos: each .demo plays a small timeline written in its HTML.
//   data-in="ms" / data-out="ms"   shown from / hidden from that time
//   data-type="ms"                 its text is typed from that time
//   data-at="ms:class;ms:-class"   classes added (or removed with -) over time
//   data-path="ms:x,y;ms:@name;ms:click"  the cursor's moves (to a point or to data-pt=name) and clicks
// A demo loops while it is on screen. With reduced motion it shows one still frame.
const CHAR_MS = 38, W = 720;
const still = matchMedia('(prefers-reduced-motion: reduce)');
const events = s => (s || '').split(';').filter(Boolean).map(p => { const i = p.indexOf(':'); return [Number(p.slice(0, i)), p.slice(i + 1)]; });

function setup(demo) {
  const stage = demo.querySelector('.scene');
  const dur = Number(demo.dataset.loop || 8000);
  const items = [...stage.querySelectorAll('[data-in],[data-out],[data-type],[data-at],[data-path]')].map(el => {
    const it = { el, in: el.dataset.in ? Number(el.dataset.in) : null, out: el.dataset.out ? Number(el.dataset.out) : null };
    if (el.dataset.type) { it.type = Number(el.dataset.type); it.text = el.textContent; el.textContent = ''; }
    if (el.dataset.at) it.at = events(el.dataset.at);
    if (el.dataset.path) it.path = events(el.dataset.path);
    return it;
  });
  // "@name" in a path: the centre of the element marked data-pt="name", wherever the layout put it
  const pointAt = name => {
    const el = stage.querySelector(`[data-pt="${name}"]`);
    if (!el || !el.getClientRects().length) return null;
    const r = el.getBoundingClientRect(), s = stage.getBoundingClientRect(), k = s.width / W;
    return [(r.left - s.left + r.width / 2) / k - 3, (r.top - s.top + r.height / 2) / k - 2]; // the arrow's tip
  };
  const render = t => {
    for (const it of items) {
      if (it.in !== null || it.out !== null) it.el.classList.toggle('on', (it.in === null || t >= it.in) && (it.out === null || t < it.out));
      if (it.type !== undefined) {
        const n = Math.max(0, Math.min(it.text.length, Math.floor((t - it.type) / CHAR_MS)));
        if (it.el.textContent.length !== n) { it.el.textContent = it.text.slice(0, n); it.el.toggleAttribute('data-filled', n > 0); }
      }
      if (it.at) {
        const on = new Map();
        for (const [ms, c] of it.at) if (ms <= t) c.startsWith('-') ? on.set(c.slice(1), false) : on.set(c, true);
        for (const [, c] of it.at) { const k = c.replace(/^-/, ''); it.el.classList.toggle(k, !!on.get(k)); }
      }
      if (it.path) {
        let pos = null, click = false;
        for (const [ms, v] of it.path) if (ms <= t) { if (v === 'click') click = t - ms < 180; else pos = v; }
        const xy = pos && (pos.startsWith('@') ? pointAt(pos.slice(1)) : pos.split(',').map(Number));
        if (xy) it.el.style.transform = `translate(${xy[0]}px, ${xy[1]}px)`;
        it.el.classList.toggle('down', click);
      }
    }
  };
  let raf = 0, start = 0, playing = false;
  const frame = now => { render((now - start) % dur); raf = requestAnimationFrame(frame); };
  const play = () => { if (playing || still.matches) return; playing = true; start = performance.now(); raf = requestAnimationFrame(frame); };
  const stop = () => { playing = false; cancelAnimationFrame(raf); };
  render(Number(demo.dataset.still || dur * 0.8));
  demo.seek = t => { stop(); render(t); }; // for checking a frame by hand
  new IntersectionObserver(([e]) => (e.isIntersecting ? play() : stop()), { threshold: 0.3 }).observe(demo);
  document.addEventListener('visibilitychange', () => (document.hidden ? stop() : play()));
  new ResizeObserver(([e]) => demo.style.setProperty('--k', e.contentRect.width / W)).observe(demo);
}
document.querySelectorAll('.demo').forEach(setup);

// copy buttons: data-copy-from="#id"
document.querySelectorAll('[data-copy-from]').forEach(btn => btn.addEventListener('click', async () => {
  const text = document.querySelector(btn.dataset.copyFrom).textContent;
  try { await navigator.clipboard.writeText(text); btn.textContent = 'Copied'; } catch { btn.textContent = 'Select and copy'; }
  setTimeout(() => (btn.textContent = 'Copy'), 1600);
}));
