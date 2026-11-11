#!/usr/bin/env python3
"""Builds docs/ from the content below: a few topic pages, one section per feature (#anchor).

Run from the site root:  python3 scripts/build-docs.py
Needs the plugin checkout next to the site (../retoucher): the demos use the plugin's own panel,
its CSS (written to docs/panel.css, scoped to .pp) and its header and composer markup, so they match it 1:1.
Each demo is a 720x450 scene; timeline.js plays its data-in / data-type / data-at / data-path timeline.
"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = open(os.path.join(ROOT, '..', 'retoucher', 'plugin', 'ui.html')).read()
SITE = 'https://retoucher.alicorak.com'

# ── the plugin's CSS, scoped to .pp ──────────────────────

def scope_selector(sel):
    sel = sel.strip()
    if sel.startswith('html'):
        return None
    sel = re.sub(r'#([A-Za-z][\w-]*)', r'.id-\1', sel)
    if sel == ':root':
        return '.pp'
    if sel.startswith('body'):
        return '.pp' + sel[4:]
    return '.pp ' + sel

def scope_css(css):
    out, i = [], 0
    while i < len(css):
        j = css.find('{', i)
        if j < 0:
            break
        head = css[i:j].strip()
        depth, k = 1, j + 1
        while depth:
            depth += {'{': 1, '}': -1}.get(css[k], 0); k += 1
        body = css[j + 1:k - 1]
        i = k
        head = re.sub(r'/\*.*?\*/', '', head, flags=re.S).strip()
        if head.startswith('@font-face'):
            continue                      # the site loads Geist itself
        if head.startswith('@keyframes'):
            out.append(head.replace('@keyframes ', '@keyframes pp-') + '{' + body + '}')
        elif head.startswith('@media'):
            out.append(head + '{' + scope_css(body) + '}')
        else:
            sels = [s for s in (scope_selector(x) for x in head.split(',')) if s]
            if sels:
                out.append(', '.join(sels) + ' {' + body + '}')
    return '\n'.join(out)

STYLE = re.search(r'<style>(.*?)</style>', UI, re.S).group(1)
PANEL_CSS = scope_css(STYLE)

def site_leaks():
    """The site styles some class names the plugin uses too (.btn, .field, .perm…). Inside the panel the
    properties only the site sets go back to the browser default; the plugin's own rules still win."""
    site = re.sub(r'/\*.*?\*/', '', open(os.path.join(ROOT, 'styles.css')).read(), flags=re.S)
    site = re.sub(r'@media[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}', '', site)
    plugin_classes = set(re.findall(r'\.([a-z][\w-]*)', STYLE))
    props = {}
    for sels, body in re.findall(r'([^{}]+)\{([^{}]*)\}', site):
        for sel in sels.split(','):
            m = re.fullmatch(r'\s*\.([a-z][\w-]*)\s*', sel)
            if m and m.group(1) in plugin_classes:
                for d in body.split(';'):
                    if ':' in d:
                        props.setdefault(m.group(1), set()).add(d.split(':')[0].strip())
    return '\n'.join(f'.pp :where(.{c}), .pp:where(.{c}) {{ ' + ' '.join(f'{p}: revert;' for p in sorted(ps)) + ' }'
                     for c, ps in sorted(props.items()))
for name in re.findall(r'@keyframes (\w[\w-]*)', STYLE):
    PANEL_CSS = re.sub(r'(animation:[^;}]*?)\b' + name + r'\b', r'\1pp-' + name, PANEL_CSS)

# ── the plugin's markup ─────────────────────────────────

def part(start, end):
    i = UI.index(start); return UI[i:UI.index(end, i) + len(end)]

HEADER = part('<header class="bar">', '</header>')
MINI = part('<button id="mini"', '</button>')
COMPOSER = part('<footer class="composer" id="composer">', '</footer>')
PICKER = UI[UI.index('<div id="picker" hidden>'):UI.index('<header class="bar">')].strip()
SVG = lambda p: f'<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">{p}</svg>'
ICON = {k: SVG(v) for k, v in re.findall(r"^  (trash|undo|reply|layers): SVG\('(.*?)'\),", UI, re.M)}
ICON['hash'] = re.search(r"^  hash: '(.*?)',", UI, re.M).group(1)

def at_id(h, id_, attrs):
    """add attributes to the element with this id"""
    return re.sub(rf'(<\w+[^>]*?\bid="{id_}")', lambda m: m.group(1) + attrs, h, count=1)

def unhide(h, id_):
    return re.sub(rf'(<\w+[^>]*?\bid="{id_}"[^>]*?) hidden', r'\1', h, count=1)

def inner(h, id_, content):
    return re.sub(rf'(<(\w+)[^>]*?\bid="{id_}"[^>]*>).*?(</\2>)', lambda m: m.group(1) + content + m.group(3), h, count=1, flags=re.S)

def seg_at(h, seg, v, attrs):
    """attributes on one button of an Options segment"""
    i = h.index(f'id="{seg}"'); j = h.index('</div>', i)
    return h[:i] + re.sub(rf'(<button data-v="{v}")', lambda m: m.group(1) + attrs, h[i:j], count=1) + h[j:]

def idify(h):
    """ids become classes (a page has several panels); the CSS was scoped the same way"""
    def f(m):
        tag = m.group(0); id_ = re.search(r'\bid="([^"]+)"', tag).group(1)
        tag = re.sub(r'\s\bid="[^"]+"', '', tag)
        if ' class="' in tag:
            return tag.replace(' class="', f' class="id-{id_} ', 1)
        return re.sub(r'^<(\w+)', rf'<\1 class="id-{id_}"', tag)
    return re.sub(r'<\w+[^>]*\bid="[^"]+"[^>]*>', f, h)

# ── scene parts ─────────────────────────────────────────

def a(**kw):
    m = {'in_': 'data-in', 'out': 'data-out', 'type_': 'data-type', 'at': 'data-at', 'path': 'data-path', 'pt': 'data-pt'}
    return ''.join(f' {m[k]}="{v}"' for k, v in kw.items() if v is not None)

