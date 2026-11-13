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

The steps still ran in perfect concentric rings, an amphitheatre (shader frames 03, 07c and 11 of 1112d). A bank shaped
by earth-moving and grass has no exact circles: with --wobble AMP every lawn or path column of the inner bank and
crest first takes the ground found up to AMP blocks further in or out along its own radius (two slow waves round the
ring whose phase drifts with the radius, so neighbouring contours wave differently; different for each silo; moss from an earlier pass goes back to lawn first), so each contour waves and the
treads vary in width; a contour running diagonally leaves lone one-column pillars and pits, which go to their
neighbours' level; then the moss is laid on the new risers. --smooth-only does that evening alone, for banks waved before it. Trunks and anything else standing on a column keep it.

Moss risers still read as dark hedge bands against the lawn (1112e). Artem's choice (12.11): 25567 sends the Fast
Better Grass resource pack (MIT, Modrinth; grass draws its top on every side), so a grass riser is lawn on all faces.
--grass turns the moss back to grass and keeps moss only below the top block of a riser 2-3 deep, where the block
under grass would be dirt.

With --hero, Silo 18's tree is replaced by hero_tree.py's: the blocks listed in --hero-clear (the previous tree's
offsets about the same base column) that are still logs or leaves go first, and a foot log under the base becomes
grass again.

  ALMIGHTY_URL=... ALMIGHTY_TOKEN_FILE=... uv run tools/silo/banks.py <layout.json> [--number N ...] [--hero]
      [--hero-clear old.json] [--wobble AMP [--smooth-only]] [--grass] [--dry]
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
WOBBLE = (28, 46)                # the inner bank and the crest (floor_r .. rim_r + 4): rings of neighbours never meet here


