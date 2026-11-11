"""Block-resolution ground heights of a world area, read from region files (a golden copy of the map).

ground: top of the natural ground, trees removed (MOTION_BLOCKING_NO_LEAVES with trunks filtered out; the sea or
river bed under water). water: the water surface where there is water, else None-like -9999. top: highest block
(WORLD_SURFACE, tree crowns included). Arrays are indexed [x - x0, z - z0].
"""
from __future__ import annotations

import os
import warnings
import zlib

import numpy as np

from site_fit import heightmap, nbt

MISSING = -9999


def read_area(world: str, x0: int, z0: int, nx: int, nz: int, min_y: int = -64, height: int = 384):
    maps = {k: np.full((nx, nz), MISSING, np.int32) for k in ("MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR", "WORLD_SURFACE")}
    for cx in range(x0 >> 4, (x0 + nx - 1 >> 4) + 1):
        for cz in range(z0 >> 4, (z0 + nz - 1 >> 4) + 1):
            path = os.path.join(world, "region", f"r.{cx >> 5}.{cz >> 5}.mca")
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                i = (cx & 31) + (cz & 31) * 32
                f.seek(i * 4)
                off = int.from_bytes(f.read(3), "big")
                if not off:
                    continue
                f.seek(off * 4096)
                ln = int.from_bytes(f.read(4), "big")
                if f.read(1)[0] != 2:
                    continue
                c = nbt(zlib.decompress(f.read(ln - 1)))
            hm = c.get("Heightmaps", {})
            for k, arr in maps.items():
                if k not in hm:
                    continue
                h = heightmap(hm[k], height) + min_y - 1          # [z][x] in the chunk
                bx, bz = cx * 16 - x0, cz * 16 - z0
                xa, za = max(bx, 0), max(bz, 0)
                xb, zb = min(bx + 16, nx), min(bz + 16, nz)
                if xa < xb and za < zb:
                    arr[xa:xb, za:zb] = h.T[xa - bx:xb - bx, za - bz:zb - bz]
    mb, of, ws = maps["MOTION_BLOCKING_NO_LEAVES"], maps["OCEAN_FLOOR"], maps["WORLD_SURFACE"]
    known = (mb > MISSING) & (of > MISSING)
    wet = known & (mb > of)                       # fluid above the bed (leaves raise OCEAN_FLOOR, not this)
    ground = np.where(wet, of, mb)
    ground = median5(np.where(known, ground, MISSING))   # trunks are one or two blocks wide
    water = np.where(wet, mb, MISSING)
    return ground, water, np.where(known, ws, MISSING)


def median5(a: np.ndarray) -> np.ndarray:
    p = np.pad(a, 2, mode="edge")
    stack = np.stack([p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(5) for j in range(5)])
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        m = np.nanmedian(np.where(stack == MISSING, np.nan, stack.astype(float)), axis=0)
    return np.where(np.isnan(m), MISSING, np.round(m)).astype(np.int32)
