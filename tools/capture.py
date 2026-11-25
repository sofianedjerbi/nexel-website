"""Screenshots for the site, taken from the real game.

Runs against a QA server of the game on a COPY of a save (never the live one, never port 7777):

    cp -R ~/nexel/nexel-worlds/saves/caves /tmp/site-qa/caves
    cd ~/nexel/nexel-worlds && PYTHONPATH=src .venv/bin/python -m nexel_worlds.server --port 7881 --world /tmp/site-qa/caves --seed 12 --dev
    ~/nexel/nexel-worlds/.venv/bin/python tools/capture.py [shot ...]      (default: all shots)

It drives one headless Chrome with the game's own test helper (tests/e2e/game.py) and writes PNGs to shots/raw/.
"""

import os
import sys
import time
from pathlib import Path

GAME = Path(os.environ.get("GAME", Path.home() / "nexel" / "nexel-worlds"))
sys.path.insert(0, str(GAME / "tests" / "e2e"))
from playwright.sync_api import sync_playwright  # noqa: E402
from game import Game  # noqa: E402

URL = os.environ.get("QA_URL", "http://127.0.0.1:7881")
OUT = Path(__file__).resolve().parent.parent / "shots" / "raw"
W, H = int(os.environ.get("SHOT_W", 1280)), int(os.environ.get("SHOT_H", 720))
QUIET = """() => { const s = document.createElement('style');
  s.textContent = '#goalhint, #goals, #chatlog, #toast, #f3 .dbg { display:none !important; }'; document.head.appendChild(s); return 1; }"""


def snap(g, name):
    g.sleep(400)
    g.page.screenshot(path=str(OUT / f"{name}.png"))
    print("shot", name, g.pos(), flush=True)


def empty(g):
    """Nothing in the pack (what an earlier scene gave is taken back)."""
    inv = {k: -n for k, n in g.server()["inventory"].items() if n}
    if inv:
        g.rpc("dev_give", items=inv)
        g.sleep(900)


def tp(g, x, y, z=0, wait=2500):
    g.rpc("dev_teleport", x=x, y=y, z=z)
    g.sleep(wait)
    g.settle("!arrivingNow", timeout=8000)


def hour(g, phase):
    g.rpc("dev_time", phase=phase)
    g.sleep(1500)


def run(only):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        state = OUT.parent / "browser_state.json"       # (the player's key, kept: the name is taken after the first run)
        ctx = b.new_context(viewport={"width": W, "height": H}, storage_state=str(state) if state.exists() else None)
        page = ctx.new_page()
        page.set_default_timeout(30000)
        g = Game(page, URL)
        g.load(zoom=int(os.environ.get("ZOOM", 4)))
        if not only or "title" in only:
            page.wait_for_function("typeof ready !== 'undefined'")
            page.wait_for_timeout(6000)
            page.screenshot(path=str(OUT / "title.png"))
            print("shot title", flush=True)
        g.join(os.environ.get("NAME", "Ada"), int(os.environ.get("ZOOM", 4)))
        g.js(QUIET)
        g.rpc("dev_admin")
        for name in SHOTS:
            if only and name not in only:
                continue
            SHOTS[name](g)
        assert not g.errors, g.errors
        ctx.storage_state(path=str(state))
        ctx.close()
        b.close()


def where(g):
    snap(g, "where")


def explore(g):
    """EXPLORE="x,y,z x,y,z ...": a shot at each, to find places worth showing."""
    for p in os.environ.get("EXPLORE", "").split():
        x, y, z = (int(v) for v in p.split(","))
        tp(g, x, y, z)
        snap(g, f"ex_{x}_{y}_{z}")


VILLAGE = (88, 186)          # two houses, a fire, a field (built by players in the save)
GORGE = (31, -25)            # a river down a stone gorge


def home(g):
    """The first screen's island, its menu put away (the island is drawn by the game behind it)."""
    g.page.goto(g.url + "/?zoom=4")
    g.page.wait_for_function("typeof ready !== 'undefined'")
    g.page.add_style_tag(content="#joinbox, #title .tag, #titlemenu { visibility:hidden !important; }")
    g.page.wait_for_timeout(7000)
    g.page.screenshot(path=str(OUT / "home.png"))
    print("shot home", flush=True)


def village(g):
    empty(g)
    tp(g, VILLAGE[0] - 2, VILLAGE[1] - 3)
    hour(g, .3)
    snap(g, "village")
    hour(g, .62)                 # (late afternoon: long shadows)
    snap(g, "village_eve")


def night(g):
    empty(g)
    tp(g, VILLAGE[0] - 1, VILLAGE[1] - 3)
    g.give(torch=1)
    g.hold_item("torch")
    g.face(0, 1)
    g.rpc("dev_time", phase=.86)
    g.sleep(4000)
    snap(g, "night")


