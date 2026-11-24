"""Crop the raw game screenshots (shots/raw/) to the site's pictures (img/), whole pixels, never scaled."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "shots" / "raw", ROOT / "img"
CROPS = {   # out name: (raw shot, box)
    "hero": ("home_wide.png", (0, 0, 1920, 640)),
    "island": ("home.png", (0, 0, 960, 540)),
    "village": ("village.png", (0, 0, 960, 540)),
    "evening": ("village_eve.png", (0, 0, 960, 540)),
    "night": ("night.png", (0, 0, 960, 540)),
    "cave-out": ("cave_out.png", (0, 0, 960, 540)),
    "cave": ("cave_in.png", (0, 0, 960, 540)),
    "cave-night": ("cave_night.png", (0, 0, 960, 540)),
    "gorge": ("ex_31_-25_0.png", (0, 0, 960, 540)),
    "build": ("build_2.png", (0, 0, 960, 540)),
    "flow-1": ("water_0.png", (250, 95, 562, 295)),
    "flow-2": ("water_2.png", (250, 95, 562, 295)),
    "flow-3": ("water_5.png", (250, 95, 562, 295)),
    "jump-1": ("jump_0.png", (324, 140, 636, 340)),
    "jump-2": ("jump_2.png", (324, 140, 636, 340)),
    "jump-3": ("jump_4.png", (324, 140, 636, 340)),
    "build-1": ("build_0.png", (306, 160, 774, 400)),
    "build-2": ("build_1.png", (306, 160, 774, 400)),
    "build-3": ("build_2.png", (306, 160, 774, 400)),
}
# older looks, from the game repo's own showcase pictures (screenshots of the game, tools/pages/)
OLD = Path.home() / "nexel" / "nexel-worlds" / "tools" / "pages"
OLDCROPS = {
    "old-hills": ("game_hills.png", (70, 110, 1030, 650)),
    "old-cave": ("underground.jpg", (160, 90, 1120, 630)),
    "old-house": ("floors.jpg", (160, 90, 1120, 630)),
    "old-build": ("build_mode.jpg", (160, 90, 1120, 630)),
}
OUT.mkdir(exist_ok=True)
for name, (src, box) in OLDCROPS.items():
    im = Image.open(OLD / src).convert("RGB").crop(box)
    if src.endswith(".jpg"):
        im.save(OUT / f"{name}.jpg", quality=90)
    else:
        im.save(OUT / f"{name}.png", optimize=True)
    print(name, im.size)
for name, (src, box) in CROPS.items():
    im = Image.open(RAW / src).convert("RGB").crop(box)
    im.save(OUT / f"{name}.png", optimize=True)
    print(name, im.size, (OUT / f"{name}.png").stat().st_size // 1024, "KB")
