"""Can a player walk it? Flood fill over a generated silo volume from the surface (offline, no server).

A vanilla player is 0.6 wide and 1.8 tall, steps up 0.6 without jumping and jumps 1.25. Each block state gets a
collision class from its name: none (air, plates, crops, banners, light), partial (slabs, carpets, beds, chests:
the player stands inside the cell on its top; stairs count as full, walked up from their low side), full (1), tall (walls and fences, 1.5: never jumped), thin
obstacles (panes, bars, chains, end rods: block the body, carry it on top) and doors (block the body but open: wooden
by hand, iron by the plates the generator puts on both sides, which this check also requires). Ladders, scaffolding
and water are climbed.

A node is a cell the player can stand in, with its feet height. Neighbouring nodes (4 directions, one row up or
down) join when the feet differ by at most 1 (one block's step or jump) and the head clears the jump; climbable cells
also join the cell above. Falls are not counted: what matters is getting in and back out, so every edge works both
ways. Everything connected to the open surface over the volume is reachable; the rest is reported by component,
with the silo level it lies on, its radius and bearing from the shaft axis (silo frame, the way in due west).

Run: python3 walk.py [--silo 1 18 ...] [--min 4]. Exit status 1 when a component of at least --min nodes (default 4,
smaller pockets are gaps between furniture) cannot be reached, or an iron door has no plate on one side.
"""
from __future__ import annotations

import argparse
import math
import sys
import time

import numpy as np

NONE, PARTIAL, FULL, TALL, THIN, DOOR, CLIMB = range(7)

# collision height of partial blocks, block units (vanilla shapes)
PARTIAL_H = {
    "carpet": 0.0625, "slab": 0.5, "bed": 0.5625, "chest": 0.875, "trapped_chest": 0.875,
    "ender_chest": 0.875, "daylight_detector": 0.375, "flower_pot": 0.375, "lantern": 0.5625, "soul_lantern": 0.5625,
    "farmland": 0.9375, "dirt_path": 0.9375, "stonecutter": 0.5625, "campfire": 0.4375, "enchanting_table": 0.75,
    "lectern": 0.875, "brewing_stand": 0.875, "candle": 0.375, "snow": 0.125, "sculk_sensor": 0.5,
    "decorated_pot": 1.0, "cauldron": 1.0, "composter": 1.0, "hopper": 1.0,
}
NO_COLLISION = ("air", "cave_air", "void_air", "light", "pressure_plate", "lever", "button", "banner", "sign", "torch",
                "wheat", "carrots", "potatoes", "beetroots", "redstone_wire", "tripwire", "short_grass", "tall_grass",
                "fern", "dead_bush", "rail", "flower", "dandelion", "poppy", "sapling", "vine", "cobweb", "structure_void")
THIN_NAMES = ("pane", "iron_bars", "chain", "end_rod", "lightning_rod", "pointed_dripstone", "glass_pane")
TALL_NAMES = ("_wall", "_fence")                 # andesite_wall, oak_fence (not wall_banner, wall_sign)


def classify(state: str) -> tuple[int, float]:
    """(collision class, top height) of a block state string. Unknown names count as full blocks."""
    if state == "<keep>":
        return FULL, 1.0                         # the world outside the volume: rock, treated as solid
    name = state.split("[", 1)[0].split(":", 1)[-1]
    props = dict(p.split("=") for p in state[len(state.split("[", 1)[0]) + 1:-1].split(",")) if "[" in state else {}
    if name in ("water", "ladder", "scaffolding", "vine", "weeping_vines", "twisting_vines", "cave_vines"):
        return CLIMB, 1.0 if name == "scaffolding" else 0.0
    if name.endswith("_door"):
        return DOOR, 0.0
    if name.endswith("_fence_gate"):
        return DOOR, 1.5
    if name.endswith("_trapdoor"):
        if props.get("open") == "true":
            return THIN, 1.0
        return (PARTIAL, 0.1875) if props.get("half") == "bottom" else (FULL, 1.0)
    if name.endswith("_wall_banner") or name.endswith("_wall_sign") or name.endswith("wall_torch"):
        return NONE, 0.0
    if name.endswith("_carpet") or name == "moss_carpet":
        return PARTIAL, PARTIAL_H["carpet"]
    if name.endswith("_slab"):
        t = props.get("type", "bottom")
        return (PARTIAL, 0.5) if t == "bottom" else (FULL, 1.0)
    if name.endswith("_stairs"):
        return FULL, 1.0                         # walked up from the low side to the top of its high half
    if name.endswith("_bed"):
        return PARTIAL, PARTIAL_H["bed"]
    if name.startswith("potted_"):
        return PARTIAL, PARTIAL_H["flower_pot"]
    if name in ("lantern", "soul_lantern") and props.get("hanging") == "true":
        return THIN, 1.0
    if name.endswith("_candle"):
        return PARTIAL, PARTIAL_H["candle"]
    if name in PARTIAL_H:
        h = PARTIAL_H[name]
        return (FULL, 1.0) if h >= 1.0 else (PARTIAL, h)
    if any(name == k or name.endswith("_" + k) for k in NO_COLLISION):
        return NONE, 0.0
    if any(k in name for k in THIN_NAMES):
        return THIN, 1.0
    if any(name.endswith(k) for k in TALL_NAMES):
        return TALL, 1.5
    return FULL, 1.0


