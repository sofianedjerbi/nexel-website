"""Screenshots of the site's pages, desk and phone, into .preview/ (git-ignored); checks that the demo boots under
a sub-path, as on GitHub Pages, and that no request fails.

    cd <dir holding a link nexel-website -> this repo> && python3 -m http.server 7882
    ~/nexel/nexel-worlds/.venv/bin/python tools/preview.py [--phone-shot]     (--phone-shot: also writes img/phone.png)
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:7882/nexel-website/"
OUT = ROOT / ".preview"
PAGES = {"home": "index.html", "devlog": "devlog/index.html", "post-ai": "devlog/ai-players.html", "post-water": "devlog/flowing-water.html"}
SIZES = {"desk": dict(viewport={"width": 1440, "height": 900}), "phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)}


def main():
    OUT.mkdir(exist_ok=True)
    bad = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        for size, opts in SIZES.items():
            ctx = b.new_context(**opts)
            page = ctx.new_page()
            page.on("response", lambda r: r.status >= 400 and bad.append(f"{r.status} {r.url}"))
            page.on("pageerror", lambda e: bad.append(f"error {e}"))
            for name, path in PAGES.items():
                page.goto(BASE + path, wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                wide = page.evaluate("document.documentElement.scrollWidth")
                if wide > opts["viewport"]["width"]:
                    bad.append(f"{size} {name}: page {wide} px wide")
                page.screenshot(path=str(OUT / f"{size}-{name}.png"), full_page=True)
                page.screenshot(path=str(OUT / f"{size}-{name}-top.png"))
                print("shot", size, name, flush=True)
            # the demo, under the sub-path: up to its first screen, then in the game
            page.goto(BASE + "play/", wait_until="load")
            page.wait_for_function("typeof ready !== 'undefined' && document.querySelector('#name')", timeout=90000)
            page.wait_for_timeout(6000)
            page.screenshot(path=str(OUT / f"{size}-play-title.png"))
            page.click("#name")
            page.keyboard.type("Preview")
            page.keyboard.press("Enter")
            page.wait_for_function("typeof meObs !== 'undefined' && meObs && myPos()", timeout=90000)
            page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT / f"{size}-play-game.png"))
            print("shot", size, "play", flush=True)
            ctx.close()
        if "--phone-shot" in sys.argv:
            ctx = b.new_context(viewport={"width": 390, "height": 700}, device_scale_factor=1, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.goto(BASE + "play/", wait_until="load")
            page.wait_for_function("typeof ready !== 'undefined' && document.querySelector('#name')", timeout=90000)
            page.click("#name")
            page.keyboard.type("Phone")
            page.keyboard.press("Enter")
            page.wait_for_function("typeof meObs !== 'undefined' && meObs && myPos()", timeout=90000)
            page.wait_for_timeout(5000)
            page.screenshot(path=str(ROOT / "img" / "phone.png"))
            ctx.close()
        b.close()
    print("problems:" if bad else "no failed requests, no page errors, nothing wider than the screen")
    for x in dict.fromkeys(bad):
        print(" ", x)


if __name__ == "__main__":
    main()
