# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Green risers on the crater banks and berms, and Silo 18's tree, in the built world.

S3E09 05, 10 and 23 show the banks as smooth mown lawn. In blocks a 4 m bank over 12 m is a flight of one-block
steps, and each riser is the side of a grass block: dirt under a thin green edge, which reads from the bowl and from the
air as concentric brown terraces (shader frames 12.11, 03 and 07c). The tufts surface.fringe put at each riser's foot
did not hide it and added stripes of their own. Here every grass or dirt block whose side is open over a lower
neighbour (1-3 blocks down; deeper is a wall, not a bank) becomes a moss block, green on every face and close to the
plains grass in tone, and the tufts go. Moss does not spread by itself (only by bone meal).

With --hero, Silo 18's tree is replaced by hero_tree.py's: the blocks listed in --hero-clear (the previous tree's
offsets about the same base column) that are still logs or leaves go first, and a foot log under the base becomes
grass again.

  ALMIGHTY_URL=... ALMIGHTY_TOKEN_FILE=... uv run tools/silo/banks.py <layout.json> [--number N ...] [--hero]
      [--hero-clear old.json] [--dry]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BANK = (28, 67)                  # surface.Site: floor_r - 2 .. out_r + 3 about each portal

SCRIPT = r"""
import net.minecraft.core.BlockPos
import net.minecraft.tags.BlockTags
import net.minecraft.world.level.levelgen.Heightmap
def lvl = server.overworld()
int cx = args.x as int, cz = args.z as int, r0 = args.r0 as int, r1 = args.r1 as int
def plant = { s -> s.isAir() || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) || (s.canBeReplaced() && s.getFluidState().isEmpty()) }
def air = Blocks.AIR.defaultBlockState()
int hero = 0, cleared = 0
if (args.hero) {
  int x = args.hero.x as int, z = args.hero.z as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) return [unloaded: 1]
  int y = lvl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1
  def tree = { s -> s.isAir() || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) }
  while (tree(lvl.getBlockState(new BlockPos(x, y, z)))) y--
  if (lvl.getBlockState(new BlockPos(x, y + 1, z)).is(BlockTags.LOGS)) {   // the old foot log in the grass's place
    y++
    lvl.setBlock(new BlockPos(x, y, z), Blocks.GRASS_BLOCK.defaultBlockState(), 18)
    cleared++
  }
  y++                                                // the first block above the ground
  for (c in (args.hero.clear ?: [])) {
    def p = new BlockPos(x + (c[0] as int), y + (c[1] as int), z + (c[2] as int))
    if (tree(lvl.getBlockState(p)) && !lvl.getBlockState(p).isAir()) { lvl.setBlock(p, air, 18); cleared++ }
  }
  for (b in args.hero.blocks) {
    def p = new BlockPos(x + (b[0] as int), y + (b[1] as int), z + (b[2] as int))
    if (b[3].contains('_log') || lvl.getBlockState(p).canBeReplaced()) {
      gm.command("setblock ${p.getX()} ${p.getY()} ${p.getZ()} ${b[3]}")
      hero++
    }
  }
}
def ground = [:]
int unloaded = 0
for (int x = cx - r1 - 1; x <= cx + r1 + 1; x++) {
  for (int z = cz - r1 - 1; z <= cz + r1 + 1; z++) {
    if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { unloaded++; continue }
    int y = lvl.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1
    int n = 0
    while (n++ < 24 && plant(lvl.getBlockState(new BlockPos(x, y, z)))) y--
    ground[x * 65536L + z] = y
  }
}
if (unloaded) return [unloaded: unloaded, hero: hero, cleared: cleared]
def moss = Blocks.MOSS_BLOCK.defaultBlockState()
int mossed = 0, tufts = 0
for (int x = cx - r1; x <= cx + r1; x++) {
  for (int z = cz - r1; z <= cz + r1; z++) {
    double d = Math.hypot(x + 0.5 - (args.rx as double), z + 0.5 - (args.rz as double))
    if (d < r0 || d > r1) continue
    int g = ground[x * 65536L + z]
    for (int dy = 1; dy <= 2; dy++) {                 // the tufts at the riser feet
      def p = new BlockPos(x, g + dy, z)
      def s = lvl.getBlockState(p)
      if (s.is(Blocks.SHORT_GRASS) || s.is(Blocks.TALL_GRASS)) { lvl.setBlock(p, air, 18); tufts++ }
    }
    int low = g
    for (o in [[1, 0], [-1, 0], [0, 1], [0, -1]]) low = Math.min(low, ground[(x + o[0]) * 65536L + z + o[1]] as int)
    int drop = g - low
    if (drop < 1 || drop > 3) continue
    for (int y = low + 1; y <= g; y++) {
      def p = new BlockPos(x, y, z)
      def s = lvl.getBlockState(p)
      if (s.is(Blocks.GRASS_BLOCK) || s.is(Blocks.DIRT)) { lvl.setBlock(p, moss, 18); mossed++ }
    }
  }
}
return [mossed: mossed, tufts: tufts, hero: hero, cleared: cleared]
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--number", type=int, nargs="*", help="silos (default: all)")
    ap.add_argument("--hero", action="store_true", help="also replace Silo 18's tree with hero_tree.py's")
    ap.add_argument("--hero-clear", help="json [[dx, dy, dz], ...]: the previous tree's blocks about its base")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    layout = json.load(open(a.layout))
    silos = [s for s in layout["silos"] if "ring" in s and not s.get("unplaced")
             and (not a.number or s["number"] in a.number)]
    h18 = None
    if a.hero:
        import hero_tree
        from paths import BEARING
        s18 = next(s for s in layout["silos"] if s.get("number") == 18 and "ring" in s)
        out = BEARING[s18.get("dir", "W")]
        x, z = hero_tree.place(s18["ring"], out)
        h18 = {"x": x, "z": z, "blocks": [[*c, st] for c, st in sorted(hero_tree.blocks(out).items())],
               "clear": json.load(open(a.hero_clear)) if a.hero_clear else []}
        print(f"Silo 18's tree at {x},{z}: {len(h18['blocks'])} blocks, clearing {len(h18['clear'])}", flush=True)
    print(f"{len(silos)} silos", flush=True)
    if a.dry:
        return
    from build_live import Bridge, settle
    br = Bridge()
    for s in sorted(silos, key=lambda s_: s_["number"]):
        rx, rz = s["ring"]
        cx, cz = int(math.floor(rx)), int(math.floor(rz))
        r1 = BANK[1]
        area = br.call("area.prepare", {"from": [cx - r1 - 2, cz - r1 - 2], "to": [cx + r1 + 2, cz + r1 + 2], "wait": 50})
        try:
            args = {"x": cx, "z": cz, "rx": rx, "rz": rz, "r0": BANK[0], "r1": r1,
                    "hero": h18 if s["number"] == 18 else None}
            for attempt in range(3):                # leased chunks finish loading a little after area.prepare
                res = br.call("script", {"code": SCRIPT, "args": args, "timeout_ms": 10000})
                if not res.get("ok"):
                    raise RuntimeError(f"script: {res}")
                print(f"silo {s['number']}: {res.get('value')}", flush=True)
                if not (res.get("value") or {}).get("unloaded"):
                    break
                args["hero"] = None if (res.get("value") or {}).get("hero") else args["hero"]
                time.sleep(10)
        finally:
            br.call("area.release", {"id": area["id"]})
        settle(br, log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