class Walk:
    """Reachability over one volume (ids indexed [x, y, z]); `pad` rows of air are added over the top."""

    def __init__(self, ids: np.ndarray, palette: list[str], pad: int = 3):
        cls = np.zeros(len(palette), np.int8)
        top = np.zeros(len(palette), np.float32)
        for i, st in enumerate(palette):
            cls[i], top[i] = classify(st)
        self.palette = palette
        X, H, Z = ids.shape
        grid = np.zeros((X, H + pad, Z), dtype=ids.dtype)
        grid[:, :H, :] = ids
        c = cls[grid]
        c[:, H:, :] = NONE
        t = top[grid]
        t[:, H:, :] = 0
        self.c, self.t = c, t
        self.ids = grid
        self.shape = grid.shape
        free = (c == NONE) | (c == DOOR) | (c == CLIMB)            # the body fits (doors once opened)
        self.free = free
        part = c == PARTIAL
        below_c = np.empty_like(c)
        below_c[:, 1:, :] = c[:, :-1, :]
        below_c[:, 0, :] = FULL
        below_t = np.empty_like(t)
        below_t[:, 1:, :] = t[:, :-1, :]
        below_t[:, 0, :] = 1.0
        up1 = np.zeros_like(free)
        up1[:, :-1, :] = free[:, 1:, :]
        up2 = np.zeros_like(free)
        up2[:, :-2, :] = free[:, 2:, :]
        ys = np.arange(self.shape[1], dtype=np.float32)[None, :, None]
        feet = np.full(self.shape, np.nan, np.float32)
        # standing inside a partial block, on its top
        m = part & up1 & ((t <= 0.2) | up2)
        feet[m] = np.broadcast_to(ys, self.shape)[m] + t[m]
        # standing in a free cell on the block below (full, thin, or the 1.5 top of a wall); climbing needs no floor
        # a swimmer at the top of water climbs out onto a block one above the surface: the water's top carries too
        water = np.zeros(len(palette), bool)
        water[[i for i, st in enumerate(palette) if st.startswith("minecraft:water")]] = True
        below_w = np.zeros_like(free)
        below_w[:, 1:, :] = water[grid[:, :-1, :]]
        support = (below_c == FULL) | (below_c == THIN) | (below_c == TALL) | ((below_c == CLIMB) & (below_t >= 1.0))
        support |= below_w & ~water[grid]
        lift = np.where(below_c == TALL, 0.5, 0.0).astype(np.float32)
        m2 = free & up1 & ~part & ((support & ((lift == 0) | up2)) | (c == CLIMB))
        feet[m2] = np.broadcast_to(ys, self.shape)[m2] + lift[m2]
        self.on_wall = m2 & (below_c == TALL) & (c != CLIMB)
        # under a roof: something solid two to five rows over the feet (a room or a deck under a deck, not the top of
        # a tank, a pillar or a roof in a tall hall)
        roof = np.zeros_like(free)
        for k in range(2, 6):
            roof[:, :-k, :] |= ~free[:, k:, :]
        self.roofed = roof
        self.feet = feet
        self.node = ~np.isnan(feet)
        self.climb = c == CLIMB

    def components(self) -> tuple[np.ndarray, np.ndarray, int]:
        """Label every node by its connected component. Returns (flat node indices, labels, n components)."""
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        X, H, Z = self.shape
        node = self.node
        idx = np.flatnonzero(node.ravel())
        pos = np.full(node.size, -1, np.int64)
        pos[idx] = np.arange(idx.size)
        feet = self.feet
        free = self.free
        rows, cols = [], []
        for dx, dz in ((1, 0), (0, 1)):
            for dy in (-1, 0, 1):
                # a: cells [x, y, z], b: [x+dx, y+dy, z+dz]
                ya0, ya1 = max(0, -dy), H - max(0, dy)
                a = (slice(0, X - dx), slice(ya0, ya1), slice(0, Z - dz))
                b = (slice(dx, X), slice(ya0 + dy, ya1 + dy), slice(dz, Z))
                fa, fb = feet[a], feet[b]
                both = node[a] & node[b]
                d = np.abs(fa - fb)
                ok = both & (d <= 1.0 + 1e-3)
                # a jump (more than a step): the low side's column needs room for the head at the high feet
                jump = ok & (d > 0.6)
                if jump.any():
                    xa, ya, za = np.nonzero(jump)
                    hi = np.maximum(fa[xa, ya, za], fb[xa, ya, za])
                    head = np.floor(hi + 1.8 - 1e-4).astype(np.int64)        # cell index of the head
                    xa_ = xa + a[0].start; ya_ = ya + a[1].start; za_ = za + a[2].start
                    low_is_a = fa[xa, ya, za] < fb[xa, ya, za]
                    lx = np.where(low_is_a, xa_, xa_ + dx)
                    lz = np.where(low_is_a, za_, za_ + dz)
                    hy = np.clip(head, 0, H - 1)
                    good = free[lx, hy, lz]
                    bad = ~good
                    ok[xa[bad], ya[bad], za[bad]] = False
                xa, ya, za = np.nonzero(ok)
                ia = (xa + a[0].start) * H * Z + (ya + a[1].start) * Z + (za + a[2].start)
                ib = ia + dx * H * Z + dy * Z + dz
                rows.append(pos[ia]); cols.append(pos[ib])
        # climbing: a climbable node and the node right over it (or under it)
        cl = self.climb & node
        a = (slice(None), slice(0, H - 1), slice(None))
        b = (slice(None), slice(1, H), slice(None))
        m = node[a] & node[b] & (cl[a] | cl[b])
        xa, ya, za = np.nonzero(m)
        ia = xa * H * Z + ya * Z + za
        rows.append(pos[ia]); cols.append(pos[ia + Z])
        r = np.concatenate(rows); c = np.concatenate(cols)
        g = coo_matrix((np.ones(r.size, np.int8), (r, c)), shape=(idx.size, idx.size)).tocsr()
        n, lab = connected_components(g, directed=False)
        return idx, lab, n

    def doors_without_plates(self) -> list[tuple[int, int, int]]:
        """Iron doors (lower halves) between two open cells with no pressure plate, button or lever on one side."""
        out = []
        X, H, Z = self.shape
        for i, st in enumerate(self.palette):
            if not st.startswith("minecraft:iron_door") or "half=lower" not in st:
                continue
            facing = st.split("facing=")[1].split(",")[0].rstrip("]")
            fx, fz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[facing]
            for x, y, z in zip(*np.nonzero(self.ids == i)):
                ends = [(x + k * fx, z + k * fz) for k in (1, -1)]
                if not all(0 <= px < X and 0 <= pz < Z and self.free[px, y, pz] for px, pz in ends):
                    continue                     # a door with a wall behind it is a sealed hatch, not a way through
                sides = []
                for k in (1, -1):
                    hit = False
                    for dy in (0, 1):
                        px, pz = x + k * fx, z + k * fz
                        if 0 <= px < X and 0 <= pz < Z:
                            s = self.palette[self.ids[px, y + dy, pz]]
                            if "pressure_plate" in s or "button" in s or "lever" in s:
                                hit = True
                    # a button or lever beside the door on the wall counts too
                    for sx, sz in ((-fz, fx), (fz, -fx)):
                        px, pz = x + k * fx + sx, z + k * fz + sz
                        if 0 <= px < X and 0 <= pz < Z:
                            s = self.palette[self.ids[px, y + 1, pz]]
                            if "button" in s or "lever" in s:
                                hit = True
                    sides.append(hit)
                if not all(sides):
                    out.append((int(x), int(y), int(z)))
        return out


