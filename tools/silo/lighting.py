"""Block light of a generated volume, and invisible light where monsters could spawn.

Since 1.18 monsters spawn only at block light 0. Every space here is lit by its model's own fittings, but a vast
hall or a corner behind a wall can still hold cells at 0; this pass finds them (air, air above, standing on a full
opaque top) and puts minecraft:light there - an invisible, non-colliding vanilla block that only emits light - at the
lowest level that does the job, so dark places (the digger void) stay dark to the eye. Propagation is vanilla's in
outline: -1 per step through anything that is not a full opaque block; slabs, stairs and other partial blocks count as
transparent (in the game some of them block a little more, which only errs toward placing more light).
"""
from __future__ import annotations

import numpy as np

from connect import base, is_full

EMIT = {
    "minecraft:ochre_froglight": 15, "minecraft:pearlescent_froglight": 15, "minecraft:verdant_froglight": 15,
    "minecraft:sea_lantern": 15, "minecraft:shroomlight": 15, "minecraft:lantern": 15, "minecraft:glowstone": 15,
    "minecraft:soul_lantern": 10, "minecraft:end_rod": 14, "minecraft:torch": 14, "minecraft:wall_torch": 14,
    "minecraft:jack_o_lantern": 15, "minecraft:lava": 15, "minecraft:campfire": 15, "minecraft:beacon": 15,
    "minecraft:glow_lichen": 7, "minecraft:brewing_stand": 1, "minecraft:magma_block": 3,
}
SEE_THROUGH = ("glass", "grate", "minecraft:light", "ice", "slime", "honey", "barrier", "spawner")


def emission(state: str) -> int:
    b = base(state)
    if b == "minecraft:light":
        for p in state[state.find("[") + 1:-1].split(","):
            if p.startswith("level="):
                return int(p[6:])
        return 15
    if b in ("minecraft:redstone_lamp", "minecraft:copper_bulb") or b.endswith("copper_bulb"):
        return 15 if "lit=true" in state else 0
    return EMIT.get(b, 0)


def opaque(state: str) -> bool:
    b = base(state)
    return is_full(state) and not any(t in b for t in SEE_THROUGH) and b != "minecraft:light"


def spawn_top(state: str) -> bool:
    """A block a monster can stand on: full and opaque, or a top slab / upside-down stair."""
    b = base(state)
    if b in ("minecraft:air", "<keep>") or b == "minecraft:light":
        return False
    if opaque(state):
        return True
    return ("slab" in b and "type=top" in state) or ("stairs" in b and "half=top" in state)


def light_map(v) -> np.ndarray:
    pal = v.palette
    em = np.array([emission(s) if i else 0 for i, s in enumerate(pal)], dtype=np.int16)
    op = np.array([opaque(s) if i else True for i, s in enumerate(pal)], dtype=bool)
    L = em[v.ids]
    clear = ~op[v.ids]
    for _ in range(15):
        n = L.copy()
        np.maximum(n[1:], L[:-1], out=n[1:])
        np.maximum(n[:-1], L[1:], out=n[:-1])
        np.maximum(n[:, 1:], L[:, :-1], out=n[:, 1:])
        np.maximum(n[:, :-1], L[:, 1:], out=n[:, :-1])
        np.maximum(n[:, :, 1:], L[:, :, :-1], out=n[:, :, 1:])
        np.maximum(n[:, :, :-1], L[:, :, 1:], out=n[:, :, :-1])
        n -= 1
        new = np.where(clear, np.maximum(L, n), L)
        if np.array_equal(new, L):
            break
        L = new
    return np.clip(L, 0, 15)


def dark_spawns(v, L=None) -> np.ndarray:
    """Cells (x, y, z) where a monster could spawn: air with air above, a spawnable top below, block light 0."""
    pal = v.palette
    air = np.array([s == "minecraft:air" for s in pal])
    top = np.array([spawn_top(s) if i else False for i, s in enumerate(pal)])
    L = light_map(v) if L is None else L
    ids = v.ids
    m = np.zeros(ids.shape, dtype=bool)
    m[:, 1:-1, :] = air[ids[:, 1:-1, :]] & air[ids[:, 2:, :]] & top[ids[:, :-2, :]] & (L[:, 1:-1, :] == 0)
    return np.argwhere(m)


def light_up(v, level_at=lambda y: 15, rounds: int = 4) -> tuple[int, int]:
    """Place invisible light over dark spawn cells until none are left (or `rounds` passes). level_at(y) gives the
    light level to use at a row. Returns (lights placed, dark cells left)."""
    placed = 0
    for _ in range(rounds):
        cells = dark_spawns(v)
        if len(cells) == 0:
            return placed, 0
        taken = np.zeros(len(cells), dtype=bool)
        order = np.lexsort((cells[:, 2], cells[:, 0], cells[:, 1]))
        for i in order:
            if taken[i]:
                continue
            x, y, z = cells[i]
            lv = int(level_at(int(y)))
            v.set(int(x), int(y) + 1, int(z), f"minecraft:light[level={lv},waterlogged=false]")
            placed += 1
            d = np.abs(cells[:, 0] - x) + np.abs(cells[:, 1] - y) + np.abs(cells[:, 2] - z)
            taken |= d <= lv - 2
    return placed, len(dark_spawns(v))
