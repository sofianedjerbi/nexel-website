# Contributing

## Commit messages: Conventional Commits

Every commit on main follows [Conventional Commits](https://www.conventionalcommits.org): CI checks each one
(`commitlint.config.mjs`: the conventional rules; body lines may be long).

    <type>(<scope>): <subject in lower case, no final full stop, about 72 characters at most>

    <body: what changed and why, as long as it needs>

- **type**: `feat` (a new page, post or demo feature), `fix`, `perf`, `refactor`, `docs`, `build`
  (a demo rebuilt from the game), `ci` (.github), `chore` (tools, anything else), `style`, `test`, `revert`.
- **scope**: `site` (landing page, css, img, fonts), `devlog`, `demo` (play/), `brain` (play/brain/), `tools`.

Optional hooks (ruff, and the message check at commit time): `uvx pre-commit install`.

## Publishing

GitHub Pages serves main as it is: a push to main is the release. There are no version tags here.
Before pushing, `python3 tools/make_site.py` (after editing `tools/landing.html` or a post) and
`python3 tools/check_links.py`; `.github/workflows/ci.yml` checks both on every pull request and push.

## Working on the code

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

### Rebuild

Pages (after editing `tools/landing.html` or a post in `devlog/posts/`):

    python3 tools/make_site.py

The demo, from a clean clone of the game repo (only committed code gets in; the built sound files and the cached
Pyodide library are copied from the game's working folder, since git does not hold them):

    GAME=~/nexel-worlds tools/build_site.sh     # GAME: your nexel-worlds checkout; REF=HEAD by default
    GAME=/path/to/nexel-worlds REF=<commit> tools/build_site.sh

It runs the game's `tools/build_pages.py` into `play/` and writes the commit it was built from in `play/BUILD`. The
music page of the old demo is skipped unless the music is rendered in that clone (it is not committed).

### Screenshots

From a QA server of the game on a copy of a save (never the live server):

    cp -R ~/nexel-worlds/saves/caves /tmp/site-qa/caves
    (cd ~/nexel-worlds && uv run nexel-worlds --port 7881 --world /tmp/site-qa/caves --seed 12 --dev)
    SHOT_W=960 SHOT_H=540 ZOOM=3 ~/nexel-worlds/.venv/bin/python tools/capture.py village night cave build
    SHOT_W=960 SHOT_H=540 ZOOM=4 ~/nexel-worlds/.venv/bin/python tools/capture.py water jump
    python3 tools/crop.py                       # shots/raw/ -> img/ (crops only, no scaling)

### Preview

Desk and phone screenshots into `.preview/`, and a check that the demo boots under a sub-path:

    mkdir -p /tmp/serve && ln -sfn "$PWD" /tmp/serve/nexel-website && (cd /tmp/serve && python3 -m http.server 7882)
    ~/nexel-worlds/.venv/bin/python tools/preview.py
