# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "httpx>=0.27"]
# ///
"""The footpaths of the 2052 complex, from the show's high oblique (Reddit frame 1, rectified by canon_fit.py).

What the frame shows, and what is laid here (dirt path on the finished ground, short grass above it removed):
- a pale path circle round every ring, where its crater meets the plain (r 64);
- the axis road due north from Silo 1 to the gate, and on south to Silo 2 (3 wide);
- the founders' lines of the plaque (S3E09) as paths from Silo 1's circle: due west to 42, due east to 25, curving
  south-west to 30 and south-east to 10; to the north a cross path 40 m beyond the 44 and 17 circles, joining the axis;
- between neighbouring rings of a flower, a short link where their circles nearly touch;
- from each circle a stub in to the crater floor, along the way out of the ramp (each ring's own bearing);
- seven rosette discs, each in the triangle of three rings where the frame shows one (concentric path rings).
With --trees, also the berm and plain trees, and the one tree before Silo 18's camera (hero_tree.py).
The rings in the frame stand within 20-40 m of the fitted layout, so the paths are laid relative to the built rings
(topology from the frame) rather than traced pixel by pixel.

  ALMIGHTY_URL=... ALMIGHTY_TOKEN_FILE=... uv run tools/silo/paths.py <layout.json> [--dry] [--png out.png]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RING_PATH_R = 110         # surface.Site.path_r: the ring path, Ø≈220 (SPEC 1)
PATH_W = 3                # surface.Site.path_half: 3 wide, two people side by side (S3E09 05)
FLOOR_R = 55              # surface.Site.floor_r
STUB_END = 24             # the stub's pad, metres from the centre on the cut's side (2052 aerial: about half the floor)
LINK_MAX = 1.08           # flower neighbours: centres within this many ring spacings
ROSETTES = [(49, 48, 43), (31, 30, 29), (32, 33, 29), (35, 29, 34), (19, 20, 14), (12, 7, 11), (13, 7, 8)]
ROSETTE_R = 41          # S3E09 aerial: ~50 m across at the old 156 m spacing, scaled to 270 like the layout
BEARING = {"W": (-1, 0), "N": (0, -1), "E": (1, 0), "S": (0, 1)}
CREST_R = 77              # surface.Site.crest_r

SCRIPT = r"""
import net.minecraft.world.level.levelgen.Heightmap
import net.minecraft.core.BlockPos
import net.minecraft.world.level.block.Blocks
def lvl = server.overworld()
int n = 0, skipped = 0
for (c in args.cols) {
  int x = c[0] as int, z = c[1] as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { skipped++; continue }
  int y = lvl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1
  def pos = new BlockPos(x, y, z)
  def st = lvl.getBlockState(pos)
  if (st.is(Blocks.GRASS_BLOCK) || st.is(Blocks.DIRT) || st.is(Blocks.COARSE_DIRT) || st.is(Blocks.PODZOL)
      || st.is(Blocks.DIRT_PATH)) {
    def up = pos.above()
    def su = lvl.getBlockState(up)
    if (!su.isAir()) {
      if (!su.canBeReplaced()) continue
      lvl.setBlock(up, Blocks.AIR.defaultBlockState(), 3)
    }
    // S3E09 05: the paths are pale beige compacted fine gravel, flush with the lawn
    lvl.setBlock(pos, Blocks.SMOOTH_SANDSTONE.defaultBlockState(), 3)
    n++
  }
}
int greened = 0
for (c in (args.floors ?: [])) {      // crater floors laid before 2052 grass: coarse dirt back to grass
  int x = c[0] as int, z = c[1] as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { skipped++; continue }
  int y = lvl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1
  def pos = new BlockPos(x, y, z)
  if (lvl.getBlockState(pos).is(Blocks.COARSE_DIRT)) { lvl.setBlock(pos, Blocks.GRASS_BLOCK.defaultBlockState(), 3); greened++ }
}
int trees = 0
for (t in (args.trees ?: [])) {       // S3E09 05, 10, 28: a few round-crowned trees on the berms, young ones on the plain
  int x = t[0] as int, z = t[1] as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { skipped++; continue }
  int y = lvl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1
  if (!lvl.getBlockState(new BlockPos(x, y, z)).is(Blocks.GRASS_BLOCK)) continue
  if (!lvl.getBlockState(new BlockPos(x, y + 1, z)).canBeReplaced()) continue
  gm.command("place feature ${t[2]} ${x} ${y + 1} ${z}")
  trees++
}
int hero = 0
if (args.hero) {                      // the tree before Silo 18's camera (hero_tree.py): logs replace, leaves fill air
  int x = args.hero.x as int, z = args.hero.z as int
  if (lvl.getChunkSource().getChunkNow(x >> 4, z >> 4) == null) { skipped++ }
  else {
    // the ground under the tree's own blocks (a rerun finds its trunk): the first block that is not air, log or leaves;
    // when the foot log (dy -1) took the grass's place, the first block above the ground is one higher
    int y = lvl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1
    def tree = { s -> s.isAir() || s.is(net.minecraft.tags.BlockTags.LOGS) || s.is(net.minecraft.tags.BlockTags.LEAVES) }
    while (tree(lvl.getBlockState(new BlockPos(x, y, z)))) y--
    y += lvl.getBlockState(new BlockPos(x, y + 1, z)).is(net.minecraft.tags.BlockTags.LOGS) ? 2 : 1
    for (b in args.hero.blocks) {
      gm.command("setblock ${x + (b[0] as int)} ${y + (b[1] as int)} ${z + (b[2] as int)} ${b[3]}" + (b[3].contains('_log') ? '' : ' keep'))
      hero++
    }
  }
}
return [placed: n, greened: greened, trees: trees, hero: hero, unloaded: skipped]
"""


def stamp(cells: set, x: float, z: float, w: int) -> None:
    r = (w - 1) / 2
    for dx in range(-int(math.ceil(r)), int(math.ceil(r)) + 1):
        for dz in range(-int(math.ceil(r)), int(math.ceil(r)) + 1):
            if math.hypot(dx, dz) <= r + 0.5:
                cells.add((int(math.floor(x + dx + 0.5)), int(math.floor(z + dz + 0.5))))


def line(cells, pts, w=2):
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) * 2))
        for t in np.linspace(0, 1, n + 1):
            stamp(cells, x0 + t * (x1 - x0), z0 + t * (z1 - z0), w)


def curve(p0, c, p1, n=40):
    """Quadratic Bezier from p0 through control c to p1."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in np.linspace(0, 1, n)]


