"""Light the chunks an offline write left dark, on the running server that owns the world.

regions.py writes chunks with isLightOn = 0 and no SkyLight/BlockLight. The game relights such a chunk only when it
loads it; until then LOD servers (LOD Server Support) and map tools read it straight from disk and draw it black.
So every offline write (build_offline.py, patch_v6.py) must end with this step, before LSS/MapSyncer pick the
chunks up and before the world is saved as a golden.

  ALMIGHTY_URL=http://10.0.6.2:<bridge> ALMIGHTY_TOKEN_FILE=<server>/config/almighty/token \\
  uv run --with httpx --with numpy --with nbtlib relight.py --world <server>/world --layout layout.json [--radius 64]

Reads the region files (read-only) for full chunks with isLightOn = 0 within --radius of each silo, loads each silo's
dark box with area.prepare, releases it (the game lights and saves the chunks as they unload), runs save-all flush and
scans again. Exit code 1 if any chunk is still dark. Then refresh LSS (/lsslod store invalidate all, then
/lsslod store backfill start once the drop is done) and MapSyncer.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import regions  # noqa: E402


def dark_chunks(world: str, silos: list[dict], radius: int) -> dict[int, list[tuple[int, int]]]:
    want, owner = collections.defaultdict(set), {}
    for s in silos:
        for cx in range((s["x"] - radius) >> 4, ((s["x"] + radius) >> 4) + 1):
            for cz in range((s["z"] - radius) >> 4, ((s["z"] + radius) >> 4) + 1):
                want[(cx >> 5, cz >> 5)].add((cx, cz))
                owner[(cx, cz)] = s["number"]
    out = collections.defaultdict(list)
    for (rx, rz), cs in want.items():
        path = f"{world}/region/r.{rx}.{rz}.mca"
        if not os.path.exists(path):
            continue
        chunks = regions.read_region(path)
        for cx, cz in cs:
            i = (cx & 31) + (cz & 31) * 32
            if i not in chunks:
                continue
            tag = regions.decode_chunk(chunks[i][1])
            if str(tag.get("Status", "")).endswith("full") and int(tag.get("isLightOn", 0)) == 0:
                out[owner[(cx, cz)]].append((cx, cz))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--layout", required=True)
    ap.add_argument("--radius", type=int, default=64)
    a = ap.parse_args()
    from build_live import Bridge, settle
    silos = json.load(open(a.layout))["silos"]
    dark = dark_chunks(a.world, silos, a.radius)
    print(f"dark chunks: {sum(map(len, dark.values()))} at {len(dark)} silos", flush=True)
    br = Bridge()
    for n in sorted(dark):
        cs = dark[n]
        x0, x1 = min(c[0] for c in cs) * 16, max(c[0] for c in cs) * 16 + 15
        z0, z1 = min(c[1] for c in cs) * 16, max(c[1] for c in cs) * 16 + 15
        r = br.call("area.prepare", {"from": [x0, z0], "to": [x1, z1], "ttl_seconds": 120, "wait": 50})
        br.call("area.release", {"id": r["id"]})
        if r.get("ready", 0) < r.get("chunks", 1):
            print(f"silo {n}: only {r.get('ready')}/{r.get('chunks')} ready", flush=True)
        settle(br, limit=1000, log=lambda m: print(m, flush=True))
        st = br.call("status", {})
        print(f"silo {n}: {len(cs)} dark, mspt {st['mspt']}", flush=True)
    br.call("command", {"commands": ["save-all flush"]})
    time.sleep(2)
    left = sum(map(len, dark_chunks(a.world, silos, a.radius).values()))
    print(f"still dark after save-all: {left}", flush=True)
    sys.exit(1 if left else 0)


if __name__ == "__main__":
    main()
