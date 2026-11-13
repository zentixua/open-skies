# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "httpx>=0.27"]
# ///
"""One biome over the levelled field, so the grass is one green.

The shader frames of 12.11 (01, 02 from the air) show dark green patches with blocky edges across the complex: the
field was levelled over Zearth's own biomes, and grass and leaves take their colour from the biome. S3E09 (01, 05, 23,
28) shows one mown lawn. Every chunk wholly inside the levelled core (field weight >= --core everywhere in it) gets
the biome most common there (sampled at the field level), by vanilla /fillbiome, one chunk column of 16 x 128 x 16
(the command's 32768 limit) at a time; /fillbiome sends the new biomes to the clients itself. Outside the core Zearth's
biomes stay, where the field already blends into its relief.

  ALMIGHTY_URL=... ALMIGHTY_TOKEN_FILE=... uv run tools/silo/biome.py <layout.json> --world <world> --state <dir> [--dry]
"""
from __future__ import annotations

import argparse
import collections
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SAMPLE = r"""
import net.minecraft.core.BlockPos
def lvl = server.overworld()
def out = [:]
for (c in args.pts) {
  int x = c[0] as int, z = c[1] as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) continue
  def key = lvl.getBiome(new BlockPos(x, args.y as int, z)).unwrapKey().map { it.location().toString() }.orElse('?')
  out[key] = (out[key] ?: 0) + 1
}
return out
"""

FILL = r"""
def lvl = server.overworld()
int done = 0, skipped = 0
for (c in args.chunks) {
  int cx = c[0] as int, cz = c[1] as int
  if (lvl.getChunkSource().getChunkNow(cx, cz) == null) { skipped++; continue }
  int x = cx * 16, z = cz * 16
  gm.command("fillbiome ${x} ${args.y0} ${z} ${x + 15} ${args.y0 + 127} ${z + 15} ${args.biome}")
  done++
}
return [done: done, unloaded: skipped]
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--world", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--core", type=float, default=0.95, help="field weight every column of a chunk must reach")
    ap.add_argument("--biome", default="auto", help="biome id, or auto: the most common in the core")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    from field import Field
    field = Field(a.layout, a.world, a.state)
    W, x0, z0 = field.weight, field.x0, field.z0
    chunks = []
    for cx in range(-(-x0 // 16), (x0 + W.shape[0]) // 16):
        for cz in range(-(-z0 // 16), (z0 + W.shape[1]) // 16):
            i, k = cx * 16 - x0, cz * 16 - z0
            if i + 16 <= W.shape[0] and k + 16 <= W.shape[1] and W[i:i + 16, k:k + 16].min() >= a.core:
                chunks.append((cx, cz))
    y0 = field.level - 40                        # 128 blocks: from under the plain's dirt to above the tallest tree
    print(f"{len(chunks)} core chunks, field level {field.level}, biome column y {y0}..{y0 + 127}", flush=True)
    if a.dry:
        return
    from build_live import Bridge, settle
    br = Bridge()
    T = 8                                        # 8 x 8 chunks a lease (deep world: see build_live.settle)
    tiles = collections.defaultdict(list)
    for cx, cz in chunks:
        tiles[(cx // T, cz // T)].append([cx, cz])
    biome = a.biome
    if biome == "auto":
        counts = collections.Counter()
        for (tx, tz), cs in sorted(tiles.items())[:: max(1, len(tiles) // 12)]:
            area = br.call("area.prepare", {"from": [tx * T * 16, tz * T * 16],
                                            "to": [tx * T * 16 + T * 16 - 1, tz * T * 16 + T * 16 - 1], "wait": 50})
            try:
                pts = [[c[0] * 16 + 8, c[1] * 16 + 8] for c in cs]
                res = br.call("script", {"code": SAMPLE, "args": {"pts": pts, "y": field.level}})
                counts.update(res.get("value") or {})
            finally:
                br.call("area.release", {"id": area["id"]})
            settle(br, log=lambda m: print(m, flush=True))
        print(f"biomes in the core (sampled): {dict(counts.most_common())}", flush=True)
        biome = counts.most_common(1)[0][0]
    print(f"filling {len(chunks)} chunks with {biome}", flush=True)
    for (tx, tz), cs in sorted(tiles.items()):
        area = br.call("area.prepare", {"from": [tx * T * 16, tz * T * 16],
                                        "to": [tx * T * 16 + T * 16 - 1, tz * T * 16 + T * 16 - 1], "wait": 50})
        try:
            for attempt in range(3):
                res = br.call("script", {"code": FILL, "args": {"chunks": cs, "y0": y0, "biome": biome},
                                         "timeout_ms": 10000})
                print(f"tile {tx},{tz}: {res.get('value')}", flush=True)
                if not (res.get("value") or {}).get("unloaded"):
                    break
                time.sleep(10)
        finally:
            br.call("area.release", {"id": area["id"]})
        settle(br, log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