def cursor(path):
    return f'<i class="s-cur"{a(path=path)}></i>'

def canvas(extra='', h1_at=None, cta_at=None, name='Home'):
    return (f'<div class="s-canvas"><div class="s-frame"><span class="s-fname">{name}</span><div class="s-art">'
            '<div class="s-nav"><span>Morning</span><span>Menu · Shop</span></div>'
            f'<p class="s-h1"{a(at=h1_at)}>Slow mornings,<br>good coffee.</p>'
            f'<span class="s-cta"{a(at=cta_at)}>Order ahead →</span>'
            f'</div></div>{extra}</div>')

def sel(x, y, w, h, **kw):
    return f'<div class="s-sel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"{a(**kw)}></div>'

H1 = (36, 210, 236, 80)      # the headline on the canvas
CTA = (36, 312, 122, 40)     # the button
H1_AT, CTA_AT = '150,240', '90,330'
LABEL = {'pending': 'Waiting', 'working': 'Working', 'question': 'Needs answer', 'done': 'Done', 'reverted': 'Reverted'}

def item(num, label, states, note, body='', acts=True, in_=None, at=None, undo=False, select=None):
    """a note as the plugin draws it. states: [(status, in, out)]"""
    st = ''.join(f'<span class="st {s}"{a(in_=i, out=o)}>{LABEL[s]}</span>' for s, i, o in states)
    act = ''
    if acts:
        act = ('<div class="acts">'
               + (f'<button class="btn ghost sm" type="button">{ICON["layers"]}Select {select}</button>' if select else '')
               + (f'<button class="btn ghost sm" type="button" data-pt="undo">{ICON["undo"]}Undo</button>' if undo else '')
               + f'<span class="grow"></span><button class="ib" type="button">{ICON["reply"]}</button><button class="ib" type="button">{ICON["trash"]}</button></div>')
    return (f'<article class="item"{a(in_=in_, at=at)}><div class="top"><span class="who"><span class="num">{ICON["hash"]}{num}</span>'
            f'<span class="lbl">{label}</span></span>{st}</div><div class="you">{note}</div>{body}{act}</article>')

def msg(frm, text, in_=None, extra=''):
    who = {'claude': 'Claude', 'user': 'You'}[frm]
    return f'<div class="msg {frm}"{a(in_=in_)}><small>{who}</small>{text}{extra}</div>'

def prog(steps):
    """steps: [(text, in, done_at)]: the last unfinished one is 'now'"""
    rows = ''
    for t, i, d in steps:
        cls_at = f'0:now;{d}:-now;{d}:done' if d is not None else '0:now'
        rows += f'<div{a(in_=i, at=cls_at)}>{t}</div>'
    return f'<div class="prog">{rows}</div>'

def bubble_perm(title, note_id=12, in_=None, out=None, allow_at=None):
    return (f'<section class="perms"{a(in_=in_, out=out)}><div class="perm" data-kind="permission"><div class="bubble">'
            f'<span class="ph2">Note #{note_id} · Asks for permission</span><b>{title}</b></div>'
            '<div class="pa"><button class="btn ghost sm" type="button" data-decide="deny">Decline</button><span class="grow"></span>'
            '<button class="btn ghost sm" type="button">Always allow</button>'
            f'<button class="btn primary sm" type="button" data-pt="allow"{a(at=allow_at)}>Allow once</button></div></div></section>')

def bubble_question(q, choices, note_id=14, in_=None, out=None, pick_at=None):
    ch = ''.join(f'<button class="pchoice" type="button"{a(pt=f"c{i}", at=(f"{pick_at}:on" if i == 0 and pick_at else None))}><span>{l}</span><small>{d}</small></button>' for i, (l, d) in enumerate(choices))
    return (f'<section class="perms"{a(in_=in_, out=out)}><div class="perm" data-kind="question"><div class="bubble">'
            f'<span class="ph2">Note #{note_id} · Asks you</span><div class="pq"><b>{q}</b><div class="pchoices">{ch}</div>'
            '<div class="pother">Or write your own answer…</div></div></div>'
            '<div class="pa"><button class="btn ghost sm" type="button">Skip</button><span class="grow"></span>'
            '<button class="btn primary sm" type="button" data-pt="answer">Send answers</button></div></div></section>')

def composer(text='', type_at=None, ctx=('Headline', 'Text · 584×88'), send_on=None, opts=None, mention='', targets='', files='',
             optline='', tweak=None):
    h = COMPOSER
    h = inner(h, 'tName', ctx[0]); h = inner(h, 'tMeta', ctx[1])
    h = at_id(h, 'thumb', ' style="background:linear-gradient(135deg,#d3d6dc,#e7e7e9)"')
    h = h.replace(' disabled', '')
    h = at_id(h, 'addSel', ' data-pt="add"'); h = at_id(h, 'makeArea', ' data-pt="area"'); h = at_id(h, 'optsBtn', ' data-pt="opts"')
    h = at_id(h, 'queue', ' data-pt="batch"')
    end = (type_at or 0) + len(text) * 38
    h = at_id(h, 'send', ' data-pt="send"' + a(at=(send_on or (f'0:off;{end}:-off' if text else '0:off'))))
    ph = re.search(r'<textarea id="note"[^>]*placeholder="([^"]*)"[^>]*></textarea>', h)
    h = h.replace(ph.group(0), f'<div class="ta" id="note" data-pt="field"><span class="ta-ph">{ph.group(1)}</span>'
                  + (f'<span class="typed"{a(type_=type_at)}>{text}</span>' if text else '') + '</div>')
    if opts:
        h = h.replace('<div class="pop opts" id="opts" hidden>', f'<div class="pop opts" id="opts"{a(in_=opts[0], out=opts[1])}>')
    if mention:
        h = unhide(inner(h, 'mention', mention[0]), 'mention'); h = at_id(h, 'mention', a(in_=mention[1], out=mention[2]))
    if targets:
        h = unhide(inner(h, 'targets', targets), 'targets')
    if files:
        h = unhide(inner(h, 'files', files), 'files')
    if optline:
        h = unhide(inner(h, 'optLine', optline[0]), 'optLine'); h = at_id(h, 'optLine', a(in_=optline[1]))
    if tweak:
        h = tweak(h)
    h = re.sub(r'\s*<input type="file"[^>]*>', '', h)
    return h

