"""research/index.html from the research notes' LaTeX (research/notes/main.tex and its sections), in the site's frame.

    python3 tools/make_research.py          (also run by tools/make_site.py)

The notes are the source: the same .tex builds the PDF. Math is left to MathJax. Each figure is the pgfplots code in
the .tex, drawn here as SVG from the same CSV (research/data/): one graph, written once, as code. The subset read:
an axis's xlabel, ylabel, ymin, ymax, ymode=log, legend, symbolic x coords; \\addplot table[x=, y=, meta=]{file}
with colour, thick, dashed, mark=*, only marks, scatter (meta 0 red, 1 green), name path + fill between (a band),
matrix plot* (a heat map); and tabular (booktabs), itemize, enumerate, theorem, proposition, proof."""

import csv
import html
import math
import re
from pathlib import Path

from make_site import ROOT, SITE, page

NOTES = ROOT / "research" / "notes"
COLOR = {"blue": "#3f6fa6", "red": "#c0503c", "orange": "#d9822b", "green": "#4f9a6a", "ink": "#5b3f36"}


def colour(opts: str) -> str:
    m = re.search(r"\b(blue|red|orange|green)\b", opts)
    return COLOR[m.group(1)] if m else COLOR["blue"]


def table(path: Path) -> list:
    with open(path) as f:
        return list(csv.DictReader(f, delimiter=" "))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---- figures: pgfplots, drawn as SVG -----------------------------------------------------------------------------
def opt(opts: str, key: str):
    m = re.search(key + r"\s*=\s*(\{[^}]*\}|[^,\]]+)", opts)
    return m.group(1).strip("{} ") if m else None