def on_circle(c, toward, r=RING_PATH_R):
    dx, dz = toward[0] - c[0], toward[1] - c[1]
    L = math.hypot(dx, dz)
    return (c[0] + r * dx / L, c[1] + r * dz / L)


def canon_lines() -> dict:
    return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "canon", "lines.json")))


def gate_distance(layout: dict, u=None) -> float:
    """Metres along the axis from Silo 1's centre to the gate canopy measured on the 2052 aerial, or to layout's gate."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canon", "surroundings.json")
    if os.path.exists(path):
        can = next((i for i in json.load(open(path))["items"] if i["id"] == "gate_canopy"), None)
        if can:
            cx = sum(p_[0] for p_ in can["line"]) / len(can["line"]); cz = sum(p_[1] for p_ in can["line"]) / len(can["line"])
            if u is None:
                b_ = math.radians(canon_lines()["axis"]["bearing_deg"]); u = (math.sin(b_), -math.cos(b_))
            return cx * u[0] + cz * u[1]
    one = next(s for s in layout["silos"] if s["number"] == 1)["ring"]
    return math.dist(one, layout["gate"])


def tangent_arc(c1, c2, side: int, n: int = 40) -> list:
    """An arc of radius RING_PATH_R touching both ring paths (centres c1, c2) from outside, on the side given."""
    dx, dz = c2[0] - c1[0], c2[1] - c1[1]
    D = math.hypot(dx, dz)
    rho = RING_PATH_R
    h = math.sqrt(max((RING_PATH_R + rho) ** 2 - (D / 2) ** 2, 0.0))
    mx, mz = (c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2
    px, pz = mx - side * dz / D * h, mz + side * dx / D * h
    t1 = (px + (c1[0] - px) * rho / (RING_PATH_R + rho), pz + (c1[1] - pz) * rho / (RING_PATH_R + rho))
    t2 = (px + (c2[0] - px) * rho / (RING_PATH_R + rho), pz + (c2[1] - pz) * rho / (RING_PATH_R + rho))
    a1, a2 = math.atan2(t1[1] - pz, t1[0] - px), math.atan2(t2[1] - pz, t2[0] - px)
    da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    return [(px + rho * math.cos(a1 + da * i / n), pz + rho * math.sin(a1 + da * i / n)) for i in range(n + 1)]


def rosette_trees(layout: dict) -> list:
    """[(x, z, r)]: the measured rosettes whose disc is trees (canon/lines.json), in world metres."""
    one = next(s for s in layout["silos"] if s["number"] == 1)["ring"]
    rot = math.radians(layout.get("rotation_deg", 0)); cs, sn = math.cos(rot), math.sin(rot); e = layout["spacing"]
    out = []
    for ro in canon_lines()["rosettes"]:
        if "tree" in ro["kind"]:
            u, v = ro["centre"][0] * e, ro["centre"][1] * e
            out.append((one[0] + u * cs - v * sn, one[1] + u * sn + v * cs, ro["outer_r_m"] - 4))
    return out


def plan(layout: dict) -> tuple[set, set]:
    """(path cells, axis road cells) in world x, z."""
    ring = {s["number"]: tuple(s["ring"]) for s in layout["silos"] if not s.get("unplaced")}
    bearing = {s["number"]: s.get("dir", "W") for s in layout["silos"]}
    spacing = layout["spacing"]
    cells, road = set(), set()
    # circles
    for c in ring.values():
        n = int(2 * math.pi * RING_PATH_R * 2)
        line(cells, [(c[0] + RING_PATH_R * math.cos(a), c[1] + RING_PATH_R * math.sin(a))
                     for a in np.linspace(0, 2 * math.pi, n)], PATH_W)
    # stubs, one straight line per ring (the 2052 aerial, S3E09 05): from the circle through the berm's cut (opposite
    # the slot) into the bowl, ending in a rounded pad ≈1.5 path widths across about halfway to the centre; the camera
    # shelter and the stair head stand on the same line beyond the centre (aerial: ≈0.55 of the floor's radius)
    for k, c in ring.items():
        if k == 1:
            continue                    # Silo 1: the path runs due south from the opening-day set (event.py)
        dx, dz = BEARING[bearing[k]]
        end = STUB_END
        line(cells, [(c[0] - end * dx, c[1] - end * dz), (c[0] - RING_PATH_R * dx, c[1] - RING_PATH_R * dz)], PATH_W)
        pr = 1.5 * PATH_W / 2 + 0.5
        for a in range(-3, 4):
            for b in range(-3, 4):
                if math.hypot(a, b) <= pr:
                    cells.add((int(math.floor(c[0] - end * dx + a + 0.5)), int(math.floor(c[1] - end * dz + b + 0.5))))
    # links between neighbours: no straight connector on any centre line in the 2052 aerial (canon/lines.json, 82
    # pairs); neighbours join by short arcs tangent to both ring paths. Here an arc of the ring path's own radius,
    # touching both circles from outside, on the side a hash picks
    nums = sorted(ring)
    for i in nums:
        for j in nums:
            if i < j and math.dist(ring[i], ring[j]) <= LINK_MAX * spacing:
                line(cells, tangent_arc(ring[i], ring[j], 1 if h01(i, j, 31) < 0.5 else -1), 2)
    # The axis, the founders' lines and the north cross are drawn in the show's own frame (gate due north of Silo 1)
    # from their measurement on the 2052 aerial (canon/lines.json, canon_lines.py: homography error 6 m rms, 12 max)
    # and turned into the world by the layout's rotation (128 degrees: "north" in the frame is not world north).
    one = ring[1]
    rot = math.radians(layout.get("rotation_deg", 0))
    cs, sn = math.cos(rot), math.sin(rot)
    W = lambda p: (one[0] + p[0] * cs - p[1] * sn, one[1] + p[0] * sn + p[1] * cs)      # frame metres -> world
    C = lambda p: ((p[0] - one[0]) * cs + (p[1] - one[1]) * sn, -(p[0] - one[0]) * sn + (p[1] - one[1]) * cs)
    lw = lambda cells_, pts, w: line(cells_, [W(p) for p in pts], w)
    meas = canon_lines()
    e = spacing
    M = {l["name"]: l for l in meas["lines"]}
    U = lambda p: (p[0] * e, p[1] * e)                     # canon units -> frame metres
    # the axis: one straight line through Silo 1's centre on the measured bearing (0.25 deg off the frame's north;
    # its halves agree within 0.08 deg), from the gate end of the measured path to where it meets Silo 2's ring path.
    # Silo 2 stays on its canon point (11 m off the line in the frame fit; moving it would break the 10 m overlay)
    b_ = math.radians(meas["axis"]["bearing_deg"])
    u = (math.sin(b_), -math.cos(b_))                       # toward the gate
    # the gate end: the canopy where the 2052 frame puts it (canon/surroundings.json, 1.54 km from Silo 1; layout's
    # gate at 1.35 km comes from the joint fit with the plaque: frame over plaque, as for Silo 2)
    t_gate = gate_distance(layout, u)
    lw(road, [(u[0] * t_gate, u[1] * t_gate), (u[0] * RING_PATH_R, u[1] * RING_PATH_R)], 3)
    two = C(ring[2])
    bx, bz = -u[0], -u[1]
    proj = two[0] * bx + two[1] * bz
    d2 = RING_PATH_R ** 2 - (two[0] - proj * bx) ** 2 - (two[1] - proj * bz) ** 2
    t_end = proj - math.sqrt(max(d2, 0.0))
    lw(road, [(bx * RING_PATH_R, bz * RING_PATH_R), (bx * t_end, bz * t_end)], 3)
    ringc = {k: C(v) for k, v in ring.items()}
    # founders' lines W (to 42) and E (to 25): measured, straight from Silo 1's ring path, then onto the far circle
    for nm, k in (("founders_west", 42), ("founders_east", 25)):
        a_, b2 = U(M[nm]["from"]), U(M[nm]["to"])
        tip = on_circle(ringc[k], b2)
        lw(cells, [a_, b2] + curve(b2, (b2[0] + (b2[0] - a_[0]) * 0.05, b2[1] + (b2[1] - a_[1]) * 0.05), tip, 12), 2)
    # 1 -> 30 and 1 -> 10: S-bends from Silo 1's south ring path (not lines in the frame)
    for k, side in ((30, -1), (10, 1)):
        a_ = (side * 20, RING_PATH_R - 4)
        b_c = on_circle(ringc[k], (0.0, 0.0))
        lw(cells, curve(a_, (a_[0] + side * 30, a_[1] + 60), b_c), 2)
    # the north cross: straight at the measured v, its ends curving onto the 44 and 17 ring paths
    nc = M["north_cross"]
    pa, pb = U(nc["from"]), U(nc["to"])
    lw(cells, [pa, pb], 2)
    for end, k in ((pa, 44), (pb, 17)):
        tip = on_circle(ringc[k], end)
        lw(cells, curve(end, (end[0], (end[1] + tip[1]) / 2), tip, 16), 2)
    # rosettes: the nine of the 2052 aerial at their measured centres and sizes (canon/lines.json): concentric ones
    # with their rings, a plain one, and circles with trees inside (the trees: rosette_trees)
    for ro in meas["rosettes"]:
        c0 = W(U(ro["centre"]))
        R0 = ro["outer_r_m"]
        radii = sorted(set([round(r, 1) for r in (ro.get("ring_radii_m_angle_mean") or [])] + [R0])) \
            if "concentric" in ro["kind"] else [R0]
        for r in radii:
            pts = [(c0[0] + r * math.cos(t), c0[1] + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, int(r * 8))]
            line(cells, pts, 2)
        if "concentric" in ro["kind"]:
            stamp(cells, c0[0], c0[1], 3)
    return cells - road, road


def h01(*v) -> float:
    """Stable 0..1 per integer tuple."""
    h = 0x9E3779B1
    for x in v:
        h = ((h ^ (int(x) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        h ^= h >> 13
    return (h & 0xFFFF) / 65535.0


def hero(layout: dict):
    """Silo 18's tree (hero_tree.py): its trunk column and blocks [[dx, dy, dz, state]], or None without Silo 18."""
    import hero_tree
    s18 = next((s_ for s_ in layout["silos"] if s_.get("number") == 18 and "ring" in s_), None)
    if s18 is None:
        return None
    out = BEARING[s18.get("dir", "W")]
    x, z = hero_tree.place(s18["ring"], out)
    return {"x": x, "z": z, "blocks": [[*c, st] for c, st in sorted(hero_tree.blocks(out).items())]}