def report(silo, walk: Walk, min_nodes: int = 4, verbose: bool = True) -> dict:
    """Unreachable components of a built silo (silo.Silo after build()), as dicts with level, radius, bearing."""
    idx, lab, n = walk.components()
    X, H, Z = walk.shape
    xs, ys, zs = np.unravel_index(idx, walk.shape)
    # the open surface over the volume: every node in the padding rows
    surf = lab[ys >= H - 3]
    start = np.bincount(surf).argmax() if surf.size else -1
    reach = lab == start
    out = {"nodes": int(idx.size), "reached": int(reach.sum()), "components": []}
    un = ~reach
    if un.any():
        sizes = np.bincount(lab[un], minlength=n)
        # A sealed room has walls round it; the top of a tank, a pillar or a parapet has only drops at its edges.
        # Edges: a node's neighbour column that holds no node of the same part within a row. It is a wall when a
        # block stands there at the node's feet, else a drop. Parts with no wall edge are tops, not rooms.
        walls = np.zeros(n, np.int64)
        um = un & (sizes[lab] >= min_nodes)
        ux, uy, uz, ul = xs[um], ys[um], zs[um], lab[um]
        flat = np.full(walk.node.size, -1, np.int64)
        flat[idx] = lab
        lab3 = flat.reshape(walk.shape)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = np.clip(ux + dx, 0, X - 1), np.clip(uz + dz, 0, Z - 1)
            same = np.zeros(ux.size, bool)
            for dy in (-1, 0, 1):
                same |= lab3[nx, np.clip(uy + dy, 0, H - 1), nz] == ul
            fits = walk.free[nx, uy, nz]                     # a wall stands at the feet, a lamp overhead is none
            np.add.at(walls, ul[~same & ~fits], 1)
        # and a part standing only on the tops of walls and fences (parapets) or with nothing over it is no room either
        floor = np.bincount(lab[un & ~walk.on_wall.ravel()[idx] & walk.roofed.ravel()[idx]], minlength=n)
        cavern_top = silo.yi(silo.void_top_rel)
        out["cavern"] = []
        for comp in np.flatnonzero((sizes >= min_nodes) & (walls > 0) & (floor > 0)):
            m = lab == comp
            cx, cy, cz = xs[m], ys[m], zs[m]
            x0, z0 = cx.mean() - silo.R, cz.mean() - silo.R
            y = int(np.median(cy))
            if any(x0_ <= cx.min() - silo.R and cx.max() - silo.R <= x1_ and y0_ <= cy.min() and cy.max() <= y1_
                   and z0_ <= cz.min() - silo.R and cz.max() - silo.R <= z1_
                   for x0_, y0_, z0_, x1_, y1_, z1_ in getattr(silo, "walk_ignore", lambda: [])()):
                continue
            # The digger void is a cavern with the model's machine in it: its ledges, legs and cage are sculpture,
            # listed but not failed. What a person uses there is checked by target below.
            (out["cavern"] if cy.max() < cavern_top else out["components"]).append({
                "nodes": int(m.sum()), "level": level_of(silo, y), "y": y,
                "r": round(math.hypot(x0, z0), 1), "bearing": round(math.degrees(math.atan2(z0, x0)) % 360),
                "at": (int(round(x0)), int(round(z0))),
                "box": [int(cx.min() - silo.R), int(cy.min()), int(cz.min() - silo.R),
                        int(cx.max() - silo.R), int(cy.max()), int(cz.max() - silo.R)],
            })
        out["components"].sort(key=lambda c: (str(c["level"]), -c["nodes"]))
    out["doors_without_plates"] = walk.doors_without_plates()
    # places a person must reach, wherever they lie: George's camp in the cavern
    out["targets"] = {}
    for name, (tx, ty, tz) in getattr(silo, "walk_targets", lambda: {})().items():
        col = [reach[np.searchsorted(idx, (tx + silo.R) * H * Z + yy * Z + (tz + silo.R))]
               for yy in range(ty, ty + 3) if walk.node[tx + silo.R, yy, tz + silo.R]]
        out["targets"][name] = bool(col and any(col))
    return out