def axis_svg(src: str, base: Path) -> str:
    a = re.search(r"\\begin\{axis\}\[(.*?)\]\s*\n", src, re.S)
    aopts = a.group(1) if a else ""
    plots = re.findall(r"\\addplot(?:\[(.*?)\])?\s*(table\[(.*?)\]\{(.*?)\}|fill between\[of=(\w+) and (\w+)\]|coordinates\s*\{(.*?)\})\s*;", src, re.S)
    legend = [x.strip() for x in re.findall(r"\\legend\{(.*?)\}", src)[0].split(",")] if "\\legend" in src else []
    if any("matrix plot" in (p[0] or "") for p in plots):
        return heatmap(plots[0], base)
    series, paths, bands = [], {}, []
    for popts, _, topts, file, b1, b2, coords in plots:
        popts = popts or ""
        if coords:
            series.append((popts, [(x, num(y), None) for x, y in re.findall(r"\(([-\d.]+),\s*([-\d.]+)\)", coords)]))
        elif file:
            rows = table((base / file).resolve())
            xk, yk, mk = opt(topts, "x"), opt(topts, "y"), opt(topts, "meta")
            pts = [(r[xk], num(r[yk]), num(r[mk]) if mk else None) for r in rows if num(r[yk]) is not None]
            name = opt(popts, "name path")
            if name:
                paths[name] = pts
            if "draw=none" not in popts:
                series.append((popts, pts))
        else:
            bands.append((popts, paths.get(b1, []), paths.get(b2, [])))
    cats = None
    if "symbolic x coords" in aopts:
        cats = []
        for _, pts in series:
            for x, *_ in pts:
                if x not in cats:
                    cats.append(x)
    xs = list(range(len(cats))) if cats else [num(x) for _, pts in series for x, *_ in pts]
    ys = [y for _, pts in series for _, y, _ in pts] + [y for _, p1, p2 in bands for _, y, _ in p1 + p2]
    logy = opt(aopts, "ymode") == "log"
    f = (lambda v: math.log10(max(v, 1e-12))) if logy else (lambda v: v)
    y0 = num(opt(aopts, "ymin")) if opt(aopts, "ymin") else min(f(y) for y in ys)
    y1 = num(opt(aopts, "ymax")) if opt(aopts, "ymax") else max(f(y) for y in ys)
    if y1 == y0:
        y1 = y0 + 1
    x0 = num(opt(aopts, "xmin")) if opt(aopts, "xmin") else min(xs)
    x1 = num(opt(aopts, "xmax")) if opt(aopts, "xmax") else (max(xs) or 1)
    whole = all(float(x).is_integer() for x in xs)
    W, H, L, B, T, R = 720, 300, 84, 46, 16, 24
    jitter = {}

    def X(x):
        if cats:
            i = cats.index(x)
            k = jitter[x] = jitter.get(x, -1) + 1
            return L + (i + 0.5 + (k - 1) * 0.18) * (W - L - R) / len(cats)
        return L + (num(x) - x0) / ((x1 - x0) or 1) * (W - L - R)

    def Y(y):
        return T + (1 - (f(y) - y0) / (y1 - y0)) * (H - T - B)
    out = [f'<line class="ax" x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}"/><line class="ax" x1="{L}" y1="{T}" x2="{L}" y2="{H - B}"/>']
    for k in range(5):                                   # (y ticks)
        v = y0 + (y1 - y0) * k / 4
        lab = tick(10 ** v) if logy else tick(v)
        yy = T + (1 - k / 4) * (H - T - B)
        out.append(f'<line class="grid" x1="{L}" y1="{yy:.1f}" x2="{W - R}" y2="{yy:.1f}"/><text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end">{lab}</text>')
    if cats:
        out += [f'<text x="{L + (i + 0.5) * (W - L - R) / len(cats):.1f}" y="{H - B + 20}" text-anchor="middle">{html.escape(c)}</text>' for i, c in enumerate(cats)]
    else:
        xt = sorted({round(x0 + (x1 - x0) * k / 4) for k in range(5)}) if whole else [x0 + (x1 - x0) * k / 4 for k in range(5)]
        out += [f'<text x="{X(v):.1f}" y="{H - B + 20}" text-anchor="middle">{tick(v)}</text>' for v in xt]
    for _, p1, p2 in bands:
        if p1 and p2:
            pts = [(X(x), Y(y)) for x, y, _ in p1] + [(X(x), Y(y)) for x, y, _ in reversed(p2)]
            out.append(f'<polygon class="band" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}"/>')
    for popts, pts in series:
        c = colour(popts)
        ms = opt(popts, "mark size")
        rad = round(1.3 * num(ms.replace("pt", "")), 1) if ms else 3
        if "only marks" in popts or "scatter" in popts:
            for x, y, m in pts:
                cc = (COLOR["green"] if m else COLOR["red"]) if "scatter" in popts else c
                out.append(f'<rect x="{X(x) - 4:.1f}" y="{Y(y) - 4:.1f}" width="8" height="8" fill="{cc}"/>' if "square" in popts
                           else f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{rad}" fill="{cc}"/>')
        else:
            d = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y, _) in enumerate(pts))
            dash = ' stroke-dasharray="6 5"' if "dashed" in popts else ""
            out.append(f'<path d="{d}" stroke="{c}" stroke-width="{3 if "thick" in popts else 2}" fill="none"{dash}/>')
            if "mark=*" in popts:
                out += [f'<rect x="{X(x) - 3:.1f}" y="{Y(y) - 3:.1f}" width="6" height="6" fill="{c}"/>' for x, y, _ in pts]
        jitter.clear()
    xl, yl = opt(aopts, "xlabel"), opt(aopts, "ylabel")
    out.append(f'<text x="{(L + W - R) / 2}" y="{H - 6}" text-anchor="middle" class="lab">{svg_label(xl or "")}</text>')
    out.append(f'<text x="12" y="{(T + H - B) / 2}" text-anchor="middle" class="lab" transform="rotate(-90 12 {(T + H - B) / 2})">{svg_label(yl or "")}</text>')
    leg = "".join(f'<span><i style="background:{colour(p)}"></i>{tex_inline(n)}</span>' for (p, _), n in zip(series, legend, strict=False))
    return f'<svg class="chart" viewBox="0 0 {W} {H}">{"".join(out)}</svg>' + (f'<div class="legend">{leg}</div>' if leg else "")


def heatmap(plot, base: Path) -> str:
    rows = table((base / plot[3]).resolve())
    n = int(max(num(r["i"]) for r in rows)) + 1
    s = 36
    cells = []
    for r in rows:
        v = num(r["cos"])
        c = f"rgba(79,154,106,{v:.2f})" if v >= 0 else f"rgba(192,80,60,{-v:.2f})"
        cells.append(f'<rect x="{int(num(r["i"])) * s}" y="{int(num(r["j"])) * s}" width="{s}" height="{s}" fill="{c}"><title>{v:.3f}</title></rect>')
    return f'<svg class="chart heat" viewBox="0 0 {n * s} {n * s}">{"".join(cells)}</svg>'


