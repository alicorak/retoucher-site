// The prompt both "Onboard your agent" buttons copy. The page shows a short version of it.
const PROMPT = `Set up Retoucher for me. It lets me leave notes on my Figma layers that you pick up, apply in the Figma file and answer in a panel inside Figma.

1. Install the Retoucher agent plugin for the agent you are:
   - Claude Code: run \`claude plugin install retoucher --marketplace alicorak/retoucher\`
   - Codex: run \`codex plugin marketplace add alicorak/retoucher\`, then install it from /plugins and tell me to trust its hooks once
   - Cursor: run \`git clone https://github.com/alicorak/retoucher.git ~/.retoucher-plugin\` and \`mkdir -p ~/.cursor/plugins/local && ln -s ~/.retoucher-plugin ~/.cursor/plugins/local/retoucher\`, then tell me to restart Cursor
2. Check that Node.js 18 or newer is installed and that the Figma MCP server is connected. If either is missing, tell me exactly how to fix it.
3. Add the Retoucher Figma plugin. It's waiting for Figma Community review, so it comes with the agent plugin: get the path of its manifest (Claude Code: \`retoucher figma-plugin\`, or \`node <plugin folder>/bridge/cli.mjs figma-plugin\`; Codex and Cursor: the \`figma_plugin_path\` tool), show me that path and tell me to import it in the Figma desktop app: Plugins → Development → Import plugin from manifest…, then open it from Plugins → Development → Retoucher.
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
    btn.classList.toggle('copied', ok);
    showToast(ok ? 'Setup prompt copied. Paste it into your agent.' : 'Couldn’t copy. Select the prompt on the page instead.');
    setTimeout(() => { label.textContent = original; btn.classList.remove('copied'); }, 1800);
  });
}

// The whole Onboard card copies, through its button so the button shows the result
for (const proxy of document.querySelectorAll('[data-copy-proxy]')) {
  proxy.addEventListener('click', () => proxy.closest('.card').querySelector('[data-copy="prompt"]').click());
}

// Bento illustrations are drawn at 325px; shrink them on narrow cards
function layout() {
  for (const art of document.querySelectorAll('.art')) {
    const cardW = art.parentElement.clientWidth;
    art.style.setProperty('--art-s', Math.min(1, (cardW - 48) / 325));
  }
}
window.addEventListener('resize', layout);
layout();
document.fonts?.ready.then(layout);

// Feature icons: play once per pointer enter, always to the end, so leaving a cell never cuts the motion.
const canPlay = matchMedia('(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)');
document.querySelectorAll('.grid li').forEach(li => {
  li.addEventListener('pointerenter', () => {
    if (!canPlay.matches || li.classList.contains('play')) return;
    li.classList.add('play');
    Promise.allSettled(li.getAnimations({ subtree: true }).map(a => a.finished)).then(() => li.classList.remove('play'));
  });
});
