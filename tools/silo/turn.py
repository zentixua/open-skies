"""Quarter turns of generated volumes about a vertical axis, block states included.

A turn is clockwise seen from above with north up (Minecraft: x east, z south): west -> north -> east -> south.
Used to point a silo's tunnel (built due west) along any of the four bearings.
"""
from __future__ import annotations

import re

import numpy as np

from volume import Volume

CW = {"north": "east", "east": "south", "south": "west", "west": "north"}


def turn_state(state: str, k: int) -> str:
    k %= 4
    if k == 0 or "[" not in state:
        return state
    name, props = state[:-1].split("[", 1)
    out = []
    for kv in props.split(","):
        key, val = kv.split("=", 1)
        if key == "facing" and val in CW:
            for _ in range(k):
                val = CW[val]
        elif key == "axis" and k % 2 and val in ("x", "z"):
            val = "z" if val == "x" else "x"
        elif key == "rotation" and val.isdigit():            # signs, banners, skulls: 16 steps, 4 per quarter
            val = str((int(val) + 4 * k) % 16)
        elif key in CW and val in ("true", "false", "none", "low", "tall", "side", "up"):   # walls, panes, fences, wire
            pass                                             # renamed below, so the side keeps its value
        elif key == "shape" and ("north" in val or "east" in val or "_" in val and val.startswith("ascending")):
            raise ValueError(f"rail shape {state!r}: not handled")
        out.append((key, val))
    sides = {key: val for key, val in out if key in CW}
    if sides:
        rot = {}
        for key, val in sides.items():
            nk = key
            for _ in range(k):
                nk = CW[nk]
            rot[nk] = val
        out = [(key, rot[key]) if key in CW else (key, val) for key, val in out]
    return name + "[" + ",".join(f"{a}={b}" for a, b in out) + "]"


def turn_points(points, k: int, px: int, pz: int):
    """World x, z points turned k quarters clockwise about px, pz."""
    out = []
    for x, z in points:
        for _ in range(k % 4):
            x, z = px - (z - pz), pz + (x - px)
        out.append((x, z))
    return out


def turn_grid(a: np.ndarray, k: int) -> np.ndarray:
    """A square [x, z] grid centred on the axis, its content turned k quarters clockwise."""
    return np.rot90(a, k % 4, axes=(0, 1)).copy()


def turn_volume(v: Volume, k: int, px: int, pz: int) -> Volume:
    """v turned k quarters clockwise about the vertical line through px, pz (integer block coordinates)."""
    k %= 4
    if k == 0:
        return v
    ox, oy, oz = v.origin
    nx, ny, nz = v.size
    ids = v.ids
    for _ in range(k):
        ids = np.rot90(ids, 1, axes=(0, 2))
        ox, oz = px - (oz + nz - 1 - pz), pz + (ox - px)
        nx, nz = nz, nx
    out = Volume((ox, oy, oz), (nx, ny, nz))
    out.palette = ["<keep>"] + [turn_state(s, k) for s in v.palette[1:]]
    out.index = {s: i for i, s in enumerate(out.palette) if i}
    out.ids = np.ascontiguousarray(ids)
    if v.block_entities:
        raise ValueError("block entities are not turned")
    return out
