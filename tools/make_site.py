"""Write the site's pages: index.html, news/index.html and one page per post (news/posts/*.md); devlog/ sends to news/.

    python3 tools/make_site.py

Plain Python, no packages. A post is a small Markdown file with a head:

    title: The jump, eight times
    date: 2026-11-23
    image: jump-2.png            (the list's picture, from img/)
    summary: one line for the list
    ---
    text: paragraphs, "## heading", "- list", **bold**, [link](url), `key`,
    ![caption](img/name.png) for a picture (at its own size), ![caption](img/clip.webm) for a short silent clip
    (it loops by itself), "video: clip.webm | caption" for a video with sound (it plays when asked), and a line
    "strip: a.png b.png c.png | caption" for frames side by side.
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "news" / "posts"
CODE = "https://github.com/sofianedjerbi/nexel-worlds"
AGENT = "https://github.com/sofianedjerbi/nexel-agent"
SITE = "https://sofianedjerbi.github.io/nexel-website/"   # (link previews and search engines need whole addresses)

# pixel icons, 7 x 7, drawn 3 px a pixel ('#' = ink)
ICONS = {
    "play": ["#      ", "###    ", "#####  ", "#######", "#####  ", "###    ", "#      "],
    "next": ["   #   ", "   ##  ", "#######", "#######", "   ##  ", "   #   ", "       "],
    "back": ["   #   ", "  ##   ", "#######", "#######", "  ##   ", "   #   ", "       "],
    "code": [" #   # ", "#     #", "#  #  #", "#  #  #", "# #   #", "#     #", " #   # "],
    "log":  ["###### ", "#    # ", "# ## # ", "#    # ", "# ## # ", "#    # ", "###### "],
    "home": ["   #   ", "  ###  ", " ##### ", "#######", " #   # ", " # # # ", " ##### "],
    "heart": [" ## ## ", "#######", "#######", "#######", " ##### ", "  ###  ", "   #   "],
    "flask": ["  ###  ", "  # #  ", "  # #  ", " #   # ", "#  #  #", "# ### #", " ##### "],
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
           f'<a href="{base}news/index.html">{icon("log")}News</a>'
           f'<a href="{base}research/index.html">{icon("flask")}Research</a>'
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
<meta property="og:image" content="{SITE}img/hero.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Nexel Worlds">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}img/hero.png">
<link rel="preload" href="{base}fonts/sprout-pixel.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="{base}css/site.css">
<link rel="icon" type="image/png" sizes="16x16" href="{base}img/emblem.png">
<link rel="icon" type="image/png" sizes="32x32" href="{base}img/emblem_32.png">
<link rel="apple-touch-icon" href="{base}img/emblem_180.png">
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


def picture(src: str, alt: str, base: str, sound: bool = False) -> str:
    """A picture, or a clip (.webm, .mp4): a silent one loops by itself, one with sound plays when asked."""
    if src.endswith((".webm", ".mp4")):
        how = "controls preload=\"metadata\"" if sound else "autoplay loop muted playsinline"
        return f'<div class="shot"><video src="{fix(src, base)}" {how} aria-label="{html.escape(alt)}"></video></div>'
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
        elif s.startswith("video:"):
            flush()
            f, _, cap = s[6:].partition("|")
            out.append(picture("img/" + f.strip(), cap.strip(), base, sound=True))
            out.append(f'<p class="cap">{inline(cap.strip(), base)}</p>')
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


def news():
    posts = sorted((read_post(f) for f in POSTS.glob("*.md")), key=lambda p: (p["date"], p.get("order", "0"), p.get("slug", p.get("file", ""))))
    out = ROOT / "news"
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
        (out / f"{p['slug']}.html").write_text(page(f"{p['title']} · Nexel Worlds news", body, "../", p["summary"]))
    items = "\n".join(f"""<li><a class="post" href="{p['slug']}.html">
<div class="thumb"><img src="../img/{p['image']}" alt="" loading="lazy"></div>
<div><h2>{html.escape(p['title'])}</h2><p class="date">{p['date']}</p><p>{html.escape(p['summary'])}</p></div>
</a></li>""" for p in reversed(posts))
    body = f"""<main class="wrap"><section>
<div class="panel">
<h1>News</h1>
<p>What is new in Nexel Worlds, shown. Every change here is already in the game: <a href="../play/">play it</a>.</p>
</div>
<ul class="posts">
{items}
</ul>
</section></main>"""
    (out / "index.html").write_text(page("News · Nexel Worlds", body, "../", "What is new in Nexel Worlds: new creatures, places and things to do, shown."))
    old = ROOT / "devlog"                    # (the old name: its links go on working)
    old.mkdir(exist_ok=True)
    (old / "index.html").write_text('<!DOCTYPE html>\n<meta charset="utf-8">\n<title>News · Nexel Worlds</title>\n'
                                    '<meta http-equiv="refresh" content="0; url=../news/">\n<a href="../news/">News</a>\n')
    return posts


def landing(posts):
    body = (ROOT / "tools" / "landing.html").read_text()
    latest = "\n".join(f'<li><a href="news/{p["slug"]}.html">{html.escape(p["title"])}</a> <span class="date">{p["date"]}</span></li>' for p in list(reversed(posts))[:4])
    body = body.replace("{{latest}}", latest)
    for name in ICONS:
        body = body.replace("{{icon:" + name + "}}", icon(name))
    (ROOT / "index.html").write_text(page("Nexel Worlds · a cozy voxel survival game you can play in your browser", body, "",
                                          "Nexel Worlds: a cozy top-down voxel survival game. Dig, build, farm and explore. Play the demo in your browser."))


def crawl(posts):
    """sitemap.xml, for search engines (Search Console): every page a player reads. (No robots.txt: one is read only at
    the root of the domain, not under /nexel-website/.)"""
    urls = [SITE, SITE + "news/", SITE + "research/", SITE + "play/"] + [f"{SITE}news/{p['slug']}.html" for p in posts]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")


if __name__ == "__main__":
    from make_research import research
    posts = news()
    landing(posts)
    research()
    crawl(posts)
    print("pages written")
