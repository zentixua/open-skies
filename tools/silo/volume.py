"""Dense block volume for one generated structure, exported later as chunk sections.

A volume is a numpy array of palette ids indexed [x, y, z] in local coordinates with a world origin. Palette entries
are block state strings as in /setblock ("minecraft:oak_stairs[facing=east,half=bottom]"). Id 0 means "leave the
world block as it is"; "minecraft:air" is an ordinary entry that clears a block.
"""
from __future__ import annotations

import numpy as np

KEEP = 0


class Volume:
    def __init__(self, origin: tuple[int, int, int], size: tuple[int, int, int]):
        self.origin = origin
        self.size = size
        self.ids = np.zeros(size, dtype=np.uint16)
        self.palette: list[str] = ["<keep>"]
        self.index: dict[str, int] = {}
        self.block_entities: dict[tuple[int, int, int], dict] = {}

    def id(self, state: str) -> int:
        if "[" not in state and ":" not in state:
            state = "minecraft:" + state
        elif ":" not in state.split("[", 1)[0]:
            state = "minecraft:" + state
        i = self.index.get(state)
        if i is None:
            i = len(self.palette)
            if i >= 65535:
                raise ValueError("palette overflow")
            self.palette.append(state)
            self.index[state] = i
        return i

    # local-coordinate helpers -------------------------------------------------------------------------------------

    def inside(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]

    def set(self, x: int, y: int, z: int, state: str, nbt: dict | None = None) -> None:
        if not self.inside(x, y, z):
            return
        self.ids[x, y, z] = self.id(state)
        if nbt is not None:
            self.block_entities[(x, y, z)] = nbt
        else:
            self.block_entities.pop((x, y, z), None)

    def get(self, x: int, y: int, z: int) -> str | None:
        if not self.inside(x, y, z):
            return None
        i = int(self.ids[x, y, z])
        return None if i == KEEP else self.palette[i]

    def box(self, x0, y0, z0, x1, y1, z1, state: str) -> None:
        """Fill the inclusive box, clipped to the volume."""
        xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1)); za, zb = sorted((z0, z1))
        xa, ya, za = max(xa, 0), max(ya, 0), max(za, 0)
        xb, yb, zb = min(xb, self.size[0] - 1), min(yb, self.size[1] - 1), min(zb, self.size[2] - 1)
        if xa > xb or ya > yb or za > zb:
            return
        self.ids[xa:xb + 1, ya:yb + 1, za:zb + 1] = self.id(state)

    def mask(self, y0: int, y1: int, m: np.ndarray, state: str) -> None:
        """Set every column where the 2D mask m[x, z] is true, for y0..y1 inclusive."""
        ya, yb = max(min(y0, y1), 0), min(max(y0, y1), self.size[1] - 1)
        if ya > yb:
            return
        sl = self.ids[:, ya:yb + 1, :]
        sl[np.broadcast_to(m[:, None, :], sl.shape)] = self.id(state)

    def used_states(self) -> list[str]:
        present = np.unique(self.ids)
        return [self.palette[i] for i in present if i != KEEP]