def plugin(items='', perms='', comp=None, at=None, mini=''):
    head = HEADER.replace('class="status" id="conn"', 'class="status ready" id="conn"').replace('Connecting…', 'Ready')
    head = at_id(head, 'miniBtn', ' data-pt="shrink"')
    m = MINI.replace('<span class="dot" id="miniDot"></span>', '<span class="dot wait" id="miniDot"></span>')
    if mini:
        m = inner(m, 'miniText', mini)
    m = at_id(m, 'mini', ' data-pt="bar"')
    return idify(f'<div class="pp s-plugin"{a(at=at)}>{head}{m}<main class="list" id="list" data-stick>{items}</main>{perms}{comp if comp is not None else composer()}</div>')

def demo(scene, loop=7000, still=None):
    st = f' data-still="{still}"' if still is not None else ''
    return f'<div class="demo" data-loop="{loop}"{st} role="img"><div class="scene" inert>{scene}</div></div>'

# ── content ─────────────────────────────────────────────
# PAGES: [(slug, title, lead, [section…])]; a section: dict(id, title, sub, line, how, note, demo, html)

PAGES = []
def page(slug, title, lead, sections):
    PAGES.append(dict(slug=slug, title=title, lead=lead, sections=sections))
def S(id, title, sub, line, demo_html=None, how=None, note=None, html_=None):
    return dict(id=id, title=title, sub=sub, line=line, demo=demo_html, how=how, note=note, html=html_)

def prompt_text():
    js = open(os.path.join(ROOT, 'main.js')).read()
    return re.search(r'const PROMPT = `(.*?)`;', js, re.S).group(1).replace('\\`', '`')