def hero_seed(n: int, k: int) -> float:
    from hero_tree import seeded
    return seeded(n, k, 977)

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
int unloaded = 0
def scan = {
  def m = [:]
  for (int x = cx - r1 - 1; x <= cx + r1 + 1; x++) {
    for (int z = cz - r1 - 1; z <= cz + r1 + 1; z++) {
      if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { unloaded++; continue }
      int y = lvl.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1
      int n = 0
      while (n++ < 24 && plant(lvl.getBlockState(new BlockPos(x, y, z)))) y--
      m[x * 65536L + z] = y
    }
  }
  m
}
def ground = scan()
if (unloaded) return [unloaded: unloaded, hero: hero, cleared: cleared]
double rx = args.rx as double, rz = args.rz as double
int moved = 0, unmossed = 0, smoothed = 0
def grassS = Blocks.GRASS_BLOCK.defaultBlockState(), dirtS = Blocks.DIRT.defaultBlockState()
if (args.wobble || args.grass) {
  // the previous pass's moss back to lawn first: the risers may move, and it is laid again below
  for (int x = cx - r1; x <= cx + r1; x++) {
    for (int z = cz - r1; z <= cz + r1; z++) {
      double d = Math.hypot(x + 0.5 - rx, z + 0.5 - rz)
      if (d < r0 || d > r1) continue
      int g = ground[x * 65536L + z]
      for (int y = g - 3; y <= g; y++) {
        def p = new BlockPos(x, y, z)
        if (lvl.getBlockState(p).is(Blocks.MOSS_BLOCK)) { lvl.setBlock(p, y == g ? grassS : dirtS, 18); unmossed++ }
      }
    }
  }
}
if (args.wobble) {
  def w = args.wobble
  // each column takes the original ground found a little further in or out along its own radius: the contours wave
  def target = [:]
  if (w.move) for (int x = cx - r1; x <= cx + r1; x++) {
    for (int z = cz - r1; z <= cz + r1; z++) {
      double d = Math.hypot(x + 0.5 - rx, z + 0.5 - rz)
      if (d < (w.r0 as double) || d > (w.r1 as double)) continue
      int g = ground[x * 65536L + z]
      def top = lvl.getBlockState(new BlockPos(x, g, z))
      if (!(top.is(Blocks.GRASS_BLOCK) || top.is(Blocks.DIRT) || top.is(Blocks.SMOOTH_SANDSTONE))) continue
      if (!lvl.getBlockState(new BlockPos(x, g + 1, z)).isAir()) continue      // a trunk or anything standing here
      boolean nearTrunk = false                      // a tree keeps its footing: no pillar, no buried foot
      for (int ax = -2; ax <= 2 && !nearTrunk; ax++)
        for (int az = -2; az <= 2 && !nearTrunk; az++)
          for (int ay = 0; ay <= 2; ay++)
            if (lvl.getBlockState(new BlockPos(x + ax, g + ay, z + az)).is(BlockTags.LOGS)) { nearTrunk = true; break }
      if (nearTrunk) continue
      double th = Math.atan2(z + 0.5 - rz, x + 0.5 - rx)
      double dl = (w.amp as double) * (0.5 * Math.sin(3 * th + (w.p1 as double) + d / 3.0) + 0.5 * Math.sin(5 * th + (w.p2 as double) - d / 4.0))
      double d2 = d + dl
      int sx = (int) Math.floor(rx + d2 * Math.cos(th)), sz = (int) Math.floor(rz + d2 * Math.sin(th))
      def g2 = ground[sx * 65536L + sz]
      if (g2 == null) continue
      int t = Math.max(g - 2, Math.min(g + 2, g2 as int))
      if (t != g) target[x * 65536L + z] = [x, z, g, t]
    }
  }
  for (e in target.values()) {
    int x = e[0], z = e[1], g = e[2], t = e[3]
    def top = lvl.getBlockState(new BlockPos(x, g, z))
    if (t > g) {
      boolean free = true
      for (int y = g + 1; y <= t; y++) free &= lvl.getBlockState(new BlockPos(x, y, z)).isAir()
      if (!free) continue
      for (int y = g; y < t; y++) lvl.setBlock(new BlockPos(x, y, z), dirtS, 18)
    } else {
      for (int y = t + 1; y <= g; y++) lvl.setBlock(new BlockPos(x, y, z), air, 18)
    }
    lvl.setBlock(new BlockPos(x, t, z), top, 18)
    moved++
  }
  ground = scan()
  // a contour running diagonally leaves single columns a block above or below all four neighbours: a lone pillar or
  // pit, not a step. Each goes to its neighbours' nearest level
  for (int pass = 0; pass < 2; pass++) {
    for (int x = cx - r1; x <= cx + r1; x++) {
      for (int z = cz - r1; z <= cz + r1; z++) {
        double d = Math.hypot(x + 0.5 - rx, z + 0.5 - rz)
        if (d < (w.r0 as double) || d > (w.r1 as double)) continue
        int g = ground[x * 65536L + z]
        def nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].collect { o -> ground[(x + o[0]) * 65536L + z + o[1]] }
        if (nb.contains(null)) continue
        int t = nb.every { it > g } ? (nb.min() as int) : nb.every { it < g } ? (nb.max() as int) : g
        if (t == g) continue
        def top = lvl.getBlockState(new BlockPos(x, g, z))
        if (!(top.is(Blocks.GRASS_BLOCK) || top.is(Blocks.DIRT))) continue
        if (!lvl.getBlockState(new BlockPos(x, Math.max(g, t) + 1, z)).isAir()) continue
        boolean nearTrunk = false
        for (int ax = -2; ax <= 2 && !nearTrunk; ax++)
          for (int az = -2; az <= 2 && !nearTrunk; az++)
            for (int ay = 0; ay <= 2; ay++)
              if (lvl.getBlockState(new BlockPos(x + ax, g + ay, z + az)).is(BlockTags.LOGS)) { nearTrunk = true; break }
        if (nearTrunk) continue
        if (t > g) { for (int y = g; y < t; y++) lvl.setBlock(new BlockPos(x, y, z), dirtS, 18) }
        else { for (int y = t + 1; y <= g; y++) lvl.setBlock(new BlockPos(x, y, z), air, 18) }
        lvl.setBlock(new BlockPos(x, t, z), top, 18)
        ground[x * 65536L + z] = t
        smoothed++
      }
    }
  }
  ground = scan()
}
def moss = Blocks.MOSS_BLOCK.defaultBlockState()
int mossed = 0, tufts = 0
for (int x = cx - r1; x <= cx + r1; x++) {
  for (int z = cz - r1; z <= cz + r1; z++) {
    double d = Math.hypot(x + 0.5 - rx, z + 0.5 - rz)
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
    for (int y = low + 1; y <= (args.grass ? g - 1 : g); y++) {     // --grass: the top stays lawn
      def p = new BlockPos(x, y, z)
      def s = lvl.getBlockState(p)
      if (s.is(Blocks.GRASS_BLOCK) || s.is(Blocks.DIRT)) { lvl.setBlock(p, moss, 18); mossed++ }
    }
  }
}
return [mossed: mossed, tufts: tufts, hero: hero, cleared: cleared, moved: moved, unmossed: unmossed, smoothed: smoothed]
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--number", type=int, nargs="*", help="silos (default: all)")
    ap.add_argument("--hero", action="store_true", help="also replace Silo 18's tree with hero_tree.py's")
    ap.add_argument("--hero-clear", help="json [[dx, dy, dz], ...]: the previous tree's blocks about its base")
    ap.add_argument("--wobble", type=float, default=0.0, metavar="AMP",
                    help="wave the inner bank's contours by up to AMP blocks before laying the moss")
    ap.add_argument("--smooth-only", action="store_true",
                    help="with --wobble: only even out lone pillars and pits left by an earlier wobble, move nothing")
    ap.add_argument("--grass", action="store_true",
                    help="the top block of every riser stays grass (green sides from the 25567 resource pack); "
                         "moss only below it, on the lower blocks of a deeper riser")
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
                    "hero": h18 if s["number"] == 18 else None, "grass": a.grass,
                    "wobble": {"r0": WOBBLE[0], "r1": WOBBLE[1], "amp": a.wobble,
                               "p1": 6.283 * hero_seed(s["number"], 1), "p2": 6.283 * hero_seed(s["number"], 2),
                               "move": not a.smooth_only}
                    if a.wobble and s["number"] != 1 else None}   # Silo 1: the opening-day set stands to r 34
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
