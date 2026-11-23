# Nexel Worlds: website

The public site of Nexel Worlds: a landing page, the playable demo under `play/`, and a devlog under `devlog/`.
Static HTML and CSS, no framework, no build step needed to serve it. Published on GitHub Pages at
https://sofianedjerbi.github.io/nexel-website/

```
index.html            landing page (written by tools/make_site.py from tools/landing.html)
devlog/               posts (written from devlog/posts/*.md)
play/                 the demo: the game's own static build, committed as built
img/                  screenshots of the game (whole pixels, never scaled)
css/site.css          the look: the game's colours and edges
fonts/                the game's pixel font
tools/                the scripts below
```

## Rebuild

Pages (after editing `tools/landing.html` or a post in `devlog/posts/`):

    python3 tools/make_site.py

The demo, from a clean clone of the game repo (only committed code gets in; the built sound files and the cached
Pyodide library are copied from the game's working folder, since git does not hold them):

    tools/build_site.sh                         # GAME=~/megastructure REF=HEAD by default
    GAME=/path/to/megastructure REF=<commit> tools/build_site.sh

It runs the game's `tools/build_pages.py` (the same build as the old demo repo) into `play/` and writes the commit
it was built from in `play/BUILD`. The music page of the old demo is skipped unless the music is rendered in that
clone (it is not committed).

Screenshots, from a QA server of the game on a copy of a save (never the live server):

    cp -R ~/megastructure/saves/caves /tmp/site-qa/caves
    (cd ~/megastructure && PYTHONPATH=src .venv/bin/python -m megastructure.server --port 7881 --world /tmp/site-qa/caves --seed 12 --dev)
    SHOT_W=960 SHOT_H=540 ZOOM=3 ~/megastructure/.venv/bin/python tools/capture.py village night cave build
    SHOT_W=960 SHOT_H=540 ZOOM=4 ~/megastructure/.venv/bin/python tools/capture.py water jump
    python3 tools/crop.py                       # shots/raw/ -> img/ (crops only, no scaling)

Preview (desk and phone screenshots into `.preview/`, and a check that the demo boots under a sub-path):

    mkdir -p /tmp/serve && ln -sfn "$PWD" /tmp/serve/nexel-website && (cd /tmp/serve && python3 -m http.server 7882)
    ~/megastructure/.venv/bin/python tools/preview.py

## Credits and licences

- Art in the screenshots and in the demo: Sprout Lands by Cup Nooble (https://cupnooble.itch.io/), used under its
  licence. The pack may not be redistributed: the site itself uses only screenshots of the game; the demo ships
  only the sheets the game uses, as the game does (`play/assets/CREDITS.md`).
- Font: `fonts/sprout-pixel.ttf` is the game's own font, drawn for Nexel Worlds (`tools/build_font.py` in the game repo).
- Music in the demo: CC0 instrument recordings (VCSL, VSCO 2 CE by Versilian Studios; FreePats guitar).
