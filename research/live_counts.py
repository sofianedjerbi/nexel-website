"""The live trials' counts in the notes, from the game's own event log of each trial (data/trials/trialN-events.jsonl.gz:
every tile change, with who and why, and every craft).  python3 live_counts.py"""

import collections
import gzip
import json
from pathlib import Path

BUILDER = {"stone", "path", "plank", "stone_wall", "wood_wall", "door", "roof", "stairs", "workbench"}   # (what a build lays or crafts with)


def counts(path, who="Rook"):
    built, on_built, causes, crafts = set(), 0, collections.Counter(), collections.Counter()
    with gzip.open(path, "rt") as f:
        for line in f:
            d = json.loads(line)
            if d.get("type") == "craft" and d.get("name") == who:
                crafts.update(dict.fromkeys(d["made"], 1))
            if d.get("type") != "tile" or d.get("by") != who:
                continue
            p = (d["x"], d["y"])
            causes[d.get("cause")] += 1
            if d.get("cause") == "place" and d.get("block") not in (None, "none"):
                built.add(p)
            elif d.get("cause") == "dig" and p in built:
                on_built += 1
    other = {k: n for k, n in crafts.items() if k not in BUILDER}
    return {"placed": causes["place"], "digs": causes["dig"], "digs_on_tiles_it_built_on": on_built,
            "crafts": sum(crafts.values()), "crafts_of_build_materials": sum(crafts.values()) - sum(other.values()),
            "crafts_of_other_things": sum(other.values()), "other_things": dict(collections.Counter(other).most_common(8))}


if __name__ == "__main__":
    for f in sorted((Path(__file__).parent / "data" / "trials").glob("trial*-events.jsonl.gz")):
        print(f.name.split("-")[0], json.dumps(counts(f)))
