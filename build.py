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
    """index.html: every board and note placed at its canvas position on a pan/zoom stage."""
    boards, notes = canvas['boards'], canvas['notes']
    pad = 80
    xs = [b['x'] for b in boards.values()] + [n['x'] for n in notes.values()]
    ys = [b['y'] for b in boards.values()] + [n['y'] for n in notes.values()]
    ox, oy = min(xs) - pad, min(ys) - pad
    width = max([b['x'] + b['w'] for b in boards.values()] + [n['x'] + n.get('w', 0) for n in notes.values()]) - ox + pad
    height = max(b['y'] + b['h'] for b in boards.values()) - oy + pad
    items = []
    for key, n in notes.items():
        pos = f'left:{n["x"] - ox}px;top:{n["y"] - oy}px'
        if n.get('kind') == 'title1':
            items.append(f'<h2 class="title" style="{pos}">{html.escape(n["text"])}</h2>')
        else:
            text = html.escape(n['text']).replace('\n', '<br>')
            items.append(f'<div class="note" style="{pos};width:{n["w"]}px;font-size:{n.get("size", 18)}px">{text}</div>')
    for name in canvas['order']:
        b, stem = boards[name], name.replace('.dc.html', '')
        title = html.escape(b['title'])
        tag = ' <span>interactive</span>' if b.get('is_interactive') else ''
        radius = b.get('radius', 14)
        items.append(f'''<a class="screen" href="screens/{stem}.html" style="left:{b["x"] - ox}px;top:{b["y"] - oy}px;width:{b["w"]}px;height:{b["h"]}px">
<span class="cap">{title}{tag}</span>
<iframe src="screens/{stem}.html" title="{title}" tabindex="-1" style="border-radius:{radius}px"></iframe></a>''')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<meta name="robots" content="noindex">
<title>{html.escape(canvas["title"])} · design</title>
{FONTS}
<style>
:root{{--paper:#E9E4DB;--ink:#1C1B19;--muted:#625B52;--glass:rgba(251,249,245,.94)}}
html,body{{height:100%;margin:0;overflow:hidden}}
body{{background:var(--paper);color:var(--ink);font:15px/1.5 'Jost',system-ui,sans-serif}}
#vp{{position:fixed;inset:0;touch-action:none;cursor:grab;user-select:none;-webkit-user-select:none}}
#vp.drag{{cursor:grabbing}}
#stage{{position:absolute;left:0;top:0;width:{width}px;height:{height}px;transform-origin:0 0}}
.title{{position:absolute;margin:0;font:500 96px/1 'Cormorant Garamond',Georgia,serif;white-space:nowrap}}
.note{{position:absolute;box-sizing:border-box;padding:28px 30px;border-radius:18px;background:#F6C77B;line-height:1.45}}
.screen{{position:absolute;display:block;color:var(--ink);text-decoration:none}}
.screen iframe{{display:block;width:100%;height:100%;border:0;background:#F3EFE8;pointer-events:none;box-shadow:0 18px 60px rgba(28,27,25,.16)}}
.screen:hover iframe,.screen:focus-visible iframe{{box-shadow:0 0 0 4px var(--ink),0 18px 60px rgba(28,27,25,.2)}}
.cap{{position:absolute;left:0;bottom:100%;margin-bottom:14px;font-size:22px;white-space:nowrap}}
.cap span{{margin-left:8px;padding:3px 10px;border-radius:12px;background:var(--ink);color:#F3EFE8;font-size:14px;letter-spacing:.06em;text-transform:uppercase;vertical-align:middle}}
.bar,.zoom{{position:fixed;z-index:2;background:var(--glass);border:1px solid #DDD6CB;border-radius:16px;box-shadow:0 6px 24px rgba(28,27,25,.1)}}
.bar{{top:calc(16px + env(safe-area-inset-top,0px));left:16px;max-width:calc(100% - 32px);box-sizing:border-box;padding:10px 16px}}
.bar h1{{margin:0;font:500 26px/1.1 'Cormorant Garamond',Georgia,serif}}
.bar p{{margin:2px 0 0;font-size:13px;color:var(--muted)}}
.zoom{{right:16px;bottom:calc(16px + env(safe-area-inset-bottom,0px));display:flex;align-items:center;padding:4px}}
.zoom button{{min-width:44px;height:44px;border:0;border-radius:12px;background:transparent;font:500 18px 'Jost',system-ui,sans-serif;color:var(--ink);cursor:pointer}}
.zoom button:hover{{background:#EDE6DA}}
.zoom output{{min-width:52px;text-align:center;font-size:13px;color:var(--muted)}}
.zoom .fit{{font-size:14px;padding:0 12px}}
</style>
</head>
<body>
<header class="bar"><h1>{html.escape(canvas["title"])}</h1><p>Drag to move · pinch or Ctrl + scroll to zoom · click a screen to open it</p></header>
<div id="vp"><div id="stage">
{"".join(items)}
</div></div>
<div class="zoom" role="group" aria-label="Zoom">
<button type="button" data-zoom="out" aria-label="Zoom out">−</button>
<output id="pct" aria-live="polite">100%</output>
<button type="button" data-zoom="in" aria-label="Zoom in">+</button>
<button type="button" data-zoom="fit" class="fit">Fit</button>
</div>
<script src="board.js"></script>
</body>
</html>
'''


if __name__ == '__main__':
    for src in sorted((ROOT / 'src').glob('*.dc.html')):
        screen(src)
    canvas = json.loads((ROOT / 'src' / 'canvas.json').read_text())
    (ROOT / 'index.html').write_text(board(canvas))
    print('built', len(list((ROOT / 'screens').glob('*.html'))), 'screens')
