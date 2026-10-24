// The prompt both "Onboard your agent" buttons copy. The page shows a short version of it.
const PROMPT = `Set up Retoucher for me. It lets me leave notes on my Figma layers that you pick up, apply in the Figma file and answer in a panel inside Figma.

1. Install the Retoucher agent plugin for the agent you are:
   - Claude Code: run \`claude plugin install retoucher --marketplace alicorak/retoucher\`
   - Codex: run \`codex plugin marketplace add alicorak/retoucher\`, then install it from /plugins and tell me to trust its hooks once
   - Cursor: run \`git clone https://github.com/alicorak/retoucher.git ~/.retoucher-plugin\` and \`mkdir -p ~/.cursor/plugins/local && ln -s ~/.retoucher-plugin ~/.cursor/plugins/local/retoucher\`, then tell me to restart Cursor
2. Check that Node.js 18 or newer is installed and that the Figma MCP server is connected. If either is missing, tell me exactly how to fix it.
3. Tell me to open the Retoucher plugin in Figma (Plugins → Retoucher).
4. Start watching my Figma notes: in Claude Code run /retoucher:watch, in Codex or Cursor use the watch-figma-notes skill.

Setup details: https://github.com/alicorak/retoucher#readme`;

const toast = document.querySelector('.toast');
let toastTimer;
function showToast(text) {
  toast.textContent = text;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 1800);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // clipboard API refused (insecure context or no permission): fall back to a hidden textarea
    const ta = Object.assign(document.createElement('textarea'), { value: text });
    ta.style.cssText = 'position:fixed;opacity:0';
    document.body.append(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  }
}

for (const btn of document.querySelectorAll('[data-copy="prompt"]')) {
  const label = btn.querySelector('[data-label]');
  const original = label.textContent;
  btn.addEventListener('click', async () => {
    const ok = await copyText(PROMPT);
    label.textContent = ok ? 'Copied' : original;
    showToast(ok ? 'Setup prompt copied. Paste it into your agent.' : 'Couldn’t copy. Select the prompt on the page instead.');
    setTimeout(() => { label.textContent = original; }, 1800);
  });
}

// ── Carousel: slides are 922×576 compositions, scaled to fit ──
const track = document.querySelector('.track');
const slides = [...track.querySelectorAll('.slide')];
const capTitle = document.querySelector('[data-cap-title]');
const cap = document.querySelector('[data-cap]');
const [prev, next] = document.querySelectorAll('.arrow');
const STAGE_W = 922, STAGE_H = 576;

function layout() {
  const vw = document.documentElement.clientWidth;
  const narrow = vw < 720;
  const avail = Math.min(STAGE_W, vw - 40);
  for (const slide of slides) {
    let s, w, h, tx, ty;
    if (narrow) {
      // phones: a 300px tall crop at 0.6, framed on the panel (or centred)
      s = 0.6; w = avail; h = 300;
      tx = slide.dataset.focus === 'panel' ? w - 12 - (534 + 360) * s : (w - STAGE_W * s) / 2;
      ty = (h - STAGE_H * s) / 2;
    } else {
      s = avail / STAGE_W; w = avail; h = STAGE_H * s; tx = 0; ty = 0;
    }
    slide.style.setProperty('--slide-w', `${w}px`);
    slide.style.setProperty('--slide-h', `${h}px`);
    const stage = slide.querySelector('.stage');
    stage.style.setProperty('--s', s);
    stage.style.setProperty('--tx', `${tx}px`);
    stage.style.setProperty('--ty', `${ty}px`);
  }
  // bento illustrations are drawn at 325px; shrink them on narrow cards
  for (const art of document.querySelectorAll('.art')) {
    const cardW = art.parentElement.clientWidth;
    art.style.setProperty('--art-s', Math.min(1, (cardW - 48) / 325));
  }
  update();
}

function current() {
  const x = track.scrollLeft;
  let best = 0;
  slides.forEach((s, i) => { if (Math.abs(s.offsetLeft - slides[0].offsetLeft - x) < Math.abs(slides[best].offsetLeft - slides[0].offsetLeft - x)) best = i; });
  return best;
}

function update() {
  const i = current();
  capTitle.textContent = slides[i].dataset.captionTitle;
  cap.textContent = slides[i].dataset.caption;
  prev.disabled = i === 0;
  next.disabled = i === slides.length - 1;
}

for (const btn of [prev, next]) {
  btn.addEventListener('click', () => {
    const i = Math.max(0, Math.min(slides.length - 1, current() + Number(btn.dataset.dir)));
    track.scrollTo({ left: slides[i].offsetLeft - slides[0].offsetLeft, behavior: 'smooth' });
  });
}
track.addEventListener('scroll', () => requestAnimationFrame(update), { passive: true });
track.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') next.click();
  if (e.key === 'ArrowLeft') prev.click();
});
window.addEventListener('resize', layout);
layout();
document.fonts?.ready.then(layout);
