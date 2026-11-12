# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "nbtlib>=2.0"]
# ///
"""Block counts per silo in a world's region files (a check after build_offline.py, on a saved world).

For each silo: blocks that are not air inside the shaft (r < 62 about the axis) from the dimension's bottom to the bowl
floor, and the chunks of its footprint that are missing or not yet lit and saved by the game (isLightOn 0: written
offline and never loaded). Compare silos with each other: the same design gives near-equal counts.

  uv run tools/silo/count_silos.py <world> <layout.json> [--number N ...]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import decode_chunk, read_region, section_states  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world"); ap.add_argument("layout")
    ap.add_argument("--number", type=int, nargs="*")
    ap.add_argument("--r", type=float, default=62)
    a = ap.parse_args()
    layout = json.load(open(a.layout))
    cache: dict = {}
    print("silo  blocks      chunks  unlit  missing")
    for s in layout["silos"]:
        if a.number and s["number"] not in a.number:
            continue
        x, z = s["x"], s["z"]
        total, chunks, unlit, missing = 0, 0, 0, 0
        R = int(a.r) + 1
        for cx in range((x - R) >> 4, ((x + R) >> 4) + 1):
            for cz in range((z - R) >> 4, ((z + R) >> 4) + 1):
                key = (cx >> 5, cz >> 5)
                if key not in cache:
                    cache.clear()
                    cache[key] = read_region(os.path.join(a.world, "region", f"r.{key[0]}.{key[1]}.mca"))
                reg = cache[key]
                i = (cx & 31) + (cz & 31) * 32
                if i not in reg:
                    missing += 1
                    continue
                tag = decode_chunk(reg[i][1])
                root = tag if "sections" in tag else tag[""]
                chunks += 1
                unlit += int(root.get("isLightOn", 1)) == 0
                X, Z = np.meshgrid(np.arange(16) + cx * 16 - x, np.arange(16) + cz * 16 - z, indexing="xy")
                inside = np.hypot(X, Z) < a.r                       # [z, x]
                if not inside.any():
                    continue
                for sec in root["sections"]:
                    if int(sec["Y"]) * 16 > 70:
                        continue
                    pal, idx = section_states(sec)
                    air = np.array([p.startswith("minecraft:air") or p.startswith("minecraft:cave_air") for p in pal])
                    g = idx.reshape(16, 16, 16)                     # y, z, x
                    total += int((~air[g] & inside[None]).sum())
        print(f"{s['number']:4d}  {total:10d}  {chunks:6d}  {unlit:5d}  {missing:7d}", flush=True)


if __name__ == "__main__":
    main()