def grove_trees(rings, ground: str, free, water: set, step: int = 5) -> list:
    """Trees where the show's 2052 aerial has groves and forest (canon_ground.py): on a jittered 5 m grid, each spot
    planted with a chance from the aerial's tree fraction (smoothed over 3 cells) weighted by how dark the canopy
    reads there, so solid dark masks become closed canopy and thin belts stay open. Dark oak where it reads dark, oak
    and big oak elsewhere; spruce joins in the outer forest (beyond 600 m from any ring). Nothing inside a ring's path
    circle (the bowls and berms carry only the crest trees)."""
    d = np.load(ground)
    from scipy.signal import convolve2d
    k3 = np.ones((3, 3)) / 9
    T = convolve2d(d["tree"].astype(float), k3, mode="same")
    D = convolve2d(d["dark"].astype(float), k3, mode="same") if "dark" in d else np.full(T.shape, 0.5)
    dens = np.clip(T * (0.6 + 0.6 * D), 0, 1)
    x0, z0, C = int(d["x0"]), int(d["z0"]), int(d["cell"])
    rx = np.array([r[0] for r in rings]); rz = np.array([r[1] for r in rings])
    out = []
    for gx in range(x0, x0 + T.shape[0] * C, step):
        for gz in range(z0, z0 + T.shape[1] * C, step):
            x, z = gx + int(h01(gx, gz, 16) * step), gz + int(h01(gx, gz, 17) * step)
            i, k_ = (x - x0) // C, (z - z0) // C
            if not (0 <= i < T.shape[0] and 0 <= k_ < T.shape[1]) or dens[i, k_] < 0.25:
                continue
            if h01(gx, gz, 19) > dens[i, k_] ** 1.2:
                continue
            dmin = float(np.min(np.hypot(rx - x, rz - z)))
            if dmin < RING_PATH_R + 6:
                continue
            if any((x + dx, z + dz) in water for dx in (-2, 0, 2) for dz in (-2, 0, 2)):
                continue
            if not free(x, z, 0):
                continue
            r = h01(gx, gz, 18)
            if dmin > 600 and r < 0.3:
                kind = "minecraft:spruce"
            elif D[i, k_] > 0.5 and r < 0.75:
                kind = "minecraft:dark_oak"
            elif r < 0.85:
                kind = "minecraft:oak"
            else:
                kind = "minecraft:fancy_oak"
            out.append([x, z, kind])
    return out