def level_of(silo, y: int):
    """Level number whose storey holds row y, or a name for the rows outside the levels."""
    p = silo.s.pitch
    top = silo.level_y(1)
    if y >= top + p:
        return "above"
    n = (top - y + p - 1) // p + 1 if y < top else 1
    from silo import LEVELS
    if n > LEVELS:
        return "below"
    return int(n)


def check(number: int, min_nodes: int = 4) -> dict:
    from silo import Silo, Spec
    if number == 1:
        from silo1 import Silo1 as cls
    else:
        cls = Silo
    s = cls(Spec(number=number), 0, 70, 0)
    v = s.build()
    w = Walk(v.ids, v.palette)
    return report(s, w, min_nodes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--silo", type=int, nargs="*", default=[1, 2, 18])
    ap.add_argument("--min", type=int, default=4)
    a = ap.parse_args()
    bad = 0
    for n in a.silo:
        t = time.time()
        r = check(n, a.min)
        missed = [k for k, ok in r["targets"].items() if not ok]
        print(f"silo {n}: {r['reached']}/{r['nodes']} nodes reachable, {len(r['components'])} unreachable parts, "
              f"{len(r['doors_without_plates'])} iron doors without a plate, targets missed: {missed or 'none'}, "
              f"{len(r['cavern'])} unreachable bits of the cavern's sculpture ({time.time() - t:.0f} s)")
        for c in r["components"]:
            print(f"  level {c['level']}: {c['nodes']} nodes at r {c['r']} bearing {c['bearing']} (x {c['at'][0]}, "
                  f"z {c['at'][1]}), box {c['box']}")
        for d in r["doors_without_plates"][:20]:
            print(f"  iron door without a plate at {d}")
        bad += len(r["components"]) + len(r["doors_without_plates"]) + len(missed)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