def water(g):
    """A river comes into a pit when its bank is cut: frames of it filling."""
    empty(g)
    tp(g, 160, 40)
    g.clear_area(12)
    g.rpc("dev_time", phase=.35)
    g.stamp(-5, -9, ["~"] * 9)                                   # a river, north-south, west of you
    g.stamp(-3, -7, ["....."] * 5, levels=["ccccc"] * 5)         # a pit three deep, a bank left between
    g.rest()
    g.face(0, 1)
    snap(g, "water_0")
    g.stamp(-4, -5, ["."], levels=["a"])                         # the bank cut: the river comes in
    for i in range(1, 9):
        g.sleep(220)
        snap(g, f"water_{i}")


def cave(g):
    """A hill with a cave in it, a fire inside; you walk in and are seen through the rock (the x-ray window)."""
    empty(g)
    tp(g, 220, 40)
    g.clear_area(16)
    x, y = g.pos()
    st = lambda ax, ay, rows, levels, **kw: g.rpc("dev_stamp", x=ax, y=ay, rows=rows, levels=levels, **kw)
    bx, by = x - 5, y - 12
    st(bx, by, ["." * 11] * 9, ["4" * 11] * 9)                                   # a hill
    st(bx + 1, by + 1, ["." * 9, "..^......", "." * 9, "." * 9, "." * 9], ["0" * 9] * 5, roofs=["4" * 9] * 5, heads=["2" * 9] * 5)
    st(bx + 5, by + 6, [".", ".", "."], ["0", "0", "0"], roofs=["4"] * 3, heads=["2"] * 3)     # its mouth, south
    g.rest()
    g.rpc("dev_time", phase=.4)
    tp(g, bx + 5, by + 10)
    snap(g, "cave_out")
    g.give(torch=3)
    g.hold_item("torch")
    tp(g, bx + 4, by + 2)                                        # beside the fire, east of it
    g.face(-1, 0)
    g.act("ignite", dir="W", **{"with": "torch"})
    g.sleep(800)
    tp(g, bx + 6, by + 4)
    g.face(0, 1)
    snap(g, "cave_in")
    g.rpc("dev_time", phase=.86)
    g.sleep(4000)
    snap(g, "cave_night")


def build(g):
    """Build mode: a wall planned with the cursor, your character building it."""
    empty(g)
    tp(g, 2, 13)
    g.clear_area(5)
    hour(g, .45)
    g.give(stone_block=40)
    g.hold_item("stone_block")
    g.face(1, 0)
    g.press("z")
    g.wait("Build.on", 3000)
    k = g.page.keyboard

    def row(arrows):
        k.down(" ")
        for a in arrows:
            at = g.js("[Build.S.at.x, Build.S.at.y]")
            k.press(a)
            g.wait(f"Build.S.at.x !== {at[0]} || Build.S.at.y !== {at[1]}", 3000)
        k.up(" ")
    row(["ArrowRight"] * 4)
    row(["ArrowLeft"] * 4)
    g.sleep(900)
    snap(g, "build_0")
    g.sleep(2500)
    snap(g, "build_1")
    g.sleep(4000)
    snap(g, "build_2")


def jump(g):
    """A jump up a block: frames a moment apart."""
    empty(g)
    tp(g, 2, 13)
    g.clear_area(6)
    hour(g, .4)
    g.stamp(-3, -4, ["......."] * 2, levels=["1111111"] * 2)       # a step a block high, north of you
    g.rest()
    g.face(0, -1)
    snap(g, "jump_0")
    k = g.page.keyboard
    k.down("ArrowUp")
    g.sleep(120)
    k.press(" ")
    for i in range(1, 9):
        g.page.screenshot(path=str(OUT / f"jump_{i}.png"))
    k.up("ArrowUp")
    print("shot jump", flush=True)


def bridge(g):
    """Earth in hand on a terrace's edge, six levels over the meadow: blocks put out at your own level, a bridge in the air."""
    empty(g)
    tp(g, 2, 13)
    g.clear_area(10)
    hour(g, .4)
    x, y = g.pos()
    g.rpc("dev_col", tiles=[[x + i, y + j] for i in range(-3, 1) for j in (-1, 0, 1)], col=[6])
    tp(g, x, y, 6)
    g.give(dirt=6)
    g.hold_item("dirt")
    g.face(1, 0)
    g.rest()
    for k in (1, 2, 3):
        g.press("e", 600)
        g.wait(f"solidAt({x + k}, {y}, 6)", 3000)
        g.hold(["d"], 60)
        g.rest()
    snap(g, "bridge")


