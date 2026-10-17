"""Build the GitHub Pages copy of The Palm app design from the canvas files in src/.

Each src/<Name>.dc.html becomes screens/<Name>.html (rendered by screens/runtime.js),
and index.html lays the screens out like the canvas. Blob ids map to files in assets/.
Run: python3 build.py
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).parent
BLOBS = {
    'a4684e793dbc2c669bf848dd51540839': 'logo.webp',
    '5ca49668d029ab1b06bfc2d3e438aecc': 'logo-white.webp',
    'f10ae0e582d91e9ea3dd83c68fd03161': 'living.webp',
    '3574bd388b856f88fa1c81fbb382af52': 'bedroom.webp',
    'cafe35534ff57193126590a216732859': 'kitchen.webp',
    'f4652383a0a3b8d92384f6088306e4ee': 'dining.webp',
    '0029a94c120ad28600ebfb2d7674ee73': 'lounge.webp',
    '614b0df907c9df4355697e7462aac7d8': 'bath.webp',
    '8291b8af9ddd6f7fe146e2428af538e6': 'building.webp',
    '128e751276267409125925527f59c21c': 'pool.webp',
    'faecb394e51c542fbfd9ea180ee42d4c': 'terrace.webp',
    'af4e738c4f27ef9e5941bbe2d1aaa377': 'sign.webp',
}
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&amp;family=Jost:wght@400;500;600&amp;display=swap" rel="stylesheet">'


def blob(m):
    name = BLOBS.get(m.group(1))
    if not name:
        raise SystemExit(f'unmapped blob {m.group(1)}')
    return '../assets/' + name


def screen(src: Path):
    text = src.read_text()
    title = re.search(r'<title>(.*?)</title>', text).group(1)
    body = re.search(r'<x-dc>(.*)</x-dc>', text, re.S).group(1)
    helmet = re.search(r'<helmet>(.*?)</helmet>', body, re.S).group(1)
    body = body.replace(f'<helmet>{helmet}</helmet>', '')
    script = re.search(r'<script type="text/x-dc"[^>]*>(.*?)</script>', text, re.S).group(1)
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} · The Palm</title>
{helmet.strip()}
</head>
<body>
<div id="dc"></div>
<template id="tpl">{body}</template>
<script src="runtime.js"></script>
<script>{script}
mount(Component);
</script>
</body>
</html>
'''
    page = re.sub(r'/_blob/([0-9a-f]{32})', blob, page)
    page = re.sub(r'href="(\w+)\.dc\.html"', r'href="\1.html"', page)
    (ROOT / 'screens' / (src.stem.replace('.dc', '') + '.html')).write_text(page)


def board(canvas):
    boards, notes = canvas['boards'], canvas['notes']
    sections = []
    for key in ('t1', 't2', 't3'):
        top = notes[key]['y'] + 270
        nxt = sorted(n['y'] + 270 for n in notes.values() if n.get('kind') == 'title1' and n['y'] + 270 > top)
        bottom = nxt[0] if nxt else 10 ** 9
        names = [n for n in canvas['order'] if top <= boards[n]['y'] < bottom]
        cards = []
        for n in names:
            b, stem = boards[n], n.replace('.dc.html', '')
            wide = b['w'] > 390
            cls = 'screen wide' if wide else 'screen'
            cards.append(f'''<figure class="{cls}">
<figcaption><a href="screens/{stem}.html">{html.escape(b["title"])}</a>{' <span>interactive</span>' if b.get('is_interactive') else ''}</figcaption>
<iframe src="screens/{stem}.html" title="{html.escape(b["title"])}" loading="lazy" style="height:{b["h"]}px"></iframe>
</figure>''')
        sections.append(f'<section><h2>{html.escape(notes[key]["text"])}</h2><div class="row">{"".join(cards)}</div></section>')
    note = html.escape(notes['ph']['text']).replace('\n', '<br>')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>The Palm App · design</title>
{FONTS}
<style>
:root{{--paper:#E9E4DB;--ink:#1C1B19;--muted:#625B52}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 'Jost',system-ui,sans-serif}}
header,section{{padding:0 clamp(16px,4vw,48px)}}
header{{padding-block:48px 8px;display:flex;flex-wrap:wrap;gap:24px 48px;align-items:flex-start;justify-content:space-between}}
h1{{margin:0;font:500 clamp(40px,6vw,64px)/1 'Cormorant Garamond',Georgia,serif}}
header p{{margin:12px 0 0;color:var(--muted);max-width:520px}}
.note{{max-width:440px;padding:18px 20px;border-radius:14px;background:#F6C77B;font-size:14px}}
h2{{margin:56px 0 20px;font:500 32px/1.1 'Cormorant Garamond',Georgia,serif}}
.row{{display:flex;gap:40px;overflow-x:auto;padding-bottom:24px;align-items:flex-start}}
.screen{{margin:0;flex:0 0 390px}}
.screen.wide{{flex:1 1 100%;min-width:min(1440px,100%)}}
figcaption{{margin-bottom:10px;font-size:14px}}
figcaption a{{color:var(--ink);text-underline-offset:3px}}
figcaption span{{margin-left:6px;padding:2px 8px;border-radius:10px;background:var(--ink);color:#F3EFE8;font-size:11px;letter-spacing:.06em;text-transform:uppercase}}
iframe{{display:block;width:390px;border:0;border-radius:44px;background:#F3EFE8;box-shadow:0 10px 40px rgba(28,27,25,.14)}}
.wide iframe{{width:100%;border-radius:14px}}
footer{{padding:40px clamp(16px,4vw,48px) 60px;color:var(--muted);font-size:13px}}
</style>
</head>
<body>
<header>
<div><h1>{html.escape(canvas["title"])}</h1>
<p>App design for The Palm by Citystake, prepared by Mizan Qist. Every screen is live: tap through the links, and try the interactive ones.</p></div>
<div class="note">{note}</div>
</header>
{"".join(sections)}
<footer>Design only. Not the finished app.</footer>
</body>
</html>
'''


if __name__ == '__main__':
    for src in sorted((ROOT / 'src').glob('*.dc.html')):
        screen(src)
    canvas = json.loads((ROOT / 'src' / 'canvas.json').read_text())
    (ROOT / 'index.html').write_text(board(canvas))
    print('built', len(list((ROOT / 'screens').glob('*.html'))), 'screens')
