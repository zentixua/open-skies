# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "nbtlib>=2.0", "httpx>=0.27"]
# ///
"""Put chunks of the live world back as they are in the golden copy, through the Almighty build method.

For repairing what a build pass took that it should not have (a village inside the plain). Block states come
from the golden region files, every block in the given y range is sent (air included), so the chunks end exactly as
golden there. Block entity contents (chest loot, signs' text) are not carried: the game creates empty ones.

  ALMIGHTY_URL=... ALMIGHTY_TOKEN_FILE=... uv run tools/silo/restore.py <golden world> --chunks 282:102 283:102 \\
      --y 50 120 --state ~/claude/silo-work/state [--dry]
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_live import Bridge, build  # noqa: E402
from regions import decode_chunk, read_region, section_states  # noqa: E402
from volume import Volume  # noqa: E402


def chunk_volume(world: str, cx: int, cz: int, y0: int, y1: int) -> Volume:
    rx, rz = cx >> 5, cz >> 5
    chunks = read_region(os.path.join(world, "region", f"r.{rx}.{rz}.mca"))
    idx = (cx & 31) + (cz & 31) * 32
    if idx not in chunks:
        raise SystemExit(f"chunk {cx},{cz} not in golden")
    root = decode_chunk(chunks[idx][1])
    v = Volume((cx * 16, y0, cz * 16), (16, y1 - y0 + 1, 16))
    for sec in root["sections"]:
        sy = int(sec["Y"])
        if sy * 16 + 15 < y0 or sy * 16 > y1 or "block_states" not in sec:
            continue
        pal, grid = section_states(sec)
        ids = np.array([v.id(p) for p in pal], dtype=np.uint16)[grid].reshape(16, 16, 16)   # [y][z][x]
        for ly in range(16):
            wy = sy * 16 + ly
            if y0 <= wy <= y1:
                v.ids[:, wy - y0, :] = ids[ly].T
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world")
    ap.add_argument("--chunks", nargs="+", required=True, help="cx:cz")
    ap.add_argument("--y", nargs=2, type=int, required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    bridge = None if a.dry else Bridge()
    for c in a.chunks:
        cx, cz = map(int, c.split(":"))
        v = chunk_volume(a.world, cx, cz, *a.y)
        build(v, f"restore_{cx}_{cz}", a.state, bridge, dry=a.dry, log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