def table(rows, head):
    return ('<table class="d-table"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in head) + '</tr></thead><tbody>'
            + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table>')

NOTHING = ('Nothing selected', 'Select layers or frames, or an area.')

def picker_html(in_, out):
    """the plugin's own area picker, with two marks"""
    h = PICKER.replace(' hidden', '', 1)
    h = h.replace('<img id="pkImg" alt="">', '<span class="s-shot"><span class="s-shot-h">Slow mornings,<br>good coffee.</span></span>')
    h = inner(h, 'pkLayer', '<div class="pk-box s-grow" style="left:150px;top:46px;width:150px;height:84px"' + a(in_=1300, at='1300:big') + '><i>1</i></div>'
                             '<div class="pk-box" style="left:40px;top:188px;width:0;height:0"' + a(in_=2800) + '><i>2</i></div>')
    h = h.replace('id="pkAdd" type="button"', 'id="pkAdd" type="button" data-pt="pkadd"')
    return h.replace('<div id="picker"', '<div id="picker"' + a(in_=in_, out=out), 1)

page('get-started', 'Get started', 'Two halves: an agent plugin on your computer and the panel inside Figma. Your agent installs the first one for you.', [
    S('setup', 'Set it up', 'Set it up in a minute.',
      'Paste the setup prompt into Claude Code, Codex or Cursor. It installs the agent plugin, starts a small bridge on your computer and checks Node.js 18+ and the Figma MCP.',
      demo('<div class="s-term"><span class="who">Your agent</span>'
           '<span class="ok"' + a(in_=700) + '>Retoucher installed</span><span class="ok"' + a(in_=1500) + '>Bridge running on localhost:4747</span>'
           '<span class="ok"' + a(in_=2300) + '>Figma MCP connected</span><span class="ok"' + a(in_=3100) + '>Figma plugin ready to import</span>'
           '<span class="ok"' + a(in_=4300) + '>Watching your notes</span></div>'
           + plugin('<div class="empty welcome"' + a(out=4300) + '><b>Retoucher works with a coding agent on your computer</b><p>Waiting for your agent…</p></div>'
                    '<div class="empty"' + a(in_=4400) + '><b>No notes yet</b><ol><li>Select layers or a frame on the canvas.</li><li>Write what should change below.</li><li>Send.</li></ol></div>',
                    comp=composer(ctx=NOTHING)), loop=7500),
      how='Then add the Figma plugin: while it waits for Figma Community review, your agent gives you a <code>manifest.json</code> to import in the Figma desktop app (<em>Plugins → Development → Import plugin from manifest…</em>). Open it, paste the file\'s link once, and start watching: <code>/retoucher:watch</code> in Claude Code, “watch my Figma notes” in Codex or Cursor.',
      html_='<div class="d-prompt-head"><b>Setup prompt</b><button class="d-copy" type="button" data-copy-from="#prompt">Copy</button></div>'
            f'<pre class="d-prompt" id="prompt">{html.escape(prompt_text())}</pre>'),
    S('status', 'What the panel says', 'Ready, not watching, not connected.',
      'The status at the top right of the panel tells you where things stand.',
      html_=table([['Ready', 'An agent is watching; notes are picked up right away.'],
                   ['Not watching', 'The bridge runs, but no agent watches. Notes wait until you start watching.'],
                   ['Not connected', 'No agent session is open (opening one starts the bridge), or the agent plugin isn\'t installed.'],
                   ['Not paired', 'Another Figma panel paired first. Ask your agent to run <code>retoucher unpair</code>.']], ['Panel', 'Meaning'])),
])

page('agent-and-privacy', 'Your agent & privacy', 'Retoucher brings no AI of its own, and nothing leaves your computer.', [
    S('agents', 'Your own agent', 'Claude Code, Codex, Cursor.',
      'The coding agent you already use reads your notes, edits the file through the Figma MCP and answers in the panel, on its own account and plan.',
      demo('<div class="s-term"><span class="who">Claude Code · watching</span>'
           '<span' + a(in_=900) + '>NEW #12 Make the headline bolder</span><span class="ok"' + a(in_=2200) + '>Edited 1 text layer</span><span class="ok"' + a(in_=3300) + '>Replied in the panel</span></div>'
           + plugin(item(12, 'Headline', [('pending', None, 1500), ('working', 1500, 3300), ('done', 3300, None)], 'Make the headline bolder',
                         msg('claude', 'Done. The headline is now Bold.', 3300), in_=900)), loop=6500),
      how='Claude Code: <code>/retoucher:watch</code>. Codex or Cursor: ask it to “watch my Figma notes”.',
      note='Notes live in <code>~/.retoucher</code>, shared by every agent, so you can switch agents and keep them.'),
    S('privacy', 'Stays on your computer', 'No server in between.',
      'The panel only talks to a bridge on your computer (<code>localhost:4747</code>). Notes, screenshots and files stay in <code>~/.retoucher</code>.',
      demo('<div class="s-wire" style="left:184px;top:214px;width:96px"></div><div class="s-wire" style="left:440px;top:214px;width:96px"></div>'
           '<div class="s-node" style="left:24px;top:170px">Figma panel<small>in your Figma</small></div>'
           '<div class="s-node" style="left:280px;top:170px">Bridge<small>localhost:4747</small></div>'
           '<div class="s-node" style="left:536px;top:170px">Your agent<small>on your computer</small></div>'
           '<i class="s-dot"' + a(at='0:p0;900:-p0;900:p1;1800:-p1;1800:p2;2700:-p2;2700:p3;3600:-p3') + '></i>', loop=4500),
      note='The bridge only answers the panel that paired with it first, so websites you visit can\'t read or send notes. To pair another panel: <code>retoucher unpair</code>.'),
])

def picked(name, meta):
    """the composer's selection: nothing, then this layer"""
    return lambda h: (h.replace(f'<div class="name" id="tName">{NOTHING[0]}</div>',
                                '<div class="name" id="tName"><span' + a(out=650) + f'>{NOTHING[0]}</span><span' + a(in_=650) + f'>{name}</span></div>')
                       .replace(f'<div class="sub" id="tMeta">{NOTHING[1]}</div>',
                                '<div class="sub" id="tMeta"><span' + a(out=650) + f'>{NOTHING[1]}</span><span' + a(in_=650) + f'>{meta}</span></div>'))

page('write-a-note', 'Write a note', 'Point at something in Figma, say what should change, send.', [
    S('notes', 'Notes on layers', 'Write it like a comment.',
      'Select a layer, write what should change, press Send. Like a Figma comment, except the agent makes the change.',
      demo(canvas(sel(*H1, in_=650), h1_at='5200:bold')
           + plugin(item(12, 'Headline', [('pending', 3000, 3800), ('working', 3800, 5200), ('done', 5200, None)], 'Make it bolder', in_=3000),
                    comp=composer('Make it bolder', 1500, ctx=NOTHING, tweak=picked('Headline', 'Text · 584×88')))
           + cursor(f'0:300,420;100:{H1_AT};650:click;1100:@field;2300:@send;2900:click'), loop=7000),
      how='Select → write → <kbd>↵</kbd> (<kbd>⇧↵</kbd> for a new line).',
      note='Select the exact layer you mean: a selection covering a whole row of screens is ambiguous, and the agent will ask. The first time, paste the file\'s link when the panel asks.'),
    S('areas', 'Areas and pins', 'Drag an area or drop a pin.',
      'Mark part of a screen instead of a layer: drag an area around it, or click to drop a pin.',
      demo(canvas(sel(20, 64, 300, 322))
           + plugin(item(21, 'Area on Home', [('pending', 5300, None)], 'Less glare here, and bolder', in_=5300),
                    comp=composer(ctx=('Home', 'Frame · 1440×900'))).replace('<header class="bar">', idify(picker_html(900, 5200)) + '<header class="bar">', 1)
           + cursor('0:300,420;100:@area;600:click;800:530,140;1300:click;1500:640,220;2200:420,280;2800:click;4300:@pkadd;4900:click'), loop=7000),
      how='Select a frame (or nothing, for what is on screen) → <em>Mark area</em> → drag or click → <em>Add</em>.',
      note='The agent gets each area\'s crop, its position, the screen it sits in and the layer underneath.'),
    S('targets', 'Several targets', 'Layers across pages.',
      'One note about several layers, even on different pages. Each keeps its own screenshot.',
      demo(canvas(sel(*H1, in_=650, out=1900) + sel(*CTA, in_=2300))
           + plugin(comp=composer('Make these two match', 4300, ctx=NOTHING,
                    targets='<span class="tchip"' + a(in_=1500) + '><span class="tt" style="background:linear-gradient(135deg,#d3d6dc,#e7e7e9)"></span><span class="tn">Headline · Home</span></span>'
                            '<span class="tchip"' + a(in_=3300) + '><span class="tt" style="background:#111"></span><span class="tn">Order ahead · Home</span></span>'))
           + cursor(f'0:300,420;100:{H1_AT};650:click;900:@add;1450:click;1700:{CTA_AT};2300:click;2700:@add;3300:click;3900:@field'), loop=7000),
      how='Select a layer → <em>+</em> → select the next one → <em>+</em> → write and send.'),
    S('files', 'Photos and files', 'Drop in screenshots.',
      'Attach a reference photo, a PDF brief or a screenshot. The agent opens them with the note.',
      demo(canvas(sel(*H1)) + '<div class="s-tag" style="left:110px;top:396px;padding:8px 10px"' + a(in_=300, out=1700) + '>moodboard.jpg</div>'
           + plugin(comp=composer('Match the mood of this photo', 2400,
                    files='<span class="athumb"' + a(in_=1700) + ' style="background:linear-gradient(160deg,#c9a27c,#6d4c35)"></span><span class="fchip"' + a(in_=2000) + '><span class="ext">PDF</span><span class="fn">brief.pdf</span></span>'))
           + cursor('0:140,410;500:140,410;1100:560,330;1700:click'), loop=6500),
      how='Drop or paste them on the panel, or use the clip button.', note='Up to 8 files per note, 12 MB each. Photos are scaled to 1600 px.'),
    S('mentions', '@mentions', 'Use your variables.',
      'Type @ to point at an exact variable, style or component. The agent uses exactly that one.',
      demo(canvas(sel(*CTA), cta_at='5400:blue')
           + plugin(item(14, 'Order ahead', [('working', 4500, 5400), ('done', 5400, None)], 'Use @color/brand for the button', in_=4500),
                    comp=composer('Use @color/brand for the button', 900, ctx=('Order ahead', 'Button · 112×32'),
                                  mention=('<div class="opt"><b>color/ink</b><span>Variable</span></div><div class="opt" data-pt="brand"' + a(at='1700:on') + '><b>color/brand</b><span>Variable</span></div><div class="opt"><b>color/paper</b><span>Variable</span></div>', 1250, 2600)))
           + cursor('0:@field;1800:@brand;2400:click;3500:@send;4100:click'), loop=7500),
      how='Type <kbd>@</kbd>, filter, pick a variable, style, component or library.', note='Library components show up once they are used on the page.'),
    S('quick-action', 'Quick action', '⌘/ and type.',
      'Send a note without opening the panel: from Figma\'s own quick actions, with whatever is selected.',
      demo(canvas(sel(*H1), h1_at='5600:bold')
           + '<div class="s-qa"' + a(in_=900, out=4600) + '><div class="q"><span>⌘/</span><span' + a(type_=1200) + '>Retoucher</span></div>'
           '<div class="r hi"' + a(in_=1700, out=2600) + '>Retoucher · Note</div><div class="q"' + a(in_=2600) + '><span>Note</span><span' + a(type_=2800) + '>Tighten the letter spacing</span></div></div>'
           '<div class="s-toast"' + a(in_=4600, out=6400) + '>Sent to Retoucher</div>', loop=7500),
      how='<kbd>⌘/</kbd> → “Retoucher” → <kbd>Tab</kbd> → write → <kbd>↵</kbd>.'),
    S('batches', 'Batches', 'Send a few at once.',
      'Collect a few notes, then send them together. The agent works through them in order.',
      demo(canvas(sel(*H1))
           + plugin(comp=composer('Shorter, one line', 1200))
           .replace('<footer class="id-composer composer">',
                    '<div class="batch"' + a(in_=950) + '><div class="head"><span>Batch · <span' + a(out=2950) + '>1 note</span><span' + a(in_=2950) + '>2 notes</span></span><button class="link" type="button">Clear</button></div>'
                    '<div class="draft"><span class="t">Make it bolder</span></div><div class="draft"' + a(in_=2950) + '><span class="t">Shorter, one line</span></div>'
                    '<div class="actions"><button class="btn primary sm" type="button" data-pt="sendall">Send all</button><label class="tog muted"><input type="checkbox"> At the same time</label></div></div>'
                    '<footer class="id-composer composer">')
           + cursor('0:560,330;400:@batch;950:click;2400:@batch;2950:click;3700:@sendall;4300:click'), loop=6500),
      how='Write → <em>Batch</em> (<kbd>⇧⌘↵</kbd>) → repeat → <em>Send all</em>.', note='<em>At the same time</em> works on notes that don\'t depend on each other in parallel.'),
])

page('while-it-works', 'While it works', 'Follow along and steer, without leaving Figma.', [
    S('steps', 'Live steps', 'See it work, as it goes.',
      'The note shows the step the agent is on and the last ones it finished. When it\'s done they fold into “N steps”.',
      demo(canvas(sel(*H1), h1_at='4600:bold')
           + plugin(item(12, 'Headline', [('working', None, 4800), ('done', 4800, None)], 'Set the headline in KMR Waldenburg',
                         prog([('Reading the headline', 300, 1300), ('Finding KMR Waldenburg on your computer', 1300, 2800), ('Changing 1 text layer', 2800, 4600)])
                         + msg('claude', 'Done, in KMR Waldenburg Bold.', 4800))), loop=7000, still=4000)),
    S('talk', 'Talk while it works', 'Reply mid-task.',
      'Write under a note any time, also while it works. The agent reads it before its next step.',
      demo(canvas(sel(*H1))
           + plugin(item(12, 'Headline', [('working', None, None)], 'Set the headline in KMR Waldenburg',
                         prog([('Finding KMR Waldenburg on your computer', None, 800), ('Changing 1 text layer', 800, None)])
                         + msg('user', 'Keep the size as it is', 2900) + msg('claude', 'Got it, I\'ll keep the size.', 3800)),
                    comp=composer('Keep the size as it is', 1100))
           + cursor('0:@field;2200:@send;2800:click'), loop=6500)),
    S('questions', 'Questions and plans', 'Answer in the panel.',
      'When the agent needs a decision, it asks here. Pick an answer or write your own, and it carries on.',
      demo(canvas(sel(*H1), h1_at='5000:bold')
           + plugin(item(14, 'Hero', [('question', None, 4200), ('working', 4200, None)], 'Make it calmer', prog([('Setting the headline to 48 pt', 4400, None)])),
                    perms=bubble_question('Which headline size?', [('48 pt', 'one step down'), ('40 pt', 'two steps down')], out=4200, pick_at=1800))
           + cursor('0:560,430;1200:@c0;1800:click;2900:@answer;3500:click'), loop=7000, still=2600),
      note='<em>Options → Show a plan first</em> shows the plan before anything changes: <em>Approve plan</em> or <em>Change</em> with a note.'),
    S('approve', 'Approve', 'Allow once, always, or decline.',
      'Permission prompts show up in the panel: <em>Allow once</em>, <em>Always allow</em> or <em>Decline</em>.',
      demo(canvas(sel(*H1), h1_at='4400:bold')
           + plugin(item(12, 'Headline', [('working', None, None)], 'Make it a bit bolder',
                         prog([('Reading the headline', None, 0), ('Changing 1 text layer', 3200, None)])),
                    perms=bubble_perm('Edit the Figma file', in_=600, out=3100, allow_at='2800:pick'))
           + cursor('0:560,330;1500:@allow;2800:click'), loop=6500, still=2400),
      note='No answer in 2 minutes, or the panel is closed: the agent asks in its own window. Works the same in Claude Code, Codex and Cursor.'),
])

page('results', 'Results', 'What comes back, and the way back.', [
    S('undo', 'Undo', 'One click back.',
      'Finished notes show a before and after picture. <em>Undo</em> puts the old values back, even with the agent offline.',
      demo(canvas(sel(*H1), h1_at='0:bold;2600:-bold')
           + plugin(item(11, 'Headline', [('done', None, 2600), ('reverted', 2600, None)], 'Make it bolder',
                         '<div class="cmp"><figure><div class="img s-before"></div><figcaption>Before</figcaption></figure><figure><div class="img s-after"></div><figcaption>After</figcaption></figure></div>',
                         undo=True))
           + cursor('0:560,250;1200:@undo;2400:click'), loop=5500, still=1500),
      note='Changes the agent couldn\'t record show no Undo button.'),
    S('versions', 'Versions', 'Two to four directions, side by side.',
      'Ask for 2–4 versions and the agent makes that many directions next to your selection. The original stays.',
      demo('<div class="s-copies"><div class="s-copy"><small>Original</small><p>Slow mornings</p></div>'
           '<div class="s-copy"' + a(in_=3200) + '><small>v1</small><p style="font-weight:800">Slow mornings</p></div>'
           '<div class="s-copy dark"' + a(in_=3700) + '><small>v2</small><p>Slow mornings</p></div></div>'
           + plugin(item(15, 'Hero', [('working', 2800, 3800), ('done', 3800, None)], 'Two moods for the hero', in_=2800),
                    comp=composer('Two moods for the hero', 1300, ctx=('Hero', 'Frame · 1440×900'), opts=(None, 1200),
                                  optline=('2 versions', 1200), tweak=lambda h: seg_at(seg_at(h, 'variations', '2', ' data-pt="v2" data-at="800:on"'), 'variations', '1', ' data-at="800:-on"')))
           + cursor('0:560,300;200:@v2;800:click;2200:@send;2700:click'), loop=6500),
      how='<em>Options → Versions</em>: 2, 3 or 4.'),
    S('references', 'References', 'Matching screens, from any MCP.',
      'Matching screens from a references MCP you have connected (Mobbin, for example) land next to your selection, and the change happens on a copy.',
      demo(canvas(sel(*H1))
           + plugin(item(16, 'Hero', [('working', None, 3200), ('done', 3200, None)], 'Find a calmer direction',
                         prog([('Looking for references', 300, 1800), ('Placing 4 of 4', 1800, 3000)])
                         + msg('claude', 'Four calm screens, and the change on a copy.', 3200,
                               '<div class="refs"><span class="ref"><span class="ph" style="background:linear-gradient(160deg,#222,#555)"></span><small>Calm</small></span><span class="ref"><span class="ph" style="background:#e9e9e7"></span><small>Headspace</small></span><span class="ref"><span class="ph" style="background:#fff;outline:1px solid #eee"></span><small>Oak</small></span></div>'))), loop=6500, still=5000),
      how='<em>Options → References</em>: 4, 8 or 12.', note='Needs a references MCP connected to your agent.'),
    S('fonts', 'Your own fonts', 'Brand fonts just work.',
      'Fonts installed on your computer work: the panel makes those text changes inside Figma, where the Figma MCP can\'t.',
      demo(canvas(sel(*H1), h1_at='4200:bold')
           + plugin(item(12, 'Headline', [('working', None, 4400), ('done', 4400, None)], 'Set the headline in KMR Waldenburg',
                         prog([('Finding KMR Waldenburg on your computer', 300, 3000), ('Changing 1 text layer', 3000, 4200)]))), loop=6500, still=2000),
      note='Family (keeping each weight), size, letter spacing and line height, with Undo. Keep the panel open in that file.'),
])

def fake_select(id_, before, after, at, pt):
    return lambda h: re.sub(rf'<select id="{id_}"[^>]*>.*?</select>',
                            f'<span class="sel-fake" data-pt="{pt}"><span' + a(out=at) + f'>{before}</span><span' + a(in_=at) + f'>{after}</span></span>', h, flags=re.S)

page('options', 'Options', 'Everything behind the Options button. The button shows what is switched on.', [
    S('whole-file', 'Whole page or whole file', 'Every page at once.',
      'Send a note with nothing selected and it is about the page. <em>Applies to → Whole file</em> makes it about every page.',
      demo('<div class="s-pages">' + ''.join(f'<div class="s-pagerow"{a(at=f"{2600 + i * 500}:done")}><i></i>{n}<em>{c} headings</em></div>' for i, (n, c) in enumerate([('Home', 4), ('Pricing', 3), ('About', 2), ('Checkout', 5), ('Account', 2)])) + '</div>'
           + plugin(item(17, 'Whole file', [('working', 2500, 5100), ('done', 5100, None)], 'All headings above 32 pt in Druk', in_=2500),
                    comp=composer('All headings above 32 pt in Druk', 1000, ctx=NOTHING, opts=(None, 900), optline=('whole file', 900),
                                  tweak=lambda h: seg_at(seg_at(h, 'scope', 'file', ' data-pt="wf" data-at="600:on"'), 'scope', 'sel', ' data-at="600:-on"')))
           + cursor('0:560,300;100:@wf;600:click;1800:@send;2400:click'), loop=7000)),
    S('design-system', 'Your design system', 'Your library, or this file.',
      '<em>Build with</em>: any library, this file only, or one library by name. Components and variables first, hard-coded values only when nothing fits.',
      demo(canvas(sel(*CTA), cta_at='3800:blue')
           + plugin(item(18, 'Order ahead', [('working', 2000, 3800), ('done', 3800, None)], 'Make this our primary button',
                         msg('claude', 'Swapped to <b>Button / Primary</b> from your library.', 3800), in_=2000),
                    comp=composer(ctx=('Order ahead', 'Button · 112×32'), opts=(None, 1900), tweak=fake_select('library', 'Any library', 'Brand UI', 900, 'lib')))
           + cursor('0:560,300;300:@lib;900:click'), loop=6500)),
    S('comments', 'Figma comments', 'Works through them.',
      '<em>Comments → Apply</em> makes the changes the open threads ask for. <em>Summarize</em> groups them into themes and a plan you approve first.',
      demo(canvas('<span class="s-cmt" style="left:250px;top:196px">AK</span><span class="s-cmt" style="left:150px;top:300px">MS</span>'
                  '<span class="s-tag" style="left:200px;top:166px"' + a(in_=300) + '>too light?</span><span class="s-tag" style="left:180px;top:330px"' + a(in_=500) + '>use the brand blue</span>', h1_at='3600:bold', cta_at='4400:blue')
           + plugin(item(19, 'Home', [('working', 1900, 4600), ('done', 4600, None)], 'Apply the comments',
                         prog([('Reading 2 open comments', 2000, 3000), ('Making the headline heavier', 3000, 3600), ('Button in color/brand', 3600, 4400)]), in_=1900),
                    comp=composer(ctx=NOTHING, opts=(None, 1500),
                                  tweak=lambda h: seg_at(seg_at(h, 'comments', 'apply', ' data-pt="apply" data-at="900:on"'), 'comments', '', ' data-at="900:-on"')))
           + cursor('0:560,300;300:@apply;900:click'), loop=7000),
      note='Needs a Figma personal access token (scope <em>File comments: read</em>), stored on your computer only.'),
    S('model-and-skill', 'Model and skill', 'A model per note.',
      '<em>Model</em> picks the model that works on the note; <em>Skill</em> picks one of your session\'s skills.',
      demo(canvas(sel(*H1))
           + plugin(item(20, 'Headline', [('working', 2600, None)], 'Rewrite in our voice', '<div class="meta"' + a(in_=2600) + '>Claude Sonnet · skill: brand-voice</div>', in_=2600),
                    comp=composer(opts=(None, 2200), tweak=lambda h: unhide(unhide(fake_select('skill', 'None', 'brand-voice', 1500, 'skill')(fake_select('model', 'Session default', 'Claude Sonnet', 800, 'model')(h)), 'modelRow'), 'skillRow')))
           + cursor('0:560,300;200:@model;800:click;900:@skill;1500:click'), loop=6000),
      note='The lists come from the agent that is watching. <em>Model</em> is hidden when it can\'t hand a note to another model.'),
])

page('in-figma', 'In Figma', 'Retoucher in the file itself.', [
    S('markers', 'Canvas markers', 'Notes on the canvas.',
      'Each open note puts a native annotation on its layers (“Claude #3 · Waiting”) that follows its status and goes away when it is done.',
      demo(canvas(sel(*H1, out=4600)
                  + '<span class="s-annot" style="left:36px;top:186px"' + a(in_=600, out=1900) + '>Claude #3 · Waiting</span>'
                  + '<span class="s-annot" style="left:36px;top:186px"' + a(in_=1900, out=4300) + '>Claude #3 · Working</span>', h1_at='4300:bold')
           + plugin(item(3, 'Headline', [('pending', 600, 1900), ('working', 1900, 4300), ('done', 4300, None)], 'Make it bolder', in_=600)), loop=6500),
      note='Turn them off with <em>Options → Show markers on canvas</em>. Other people\'s annotations are never touched.'),
    S('select-to-find', 'Select to find', 'Click a layer, see its note.',
      'Select a layer on the canvas and its note lights up in the panel. Click a note to select its layers.',
      demo(canvas(sel(*H1, in_=900, out=3300) + sel(*CTA, in_=3500))
           + plugin(item(12, 'Headline', [('done', None, None)], 'Make it bolder', at='900:hit;3300:-hit')
                    + item(13, 'Order ahead', [('done', None, None)], 'Warmer button', at='3500:hit'))
           + cursor(f'0:300,420;200:{H1_AT};850:click;2700:{CTA_AT};3300:click'), loop=6000)),
    S('small-mode', 'Small mode', 'Shrink it to a bar.',
      'Shrink the panel to a small bar you can park anywhere. It still tells you when a note needs you.',
      demo(canvas()
           + plugin(item(14, 'Hero', [('question', None, None)], 'Make it calmer'),
                    perms=bubble_question('Which headline size?', [('48 pt', 'one step down'), ('40 pt', 'two steps down')]),
                    at='900:mini;4400:-mini', mini='<span class="ask">1 needs an answer</span>')
           + cursor('0:560,300;200:@shrink;800:click;3200:@bar;3800:click'), loop=6500, still=2500),
      how='The shrink button in the header; click the bar to open the panel again. It opens the way you left it.'),
])

TROUBLE = [
    ['Panel says <em>Not connected</em>', 'Open your agent; the plugin starts the bridge when a session starts. Check <code>curl localhost:4747/health</code>.'],
    ['Panel says <em>Not paired</em>', 'Another Figma panel paired first. Ask your agent to run <code>retoucher unpair</code>, then reopen the panel.'],
    ['Notes stay <em>Waiting</em>', 'The panel says <em>Not watching</em>: start watching (<code>/retoucher:watch</code> in Claude Code).'],
    ['Port 4747 is in use', 'Your agent says so when a session starts. Free the port.'],
    ['The agent can\'t edit the file', 'The Figma MCP isn\'t connected to your agent, or your Figma seat has no edit access to the file.'],
    ['Send stays disabled', 'It needs a note and the file\'s link: paste the link when the panel asks (once per file).'],
]
page('troubleshooting', 'Troubleshooting', 'The usual cases, and the fix.', [
    S('common', 'Common problems', '', 'Most problems are one of these.', html_=table(TROUBLE, ['Symptom', 'Fix'])),
    S('help', 'Still stuck?', '', 'Open an issue on <a href="https://github.com/alicorak/retoucher/issues">GitHub</a> with what the panel says and what your agent printed.'),
])

# ── page shell ──────────────────────────────────────────

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'

def shell(title, desc, path, depth, body):
    up = '../' * depth
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:image" content="{SITE}/assets/og.png">
  <link rel="canonical" href="{SITE}/{path}">
  <link rel="icon" href="{up}assets/icon.png" type="image/png">
  {FONTS}
  <link rel="stylesheet" href="{up}styles.css">
  <link rel="stylesheet" href="{up}docs/panel.css">
  <link rel="stylesheet" href="{up}docs/docs.css">
</head>
<body>
<header class="d-top">
  <a class="d-brand" href="{up}"><img src="{up}assets/icon.png" width="24" height="24" alt="">Retoucher <span>Docs</span></a>
  <nav><a href="{up}docs/get-started/">Get started</a><a href="https://github.com/alicorak/retoucher">GitHub</a><a href="{up}">Home</a></nav>
</header>
{body}
<script src="{up}timeline.js" defer></script>
</body>
</html>
'''

def plain(s):
    return re.sub(r'<[^>]+>', '', s)

def nav(cur, up):
    out = []
    for p in PAGES:
        here = p['slug'] == cur
        subs = ''.join(f'<li><a href="{up}docs/{p["slug"]}/#{s["id"]}">{s["title"]}</a></li>' for s in p['sections']) if here else ''
        out.append(f'<li><a href="{up}docs/{p["slug"]}/"{" aria-current=\"page\"" if here else ""}>{p["title"]}</a>{f"<ul>{subs}</ul>" if subs else ""}</li>')
    return '<nav class="d-nav" aria-label="Docs"><ul>' + ''.join(out) + '</ul></nav>'

def section(s):
    parts = [f'<h2><a href="#{s["id"]}">{s["title"]}</a></h2>', f'<p class="d-line">{s["line"]}</p>']
    if s['html']:
        parts.append(s['html'])
    if s['demo']:
        parts.append(s['demo'])
    if s['how']:
        parts.append(f'<p class="d-how"><span>How</span>{s["how"]}</p>')
    if s['note']:
        parts.append(f'<p class="d-note">{s["note"]}</p>')
    return f'<section class="d-feat" id="{s["id"]}">' + ''.join(parts) + '</section>'

def topic(p):
    i = PAGES.index(p)
    prev, nxt = (PAGES[i - 1] if i else None), (PAGES[i + 1] if i + 1 < len(PAGES) else None)
    pn = ('<nav class="d-pn">' + (f'<a href="../{prev["slug"]}/"><span>Previous</span>{prev["title"]}</a>' if prev else '<span></span>')
          + (f'<a class="next" href="../{nxt["slug"]}/"><span>Next</span>{nxt["title"]}</a>' if nxt else '') + '</nav>')
    toc = '' if len(p['sections']) < 3 else '<p class="d-toc">' + ''.join(f'<a href="#{s["id"]}">{s["title"]}</a>' for s in p['sections']) + '</p>'
    body = f'''<div class="d-wrap">
{nav(p["slug"], "../../")}
<main class="d-main">
  <div><p class="d-eyebrow">Docs <a class="d-all" href="../">· All topics</a></p><h1>{p["title"]}</h1></div>
  <p class="d-lead">{p["lead"]}</p>
  {toc}
  {"".join(section(s) for s in p["sections"])}
  {pn}
</main>
</div>'''
    return shell(f'{p["title"]} · Retoucher Docs', plain(p['lead']), f'docs/{p["slug"]}/', 2, body)

def overview():
    groups = ''.join(
        f'<section class="d-group"><h2><a href="{p["slug"]}/">{p["title"]}</a></h2><p class="d-line">{p["lead"]}</p><div class="d-cards">'
        + ''.join(f'<a href="{p["slug"]}/#{s["id"]}"><b>{s["title"]}</b><span>{s["sub"]}</span></a>' for s in p['sections'] if s['sub'])
        + '</div></section>' for p in PAGES)
    body = f'''<div class="d-wrap">
{nav(None, "../")}
<main class="d-main">
  <div><p class="d-eyebrow">Docs</p><h1>How Retoucher works</h1></div>
  <p class="d-lead">Every feature in a short demo and a line or two. New here? Start with <a href="get-started/">Get started</a>.</p>
  <div class="d-groups">{groups}</div>
</main>
</div>'''
    return shell('Docs · Retoucher', 'How every Retoucher feature works, in short demos.', 'docs/', 1, body)

def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text)

# folders of pages that no longer exist go
keep = {p['slug'] for p in PAGES}
for d in os.listdir(os.path.join(ROOT, 'docs')):
    full = os.path.join(ROOT, 'docs', d)
    if os.path.isdir(full) and d not in keep:
        for f in os.listdir(full):
            os.remove(os.path.join(full, f))
        os.rmdir(full)

write('docs/panel.css', '/* Generated by scripts/build-docs.py from the plugin\'s ui.html: its CSS, scoped to .pp. Don\'t edit. */\n' + site_leaks() + '\n' + PANEL_CSS + '\n')
write('docs/index.html', overview())
for p in PAGES:
    write(f'docs/{p["slug"]}/index.html', topic(p))
urls = ['/', '/docs/'] + [f'/docs/{p["slug"]}/' for p in PAGES]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      + ''.join(f'<url><loc>{SITE}{u}</loc></url>' for u in urls) + '</urlset>\n')
llms = open(os.path.join(ROOT, 'llms.txt')).read()
docs = '\n'.join(f'- [{p["title"]}]({SITE}/docs/{p["slug"]}/): ' + plain(p['lead']) for p in PAGES)
llms = re.sub(r'\n## Docs\n.*', '', llms, flags=re.S).rstrip('\n') + '\n\n## Docs\n\n' + docs + '\n'
write('llms.txt', llms)
print(len(PAGES), 'pages,', sum(len(p['sections']) for p in PAGES), 'sections')