# Clips: the world's own picture (the canvas, no bar or hearts over it) recorded in the page, and with `sound` what the
# game plays (its effects and its music), into one .webm: no other program needed. Written straight to img/.
REC = """(sound) => { const s = document.getElementById('c').captureStream(30);
  if (sound && audio) { const d = audio.createMediaStreamDestination(); soundOut.connect(d); musicOut.connect(d); d.stream.getAudioTracks().forEach((t) => s.addTrack(t)); }
  const kind = sound ? 'video/webm;codecs=vp9,opus' : 'video/webm;codecs=vp9';
  window.__rec = new MediaRecorder(s, {mimeType: kind, videoBitsPerSecond: 5e6}); window.__chunks = [];
  __rec.ondataavailable = (e) => e.data.size && __chunks.push(e.data); __rec.start(250); return 1; }"""
STOP = """() => new Promise((ok) => { __rec.onstop = () => { const r = new FileReader();
  r.onload = () => ok(r.result.split(',')[1]); r.readAsDataURL(new Blob(__chunks, {type: 'video/webm'})); }; __rec.stop(); })"""
IMG = Path(__file__).resolve().parent.parent / "img"


def clip(g, name, play, sound=False):
    """Record `play(g)` into img/<name>.webm."""
    import base64
    g.page.evaluate(REC, sound)
    play(g)
    data = base64.b64decode(g.page.evaluate(STOP))
    (IMG / f"{name}.webm").write_bytes(data)
    print("clip", name, f"{len(data) / 1e6:.1f} MB", flush=True)


def stage(g, at, phase, r=10):
    """A clear patch of meadow at `at`, at that hour, nothing in hand, nothing about."""
    empty(g)
    tp(g, *at)
    g.clear_area(r)
    g.rpc("dev_creatures", clear=r + 4)
    hour(g, phase)
    g.rpc("dev_needs", hp=20, hunger=20)


def creatures(g):
    """The new wild ones and the hob: a clip each."""
    stage(g, (300, 40), .4)
    g.give(wood=12)
    g.hold_item("wood")
    g.face(1, 0)
    g.rest()
    g.rpc("dev_creatures", kind="gustling", dx=4, dy=0)
    clip(g, "gustling", lambda g: g.sleep(9000))
    stage(g, (300, 40), .4)
    g.face(1, 0)
    g.rest()
    g.rpc("dev_creatures", kind="snapbloom", dx=3, dy=0)
    clip(g, "snapbloom", lambda g: g.sleep(8000))
    stage(g, (300, 40), .86)
    g.face(1, 0)
    g.rest()
    g.rpc("dev_creatures", kind="grumblestump", dx=4, dy=0)
    clip(g, "grumblestump", lambda g: g.sleep(9000))
    stage(g, (300, 40), .86)
    g.give(hob=1)
    g.face(1, 0)
    g.rest()
    g.act("place", dir="E", item="hob")
    g.sleep(1500)
    g.rpc("dev_creatures", kind="grumblestump", dx=5, dy=1)
    clip(g, "hob", lambda g: g.sleep(9000))


def bridge_clip(g):
    """Blocks put out over a drop, at your own level, and walked on."""
    stage(g, (2, 13), .4)
    x, y = g.pos()
    g.rpc("dev_col", tiles=[[x + i, y + j] for i in range(-3, 1) for j in (-1, 0, 1)], col=[6])
    tp(g, x, y, 6)
    g.give(dirt=6)
    g.hold_item("dirt")
    g.face(1, 0)
    g.rest()

    def play(g):
        g.sleep(600)
        for k in (1, 2, 3):
            g.press("e", 700)
            g.wait(f"solidAt({x + k}, {y}, 6)", 3000)
            g.hold(["d"], 60)
            g.rest()
            g.sleep(300)
        g.sleep(800)
    clip(g, "bridge", play)


def fall_clip(g):
    """Walking off a ledge six high: one smooth fall, the hurt shown as you land."""
    stage(g, (2, 13), .4)
    x, y = g.pos()
    g.rpc("dev_col", tiles=[[x + i, y + j] for i in range(-3, 1) for j in (-1, 0, 1)], col=[6])
    tp(g, x - 2, y, 6)
    g.face(1, 0)
    g.rest()
    clip(g, "fall", lambda g: (g.sleep(500), g.hold(["d"], 900), g.sleep(1500)))


def sky(g):
    """The new sky: by night the moon and the stars, at noon the sun's rays."""
    stage(g, (300, 40), .9)
    g.sleep(2500)
    snap(g, "sky_night")
    hour(g, .25)
    snap(g, "sky_day")


SHOTS = {"where": where, "explore": explore, "home": home, "village": village, "night": night, "water": water,
         "cave": cave, "build": build, "jump": jump, "bridge": bridge, "creatures": creatures, "bridge_clip": bridge_clip,
         "fall_clip": fall_clip, "sky": sky}

if __name__ == "__main__":
    t0 = time.time()
    run(sys.argv[1:])
    print(f"done in {time.time() - t0:.0f} s")
