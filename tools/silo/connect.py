"""Connection states for panes, iron bars, fences and walls, computed from their neighbours.

The bridge places blocks the way /fill does: no shape updates, so a pane or a wall keeps the state it was written
with. Written bare ("minecraft:iron_bars") it stands as a lone post. This pass gives each one the north/east/south/west
(and for walls up) properties vanilla would compute (CrossCollisionBlock / WallBlock.getStateForPlacement), from the
volume itself. Simplifications, all on the safe side of looks: a wall side is "tall" only under a full block, and a
wall drops its post only when it runs straight through.
"""
from __future__ import annotations

import numpy as np

PARTIAL = ("slab", "stairs", "_wall", "fence", "pane", "iron_bars", "door", "trapdoor", "carpet", "_bed", "chain",
           "lantern", "torch", "button", "pressure_plate", "rail", "sign", "banner", "pot", "flower", "leaves", "air",
           "water", "lava", "lectern", "cauldron", "hopper", "anvil", "brewing_stand", "grindstone", "bell", "scaffolding",
           "rod", "candle", "cake", "azalea", "fern", "grass", "wheat", "carrots", "potatoes", "beetroots", "dripstone",
           "ladder", "vine", "snow", "head", "skull", "stonecutter", "enchanting", "daylight", "composter", "chest",
           "end_rod", "campfire", "lily", "conduit", "heavy_core", "decorated_pot", "<keep>")
EXCEPTIONS = ("leaves", "barrier", "pumpkin", "melon", "shulker_box")
DIRS = (("north", 0, -1), ("east", 1, 0), ("south", 0, 1), ("west", -1, 0))


def base(state: str) -> str:
    return state.split("[", 1)[0]


def kind_of(state: str) -> int:
    """0 other, 1 pane/bars, 2 wooden fence, 3 nether brick fence, 4 wall, 5 fence gate."""
    b = base(state)
    if b.endswith("glass_pane") or b == "minecraft:iron_bars":
        return 1
    if b.endswith("_fence_gate"):
        return 5
    if b == "minecraft:nether_brick_fence":
        return 3
    if b.endswith("_fence"):
        return 2
    if b.endswith("_wall") and not any(t in b for t in ("wall_sign", "wall_torch", "wall_banner", "wall_head",
                                                         "wall_hanging_sign", "wall_fan", "wall_skull")):
        return 4
    return 0


def is_full(state: str) -> bool:
    b = base(state)
    return not any(t in b for t in PARTIAL) and not any(t in b for t in EXCEPTIONS)


def connect(v) -> int:
    """Rewrite every pane, bars, fence and wall in the volume with its connections. Returns how many."""
    pal = v.palette
    kind = np.array([kind_of(s) if i else 0 for i, s in enumerate(pal)], dtype=np.int8)
    full = np.array([bool(i) and is_full(s) for i, s in enumerate(pal)], dtype=bool)
    k3 = kind[v.ids]
    pos = np.argwhere((k3 >= 1) & (k3 <= 4))
    if len(pos) == 0:
        return 0
    X, Y, Z = pos[:, 0], pos[:, 1], pos[:, 2]
    sx, sy, sz = v.ids.shape
    me = k3[X, Y, Z]
    bits = np.zeros(len(pos), dtype=np.int32)
    for j, (_, dx, dz) in enumerate(DIRS):
        nx, nz = X + dx, Z + dz
        ok = (nx >= 0) & (nx < sx) & (nz >= 0) & (nz < sz)
        nid = np.zeros(len(pos), dtype=np.int64)
        nid[ok] = v.ids[nx[ok], Y[ok], nz[ok]]
        nk, nf = kind[nid], full[nid]
        c = nf | (nk == 5)
        c |= (me == 1) & ((nk == 1) | (nk == 4))
        c |= (me == 4) & ((nk == 1) | (nk == 4))
        c |= (me == 2) & (nk == 2)
        c |= (me == 3) & (nk == 3)
        bits |= c.astype(np.int32) << j
    above = np.zeros(len(pos), dtype=np.int64)
    ok = Y + 1 < sy
    above[ok] = v.ids[X[ok], Y[ok] + 1, Z[ok]]
    tall = full[above]
    cur = v.ids[X, Y, Z]
    key = cur.astype(np.int64) * 64 + bits * 2 + tall
    out = np.empty(len(pos), dtype=np.uint16)
    for k in np.unique(key):
        i0 = int(k // 64)
        b, t = int(k % 64) // 2, int(k % 2)
        name = base(pal[i0])
        kd = kind[i0]
        on = [(b >> j) & 1 for j in range(4)]
        if kd == 4:
            side = "tall" if t else "low"
            straight = on in ([1, 0, 1, 0], [0, 1, 0, 1])
            props = ",".join(f"{d}={side if on[j] else 'none'}" for j, (d, _, _) in enumerate(DIRS))
            state = f"{name}[{props},up={'false' if straight and not t else 'true'},waterlogged=false]"
        else:
            props = ",".join(f"{d}={'true' if on[j] else 'false'}" for j, (d, _, _) in enumerate(DIRS))
            state = f"{name}[{props},waterlogged=false]"
        out[key == k] = v.id(state)
    v.ids[X, Y, Z] = out
    return len(pos)


def tidy(v) -> int:
    """Remove halves left alone where a room overwrote part of something: a bed without its other half, a door
    without its other half, a pressure plate with no door next to it. Returns how many cells were cleared."""
    pal = v.palette
    air = v.id("minecraft:air")
    step = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
    props = [dict(p.split("=") for p in s[s.index("[") + 1:-1].split(",")) if "[" in s else {} for s in pal]
    names = [base(s) for s in pal]
    bed = np.array([n.endswith("_bed") for n in names])
    door = np.array([n.endswith("_door") for n in names])
    # door plates only (heavy weighted, silo.PLATE): a wooden plate on a fence is a table top, not a stray
    plate = np.array([n == "minecraft:heavy_weighted_pressure_plate" for n in names])
    sx, sy, sz = v.ids.shape
    cleared = 0
    for x, y, z in np.argwhere(bed[v.ids]):
        p = props[v.ids[x, y, z]]
        dx, dz = step[p["facing"]]
        k = -1 if p["part"] == "head" else 1
        ox, oz = x + k * dx, z + k * dz
        ok = 0 <= ox < sx and 0 <= oz < sz and bed[v.ids[ox, y, oz]] and props[v.ids[ox, y, oz]].get("part") != p["part"]
        if not ok:
            v.ids[x, y, z] = air
            cleared += 1
    for x, y, z in np.argwhere(door[v.ids]):
        p = props[v.ids[x, y, z]]
        oy = y + (1 if p["half"] == "lower" else -1)
        if not (0 <= oy < sy and door[v.ids[x, oy, z]] and props[v.ids[x, oy, z]].get("half") != p["half"]):
            v.ids[x, y, z] = air
            cleared += 1
    for x, y, z in np.argwhere(plate[v.ids]):
        near = v.ids[max(0, x - 1):x + 2, y, max(0, z - 1):z + 2]
        if not door[near].any():
            v.ids[x, y, z] = air
            cleared += 1
    return cleared