def svg_label(t: str) -> str:
    """A label inside a graph: SVG text, where MathJax does not reach: the few symbols used, as Unicode."""
    sub = {r"\\psi": "ψ", r"\\delta": "δ", r"\\gamma": "\u03b3", r"\\theta": "θ", r"\\cos": "cos", r"\\pi": "π",
           r"_1": "₁", r"_2": "₂", r"\\,": " "}
    t = t.replace("$", "")
    for k, v in sub.items():
        t = re.sub(k, v, t)
    return html.escape(re.sub(r"[{}\\]", "", t))


def tick(v: float) -> str:
    a = abs(v)
    if a >= 1000:
        return f"{v:,.0f}".replace(",", " ")
    if a >= 10 or a == 0:
        return f"{v:.0f}"
    if a >= 0.01:
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return f"{v:.0e}"


# ---- text ---------------------------------------------------------------------------------------------------------
def tex_inline(t: str) -> str:
    """Prose LaTeX to HTML, math left as $...$ for MathJax."""
    parts = re.split(r"(\$[^$]*\$)", t)
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(html.escape(p, quote=False))
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"\\textbf\{([^}]*)\}", r"<b>\1</b>", p)
        p = re.sub(r"\\emph\{([^}]*)\}", r"<em>\1</em>", p)
        p = re.sub(r"\\texttt\{([^}]*)\}", r"<code>\1</code>", p)
        p = p.replace("``", "“").replace("''", "”").replace("---", "—").replace("--", "\u2013").replace("\\,", "\u00a0")
        p = p.replace("\\ ", " ").replace("\\%", "%").replace("\\&", "&amp;").replace("\\S", "§").replace("~", " ")
        p = p.replace("\\noindent", "").replace("\\!", "").replace("\\dots", "…").replace("\\_", "_")
        out.append(p)
    return "".join(out)


def blocks(t: str, base: Path) -> str:
    """A section's body: environments as cards, lists, tables and figures; the rest in paragraphs."""
    keep = {}

    def stash(h):
        keep[k := f"\x00{len(keep)}\x00"] = h
        return f"\n\n{k}\n\n"

    def figure(m):
        body = m.group(1)
        cap = re.search(r"\\caption\{(.*)\}", body, re.S)
        cap = cap.group(1) if cap else ""
        if "\\begin{tabular}" in body:
            return stash(f'<figure>{tabular(body)}<figcaption>{tex_inline(cap)}</figcaption></figure>')
        return stash(f'<figure>{axis_svg(body, base)}<figcaption>{tex_inline(cap)}</figcaption></figure>')
    t = re.sub(r"\\begin\{(?:figure|table)\}(?:\[[^\]]*\])?(.*?)\\end\{(?:figure|table)\}", figure, t, flags=re.S)

    def lst(m):
        kind = "ol" if m.group(1) == "enumerate" else "ul"
        items = [i.strip() for i in re.split(r"\\item\s", m.group(2)) if i.strip()]
        return stash(f"<{kind} class=\"notes\">" + "".join(f"<li>{tex_inline(i)}</li>" for i in items) + f"</{kind}>")
    t = re.sub(r"\\begin\{(itemize|enumerate)\}(.*?)\\end\{\1\}", lst, t, flags=re.S)

    def card(m):
        kind, note, inner = m.group(1), m.group(2), m.group(3).strip()
        if kind == "proof":
            return stash(f'<details class="proof"><summary>Proof</summary><div>{tex_inline(inner)} <span class="qed">∎</span></div></details>')
        note = f' <span class="note">({tex_inline(note[1:-1])})</span>' if note else ""
        return stash(f'<div class="thm"><div class="kind">{kind.title()}{note}</div>{tex_inline(inner)}</div>')
    t = re.sub(r"\\begin\{(theorem|proposition|proof)\}(\[[^\]]*\])?(.*?)\\end\{\1\}", card, t, flags=re.S)
    t = re.sub(r"\\emph\{So:\}(.*?)(?=\n\s*\n|\Z)", lambda m: stash(f'<p class="lesson"><b>So</b>{tex_inline(m.group(1))}</p>'), t, flags=re.S)
    t = re.sub(r"\\noindent Check\.(.*?)(?=\n\s*\n|\Z)", lambda m: stash(f'<p class="check"><b>Check</b>{tex_inline(m.group(1))}</p>'), t, flags=re.S)
    out = []
    for p in (p.strip() for p in re.split(r"\n\s*\n", t)):
        if p in keep:
            out.append(keep[p])
        elif p:
            out.append(f"<p>{tex_inline(p)}</p>")
    return "\n".join(out)


