#!/usr/bin/env python3
"""Builds docs/ (one page per feature) from the content below.

Run from the site root:  python3 scripts/build-docs.py
Each demo is a 720x450 scene; timeline.js plays the data-in / data-type / data-at / data-path timeline.
"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://retoucher.alicorak.com'

# ── scene parts ─────────────────────────────────────────

def a(**kw):
    """timeline attributes: in_, out, type_, at, path"""
    m = {'in_': 'data-in', 'out': 'data-out', 'type_': 'data-type', 'at': 'data-at', 'path': 'data-path'}
    return ''.join(f' {m[k]}="{v}"' for k, v in kw.items() if v is not None)

def cursor(path):
    return f'<i class="s-cur"{a(path=path)}></i>'

def canvas(extra='', h1_at=None, cta_at=None, name='Home'):
    return (f'<div class="s-canvas"><div class="s-frame"><span class="s-fname">{name}</span><div class="s-art">'
            '<div class="s-nav"><span>Morning</span><span>Menu · Visit · Shop</span></div>'
            f'<p class="s-h1"{a(at=h1_at)}>Slow mornings,<br>good coffee.</p>'
            f'<span class="s-cta"{a(at=cta_at)}>Order ahead →</span>'
            f'</div></div>{extra}</div>')

def sel(x, y, w, h, **kw):
    return f'<div class="s-sel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"{a(**kw)}></div>'

H1_SEL = (48, 210, 268, 80)      # the headline on the canvas
CTA_SEL = (48, 312, 122, 40)     # the button

def top(num, label, pills):
    """pills: [(kind, text, in, out)] kind = working | warn | ok"""
    ps = ''.join(f'<span class="pill pill-{k}"{a(in_=i, out=o)}><i class="dot"></i>{t}</span>' for k, t, i, o in pills)
    return (f'<div class="note-top"><span class="nt"><span class="nt-num"><img src="../../assets/hash.svg" width="14" height="14" alt="#">{num}</span>'
            f'<span>{label}</span></span><span class="s-pills">{ps}</span></div>')

def note(text, in_=None, out=None):
    return f'<p class="note-text"{a(in_=in_, out=out)}>{text}</p>'

def steps(items):
    """items: [(text, in, done_at)]"""
    lis = ''.join(f'<li{a(in_=i, at=(f"{d}:done" if d is not None else None))}>'
                  '<img class="sp spin" src="../../assets/loader.svg" width="14" height="14" alt="">'
                  f'<img class="ck" src="../../assets/check-faint.svg" width="14" height="14" alt="">{t}</li>' for t, i, d in items)
    return f'<ul class="steps">{lis}</ul>'

def reply(text, in_=None, label='Claude', extra=''):
    return f'<div class="s-reply"{a(in_=in_)}><small>{label}</small>{text}{extra}</div>'

def perm(title, in_=None, out=None, label='Asks for permission'):
    return f'<div class="perm"{a(in_=in_, out=out)}><span class="mono">{label}</span><strong>{title}</strong></div>'

def perm_actions(in_=None, out=None, at=None):
    return (f'<div class="perm-actions"{a(in_=in_, out=out)}><span class="pbtn">Decline</span>'
            f'<span class="pbtn-group"><span class="pbtn">Always allow</span><span class="pbtn dark" data-pt="allow"{a(at=at)}>Allow once</span></span></div>')

NOTHING = ('Nothing selected', 'The note is about the page.')

def composer(typed='', type_at=None, ctx=('Headline', 'Text · Home'), ctx2=None, ctx2_at=None, above='', tools=''):
    add = '<span class="s-add" data-pt="add">+</span>'
    c = f'<div class="s-ctx"{a(out=ctx2_at) if ctx2 else ""}><i></i><span>{ctx[0]}<small>{ctx[1]}</small></span>{add}</div>'
    if ctx2:
        c += f'<div class="s-ctx"{a(in_=ctx2_at)}><i></i><span>{ctx2[0]}<small>{ctx2[1]}</small></span>{add}</div>'
    t = f'<span class="typed"{a(type_=type_at)}>{typed}</span>' if typed else ''
    return (f'<div class="s-comp">{above}{c}<div class="field" data-pt="field"><span class="ph">What should change?</span>{t}'
            '<span class="send" data-pt="send"><img src="../../assets/arrow-up-white.svg" width="20" height="20" alt=""></span></div>'
            f'{tools}</div>')

def panel(notes, comp=None, pop=''):
    return ('<div class="s-panel"><div class="s-head"><b>Retoucher</b><span class="status">'
            '<img src="../../assets/logo-claude-ok.svg" width="14" height="14" alt="">Ready</span></div>'
            f'<div class="s-notes">{"".join(notes)}</div>{comp if comp is not None else composer()}{pop}</div>')


# ── pages ───────────────────────────────────────────────

GROUPS = ['Start', 'Write a note', 'While it works', 'What it changes', 'Options', 'In Figma']
P = []

def page(slug, group, title, sub, lead, how, know, scene, loop=8000, still=None):
    P.append(dict(slug=slug, group=group, title=title, sub=sub, lead=lead, how=how, know=know, scene=scene, loop=loop, still=still))

# Start
page('get-started', 'Start', 'Get started', 'Set it up in a minute.',
     'Retoucher has two halves: an agent plugin that runs on your computer, and the panel inside Figma. Your agent installs the first one for you.',
     ['Copy the setup prompt below and paste it into Claude Code, Codex or Cursor.',
      'Your agent installs the Retoucher agent plugin, starts a small bridge on your computer and checks that Node.js 18+ and the Figma MCP are ready.',
      'Add the Figma plugin. It is waiting for Figma Community review, so for now your agent shows you a <code>manifest.json</code> to import in the Figma desktop app: <em>Plugins → Development → Import plugin from manifest…</em>',
      'Open it from <em>Plugins → Development → Retoucher</em> and paste the file\'s link once when the panel asks.',
      'Start watching: <code>/retoucher:watch</code> in Claude Code, or ask Codex or Cursor to “watch my Figma notes”. The panel says <em>Ready</em>.'],
     ['The panel\'s top right tells you where things stand: <em>Ready</em> (an agent is watching), <em>Not watching</em> (notes wait until you start watching), <em>Not connected</em> (no agent session is open).',
      'You need edit access to the Figma files you want to change.',
      'Stuck? The <a href="https://github.com/alicorak/retoucher#troubleshooting">troubleshooting table</a> covers the usual cases.'],
     '<div class="s-term"><span class="who">Your agent</span>'
     '<span class="ok"' + a(in_=700) + '>Retoucher installed</span>'
     '<span class="ok"' + a(in_=1500) + '>Bridge running on localhost:4747</span>'
     '<span class="ok"' + a(in_=2300) + '>Figma MCP connected</span>'
     '<span class="ok"' + a(in_=3100) + '>Figma plugin ready to import</span>'
     '<span class="ok"' + a(in_=4300) + '>Watching your notes</span></div>'
     + '<div class="s-panel"><div class="s-head"><b>Retoucher</b><span class="status" style="color:var(--muted)"' + a(out=4300) + '><i class="dot" style="background:#d6453d"></i>Not connected</span>'
     '<span class="status"' + a(in_=4300) + '><img src="../../assets/logo-claude-ok.svg" width="14" height="14" alt="">Ready</span></div>'
     '<div class="s-notes" style="justify-content:center;text-align:center;color:var(--muted);font-size:13px"><p' + a(out=4300) + '>Waiting for your agent…</p><p' + a(in_=4500) + '>Select a layer and write what should change.</p></div>' + composer(ctx=NOTHING) + '</div>',
     loop=7500)

page('agents', 'Start', 'Your own agent', 'Claude Code, Codex, Cursor.',
     'Retoucher doesn\'t bring its own AI. The coding agent you already use reads your notes, edits the file through the Figma MCP and answers in the panel.',
     ['Install the Retoucher agent plugin in the agent you use (see <a href="../get-started/">Get started</a>).',
      'Open that agent in any folder. Opening a session starts the bridge, so the panel connects by itself.',
      'Start watching. Claude Code: <code>/retoucher:watch</code>. Codex or Cursor: ask it to “watch my Figma notes”.',
      'Send notes from the panel. The agent picks each one up as it arrives.'],
     ['It works on your agent\'s own account and plan; Retoucher calls no AI service itself.',
      'Claude Code uses the <code>retoucher</code> command; Codex and Cursor use the same actions as tools of the <code>retoucher</code> MCP server.',
      'Notes live in <code>~/.retoucher</code>, shared by every agent, so you can switch agents and keep your notes.'],
     '<div class="s-node" style="left:24px;top:40px"' + a(in_=200) + '><span style="display:flex;gap:8px"><img src="../../assets/logo-claude.svg" width="18" height="18" alt=""><img src="../../assets/logo-openai.svg" width="18" height="18" alt=""><img src="../../assets/logo-cursor.svg" width="18" height="18" alt=""></span>Your agent<small>Claude Code, Codex or Cursor</small></div>'
     '<div class="s-term" style="top:170px;height:240px"' + a(in_=600) + '><span class="who">watching</span>'
     '<span' + a(in_=1400) + '>NEW #12 Make the headline bolder</span>'
     '<span class="ok"' + a(in_=2400) + '>Edited 1 text layer</span>'
     '<span class="ok"' + a(in_=3400) + '>Replied in the panel</span></div>'
     + panel([top(12, 'Headline', [('working', 'Waiting', 900, 2000), ('working', 'Working', 2000, 3400), ('ok', 'Done', 3400, None)]),
              note('Make the headline bolder', 900),
              reply('Done. The headline is now Bold.', 3400)]),
     loop=7000)

page('privacy', 'Start', 'Stays on your computer', 'Notes stay local.',
     'The panel talks to a bridge on your own computer and nothing else. Notes, screenshots and files never leave your machine.',
     ['The agent plugin starts the bridge on <code>localhost:4747</code> when your agent opens.',
      'The first Figma panel that connects pairs with the bridge and gets a key.',
      'From then on the bridge only answers requests that carry that key.'],
     ['Notes, screenshots and attachments are kept in <code>~/.retoucher</code>.',
      'Websites you visit can reach <code>localhost</code> too, so the key matters: without it a page can\'t read or send notes, or answer permission prompts.',
      'Need to pair another panel? Ask your agent to run <code>retoucher unpair</code>.',
      'The Figma comments option uses your personal Figma token, stored on your computer only.'],
     '<div class="s-wire" style="left:184px;top:214px;width:96px"></div><div class="s-wire" style="left:440px;top:214px;width:96px"></div>'
     '<div class="s-node" style="left:24px;top:170px;width:160px">Figma panel<small>in your Figma</small></div>'
     '<div class="s-node" style="left:280px;top:170px;width:160px">Bridge<small>localhost:4747</small></div>'
     '<div class="s-node" style="left:536px;top:170px;width:160px">Your agent<small>on your computer</small></div>'
     '<i class="s-dot"' + a(at='0:p0;900:-p0;900:p1;1800:-p1;1800:p2;2700:-p2;2700:p3;3600:-p3') + '></i>'
     '<div class="s-node" style="left:200px;top:320px;width:320px;align-items:center;color:var(--gray);font-weight:400;font-size:13px;box-shadow:none;background:none">Notes, screenshots and files stay in ~/.retoucher</div>',
     loop=4500)

# Write a note
page('notes', 'Write a note', 'Notes on layers', 'Write it like a comment.',
     'Select a layer, write what should change and send. It works like a Figma comment, except your agent does the change.',
     ['Select one or more layers on the canvas, or nothing for the whole page.',
      'Write the change in the box at the bottom of the panel.',
      'Press <em>Send</em> (<kbd>↵</kbd>). <kbd>⇧↵</kbd> starts a new line.',
      'The note appears in the panel and moves through <em>Waiting → Working → Done</em>.'],
     ['Select the exact layer you mean. A selection that covers a whole row of screens is ambiguous, and the agent will ask.',
      'Notes read like a chat, newest at the bottom. Click a note to jump to its layers.',
      'The first time, paste the file\'s link when the panel asks: Figma doesn\'t tell plugins which file is open.'],
     canvas(sel(*H1_SEL, in_=900), h1_at='4600:bold')
     + panel([top(12, 'Headline', [('working', 'Waiting', 3100, 3800), ('working', 'Working', 3800, 4600), ('ok', 'Done', 4600, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=3100)),
              note('Make it bolder', 3100)],
             composer('Make it bolder', 1500, ctx2=('Headline', 'Text · Home'), ctx2_at=900))
     + cursor('0:560,300;300:180,240;800:click;1300:@field;2400:@send;2900:click'),
     loop=7000)

page('areas', 'Write a note', 'Areas and pins', 'Drag an area or drop a pin.',
     'Point at a part of a screen instead of a layer: drag a box around it or drop a pin, like a pinned Figma comment.',
     ['Select a frame, or nothing for what is on screen.',
      'Press <em>Mark area</em> next to the selection in the panel. A big picture of the frame opens.',
      'Drag to mark an area, or click to drop a pin. Add as many as you need.',
      'Press <em>Add</em>, then write the note and send.'],
     ['The agent gets each area\'s crop, its position, the screen it sits in and the layer underneath.',
      'Number your areas in the note (“1: less glare, 2: bolder”) when you mark more than one.',
      '<kbd>Backspace</kbd> removes the last mark.'],
     '<div class="s-picker"><div class="bar"><span>Mark areas</span><span style="color:var(--muted);font-weight:400">Drag for an area, click for a pin</span><span class="pbtn dark" style="height:26px" data-pt="addarea">Add</span></div>'
     '<div class="stage"><div class="s-box s-grow" style="left:360px;top:60px;width:240px;height:110px"' + a(in_=700, at='800:big') + '><b>1</b></div>'
     '<span class="s-tag" style="left:400px;top:24px"' + a(in_=1600) + '>less glare here</span>'
     '<div class="s-box" style="left:120px;top:250px;width:20px;height:20px;border-radius:50%"' + a(in_=2650) + '><b>2</b></div>'
     '<span class="s-tag" style="left:150px;top:252px"' + a(in_=3200) + '>bolder</span></div></div>'
     + cursor('0:300,260;100:372,112;700:click;800:612,222;2000:142,312;2600:click;3200:@addarea;3800:click'),
     loop=6000)

page('targets', 'Write a note', 'Several targets', 'Layers across pages.',
     'One note can be about several layers, even on different pages. Each keeps its own screenshot.',
     ['Select the first layer and press <em>+</em> (Add selection) in the panel.',
      'Select the next one, on this page or another, and press <em>+</em> again.',
      'Write the note once and send it.'],
     ['If you add nothing, the current selection is used.',
      'Handy for “make these match”: the agent sees every target side by side.'],
     canvas(sel(*H1_SEL, in_=650, out=1900) + sel(*CTA_SEL, in_=2300))
     + panel([], composer('Make these two match', 4300, ctx=NOTHING, above='<div style="display:flex;gap:6px;flex-wrap:wrap"><span class="s-chip"' + a(in_=1500) + '><i></i>Headline · Home</span><span class="s-chip"' + a(in_=3300) + '><i></i>Order ahead · Home</span></div>'))
     + cursor('0:400,380;100:180,240;650:click;900:@add;1450:click;1700:100,330;2300:click;2700:@add;3300:click;3900:@field'),
     loop=7000)

page('files', 'Write a note', 'Photos and files', 'Drop in screenshots.',
     'Attach a reference photo, a PDF brief or a screenshot to the note. The agent opens them with the note.',
     ['Drop files anywhere on the panel, paste them (screenshots too), or press the clip button.',
      'They appear under the note as chips; remove one with its ×.',
      'Write the note and send.'],
     ['Up to 8 files per note, 12 MB each. Photos are scaled to 1600 px.',
      'Any file type works: images, PDFs, text, design specs.'],
     canvas(sel(*H1_SEL, in_=300))
     + '<div class="s-tag" style="left:150px;top:380px;padding:8px 10px"' + a(in_=500, out=1700) + '>moodboard.jpg</div>'
     + panel([], composer('Match the mood of this photo', 2600, ctx=('Headline', 'Text · Home'), above='<div style="display:flex;gap:6px"><span class="s-chip"' + a(in_=1700) + '><i></i>moodboard.jpg</span><span class="s-chip"' + a(in_=2200) + '>brief.pdf</span></div>'))
     + cursor('0:180,388;500:180,388;1100:560,300;1700:click'),
     loop=6500)

page('mentions', 'Write a note', '@mentions', 'Use your variables.',
     'Type @ in a note to pick a variable, style or component. The agent uses exactly the one you named.',
     ['Type <kbd>@</kbd> in the note box.',
      'Keep typing to filter, then pick a variable, text style, effect style, component or library.',
      'The mention is added to the note; send it as usual.'],
     ['Library components show up once they are used on the page.',
      'Mentions are listed under the note, so you can see what the agent was given.'],
     canvas(sel(*CTA_SEL, in_=300), cta_at='5200:blue')
     + panel([top(14, 'Order ahead', [('working', 'Working', 4400, 5200), ('ok', 'Done', 5200, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=4400)),
              note('Use <span class="mention">@color/brand</span> for the button', 4400)],
             composer('Use @color/brand for the button', 900, ctx=('Order ahead', 'Button · Home')),
             pop='<div class="s-pop"' + a(in_=1250, out=2600) + '><span class="lbl">Variables</span><span class="row"><i style="background:#111"></i>color/ink</span>'
                 '<span class="row" data-pt="brand"' + a(at='1700:hi') + '><i style="background:#1f78ff"></i>color/brand</span><span class="row"><i style="background:#f6f6f5;box-shadow:inset 0 0 0 1px #ddd"></i>color/paper</span></div>')
     + cursor('0:@field;1800:@brand;2400:click;3500:@send;4100:click'),
     loop=7500)

page('quick-action', 'Write a note', 'Quick action', '⌘/ and type.',
     'Send a note without opening the panel: from Figma\'s own quick actions, with whatever is selected.',
     ['Select the layers the note is about.',
      'Press <kbd>⌘/</kbd> in Figma and type “Retoucher”.',
      'Press <kbd>Tab</kbd>, write the note and press <kbd>↵</kbd>.'],
     ['The note goes out with the current selection, exactly like one sent from the panel.',
      'Open the panel later to follow the note and read the answer.'],
     canvas(sel(*H1_SEL, in_=200), h1_at='5600:bold')
     + '<div class="s-qa"' + a(in_=900, out=4600) + '><div class="q"><span>⌘/</span><span' + a(type_=1200) + '>Retoucher</span></div>'
     '<div class="r hi"' + a(in_=1700, out=2600) + '>Retoucher · Note</div>'
     '<div class="q"' + a(in_=2600) + '><span>Note</span><span' + a(type_=2800) + '>Tighten the letter spacing</span></div></div>'
     '<div class="s-toast"' + a(in_=4600, out=6400) + '>Sent to Retoucher</div>',
     loop=7500)

page('batches', 'Write a note', 'Batches', 'Send a few at once.',
     'Collect several notes, then send them together. The agent works through them in order, or at the same time when they don\'t depend on each other.',
     ['Write a note and press <em>Batch</em> (<kbd>⇧⌘↵</kbd>) instead of Send.',
      'Repeat for the other notes; they wait in the batch list.',
      'Press <em>Send all</em>. Turn on <em>At the same time</em> if the notes are independent.'],
     ['Each note in a batch still gets its own status, steps and Undo.',
      'Clear the batch any time before sending.'],
     canvas(sel(*H1_SEL, in_=200))
     + panel([], composer('', None, ctx=('Headline', 'Text · Home'),
                          above='<div class="s-reply" style="max-width:none;align-self:stretch;border-radius:16px;background:var(--brand-soft);border:0"' + a(in_=1200) + '><small>Batch</small>'
                                '<span style="display:block"' + a(in_=1200) + '>1. Make it bolder</span><span style="display:block"' + a(in_=2600) + '>2. Shorter, one line</span><span style="display:block"' + a(in_=4000) + '>3. Warmer button</span>'
                                '<span class="pbtn dark" style="height:26px;margin-top:8px" data-pt="sendall"' + a(in_=4200) + '>Send all</span></div>',
                          tools='<div class="s-tools"><span class="grow"></span><span class="s-chip" data-pt="batch"' + a(at='1000:hi') + '>Batch</span></div>'))
     + cursor('0:560,300;450:@batch;1000:click;1950:@batch;2500:click;3350:@batch;3900:click;4400:@sendall;5000:click'),
     loop=7000)

# While it works
page('steps', 'While it works', 'Live steps', 'See it work, as it goes.',
     'While the agent works, the note shows the step it is on and the last ones it finished.',
     ['Send a note. When the agent picks it up the note says <em>Working</em>.',
      'Each step appears under the note as it happens.',
      'When it is done, the steps fold into “N steps” under the reply.'],
     ['Steps are written in your words, not the agent\'s: “Finding KMR Waldenburg on your computer”.',
      'Want to change course? Write under the note while it works (see <a href="../talk/">Talk while it works</a>).'],
     canvas(sel(*H1_SEL), h1_at='4600:bold')
     + panel([top(12, 'Headline', [('working', 'Working', None, 4800), ('ok', 'Done', 4800, None)]),
              note('Set the headline in KMR Waldenburg'),
              steps([('Reading the headline', 300, 1300), ('Finding KMR Waldenburg on your computer', 1300, 2800), ('Changing 1 text layer', 2800, 4600)]),
              reply('Done, in KMR Waldenburg.', 4800)]),
     loop=7000, still=4000)

page('talk', 'While it works', 'Talk while it works', 'Reply mid-task.',
     'Write under any note at any time, also while the agent is working. It gets the message right away.',
     ['Hover a note and press the reply arrow, or write in the box that opens under it.',
      'Send the message. It shows in the note like a chat.',
      'The agent reads it before its next step and adjusts.'],
     ['A note that is done stays open for follow-ups: “Not quite right? Say why…”.',
      'Use it to correct course instead of starting a new note.'],
     canvas(sel(*H1_SEL))
     + panel([top(12, 'Headline', [('working', 'Working', None, None)]),
              note('Set the headline in KMR Waldenburg'),
              steps([('Finding KMR Waldenburg on your computer', None, 800), ('Changing 1 text layer', 800, None)]),
              note('Keep the size as it is', 2900),
              reply('Got it, I\'ll keep the size.', 3800)],
             composer('Keep the size as it is', 1100, ctx=('Headline', 'Text · Home')))
     + cursor('0:@field;2200:@send;2800:click'),
     loop=6500)

page('questions', 'While it works', 'Questions and plans', 'Answer in the panel.',
     'When the agent needs a decision, it asks in the panel. Pick an answer, or write your own, and it carries on.',
     ['A question card appears under the note with the options the agent proposes.',
      'Pick one (or several), or write your own answer, and press <em>Send answer</em>.',
      'For bigger changes the agent can show a plan first: <em>Approve plan</em> or <em>Change</em> with a note.'],
     ['Turn on <em>Options → Show a plan first</em> to see the plan before anything changes.',
      'Open questions it asks in the note itself: answer in the box under the note.'],
     canvas(sel(*H1_SEL), h1_at='5000:bold')
     + panel([top(14, 'Hero', [('warn', 'Needs answer', None, 4200), ('working', 'Working', 4200, None)]),
              '<div class="perm" style="align-self:stretch;gap:8px"' + a(out=4200) + '><span class="mono">Asks you</span><strong>Which headline size?</strong>'
              '<span class="opt" data-pt="opt1"' + a(at='1800:on') + '><i></i>48 pt · one step down</span><span class="opt"><i></i>40 pt · two steps down</span></div>'
              '<div class="opt-actions"' + a(out=4200) + '><span class="pbtn">Skip</span><span class="pbtn dark" data-pt="answer">Send answer</span></div>',
              steps([('Setting the headline to 48 pt', 4400, None)])])
     + cursor('0:560,420;1200:@opt1;1800:click;2900:@answer;3500:click'),
     loop=7000, still=2600)

page('approve', 'While it works', 'Approve', 'Allow once, always, or decline.',
     'When the agent needs permission for a tool, the question shows in the panel. No need to go back to the agent\'s window.',
     ['A permission card appears under the note: what the agent wants to do.',
      'Press <em>Allow once</em>, <em>Always allow</em> or <em>Decline</em>.',
      'The agent continues (or stops) right away.'],
     ['<em>Always allow</em> saves the same rule your agent\'s “don\'t ask again” would.',
      'If the panel is closed or nobody answers within 2 minutes, the agent asks in its own window as usual.',
      'In Cursor this covers MCP tools (the Figma edits); shell commands are still approved in Cursor.'],
     canvas(sel(*H1_SEL), h1_at='4400:bold')
     + panel([top(12, 'Headline', [('working', 'Working', None, None)]),
              note('Make it a bit bolder'),
              steps([('Reading the headline', None, 0)]),
              perm('Edit the Figma file', 600, 3100),
              perm_actions(600, 3100, at='2800:pick'),
              steps([('Changing 1 text layer', 3200, None)])])
     + cursor('0:560,300;1500:@allow;2800:click'),
     loop=6500, still=2400)

# What it changes
page('fonts', 'What it changes', 'Your own fonts', 'Brand fonts just work.',
     'The Figma MCP can\'t load fonts installed on your computer. Retoucher can: the agent sends text changes to the panel, which runs them inside your Figma.',
     ['Write a note that touches type: “Set the headline in KMR Waldenburg”.',
      'The agent looks the font up among the fonts your Figma sees.',
      'The panel changes the text in Figma: family (keeping each weight), size, letter spacing, line height.'],
     ['Keep the panel open in that file while the agent works.',
      'Undo works for these changes too.'],
     canvas(sel(*H1_SEL), h1_at='4200:bold')
     + panel([top(12, 'Headline', [('working', 'Working', None, 4400), ('ok', 'Done', 4400, None)]),
              note('Set the headline in KMR Waldenburg'),
              '<div class="s-pop" style="position:static;box-shadow:0 0 0 1px var(--border)"' + a(in_=800, out=3000) + '><span class="lbl">Fonts on this computer</span><span class="row">Inter</span><span class="row"' + a(at='1800:hi') + '>KMR Waldenburg<span style="margin-left:auto" class="s-mono">Local</span></span><span class="row">GT Pressura Mono</span></div>',
              steps([('Finding KMR Waldenburg on your computer', 300, 3000), ('Changing 1 text layer', 3000, 4200)])]),
     loop=6500, still=2000)

page('undo', 'What it changes', 'Undo', 'One click back.',
     'Every finished note shows a before and after picture. <em>Undo</em> puts the old values back, even when the agent is offline.',
     ['Open a finished note to see <em>Before</em> and <em>After</em>.',
      'Not happy? Press <em>Undo</em>.',
      'The layers go back to how they were and the note says <em>Reverted</em>.'],
     ['The agent records the old values before it edits: layer properties, styles, instance properties and swaps, variable bindings, variables, moved and new layers.',
      'Changes the agent couldn\'t record show no Undo button.'],
     canvas(sel(*H1_SEL), h1_at='0:bold;2600:-bold')
     + panel([top(11, 'Headline', [('ok', 'Done', None, 2600), ('working', 'Reverted', 2600, None)]),
              note('Make it bolder'),
              '<div class="s-ba"><div style="font-weight:500">Slow mornings</div><div>Slow mornings</div></div>'
              '<div style="display:flex;justify-content:space-between" class="s-mono"><span>Before</span><span style="width:50%">After</span></div>',
              '<span class="undo" style="align-self:flex-start" data-pt="undo"' + a(out=2600) + '><img src="../../assets/rotate-ccw.svg" width="14" height="14" alt="">Undo</span>'])
     + cursor('0:560,250;1200:@undo;2400:click'),
     loop=5500, still=1500)

page('versions', 'What it changes', 'Versions', 'Two to four directions, side by side.',
     'Ask for 2 to 4 versions and the agent makes that many different directions next to your selection. The original stays as it is.',
     ['Select the frame.',
      'Open <em>Options → Versions</em> and pick 2, 3 or 4.',
      'Write what you\'re after (“three moods for the hero”) and send.',
      'The copies appear side by side on the canvas.'],
     ['Each version is a real, editable copy, not a picture.',
      'Pick the one you like and delete the others, or keep going with a follow-up.'],
     '<div class="s-copies"><div class="s-copy"><small>Original</small><p>Slow mornings</p></div>'
     '<div class="s-copy"' + a(in_=3200) + '><small>v1</small><p style="font-weight:800">Slow mornings</p></div>'
     '<div class="s-copy dark"' + a(in_=3700) + '><small>v2</small><p>Slow mornings</p></div></div>'
     + panel([top(15, 'Hero', [('working', 'Working', 2800, 3800), ('ok', 'Done', 3800, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=2800)),
              note('Two moods for the hero', 2800)],
             composer('Two moods for the hero', 1300, ctx=('Hero', 'Frame · Home'),
                      above='<div class="s-opt"><span>Versions</span><span class="s-seg"' + a(at='800:moved') + '><span class="on">1</span><span data-pt="v2"' + a(at='800:pick') + '>2</span><span>3</span><span>4</span></span></div>'))
     + cursor('0:560,300;200:@v2;800:click;2200:@send;2700:click'),
     loop=6500)

page('references', 'What it changes', 'References', 'Matching screens, from any MCP.',
     'Ask for references and the agent first finds matching screens through a references MCP you have connected, puts them next to your selection, then makes the change on a copy.',
     ['Connect a references MCP to your agent (Mobbin, for example).',
      'Open <em>Options → References</em> and pick 4, 8 or 12.',
      'Send the note. The references land next to your selection and show in the reply as thumbnails.'],
     ['Thumbnails open the screen at its source.',
      'Without a references MCP the agent says so in the reply and stops.'],
     canvas(sel(*H1_SEL))
     + panel([top(16, 'Hero', [('working', 'Working', None, 3200), ('ok', 'Done', 3200, None)]),
              note('Find a calmer direction'),
              steps([('Looking for references', 300, 1800), ('Placing 4 of 4', 1800, 3000)]),
              reply('Four calm onboarding screens, and the change on a copy.', 3200, extra='<span class="s-thumbs" style="margin-top:8px"><i></i><i></i><i></i></span>')]),
     loop=6500, still=5000)

# Options
page('whole-file', 'Options', 'Whole page or whole file', 'Every page at once.',
     'A note doesn\'t have to be about a selection. Send it with nothing selected for the page, or switch to the whole file.',
     ['For the current page: clear the selection and send the note.',
      'For every page: open <em>Options → Applies to</em> and pick <em>Whole file</em>.',
      'Write the rule (“all headings above 32 pt in Druk”) and send.'],
     ['The agent goes page by page and reports what it changed.',
      'Good for sweeping changes: dark mode for every screen, a font swap, renaming layers.'],
     cursor('0:560,300;200:@wf;800:click') + '<div class="s-pages">' + ''.join(f'<div class="s-pagerow"{a(at=f"{2000 + i * 600}:done")}><i></i>{n}<em>{c} headings</em></div>' for i, (n, c) in enumerate([('Home', 4), ('Pricing', 3), ('About', 2), ('Checkout', 5), ('Account', 2)])) + '</div>'
     + panel([top(17, 'Whole file', [('working', 'Working', 1600, 5000), ('ok', 'Done', 5000, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=1600)),
              note('All headings above 32 pt in Druk', 1600)],
             composer('', None, ctx=NOTHING, above='<div class="s-opt"><span>Applies to</span><span class="s-seg"' + a(at='800:moved') + '><span class="on">Selection</span><span data-pt="wf"' + a(at='800:pick') + '>Whole file</span></span></div>')),
     loop=7000)

page('design-system', 'Options', 'Your design system', 'Your library, or this file.',
     'Tell the agent what to build with: any library, only this file, or one library by name. It uses your components and variables first.',
     ['Open <em>Options → Build with</em>.',
      'Pick <em>Any library</em>, <em>This file only</em> or a library name.',
      'Send the note.'],
     ['The agent builds from the file\'s components and variables, follows a Figma Spec if there is one, and uses hard-coded values only when nothing fits.',
      'Combine it with <a href="../mentions/">@mentions</a> to point at one exact component.'],
     canvas(sel(*CTA_SEL), cta_at='3800:blue')
     + cursor('0:560,300;300:@lib;900:click')
     + panel([top(18, 'Order ahead', [('working', 'Working', 2000, 3800), ('ok', 'Done', 3800, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=2000)),
              note('Make this our primary button', 2000),
              reply('Swapped to <span class="mention">Button / Primary</span> from Kanso UI.', 3800)],
             composer('', None, ctx=('Order ahead', 'Button · Home'), above='<div class="s-opt"><span>Build with</span><span class="s-select" data-pt="lib"><span' + a(out=900) + '>Any library</span><span' + a(in_=900) + '>Kanso UI</span></span></div>')),
     loop=6500)

page('comments', 'Options', 'Figma comments', 'Works through them.',
     'Point the agent at the open comment threads on your layers. It applies what they ask for, or summarizes them into a plan first.',
     ['Open <em>Options → Comments</em>.',
      'Pick <em>Apply</em> to make the changes the threads ask for, or <em>Summarize</em> to get themes, conflicts and a plan you approve first.',
      'The first time, paste a Figma personal access token (scope <em>File comments: read</em>).'],
     ['The token is stored on your computer only.',
      'Resolved threads are left out unless you ask for them.'],
     canvas('<span class="s-cmt" style="left:300px;top:196px">AK</span><span class="s-cmt" style="left:160px;top:300px">MS</span>'
            '<span class="s-tag" style="left:330px;top:170px"' + a(in_=300) + '>too light?</span><span class="s-tag" style="left:190px;top:330px"' + a(in_=500) + '>use the brand blue</span>',
            h1_at='3600:bold', cta_at='4400:blue')
     + cursor('0:560,300;300:@apply;900:click')
     + panel([top(19, 'Home', [('working', 'Working', 1800, 4600), ('ok', 'Done', 4600, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=1800)),
              steps([('Reading 2 open comments', 1900, 3000), ('Making the headline heavier', 3000, 3600), ('Button in color/brand', 3600, 4400)])],
             composer('', None, ctx=NOTHING, above='<div class="s-opt"><span>Comments</span><span class="s-seg"' + a(at='900:moved') + '><span class="on">Off</span><span data-pt="apply"' + a(at='900:pick') + '>Apply</span><span>Summarize</span></span></div>')),
     loop=7000)

page('model-and-skill', 'Options', 'Model and skill', 'A model per note.',
     'Pick which model works on a note, and which of your agent\'s skills it should use.',
     ['Open <em>Options → Model</em> and pick one of the models your agent can hand a note to.',
      'Open <em>Options → Skill</em> to pick a skill from the watching session.',
      'Send the note. The chosen model works on it as a helper agent.'],
     ['The lists come from the agent that is watching, with their full names.',
      'The Model row is hidden when the agent can\'t pick a model.'],
     canvas(sel(*H1_SEL))
     + cursor('0:560,300;200:@model;800:click;900:@skill;1500:click')
     + panel([top(20, 'Headline', [('working', 'Working', 2400, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=2400)),
              note('Rewrite in our voice', 2400),
              '<div class="meta s-mono" style="text-align:right"' + a(in_=2400) + '>Claude Sonnet · skill: brand-voice</div>'],
             composer('', None, ctx=('Headline', 'Text · Home'),
                      above='<div class="s-opt"><span>Model</span><span class="s-select" data-pt="model"><span' + a(out=800) + '>Session default</span><span' + a(in_=800) + '>Claude Sonnet</span></span></div>'
                            '<div class="s-opt"><span>Skill</span><span class="s-select" data-pt="skill"><span' + a(out=1500) + '>None</span><span' + a(in_=1500) + '>brand-voice</span></span></div>')),
     loop=6000)

# In Figma
page('markers', 'In Figma', 'Canvas markers', 'Notes on the canvas.',
     'Each open note adds a native Figma annotation on its layers, so everyone in the file sees what is being worked on.',
     ['Send a note. Its layers get an annotation like “Claude #3 · Waiting”.',
      'The annotation follows the status as the agent works.',
      'When the note is done or deleted, the annotation disappears.'],
     ['Turn them off with <em>Options → Show markers on canvas</em>.',
      'Other people\'s annotations are never touched.'],
     canvas(sel(*H1_SEL, out=4600)
            + '<span class="s-annot" style="left:48px;top:186px"' + a(in_=600, out=1900) + '>Claude #3 · Waiting</span>'
            + '<span class="s-annot" style="left:48px;top:186px"' + a(in_=1900, out=4300) + '>Claude #3 · Working</span>', h1_at='4300:bold')
     + panel([top(3, 'Headline', [('working', 'Waiting', 600, 1900), ('working', 'Working', 1900, 4300), ('ok', 'Done', 4300, None)]).replace('<div class="note-top"', '<div class="note-top"' + a(in_=600)),
              note('Make it bolder', 600)]),
     loop=6500)

page('select-to-find', 'In Figma', 'Select to find', 'Click a layer, see its note.',
     'Select a layer on the canvas and the note about it lights up in the panel.',
     ['Click a layer that has a note.',
      'The note about it is highlighted and scrolled into view.',
      'Click a note to go the other way: Figma selects its layers.'],
     ['After a change, the agent can offer <em>Select N layers</em> to show exactly what it touched.'],
     canvas(sel(*H1_SEL, in_=900, out=3300) + sel(*CTA_SEL, in_=3500))
     + panel(['<div' + a(at='900:s-hit;3300:-s-hit') + ' style="display:flex;flex-direction:column;gap:8px;margin:0 -14px;padding:0 14px 10px">' + top(12, 'Headline', [('ok', 'Done', None, None)]) + note('Make it bolder') + '</div>',
              '<div' + a(at='3500:s-hit') + ' style="display:flex;flex-direction:column;gap:8px;margin:0 -14px;padding:0 14px 10px">' + top(13, 'Order ahead', [('ok', 'Done', None, None)]) + note('Warmer button') + '</div>'])
     + cursor('0:400,420;200:180,240;850:click;2700:100,330;3300:click'),
     loop=6000)

page('small-mode', 'In Figma', 'Small mode', 'Shrink it to a bar.',
     'Shrink the panel to a small bar that you can park anywhere. It still tells you when a note needs you.',
     ['Press the shrink button in the panel\'s header.',
      'The panel becomes a small bar; drag it by Figma\'s title bar.',
      'Click the bar to open the full panel again.'],
     ['The bar shows when a note needs your answer, or how many are in progress.',
      'Retoucher opens the way you left it.'],
     canvas()
     + '<div class="s-mini"' + a(at='900:small;4400:-small') + '><div class="bar" data-pt="bar"' + a(in_=1300, out=4300) + '><i class="dot" style="background:var(--warn)"></i><b>1 needs an answer</b></div>'
     '<div class="s-head"' + a(at='900:gone;4500:-gone') + '><img src="../../assets/minimize.svg" width="14" height="14" alt="" style="opacity:.5" data-pt="shrink"><b>Retoucher</b><span class="status"><img src="../../assets/logo-claude-ok.svg" width="14" height="14" alt="">Ready</span></div>'
     '<div class="s-notes" style="position:absolute;inset:40px 0 0"' + a(at='900:gone;4500:-gone') + '>' + top(14, 'Hero', [('warn', 'Needs answer', None, None)]) + note('Make it calmer') + '<div class="perm" style="align-self:stretch"><span class="mono">Asks you</span><strong>Which headline size?</strong></div></div></div>'
     + cursor('0:560,300;200:@shrink;800:click;3200:@bar;3800:click'),
     loop=6500, still=2500)

ORDER = [p['slug'] for g in GROUPS for p in P if p['group'] == g]
BY = {p['slug']: p for p in P}

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

def nav(cur, up):
    out = []
    for g in GROUPS:
        items = ''.join(f'<li><a href="{up}docs/{p["slug"]}/"{" aria-current=\"page\"" if p["slug"] == cur else ""}>{p["title"]}</a></li>' for p in P if p['group'] == g)
        out.append(f'<section><h4>{g}</h4><ul>{items}</ul></section>')
    return '<nav class="d-nav" aria-label="Features">' + ''.join(out) + '</nav>'

def prompt_block():
    js = open(os.path.join(ROOT, 'main.js')).read()
    text = re.search(r'const PROMPT = `(.*?)`;', js, re.S).group(1).replace('\\`', '`')
    return ('<section class="d-sec"><div class="d-prompt-head"><h2>Setup prompt</h2><button class="d-copy" type="button" data-copy-from="#prompt">Copy</button></div>'
            f'<pre class="d-prompt" id="prompt">{html.escape(text)}</pre></section>')

def feature(p):
    i = ORDER.index(p['slug'])
    prev, nxt = (BY[ORDER[i - 1]] if i else None), (BY[ORDER[i + 1]] if i + 1 < len(ORDER) else None)
    pn = ('<nav class="d-pn">'
          + (f'<a href="../{prev["slug"]}/"><span>Previous</span>{prev["title"]}</a>' if prev else '<span></span>')
          + (f'<a class="next" href="../{nxt["slug"]}/"><span>Next</span>{nxt["title"]}</a>' if nxt else '')
          + '</nav>')
    st = f' data-still="{p["still"]}"' if p['still'] is not None else ''
    body = f'''<div class="d-wrap">
{nav(p["slug"], "../../")}
<main class="d-main">
  <div><p class="d-eyebrow">{p["group"]} <a class="d-all" href="../">· All features</a></p><h1>{p["title"]}</h1></div>
  <p class="d-lead">{p["lead"]}</p>
  <div class="demo" data-loop="{p["loop"]}"{st} role="img" aria-label="Demo: {html.escape(p["title"])}"><div class="scene">{p["scene"]}</div></div>
  {prompt_block() if p["slug"] == "get-started" else ""}
  <section class="d-sec"><h2>How to use it</h2><ol class="d-how">{"".join(f"<li><span>{s}</span></li>" for s in p["how"])}</ol></section>
  <section class="d-sec"><h2>Good to know</h2><ul class="d-know">{"".join(f"<li>{s}</li>" for s in p["know"])}</ul></section>
  {pn}
</main>
</div>'''
    desc = re.sub(r'<[^>]+>', '', p['lead'])
    return shell(f'{p["title"]} · Retoucher Docs', desc, f'docs/{p["slug"]}/', 2, body)

def overview():
    groups = ''.join(
        f'<section class="d-group"><h2>{g}</h2><div class="d-cards">'
        + ''.join(f'<a href="{p["slug"]}/"><b>{p["title"]}</b><span>{p["sub"]}</span></a>' for p in P if p['group'] == g)
        + '</div></section>' for g in GROUPS)
    body = f'''<div class="d-wrap">
{nav(None, "../")}
<main class="d-main">
  <div><p class="d-eyebrow">Docs</p><h1>How Retoucher works</h1></div>
  <p class="d-lead">Every feature in a short demo and a few steps. New here? Start with <a href="get-started/">Get started</a>.</p>
  <div class="d-groups">{groups}</div>
</main>
</div>'''
    return shell('Docs · Retoucher', 'How every Retoucher feature works, in short demos and steps.', 'docs/', 1, body)

def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(text)

write('docs/index.html', overview())
for p in P:
    write(f'docs/{p["slug"]}/index.html', feature(p))
urls = ['/', '/docs/'] + [f'/docs/{s}/' for s in ORDER]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
      + ''.join(f'<url><loc>{SITE}{u}</loc></url>' for u in urls) + '</urlset>\n')
print(len(P), 'pages')
