// Timelines written in HTML, played by this file (docs demos and the home cards).
//   data-in="ms" / data-out="ms"   shown from / hidden from that time
//   data-type="ms"                 its text is typed from that time
//   data-at="ms:class;ms:-class"   classes added (or removed with -) over time
//   data-path="ms:x,y;ms:@name;ms:click"  the cursor's moves (to a point or to data-pt=name) and clicks
//   data-stick                     a scrolling list kept scrolled to its end
// Docs (.demo): loops while on screen. Home ([data-tl]): rests on its last frame, which is the static
// illustration, and plays once when the pointer enters its card (on touch screens: once when it scrolls in).
// With reduced motion nothing plays.
const CHAR_MS = 38;
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const fine = matchMedia('(hover: hover) and (pointer: fine)');
const events = s => (s || '').split(';').filter(Boolean).map(p => { const i = p.indexOf(':'); return [Number(p.slice(0, i)), p.slice(i + 1)]; });

function timeline(stage) {
  stage.classList.add('tl');
  const items = [...stage.querySelectorAll('[data-in],[data-out],[data-type],[data-at],[data-path]')].map(el => {
    const it = { el, in: el.dataset.in ? Number(el.dataset.in) : null, out: el.dataset.out ? Number(el.dataset.out) : null };
    if (el.dataset.type) { it.type = Number(el.dataset.type); it.text = el.textContent; el.textContent = ''; }
    if (el.dataset.at) it.at = events(el.dataset.at);
    if (el.dataset.path) it.path = events(el.dataset.path);
    return it;
  });
  // "@name": the centre of the element marked data-pt="name", wherever the layout put it
  const pointAt = name => {
    const el = stage.querySelector(`[data-pt="${name}"]`);
    if (!el || !el.getClientRects().length) return null;
    const r = el.getBoundingClientRect(), s = stage.getBoundingClientRect(), k = s.width / stage.offsetWidth;
    return [(r.left - s.left + r.width / 2) / k - 3, (r.top - s.top + r.height / 2) / k - 2]; // the arrow's tip
  };
  // data-stick: a list that keeps its newest item in view, like the plugin's own list
  const sticky = [...stage.querySelectorAll('[data-stick]')];
  return t => {
    for (const it of items) {
      if (it.in !== null || it.out !== null) it.el.classList.toggle('shown', (it.in === null || t >= it.in) && (it.out === null || t < it.out));
      if (it.type !== undefined) {
        const n = Math.max(0, Math.min(it.text.length, Math.floor((t - it.type) / CHAR_MS)));
        if (it.el.textContent.length !== n) { it.el.textContent = it.text.slice(0, n); it.el.toggleAttribute('data-filled', n > 0); }
      }
      if (it.at) {
        // before its first event a class is off if that event adds it, on if it removes it
        const on = new Map();
        for (const [, c] of it.at) { const k = c.replace(/^-/, ''); if (!on.has(k)) on.set(k, c.startsWith('-')); }
        for (const [ms, c] of it.at) if (ms <= t) on.set(c.replace(/^-/, ''), !c.startsWith('-'));
        for (const [k, v] of on) it.el.classList.toggle(k, v);
      }
      if (it.path) {
        let pos = null, click = false;
        for (const [ms, v] of it.path) if (ms <= t) { if (v === 'click') click = t - ms < 180; else pos = v; }
        const xy = pos && (pos.startsWith('@') ? pointAt(pos.slice(1)) : pos.split(',').map(Number));
        if (xy) it.el.style.transform = `translate(${xy[0]}px, ${xy[1]}px)`;
        it.el.classList.toggle('down', click);
      }
    }
    for (const el of sticky) el.scrollTop = el.scrollHeight;
  };
}

// docs: a 720×450 scene scaled to the column, looping while visible
document.querySelectorAll('.demo').forEach(demo => {
  const render = timeline(demo.querySelector('.scene'));
  const dur = Number(demo.dataset.loop || 8000);
  let raf = 0, start = 0, playing = false;
  const frame = now => { render((now - start) % dur); raf = requestAnimationFrame(frame); };
  const play = () => { if (playing || reduce.matches) return; playing = true; start = performance.now(); raf = requestAnimationFrame(frame); };
  const stop = () => { playing = false; cancelAnimationFrame(raf); };
  render(Number(demo.dataset.still || dur * 0.8));
  demo.seek = t => { stop(); render(t); }; // for checking a frame by hand
  new IntersectionObserver(([e]) => (e.isIntersecting ? play() : stop()), { threshold: 0.3 }).observe(demo);
  document.addEventListener('visibilitychange', () => (document.hidden ? stop() : play()));
  new ResizeObserver(([e]) => demo.style.setProperty('--k', e.contentRect.width / 720)).observe(demo);
});

// home: rest on the last frame, play once per pointer enter, always to the end
document.querySelectorAll('[data-tl]').forEach(art => {
  const render = timeline(art);
  const dur = Number(art.dataset.tl);
  const card = art.closest('.card') || art;
  let playing = false;
  render(dur);
  const play = () => {
    if (playing || reduce.matches) return;
    playing = true;
    const start = performance.now();
    const frame = now => {
      const t = now - start;
      render(Math.min(t, dur));
      if (t < dur) requestAnimationFrame(frame); else playing = false;
    };
    requestAnimationFrame(frame);
  };
  card.addEventListener('pointerenter', () => { if (fine.matches) play(); });
  if (!fine.matches) {
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { io.disconnect(); play(); } }, { threshold: 0.6 });
    io.observe(art);
  }
  art.seek = render; // for checking a frame by hand
});

// copy buttons: data-copy-from="#id"
document.querySelectorAll('[data-copy-from]').forEach(btn => btn.addEventListener('click', async () => {
  const text = document.querySelector(btn.dataset.copyFrom).textContent;
  try { await navigator.clipboard.writeText(text); btn.textContent = 'Copied'; } catch { btn.textContent = 'Select and copy'; }
  setTimeout(() => (btn.textContent = 'Copy'), 1600);
}));
