"""Write the site's pages: index.html, devlog/index.html and one page per post (devlog/posts/*.md).

    python3 tools/make_site.py

Plain Python, no packages. A post is a small Markdown file with a head:

    title: The jump, eight times
    date: 2026-11-23
    image: jump-2.png            (the list's picture, from img/)
    summary: one line for the list
    ---
    text: paragraphs, "## heading", "- list", **bold**, [link](url), `key`,
    ![caption](img/name.png) for a picture (at its own size), and a line "strip: a.png b.png c.png | caption"
    for frames side by side.
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "devlog" / "posts"
CODE = "https://github.com/sofianedjerbi/nexel-worlds"
AGENT = "https://github.com/sofianedjerbi/nexel-agent"

# pixel icons, 7 x 7, drawn 3 px a pixel ('#' = ink)
ICONS = {
    "play": ["#      ", "###    ", "#####  ", "#######", "#####  ", "###    ", "#      "],
    "next": ["   #   ", "   ##  ", "#######", "#######", "   ##  ", "   #   ", "       "],
    "back": ["   #   ", "  ##   ", "#######", "#######", "  ##   ", "   #   ", "       "],
    "code": [" #   # ", "#     #", "#  #  #", "#  #  #", "# #   #", "#     #", " #   # "],
    "log":  ["###### ", "#    # ", "# ## # ", "#    # ", "# ## # ", "#    # ", "###### "],
    "home": ["   #   ", "  ###  ", " ##### ", "#######", " #   # ", " # # # ", " ##### "],
    "heart": [" ## ## ", "#######", "#######", "#######", " ##### ", "  ###  ", "   #   "],
}


def icon(name: str) -> str:
    rows = ICONS[name]
    rects = "".join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#")
    return f'<svg class="i" viewBox="0 0 7 7" aria-hidden="true">{rects}</svg>'


# A page the browser kept (GitHub Pages lets it keep one ten minutes, and nothing here can say otherwise) is asked of
# the site again; if the site's has changed (a deploy since), the page is loaded again with it. Only a kept page: one
# that came over the network is the site's own. Once a page, never in a loop.
FRESH = """<script>
(() => { const n = performance.getEntriesByType("navigation")[0], u = location.href.split("#")[0];
  if (!n || n.transferSize !== 0 || sessionStorage.getItem("fresh " + u)) return;
  Promise.all([fetch(u, {cache: "force-cache"}), fetch(u, {cache: "no-cache"})]).then((r) => Promise.all(r.map((x) => x.text())))
    .then(([kept, now]) => { if (kept !== now) { sessionStorage.setItem("fresh " + u, 1); location.reload(); } }).catch(() => {}); })();
