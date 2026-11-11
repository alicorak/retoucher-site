// Screenshots of alicorak.com for the hero story: before.jpg, and after.jpg with the project titles 1.6x.
// Run: node scripts/capture-alicorak.mjs https://alicorak.com <out dir>, then
//   sips -Z 1240 -s format jpeg -s formatOptions 82 <out>/before.jpg --out assets/stage/alicorak-before.jpg (and after)
// If the page layout changes, update .am-pick (the DATALAND title box) in styles.css from the printed rects (halved).
import { spawn } from 'node:child_process';
import fs from 'node:fs';
const [,, url, outDir] = process.argv;
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', '--remote-debugging-port=9333', '--user-data-dir=' + outDir + '/prof', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws;
for (let i = 0; i < 50; i++) { try { const j = await (await fetch('http://127.0.0.1:9333/json')).json(); const p = j.find(t => t.type === 'page'); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); break; } } catch {} await sleep(200); }
await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJs = async expr => (await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1240, height: 800, deviceScaleFactor: 2, mobile: false });
await send('Page.navigate', { url });
await sleep(6000);
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 88 }); fs.writeFileSync(outDir + '/' + name, Buffer.from(r.result.data, 'base64')); };
await evalJs(`document.getAnimations().forEach(a => a.pause()); document.querySelectorAll('*').forEach(e => { if (getComputedStyle(e).animationName !== 'none') e.style.animationPlayState = 'paused'; }); true`);
await sleep(300);
// the title is the caption's own text; the subtitle is its child
const rectOf = `(() => { const caps = [...document.querySelectorAll('p[class*="caption"]')]; const out = caps.map(p => { const r = document.createRange(); r.selectNodeContents(p.firstChild); const b = p.firstChild.nodeType === 1 ? p.firstChild.getBoundingClientRect() : r.getBoundingClientRect(); return [p.firstChild.textContent.trim(), Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; }).filter(x => x[1] >= 0 && x[1] < 1240); return out; })()`;
console.log('before', JSON.stringify(await evalJs(rectOf)));
console.log('imgTop', await evalJs(`Math.round([...document.querySelectorAll('main img')].find(i => i.getBoundingClientRect().x >= 0).getBoundingClientRect().y)`));
await shot('before.jpg');
await evalJs(`document.querySelectorAll('p[class*="caption"]').forEach(p => { const t = p.firstChild; const w = document.createElement('span'); w.textContent = t.textContent; w.style.cssText = 'display:inline-block;transform:scale(1.6);transform-origin:0 100%'; p.replaceChild(w, t); }); true`);
await sleep(400);
console.log('imgTop', await evalJs(`Math.round([...document.querySelectorAll('main img')].find(i => i.getBoundingClientRect().x >= 0).getBoundingClientRect().y)`));
console.log('after', JSON.stringify(await evalJs(rectOf)));
await shot('after.jpg');
ws.close(); chrome.kill();