def tabular(body: str) -> str:
    inner = re.search(r"\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}", body, re.S).group(1)
    inner = re.sub(r"\\(toprule|midrule|bottomrule)", "", inner)
    rows = [r.strip() for r in inner.split("\\\\") if r.strip()]
    cells = [[tex_inline(c.strip()) for c in r.split("&")] for r in rows]
    head = "".join(f"<th>{c}</th>" for c in cells[0])
    return '<table class="data"><tr>' + head + "</tr>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in cells[1:]) + "</table>"


def key_results() -> str:
    """The headline numbers, read from the data the notes ship (research/data), so the page cannot drift from them."""
    import math
    data = ROOT / "research" / "data"
    if not (data / "sim_board.csv").exists():
        return ""
    board = table(data / "sim_board.csv")
    k, n = sum(int(r["whole"]) for r in board), len(board)
    p, z = k / n, 1.96
    c, h = (p + z * z / (2 * n)) / (1 + z * z / n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    sc = {(r["scenario"], r["controller"]): r for r in table(data / "scenarios.csv")} if (data / "scenarios.csv").exists() else {}
    axe = (sc.get(("craft_axe", "learned")), sc.get(("craft_axe", "skills")))
    tiles = [(f"{k} / {n}", f"designs built from an empty inventory (95% {c - h:.0%}\u2013{c + h:.0%})"),
             ("6/6 · 8/8", "trial 7: the room the agent built, judged works · makes sense"),
             ("181 \u2192 104", "wood in a house's bill, per-cell vs least (Theorem 1)")]
    if all(axe):
        tiles.append((f'{axe[0]["success"]} \u2192 {axe[1]["success"]} / 20', "axe crafted: learned body vs code skill"))
    return '<div class="kpis">' + "".join(f'<div class="kpi"><b>{v}</b><span>{t}</span></div>' for v, t in tiles) + "</div>"


def research():
    main = (NOTES / "main.tex").read_text()
    title = tex_inline(re.search(r"\\title\{(.*?)\}\n", main, re.S).group(1))
    author = tex_inline(re.search(r"\\author\{(.*?)\}\n", main, re.S).group(1))
    secs = []
    for name in re.findall(r"\\input\{(.*?)\}", main):
        f = NOTES / f"{name}.tex"
        t = f.read_text()
        m = re.search(r"\\section\*\{(.*?)\}", t)
        head = tex_inline(m.group(1)) if m else ""
        body = blocks(t[m.end():] if m else t, NOTES)       # (paths from main.tex, as LaTeX reads them)
        if m:
            secs.append([Path(name).name, head, body])
        elif secs:
            secs[-1][2] += body                          # (a file without a heading continues the one before)
    toc = "".join(f'<li><a href="#{n}">{h}</a></li>' for n, h, _ in secs)
    content = "".join(f'<section class="panel paper" id="{n}"><h2><a class="anchor" href="#{n}">{h}</a></h2>{b}</section>'
                      for n, h, b in secs)
    rev = re.search(r"revision (\d+) \(([^)]*)\)", author)
    badge = f'<span class="badge">revision {rev.group(1)} · {rev.group(2)}</span>' if rev else ""
    src = "https://github.com/sofianedjerbi/nexel-website/tree/main/research"
    body = f"""<script>window.MathJax={{tex:{{inlineMath:[['$','$']]}},chtml:{{scale:0.95}}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<main class="wrap research">
<section class="panel lead"><div class="eyebrow">Research notes {badge}</div><h1>{title}</h1>
{key_results()}
<p class="files"><a href="notes/main.tex">LaTeX source</a> · <a href="live_counts.py">live counts</a> ·
<a href="https://github.com/sofianedjerbi/nexel-agent/blob/main/tools/theorems.py">theorem checks</a> ·
<a href="https://github.com/sofianedjerbi/nexel-agent/blob/main/tools/scenarios.py">scenarios</a> ·
<a href="{src}">data and history</a></p></section>
<div class="rgrid"><nav class="rtoc" aria-label="Contents"><div class="eyebrow">Contents</div><ol>{toc}</ol></nav>
<div class="rmain">{content}</div></div>
</main>"""
    (ROOT / "research" / "index.html").write_text(page("Research · Nexel Worlds", body, "../",
                                                       "Research notes on Nexel Worlds' AI player: what failed, why, and the theory for what is next.",
                                                       "research"))
    return SITE + "research/"


if __name__ == "__main__":
    print(research())