def trees(layout: dict, avoid: set, keep_clear=(), ground: str | None = None, water: set | None = None) -> list:
    """Tree spots: 0-2 on each berm crest (S3E09 10: a round-crowned tree on the crest, another nearby), then the
    plain's trees: with ground (canon_ground.py's npz) the groves and belts where the show's 2052 aerial has them,
    otherwise young trees scattered over the plain (05, 28); never on a path, a pond, a bowl floor or an earlier tree's
    crown."""
    rings = [s_["ring"] for s_ in layout["silos"] if "ring" in s_]
    out, taken = [], list(keep_clear)
    def free(x, z, r):
        if any(math.hypot(x - a, z - b) < r for a, b in taken):
            return False
        return not any((x + dx, z + dz) in avoid for dx in range(-4, 5) for dz in range(-4, 5))
    for k, (rx, rz) in enumerate(rings):
        for j in range(1 + int(h01(k, 1) * 1.99)):          # 1-2 on every crest (S3E09 10, 23)
            a = 2 * math.pi * h01(k, j, 2)
            x, z = int(round(rx + CREST_R * math.cos(a))), int(round(rz + CREST_R * math.sin(a)))
            if free(x, z, 12):
                out.append([x, z, "minecraft:fancy_oak" if h01(k, j, 3) < 0.3 else "minecraft:oak"])
                taken.append((x, z))
    # rosettes whose disc the 2052 aerial shows as trees (canon/lines.json): a dense grove inside the circle path
    for rx, rz, r in rosette_trees(layout):
        for gx in range(int(rx - r), int(rx + r) + 1, 4):
            for gz in range(int(rz - r), int(rz + r) + 1, 4):
                x, z = gx + int(h01(gx, gz, 41) * 3), gz + int(h01(gx, gz, 42) * 3)
                if math.hypot(x - rx, z - rz) <= r - 2 and free(x, z, 0):
                    out.append([x, z, "minecraft:dark_oak" if h01(gx, gz, 43) < 0.6 else "minecraft:oak"])
                    taken.append((x, z))
    if ground:
        return out + grove_trees(rings, ground, free, water or set())
    xs = [r[0] for r in rings]; zs = [r[1] for r in rings]
    G = 40
    for gx in range(int(min(xs)) - 200, int(max(xs)) + 200, G):
        for gz in range(int(min(zs)) - 200, int(max(zs)) + 200, G):
            if h01(gx, gz, 5) > 0.3:
                continue
            x, z = gx + int(h01(gx, gz, 6) * G), gz + int(h01(gx, gz, 7) * G)
            d = min(math.hypot(x - a, z - b) for a, b in rings)
            if d < RING_PATH_R + 10 or d > 250 or not free(x, z, 15):
                continue
            out.append([x, z, "minecraft:birch" if h01(gx, gz, 8) < 0.35 else "minecraft:oak"])
            taken.append((x, z))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--png")
    ap.add_argument("--event", action="store_true", help="also Silo 1's opening-day set (event.py), with its path and apron")
    ap.add_argument("--state", help="build_live state directory (for --event)")
    ap.add_argument("--trees", action="store_true", help="also plant the berm and plain trees")
    ap.add_argument("--event-only", action="store_true", help="only rebuild Silo 1's opening-day set (implies --event)")
    a = ap.parse_args()
    a.event = a.event or a.event_only
    layout = json.load(open(a.layout))
    cells, road = plan(layout)
    one = next(s_ for s_ in layout["silos"] if s_["number"] == 1)
    rx1, rz1 = int(math.floor(one["ring"][0])), int(math.floor(one["ring"][1]))
    if a.event:
        import event
        event.set_rotation(layout.get("rotation_deg", 0))
        p_, apron = event.ground_paths(rx1, rz1)
        cells |= set(p_) | set(apron)
    allc = sorted(cells | road)
    floors = set()
    for s_ in layout["silos"]:
        if "ring" in s_:
            rx, rz = s_["ring"]
            for dx in range(-FLOOR_R - 4, FLOOR_R + 5):
                for dz in range(-FLOOR_R - 4, FLOOR_R + 5):
                    if math.hypot(dx, dz) <= FLOOR_R + 4:
                        floors.add((int(math.floor(rx + dx)), int(math.floor(rz + dz))))
    floors -= set(allc)
    h18 = hero(layout) if a.trees else None
    spots = trees(layout, set(allc), [(h18["x"], h18["z"])] if h18 else []) if a.trees else []
    if h18 and any((h18["x"] + dx, h18["z"] + dz) in cells | road for dx in range(-3, 4) for dz in range(-3, 4)):
        raise SystemExit(f"Silo 18's tree at {h18['x']},{h18['z']} stands on a path")
    print(f"{len(cells)} path cells, {len(road)} road cells, {len(spots)} trees"
          + (f", Silo 18's tree at {h18['x']},{h18['z']} ({len(h18['blocks'])} blocks)" if h18 else ""), flush=True)
    if a.png:
        from PIL import Image
        xs = [c[0] for c in allc]; zs = [c[1] for c in allc]
        x0, z0 = min(xs), min(zs)
        img = np.zeros((max(zs) - z0 + 1, max(xs) - x0 + 1), np.uint8)
        for x, z in allc:
            img[z - z0, x - x0] = 255
        Image.fromarray(img).save(a.png)
    if a.dry:
        return
    from build_live import Bridge, settle
    br = Bridge()
    T = 128                                  # 8x8 chunks a tile (deep world: see build_live.settle)
    tiles, ftiles = {}, {}
    for x, z in allc:
        tiles.setdefault((x // T, z // T), []).append([x, z])
    for x, z in floors:
        ftiles.setdefault((x // T, z // T), []).append([x, z])
    ttiles = {}
    for t in spots:
        ttiles.setdefault((t[0] // T, t[1] // T), []).append(t)
    htile = (h18["x"] // T, h18["z"] // T) if h18 else None
    for key in list(ftiles) + list(ttiles) + ([htile] if htile else []):
        tiles.setdefault(key, [])
    if a.event_only:
        tiles = {}
    for (tx, tz), cols in sorted(tiles.items()):
        area = br.call("area.prepare", {"from": [tx * T, tz * T], "to": [tx * T + T - 1, tz * T + T - 1], "wait": 50})
        try:
            for attempt in range(3):
                res = br.call("script", {"code": SCRIPT, "args": {"cols": cols, "floors": ftiles.get((tx, tz), []),
                                                                      "trees": ttiles.get((tx, tz), []),
                                                                      "hero": h18 if (tx, tz) == htile else None},
                                           "timeout_ms": 10000})
                if not res.get("ok"):
                    raise RuntimeError(f"script: {res}")
                print(f"tile {tx * T},{tz * T}: {res.get('value')}", flush=True)
                if not res["value"].get("unloaded"):
                    break
                time.sleep(10)
        finally:
            br.call("area.release", {"id": area["id"]})
        settle(br, log=lambda m: print(m, flush=True))
    if a.event:
        import event
        from build_live import build
        area = br.call("area.prepare", {"from": [rx1 - 48, rz1 - 48], "to": [rx1 + 48, rz1 + 48], "wait": 50,
                                               "ttl_seconds": 3600})
        try:
            code = ("import net.minecraft.world.level.levelgen.Heightmap\n"
                    "return server.overworld().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, args.x, args.z) - 1")
            fy = br.call("script", {"code": code, "args": {"x": rx1 - 3, "z": rz1 - 21}})["value"]
            print(f"opening-day set on floor y {fy}", flush=True)
            build(event.build(rx1, rz1, int(fy)), "event1", a.state, br, log=lambda m: print(m, flush=True))
        finally:
            br.call("area.release", {"id": area["id"]})


if __name__ == "__main__":
    main()
