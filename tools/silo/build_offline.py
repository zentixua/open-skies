# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "scipy", "nbtlib>=2.0"]
# ///
"""Build the 1:1 complex (SPEC-1to1.md) straight into a stopped world's region files (regions.apply), no server.

The live bridge build (build_live.py) holds every touched chunk in a running server: at 1:1 a silo is 81 chunks of
76 sections (1216 blocks tall), ×2.4 the blocks of the first draft, and the host has no heap to spare for that next to
25565-25567. Here every part is a Volume written into the region files of a copy of the golden world; the game
recomputes the edited chunks' light and heightmaps when it loads them (regions.py).

  uv run tools/silo/build_offline.py layout --placements placements.json --pick 2 --terrain terrain3.npz --out layout.json
  uv run tools/silo/build_offline.py build --layout layout.json --golden <golden world> --world <world copy> \\
      --state <dir> [--number N ...] [--what plain silos trees biome all]

Order: the plain (field.py, with the paths on it), then each silo with its bore and its site (surface.py: bowl,
banks, ring path, slot curb, camera block), Silo 1's opening-day set (event.py), the trees and Silo 18's tree, and one
biome over the levelled core (biome.py's rule, offline). Progress is kept in <state>/done.json, so a rerun goes on
where it stopped; --number rebuilds the named silos.
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
from volume import Volume  # noqa: E402

DIM_MIN_Y = -896                 # datapack/silo_depth: min_y -896, height 1216
FIRST = {1: "W"}                 # Silo 1's way out: world west = the frame's south-south-east at 128 degrees, clear of the
                                 # opening-day set (event.py: north half, small tents west, the path due south)


def log(m):
    print(time.strftime("%H:%M:%S "), m, flush=True)


def h01(*v) -> float:
    h = 0x9E3779B1
    for x in v:
        h = ((h ^ (int(x) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        h ^= h >> 13
    return (h & 0xFFFF) / 65535.0


CARD = {"W": (-1, 0), "N": (0, -1), "E": (1, 0), "S": (0, 1)}
GROUPS = [(2, 6), (7, 13), (14, 21), (22, 28), (29, 35), (36, 42), (43, 50)]   # founders' plaque hubs


def faces_group(silos: list, s: dict, bearing: float, margin: float = math.radians(30)) -> bool:
    """Would a berm cut at this world bearing (atan2(dz, dx)) open toward another silo of the same group? Through a
    cut the camera of 17 saw 16 (12.11 line-of-sight check), which the show rules out ("the six other silos in their
    group" could see fugitives only once they were on the berm, S3E10)."""
    n = s["number"]
    grp = next((g for g in GROUPS if g[0] <= n <= g[1]), None)
    if not grp:
        return False
    for o in silos:
        if o is s or not grp[0] <= o["number"] <= grp[1]:
            continue
        b = math.atan2(o["z"] - s["z"], o["x"] - s["x"])
        if abs((b - bearing + math.pi) % (2 * math.pi) - math.pi) < margin:
            return True
    return False


def cut_bearing(s: dict, k: int) -> float:
    """The berm cut's bearing in the silo's own frame (way in due west): opposite the slot, due east; Silo 1's is
    where the path from the opening-day set leaves due south (event.py), turned into its frame."""
    if s["number"] != 1:
        return 0.0
    import event
    sx, sz = event.to_world(0, 1)                  # the frame's south (event.set_rotation done by the Builder)
    return math.atan2(sz, sx) - k * math.pi / 2


# layout ------------------------------------------------------------------------------------------------------------

def make_layout(a) -> None:
    """layout.json for the 1:1 complex: ring centres straight from the show's layout (canon_layout.json) at edge
    --spacing, turned by the pick's rotation about the pick's Silo 1. Only Silo 1 and the rotation come from
    silo_site's search (branch silo-site-1to1): its other points are the old design's shafts, REACH off each ring
    along a tunnel bearing, and taking them as rings put 33 of 50 silos 159-231 m off canon (13.11). Rings never
    move; one over a buried structure is listed as a conflict. canon_check fails the layout if any silo
    ends up more than 10 m off the show."""
    from site_fit import canon_layout
    import canon_check
    picks = json.load(open(a.placements))
    p = picks[a.pick - 1]
    here = os.path.dirname(os.path.abspath(__file__))
    canon = json.load(open(os.path.join(here, "canon_layout.json")))
    s1 = next(s for s in p["silos"] if s["n"] == 1)
    ox, oz = s1["x"], s1["z"]
    rings = canon_layout(os.path.join(here, "canon_layout.json"), math.radians(p["rot"]), a.spacing)[0]
    t = np.load(a.terrain, allow_pickle=True)
    x0, z0, bes, under = int(t["x0"]), int(t["z0"]), t["bes"], t["bes_under"]

    def buried(x, z, r=64):
        """Chunks with a buried structure (>= 5 block entities under the ground) within r of the shaft."""
        hits = []
        for cx in range(int((x - r - x0) // 16), int((x + r - x0) // 16) + 1):
            for cz in range(int((z - r - z0) // 16), int((z + r - z0) // 16) + 1):
                if 0 <= cx < under.shape[0] and 0 <= cz < under.shape[1] and under[cx, cz] >= 5 and \
                        math.hypot(x0 + cx * 16 + 8 - x, z0 + cz * 16 + 8 - z) <= r + 8:
                    hits.append((cx, cz))
        return hits

    silos = []
    for i, (rx, rz) in enumerate(rings):
        n = i + 1
        x, z = round(ox + rx), round(oz + rz)
        # the shaft (outer wall 60 m) replaces what it cuts; a move far enough to clear a buried structure (16-72 m
        # on Zearth) would break the show's layout, which is what the player sees, so the ring stays and the
        # conflict is listed
        conflict = "buried structure" if buried(x, z) else ""
        if conflict:
            log(f"silo {n} at {x},{z}: buried structure within 64 m of the shaft (kept on canon)")
        silos.append({"number": n, "x": x, "z": z, "ring": [x, z], "conflict": conflict})
    # each ring's axis (S3E09 aerials, the 2052 frame): outer ring path -> stub -> the berm's one cut -> path over the
    # bowl -> the slot's head -> the slot -> the camera block behind it. dir is the side the slot lies on (the way in,
    # silo.py's due west); the cut is on the opposite side. Each ring its own side (hash order), the first of the four
    # whose cut does not open toward a silo of the same group (the berm hides them from each other).
    for s_ in silos:
        n = s_["number"]
        if n in FIRST:
            s_["dir"] = FIRST[n]
            continue
        start = int(h01(n, 11) * 4) % 4
        for j in range(4):
            d = "WNES"[(start + j) % 4]
            dx, dz = CARD[d]
            if not faces_group(silos, s_, math.atan2(-dz, -dx)):
                break
        else:
            # a flower's hub: its group all round; the cut goes where the nearest of them is farthest off its bearing
            def clear(d):
                dx, dz = CARD[d]
                b = math.atan2(-dz, -dx)
                return min(abs((math.atan2(o["z"] - s_["z"], o["x"] - s_["x"]) - b + math.pi) % (2 * math.pi) - math.pi)
                           for o in silos if o is not s_ and math.dist((o["x"], o["z"]), (s_["x"], s_["z"])) < 1.5 * a.spacing)
            d = max("WNES", key=clear)
            log(f"silo {n}: every cut faces a neighbour; {d}, {math.degrees(clear(d)):.0f} degrees off the nearest")
        s_["dir"] = d
    one = silos[0]
    rot = math.radians(p["rot"])
    cs, sn = math.cos(rot), math.sin(rot)
    gx, gz = canon["gate"]
    gate = [round(one["x"] + a.spacing * (gx * cs - gz * sn)), round(one["z"] + a.spacing * (gx * sn + gz * cs))]
    t = np.load(a.terrain, allow_pickle=True)
    x0, z0, bes = int(t["x0"]), int(t["z0"]), t["bes"]
    xs, zs = [s["x"] for s in silos], [s["z"] for s in silos]
    towns = []
    for i, k in zip(*np.nonzero(bes >= 6)):
        tx, tz = x0 + i * 16 + 8, z0 + k * 16 + 8
        if not (min(xs) - 500 <= tx <= max(xs) + 500 and min(zs) - 500 <= tz <= max(zs) + 500):
            continue
        # builds under a bowl or its ring path go with the plain (silos 13 and 44, SPEC 6); farther ones stay
        if min(math.hypot(tx - s["x"], tz - s["z"]) for s in silos) < 125:
            continue
        towns.append([int(tx), int(tz)])
    out = {"spacing": a.spacing, "canon": True, "scale": "1:1", "gate": gate, "centre": p["centre"],
           "rotation_deg": p["rot"], "silos": silos, "towns": towns,
           "source": f"canon_layout.json about Silo 1 and rotation of silo-site-1to1 placements.json pick {a.pick}"}
    res = canon_check.check(out)
    bad = [r for r in res if r[1] > 10]
    if bad:
        raise SystemExit(f"layout off canon: " + ", ".join(f"silo {n} {e:.0f} m" for n, e, *_ in bad))
    json.dump(out, open(a.out, "w"), indent=1)
    log(f"{a.out}: {len(silos)} silos, gate {gate}, {len(towns)} town chunks kept")


# build -------------------------------------------------------------------------------------------------------------

class Builder:
    def __init__(self, a):
        from field import Field
        import paths
        self.a = a
        self.layout = json.load(open(a.layout))
        os.makedirs(a.state, exist_ok=True)
        self.done_path = os.path.join(a.state, "done.json")
        self.done = json.load(open(self.done_path)) if os.path.exists(self.done_path) else {}
        self.field = Field(a.layout, a.golden, a.state)
        log(f"field level y {self.field.level}")
        cells, road = paths.plan(self.layout)
        one = next(s for s in self.layout["silos"] if s["number"] == 1)
        import event
        event.set_rotation(self.layout.get("rotation_deg", 0))
        p_, apron = event.ground_paths(one["x"], one["z"])
        self.path_cells = cells | set(p_) | set(apron)
        self.road_cells = road
        self.heights = {}                      # finished ground per site: (x0, z0, T, zone) in world frame
        hp = os.path.join(a.state, "heights.npz")
        if os.path.exists(hp):
            d = np.load(hp, allow_pickle=True)
            self.heights = d["h"].item()

    def mark(self, key: str, info=True) -> None:
        self.done[key] = info
        json.dump(self.done, open(self.done_path, "w"), indent=0)

    def apply(self, vols: list[Volume], what: str) -> None:
        import regions
        t0 = time.time()
        st = regions.apply(self.a.world, [v for v in vols if v is not None], DIM_MIN_Y, log=lambda m: None)
        log(f"{what}: {st['chunks']} chunks, {st['sections']} sections, {st['block_entities']} block entities, "
            f"{st['missing_chunks']} missing, {time.time() - t0:.0f}s")

    def grid(self, cells: set, x: int, z: int, R: int) -> np.ndarray:
        g = np.zeros((2 * R + 1, 2 * R + 1), bool)
        for cx, cz in cells:
            i, k = cx - x + R, cz - z + R
            if 0 <= i <= 2 * R and 0 <= k <= 2 * R:
                g[i, k] = True
        return g

    # the plain -------------------------------------------------------------------------------------------------
    def plain(self) -> None:
        from surface import Site
        batch, names = [], []
        for name, v in self.field.tiles(skip_site=Site.zone_r - 1, paths=self.path_cells | self.road_cells):
            if self.done.get(name):
                continue
            batch.append(v)
            names.append(name)
            if len(batch) >= 16:
                self.apply(batch, f"plain {names[0]}..{names[-1]}")
                for n in names:
                    self.mark(n)
                batch, names = [], []
        if batch:
            self.apply(batch, f"plain {names[0]}..{names[-1]}")
            for n in names:
                self.mark(n)

    # silos ---------------------------------------------------------------------------------------------------------
    def silo(self, s: dict) -> None:
        import machines
        from silo import Silo, Spec
        from silo1 import Silo1
        from surface import Site
        from tunnels import TURNS
        from turn import turn_grid, turn_points, turn_volume
        n, x, z = s["number"], s["x"], s["z"]
        k = TURNS[s["dir"]]
        plain = self.field_height(x, z)
        grade = plain - Site.floor_drop
        silo = (Silo1 if n == 1 else Silo)(Spec(number=n), x, grade, z)
        t0 = time.time()
        vol = turn_volume(silo.build(), k, x, z)
        log(f"silo {n} at {x} {grade} {z} ({s['dir']}): generated in {time.time() - t0:.0f}s, lights {silo.lights}")
        # the digger's bore out of the void, unless it would pass near another shaft
        b = machines.bearing(machines.TUN_PHI) + k * math.pi / 2
        r0, r1 = silo.s.void_radius - 2, silo.s.void_radius - 2 + machines.TUN_LEN + 1
        ax_, az_ = x + r0 * math.cos(b), z + r0 * math.sin(b)
        dx_, dz_ = (r1 - r0) * math.cos(b), (r1 - r0) * math.sin(b)

        def clear(o):
            t = max(0.0, min(1.0, ((o["x"] - ax_) * dx_ + (o["z"] - az_) * dz_) / (dx_ * dx_ + dz_ * dz_)))
            return math.hypot(o["x"] - ax_ - t * dx_, o["z"] - az_ - t * dz_) - silo.s.r_outer
        gap = min(clear(o) for o in self.layout["silos"] if o is not s)
        bore = turn_volume(silo.tunnel_volume(), k, x, z) if gap >= 5 else None
        # the site, in the silo's frame
        R = Site.radius
        grids = [turn_grid(g, -k) for g in self.field.slice(x, z, R)]
        paths_g = turn_grid(self.grid(self.path_cells, x, z, R), -k)
        road_g = turn_grid(self.grid(self.road_cells, x, z, R), -k)
        others = [turn_points([(o["x"], o["z"])], -k, x, z)[0] for o in self.layout["silos"] if o is not s]
        gap_b = cut_bearing(s, k)            # every ring has its one cut (the 2052 frame, S3E09 aerials)
        site = Site(silo, *grids, neighbours=others, paths=paths_g, road=road_g, gap_bearing=gap_b, wobble=n != 1)
        svol = turn_volume(site.build(), k, x, z)
        self.heights[n] = (x - R, z - R, turn_grid(site.T, k), turn_grid(site.zone, k))
        np.savez_compressed(os.path.join(self.a.state, "heights.npz"), h=np.array(self.heights, dtype=object))
        vols = [vol, bore, svol]
        if n == 1:
            import event
            vols.append(event.build(x, z, grade))
        self.apply(vols, f"silo {n}")
        self.mark(f"silo{n}", {"grade": grade, "dir": s["dir"], "bore": bore is not None, "gap": gap_b is not None,
                               "lights": list(silo.lights), "bottom": vol.origin[1]})

    def field_height(self, x: int, z: int) -> int:
        """Plain level round a shaft: the mean plain height within 34 of the axis (build_live.grade_of)."""
        h, *_ = self.field.slice(x, z, 34)
        r = np.hypot(*np.meshgrid(np.arange(69) - 34, np.arange(69) - 34, indexing="ij"))
        vals = h[(r <= 34) & (h > -9999)]
        return int(round(float(vals.mean()))) if len(vals) else self.field.level

    # trees ---------------------------------------------------------------------------------------------------------
    def ground_at(self, x: int, z: int) -> int:
        for x0, z0, T, zone in self.heights.values():
            i, k = x - x0, z - z0
            if 0 <= i < T.shape[0] and 0 <= k < T.shape[1] and zone[i, k]:
                return int(T[i, k])
        f = self.field
        return int(f.height[x - f.x0, z - f.z0])

    def trees(self) -> None:
        import hero_tree
        import paths
        from tunnels import TURNS
        from trees import tree_blocks
        s18 = next((s for s in self.layout["silos"] if s["number"] == 18), None)
        hero = None
        if s18:
            (hx, hz), out = hero_tree.place_1to1((s18["x"], s18["z"]), TURNS[s18["dir"]])
            hero = (hx, hz, hero_tree.blocks(out))
        avoid = self.path_cells | self.road_cells
        cg = self.a.canon_ground
        spots = paths.trees(self.layout, avoid, [(hero[0], hero[1])] if hero else [], ground=cg,
                            water=self.pond_cells() if cg else None)
        f = self.field
        inside = lambda x, z: 4 <= x - f.x0 < f.height.shape[0] - 4 and 4 <= z - f.z0 < f.height.shape[1] - 4
        vols = []
        outside = [s for s in spots if not inside(s[0], s[1])]
        spots = [s for s in spots if inside(s[0], s[1])]
        for x, z, kind in spots:
            g = self.ground_at(x, z)
            vols.append(self.tree_volume(x, g, z, tree_blocks(kind, int(h01(x, z, 9) * 1e6))))
        if outside and cg:
            vols += self.forest(outside, tree_blocks)
        log(f"trees: {len(spots)} on the plain, {len(vols) - len(spots)} beyond it")
        if hero:
            hx, hz, blocks = hero
            vols.append(self.tree_volume(hx, self.ground_at(hx, hz), hz, blocks))
        self.apply(vols, f"trees: {len(spots)} and Silo 18's")
        self.mark("trees", {"count": len(spots), "hero": [hero[0], hero[1]] if hero else None})

    def slots(self) -> None:
        """Open every slot to the sky: air over its columns from the bowl floor up (the site pass used to leave the
        golden ground there; surface.py now clears it, this fixes a world built before that)."""
        from silo import EXIT_X, RAMP_X, RAMP_Z
        from tunnels import TURNS
        from turn import turn_points
        vols = []
        for s in self.layout["silos"]:
            n = s["number"]
            g = self.done.get(f"silo{n}", {}).get("grade")
            if g is None:
                continue
            cols = [(s["x"] + x, s["z"] + z) for x in range(RAMP_X[1] + 1, EXIT_X) for z in range(RAMP_Z[0], RAMP_Z[1] + 1)]
            cols = turn_points(cols, TURNS[s["dir"]], s["x"], s["z"])
            xs = [c[0] for c in cols]; zs = [c[1] for c in cols]
            top = 200
            v = Volume((min(xs), g + 1, min(zs)), (max(xs) - min(xs) + 1, top - g, max(zs) - min(zs) + 1))
            for x, z in cols:
                v.ids[x - min(xs), :, z - min(zs)] = v.id("minecraft:air")
            vols.append(v)
            # the steps (silo.way_out's state was smooth_stone_stairs, which vanilla lacks: the game made them air)
            from silo import STEPS
            from turn import turn_volume
            st = Volume((s["x"] + RAMP_X[1] + 1, g - STEPS, s["z"] + RAMP_Z[0]),
                        (EXIT_X - RAMP_X[1], STEPS + 1, RAMP_Z[1] - RAMP_Z[0] + 1))
            for i, x in enumerate(range(RAMP_X[1] + 1, EXIT_X + 1)):
                ys = g - STEPS + 1 + i - (g - STEPS)          # the step's row in the volume (its top at k - 1)
                for kz in range(st.size[2]):
                    st.set(i, ys, kz, "minecraft:polished_andesite_stairs[facing=east,half=bottom,shape=straight,"
                           "waterlogged=false]")
                    for yy in range(ys + 1, st.size[1]):
                        st.set(i, yy, kz, "minecraft:air")
            vols.append(turn_volume(st, TURNS[s["dir"]], s["x"], s["z"]))
        self.apply(vols, f"slots opened: {len(vols) // 2}")

    def forest(self, spots: list, tree_blocks) -> list:
        """The forest the 2052 aerial shows round the field, on Zearth's own ground beyond the plain: heights from the
        golden world (trees removed), no tree where the golden already has a crown or where a town's builds stand;
        where the aerial shows forest over one of Zearth's lakes, the lake is filled to its surface first (dirt, grass
        on top)."""
        from heights import read_area, MISSING
        xs = [s[0] for s in spots]; zs = [s[1] for s in spots]
        X0, Z0 = min(xs) - 6, min(zs) - 6
        nx, nz = max(xs) - X0 + 7, max(zs) - Z0 + 7
        t0 = time.time()
        ground, water, top = read_area(self.a.golden, X0, Z0, nx, nz, min_y=-64, height=384)
        log(f"golden heights {nx} x {nz} in {time.time() - t0:.0f}s")
        t = np.load(self.a.terrain_for_towns, allow_pickle=True) if getattr(self.a, "terrain_for_towns", None) else None
        # Zearth's lakes where the aerial reads closed forest (tree fraction over half, smoothed) and they are at most
        # 12 deep are filled to their surface: the forest stands on them as the frame shows
        from scipy.signal import convolve2d
        cgd = np.load(self.a.canon_ground)
        Tm = convolve2d(cgd["tree"].astype(float), np.ones((5, 5)) / 25, mode="same")
        cx0, cz0, C = int(cgd["x0"]), int(cgd["z0"]), int(cgd["cell"])
        II, KK = np.meshgrid(np.arange(nx) + X0, np.arange(nz) + Z0, indexing="ij")
        ci = np.clip((II - cx0) // C, 0, Tm.shape[0] - 1); ck = np.clip((KK - cz0) // C, 0, Tm.shape[1] - 1)
        wet = (water != MISSING) & (ground != MISSING) & (water - ground <= 12) & (Tm[ci, ck] > 0.5)
        f = self.field
        inplain = (II - f.x0 >= 0) & (II - f.x0 < f.height.shape[0]) & (KK - f.z0 >= 0) & (KK - f.z0 < f.height.shape[1])
        wet &= ~inplain
        vols = []
        for x, z, kind in spots:
            i, k = x - X0, z - Z0
            g = int(ground[i, k])
            if g == MISSING:
                continue
            if t is not None:
                bx, bz = (x - int(t["x0"])) // 16, (z - int(t["z0"])) // 16
                if 0 <= bx < t["bes"].shape[0] and 0 <= bz < t["bes"].shape[1] and t["bes"][bx, bz] >= 3:
                    continue                   # a town or a build: Zearth's own, left alone
            if water[i, k] != MISSING:
                if not wet[i, k]:
                    continue
                g = int(water[i, k])           # on the filled lake
            elif top[i, k] - g > 3:
                continue                       # Zearth already has a crown here
            vols.append(self.tree_volume(x, g, z, tree_blocks(kind, int(h01(x, z, 9) * 1e6))))
        n_fill = int(wet.sum())
        if n_fill:
            for bx in range(0, nx, 16):         # one volume per 16 x 16 block of columns
                for bz in range(0, nz, 16):
                    m = wet[bx:bx + 16, bz:bz + 16]
                    if not m.any():
                        continue
                    gb = ground[bx:bx + 16, bz:bz + 16]; ws = water[bx:bx + 16, bz:bz + 16]
                    lo, hi = int(gb[m].min()) + 1, int(ws[m].max()) + 1
                    v = Volume((X0 + bx, lo, Z0 + bz), (m.shape[0], hi - lo + 1, m.shape[1]))
                    for i, k in zip(*np.nonzero(m)):
                        for y in range(int(gb[i, k]) + 1, int(ws[i, k])):
                            v.set(i, y - lo, k, "minecraft:dirt")
                        v.set(i, int(ws[i, k]) - lo, k, "minecraft:grass_block[snowy=false]")
                        v.set(i, int(ws[i, k]) + 1 - lo, k, "minecraft:air")
                    vols.append(v)
            log(f"Zearth's lakes filled under the forest: {n_fill} columns")
        return vols

    def pond_cells(self) -> set:
        """Columns of the ponds the show's 2052 aerial has at the complex's edges (canon_ground.py, water over half
        of a 4 m cell, smoothed), never within a ring's path circle or on a path."""
        if hasattr(self, "_ponds"):
            return self._ponds
        from scipy.signal import convolve2d
        import paths
        d = np.load(self.a.canon_ground)
        W = convolve2d(d["water"].astype(float), np.ones((3, 3)) / 9, mode="same")
        x0, z0, C = int(d["x0"]), int(d["z0"]), int(d["cell"])
        rings = [s["ring"] for s in self.layout["silos"]]
        avoid = self.path_cells | self.road_cells
        out = set()
        for i, k in zip(*np.nonzero(W >= 0.5)):
            cx, cz = x0 + i * C, z0 + k * C
            if min(math.hypot(cx - a, cz - b) for a, b in rings) < paths.RING_PATH_R + 10:
                continue
            f = self.field
            if not (0 <= cx - f.x0 and cx + C - f.x0 <= f.height.shape[0] and 0 <= cz - f.z0
                    and cz + C - f.z0 <= f.height.shape[1]):
                continue                     # beyond the plain's grid: Zearth's own land, left as it is
            for dx in range(C):
                for dz in range(C):
                    c = (cx + dx, cz + dz)
                    if not any((c[0] + a, c[1] + b) in avoid for a in (-2, 0, 2) for b in (-2, 0, 2)):
                        out.add(c)
        self._ponds = out
        return out

    def ponds(self) -> None:
        """Dig the ponds: each connected pond's surface 1 under its lowest bank column, 2-3 deep, a clay bed."""
        if not self.a.canon_ground:
            return
        from scipy import ndimage
        cells = self.pond_cells()
        if not cells:
            return
        xs = [c[0] for c in cells]; zs = [c[1] for c in cells]
        X0, Z0 = min(xs), min(zs)
        m = np.zeros((max(xs) - X0 + 1, max(zs) - Z0 + 1), bool)
        for x, z in cells:
            m[x - X0, z - Z0] = True
        lab, n = ndimage.label(m)
        depth = ndimage.distance_transform_edt(m)
        vols = []
        for p in range(1, n + 1):
            ii, kk = np.nonzero(lab == p)
            if len(ii) < 30:
                continue
            g = np.array([self.ground_at(X0 + i, Z0 + k) for i, k in zip(ii, kk)])
            level = int(g.min()) - 1
            top = int(g.max())
            bx, bz = X0 + ii.min(), Z0 + kk.min()
            v = Volume((bx, level - 4, bz), (ii.max() - ii.min() + 1, top - level + 6, kk.max() - kk.min() + 1))
            for i, k, gg in zip(ii, kk, g):
                dd = min(3, 1 + int(depth[i, k] // 3))       # 2 at the bank, 3-4 in the middle
                li, lk = i - ii.min(), k - kk.min()
                bed = level - dd
                v.set(li, bed - (level - 4), lk, "minecraft:clay")
                for y in range(bed + 1, level + 1):
                    v.set(li, y - (level - 4), lk, "minecraft:water[level=0]")
                for y in range(level + 1, gg + 2):
                    v.set(li, y - (level - 4), lk, "minecraft:air")
            vols.append(v)
        self.apply(vols, f"ponds: {len(vols)}, {len(cells)} columns")
        self.mark("ponds", {"count": len(vols), "columns": len(cells)})

    @staticmethod
    def tree_volume(x: int, ground: int, z: int, blocks: dict) -> Volume:
        """Blocks {(dx, dy, dz): state} about a trunk standing on (x, ground, z); dy 0 is the first block above."""
        xs = [d[0] for d in blocks]; ys = [d[1] for d in blocks]; zs = [d[2] for d in blocks]
        v = Volume((x + min(xs), ground + 1 + min(ys), z + min(zs)),
                   (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, max(zs) - min(zs) + 1))
        for (dx, dy, dz), st in blocks.items():
            v.set(dx - min(xs), dy - min(ys), dz - min(zs), st)
        return v

    # biome ---------------------------------------------------------------------------------------------------------
    def biome(self, biome: str = "minecraft:plains", core: float = 0.99) -> None:
        """One biome over every chunk wholly inside the levelled core (biome.py's rule, written into the sections)."""
        import nbtlib
        from nbtlib import Compound, List, String
        import regions
        f = self.field
        w = f.weight
        chunks = []
        for cx in range((f.x0 >> 4) + 1, (f.x0 + f.nx) >> 4):
            for cz in range((f.z0 >> 4) + 1, (f.z0 + f.nz) >> 4):
                i, k = cx * 16 - f.x0, cz * 16 - f.z0
                if i < 0 or k < 0 or i + 16 > w.shape[0] or k + 16 > w.shape[1]:
                    continue
                if w[i:i + 16, k:k + 16].min() >= core:
                    chunks.append((cx, cz))
        by_region = {}
        for cx, cz in chunks:
            by_region.setdefault((cx >> 5, cz >> 5), []).append((cx, cz))
        n = 0
        for (rx, rz), cl in sorted(by_region.items()):
            path = os.path.join(self.a.world, "region", f"r.{rx}.{rz}.mca")
            reg = regions.read_region(path)
            for cx, cz in cl:
                i = (cx & 31) + (cz & 31) * 32
                if i not in reg:
                    continue
                ts, payload = reg[i]
                tag = regions.decode_chunk(payload)
                root = tag if "sections" in tag else tag[""]
                for sec in root["sections"]:
                    sec["biomes"] = Compound({"palette": List[String]([String(biome)])})
                reg[i] = (ts, regions.encode_chunk(tag))
                n += 1
            regions.write_region(path, reg)
        log(f"biome {biome} over {n} core chunks")
        self.mark("biome", n)


def walk_gate() -> None:
    """No silo goes into a world unless a person can walk every room of it from the surface (walk.py): Silo 1 and
    the regular silo (2-50 build the same volume)."""
    import walk
    for n in (1, 2):
        r = walk.check(n)
        bad = r["components"] or r["doors_without_plates"] or [k for k, ok in r["targets"].items() if not ok]
        if bad:
            sys.exit(f"walk.py: silo {n} has unreachable places or one-way doors; run `python3 walk.py --silo {n}`")
        print(f"walk.py: silo {n} walkable", flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("layout")
    lp.add_argument("--placements", required=True)
    lp.add_argument("--pick", type=int, default=2)
    lp.add_argument("--terrain", required=True, help="site_fit terrain3.npz of the golden world")
    lp.add_argument("--spacing", type=float, default=270)
    lp.add_argument("--out", required=True)
    bp = sub.add_parser("build")
    bp.add_argument("--layout", required=True)
    bp.add_argument("--golden", required=True, help="golden world (read only: heights)")
    bp.add_argument("--world", required=True, help="the world copy to write")
    bp.add_argument("--state", required=True)
    bp.add_argument("--number", type=int, nargs="*")
    bp.add_argument("--what", nargs="*", default=["all"], choices=["plain", "silos", "slots", "ponds", "trees", "biome", "all"])
    bp.add_argument("--terrain-for-towns", help="site_fit terrain3.npz: block entities per chunk (Zearth's towns stay)")
    bp.add_argument("--canon-ground", help="canon_ground.py's npz: ponds and the plain's groves where the show's 2052 "
                    "aerial has them")
    a = ap.parse_args()
    if a.cmd == "layout":
        make_layout(a)
        return
    b = Builder(a)
    what = set(a.what)
    if what & {"plain", "all"}:
        b.plain()
    if what & {"silos", "all"}:
        walk_gate()
        for s in b.layout["silos"]:
            if a.number and s["number"] not in a.number:
                continue
            if not a.number and b.done.get(f"silo{s['number']}"):
                continue
            b.silo(s)
    if "slots" in what:
        b.slots()
    if what & {"ponds", "all"}:
        b.ponds()
    if what & {"trees", "all"}:
        b.trees()
    if what & {"biome", "all"}:
        b.biome()


if __name__ == "__main__":
    main()