</script>"""


def page(title: str, body: str, base: str, desc: str, active: str = "") -> str:
    """The frame round every page. base: the way back to the site's root ("" or "../")."""
    nav = (f'<a href="{base}index.html">{icon("home")}Home</a>'
           f'<a href="{base}devlog/index.html">{icon("log")}Devlog</a>'
           f'<a href="{base}play/">{icon("play")}Play</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:image" content="{base}img/hero.png">
<link rel="preload" href="{base}fonts/sprout-pixel.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="{base}css/site.css">
<link rel="icon" href="{base}img/favicon.png">
{FRESH}
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{base}index.html">Nexel Worlds</a>
<nav class="nav">{nav}</nav>
</div></header>
{body}
<footer class="foot"><div class="wrap">
<p>Nexel Worlds is made by <a href="https://github.com/sofianedjerbi">sofianedjerbi</a>. Code: <a href="{CODE}">nexel-worlds</a> (the game) and <a href="{AGENT}">nexel-agent</a> (the AI players).</p>
<p>Art: Sprout Lands by <a href="https://cupnooble.itch.io/">Cup Nooble</a>. The pictures on this site are screenshots of the game.</p>
</div></footer>
</body>
</html>
"""


def inline(t: str, base: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<kbd>\1</kbd>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{fix(m.group(2), base)}">{m.group(1)}</a>', t)
    return t


def fix(url: str, base: str) -> str:
    return url if re.match(r"https?:|#|mailto:", url) else base + url


def picture(src: str, alt: str, base: str) -> str:
    return f'<div class="shot"><img src="{fix(src, base)}" alt="{html.escape(alt)}" loading="lazy"></div>'


def markdown(text: str, base: str) -> str:
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para), base) + "</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i, base)}</li>" for i in items) + "</ul>")
            items.clear()
    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("## "):
            flush()
            out.append(f"<h2>{inline(s[3:], base)}</h2>")
        elif s.startswith("- "):
            if para:
                flush()
            items.append(s[2:])
        elif m := re.match(r"!\[(.*)\]\((.+)\)$", s):
            flush()
            out.append(picture(m.group(2), m.group(1), base))
            out.append(f'<p class="cap">{inline(m.group(1), base)}</p>')
        elif s.startswith("strip:"):
            flush()
            files, _, cap = s[6:].partition("|")
            out.append('<div class="strip">' + "".join(picture("img/" + f, cap.strip(), base) for f in files.split()) + "</div>")
            out.append(f'<p class="cap">{inline(cap.strip(), base)}</p>')
        elif s.startswith("<"):
            flush()
            out.append(s)
        else:
            para.append(s)
    flush()
    return "\n".join(out)


def read_post(f: Path) -> dict:
    head, _, body = f.read_text().partition("\n---\n")
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    return {**meta, "slug": re.sub(r"^\d+-", "", f.stem), "body": body}


def devlog():
    posts = sorted((read_post(f) for f in POSTS.glob("*.md")), key=lambda p: (p["date"], p.get("order", "0"), p.get("slug", p.get("file", ""))))
    out = ROOT / "devlog"
    for i, p in enumerate(posts):
        prev = posts[i - 1] if i else None
        nxt = posts[i + 1] if i + 1 < len(posts) else None
        links = ('<div class="post-nav">'
                 + (f'<a class="btn small ghost" href="{prev["slug"]}.html">{icon("back")}{html.escape(prev["title"])}</a>' if prev else "<span></span>")
                 + (f'<a class="btn small ghost" href="{nxt["slug"]}.html">{html.escape(nxt["title"])}{icon("next")}</a>' if nxt else "")
                 + "</div>")
        body = f"""<main class="wrap"><section>
<article class="panel post-body">
<p class="date">{p["date"]}</p>
<h1>{html.escape(p["title"])}</h1>
<p></p>
{markdown(p["body"], "../")}
</article>
{links}
<p></p>
</section></main>"""
        (out / f"{p['slug']}.html").write_text(page(f"{p['title']} · Nexel Worlds devlog", body, "../", p["summary"]))
    items = "\n".join(f"""<li><a class="post" href="{p['slug']}.html">
<div class="thumb"><img src="../img/{p['image']}" alt="" loading="lazy"></div>
<div><h2>{html.escape(p['title'])}</h2><p class="date">{p['date']}</p><p>{html.escape(p['summary'])}</p></div>
</a></li>""" for p in reversed(posts))
    body = f"""<main class="wrap"><section>
<div class="panel">
<h1>Devlog</h1>
<p>How Nexel Worlds got made, a few days at a time. Short and honest: what worked, what did not, what we measured.
The full day-by-day notes live in the code repo's <a href="{CODE}/blob/main/JOURNAL.md">JOURNAL.md</a>.</p>
</div>
<ul class="posts">
{items}
</ul>
</section></main>"""
    (out / "index.html").write_text(page("Devlog · Nexel Worlds", body, "../", "How Nexel Worlds got made: short, honest posts."))
    return posts


def landing(posts):
    body = (ROOT / "tools" / "landing.html").read_text()
    latest = "\n".join(f'<li><a href="devlog/{p["slug"]}.html">{html.escape(p["title"])}</a> <span class="date">{p["date"]}</span></li>' for p in list(reversed(posts))[:4])
    body = body.replace("{{latest}}", latest)
    for name in ICONS:
        body = body.replace("{{icon:" + name + "}}", icon(name))
    (ROOT / "index.html").write_text(page("Nexel Worlds · a cozy voxel survival game you can play in your browser", body, "",
                                          "Nexel Worlds: a cozy top-down voxel survival game. Dig, build, farm and explore. Play the demo in your browser."))


if __name__ == "__main__":
    landing(devlog())
    print("pages written")
