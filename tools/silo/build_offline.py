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
FIRST = {1: "E"}                 # Silo 1's way out faces south-east, clear of the opening-day set in the north half


def log(m):
    print(time.strftime("%H:%M:%S "), m, flush=True)


def h01(*v) -> float:
    h = 0x9E3779B1
    for x in v:
        h = ((h ^ (int(x) & 0xFFFFFFFF)) * 0x85EBCA6B) & 0xFFFFFFFF
        h ^= h >> 13
    return (h & 0xFFFF) / 65535.0


# layout ------------------------------------------------------------------------------------------------------------

def make_layout(a) -> None:
    """layout.json for one placement of silo_site's search (branch silo-site-1to1): shafts, shifts applied, a bearing
    for each silo's way out (each ring its own side, SPEC 1), the gate on the canon axis, Zearth's towns to keep."""
    picks = json.load(open(a.placements))
    p = picks[a.pick - 1]
    canon = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "canon_layout.json")))
    silos = []
    for s in p["silos"]:
        x, z = s["x"], s["z"]
        if s.get("shift"):
            x, z = x + s["shift"][0], z + s["shift"][1]
        n = s["n"]
        d = FIRST.get(n) or "WNES"[int(h01(n, 11) * 4) % 4]
        silos.append({"number": n, "x": x, "z": z, "dir": d, "ring": [x, z], "water_here": s.get("water", False),
                      "conflict": s.get("conflict", "")})
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
           "source": f"silo-site-1to1 placements.json pick {a.pick}"}
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
        gap_b = math.pi if h01(n, 2) < 0.5 else None
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
        spots = paths.trees(self.layout, avoid, [(hero[0], hero[1])] if hero else [])
        vols = []
        for x, z, kind in spots:
            g = self.ground_at(x, z)
            vols.append(self.tree_volume(x, g, z, tree_blocks(kind, int(h01(x, z, 9) * 1e6))))
        if hero:
            hx, hz, blocks = hero
            vols.append(self.tree_volume(hx, self.ground_at(hx, hz), hz, blocks))
        self.apply(vols, f"trees: {len(spots)} and Silo 18's")
        self.mark("trees", {"count": len(spots), "hero": [hero[0], hero[1]] if hero else None})

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
    bp.add_argument("--what", nargs="*", default=["all"], choices=["plain", "silos", "trees", "biome", "all"])
    a = ap.parse_args()
    if a.cmd == "layout":
        make_layout(a)
        return
    b = Builder(a)
    what = set(a.what)
    if what & {"plain", "all"}:
        b.plain()
    if what & {"silos", "all"}:
        for s in b.layout["silos"]:
            if a.number and s["number"] not in a.number:
                continue
            if not a.number and b.done.get(f"silo{s['number']}"):
                continue
            b.silo(s)
    if what & {"trees", "all"}:
        b.trees()
    if what & {"biome", "all"}:
        b.biome()


if __name__ == "__main__":
    main()
