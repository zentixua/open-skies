"""The plain the complex stands on: one open grassland across the whole field, easing into the natural land.

In the show's 2052 scenes the silos lie in open, rolling grassland. Here the natural ground under the field is
low-passed (a Gaussian over land only, so river beds do not pull it down), changes are capped, and the plain
weight falls from 1 within --core of the nearest silo to 0 at --edge, with a ragged edge so the forest boundary
reads as natural. Inside the plain trees are cleared; water stays, and land next to water is never lowered (so no
water spills). Each silo's own site (site.py) blends into this plain.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from heights import MISSING, read_area
from site import hash01, smooth
from volume import Volume

SIGMA = 40.0          # metres of the low-pass
MAX_CHANGE = 9        # blocks the plain may move the natural ground
CORE, EDGE = 150.0, 240.0
TREES_OUT = 0.5       # plain weight above which trees are cleared
SHORE = 8             # land within this many blocks of water is not lowered


def gaussian_conv(a: np.ndarray, w: np.ndarray, sigma_cells: float) -> np.ndarray:
    """Normalised convolution: weighted mean of a with weights w under a Gaussian."""
    r = int(3 * sigma_cells)
    ax = np.arange(-r, r + 1)
    g = np.exp(-ax ** 2 / (2 * sigma_cells ** 2))
    g /= g.sum()

    def sep(m):
        m = np.apply_along_axis(lambda v: np.convolve(v, g, mode="same"), 0, m)
        return np.apply_along_axis(lambda v: np.convolve(v, g, mode="same"), 1, m)
    num = sep(a * w)
    den = sep(w)
    return np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0)


class Field:
    def __init__(self, layout_path: str, world: str, cache_dir: str):
        self.layout = json.load(open(layout_path))
        self.silos = self.layout["silos"]
        xs = [s["x"] for s in self.silos]; zs = [s["z"] for s in self.silos]
        m = int(EDGE + 3 * SIGMA + 16)
        self.x0, self.z0 = min(xs) - m, min(zs) - m
        self.nx, self.nz = max(xs) + m - self.x0 + 1, max(zs) + m - self.z0 + 1
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir, f"field_{self.x0}_{self.z0}_{self.nx}_{self.nz}.npz")
        if os.path.exists(cache):
            d = np.load(cache)
            self.ground, self.water, self.top = d["ground"], d["water"], d["top"]
        else:
            self.ground, self.water, self.top = read_area(world, self.x0, self.z0, self.nx, self.nz)
            np.savez_compressed(cache, ground=self.ground, water=self.water, top=self.top)
        self._plain()

    def _plain(self) -> None:
        known = self.ground > MISSING
        land = known & (self.water <= MISSING)
        g = np.where(known, self.ground, 0).astype(float)
        smooth_g = gaussian_conv(g, land.astype(float), SIGMA)
        X = np.arange(self.nx)[:, None] + self.x0
        Z = np.arange(self.nz)[None, :] + self.z0
        d = np.full((self.nx, self.nz), 1e9)
        for s in self.silos:
            d = np.minimum(d, np.hypot(X - s["x"], Z - s["z"]))
        rag = 30 * (hash01(X // 24, Z // 24, 7) - 0.5) + 12 * (hash01(X // 7, Z // 7, 9) - 0.5)
        self.weight = 1 - smooth(CORE, EDGE, d + rag)
        self.dist = d
        change = np.clip(smooth_g - g, -MAX_CHANGE, MAX_CHANGE)
        # never lower land near water
        wet = (self.water > MISSING).astype(float)
        near_water = np.zeros_like(wet, bool)
        if wet.any():
            k = np.ones(2 * SHORE + 1) / (2 * SHORE + 1)
            nw = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, wet)
            nw = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, nw)
            near_water = nw > 0
        change = np.where(near_water, np.maximum(change, 0), change)
        plain = g + self.weight * change
        self.height = np.where(land, np.round(plain), np.where(known, self.ground, MISSING)).astype(np.int32)
        self.land = land

    def slice(self, x: int, z: int, radius: int):
        """height (plain), water and top arrays around x, z, as heights.read_area returns them."""
        i, k = x - radius - self.x0, z - radius - self.z0
        n = 2 * radius + 1
        sl = (slice(i, i + n), slice(k, k + n))
        return self.height[sl], self.water[sl], self.top[sl]

    def tiles(self, size: int = 128, skip_site: float = 100):
        """Plain tiles, nearest to Silo 1 first: (name, Volume) without columns a silo site rebuilds anyway."""
        s1 = self.silos[0]
        tiles = []
        for i in range(0, self.nx, size):
            for k in range(0, self.nz, size):
                w = self.weight[i:i + size, k:k + size]
                if w.max() <= 0.02:
                    continue
                cx, cz = self.x0 + i + size // 2, self.z0 + k + size // 2
                tiles.append((math.hypot(cx - s1["x"], cz - s1["z"]), i, k))
        tiles.sort()
        for _, i, k in tiles:
            v = self.tile(i, k, size, skip_site)
            if v is not None:
                yield f"plain_{self.x0 + i}_{self.z0 + k}", v

    def tile(self, i: int, k: int, size: int, skip_site: float) -> Volume | None:
        sl = (slice(i, i + size), slice(k, k + size))
        w, h, n, top = self.weight[sl], self.height[sl], self.ground[sl], self.top[sl]
        land, dist = self.land[sl], self.dist[sl]
        work = land & (w > 0.02) & (dist > skip_site)
        if not work.any():
            return None
        clear = work & (w > TREES_OUT)
        lo = int(np.minimum(h, n)[work].min()) - 3
        hi = int(np.maximum(np.where(clear, top, h), np.maximum(h, n))[work].max()) + 1
        nx, nz = h.shape
        v = Volume((self.x0 + i, lo, self.z0 + k), (nx, hi - lo + 1, nz))
        ids = v.ids
        grass, dirt, air, tall = v.id("minecraft:grass_block"), v.id("minecraft:dirt"), v.id("minecraft:air"), v.id("minecraft:short_grass")
        X = np.arange(nx)[:, None] + self.x0 + i
        Z = np.arange(nz)[None, :] + self.z0 + k
        tuft = hash01(X, Z, 3) < 0.3
        for a, b in zip(*np.nonzero(work)):
            t, nat = int(h[a, b]), int(n[a, b])
            col = ids[a, :, b]
            if t != nat:
                col[min(t, nat) - 2 - lo:t - lo] = dirt
                col[t - lo] = grass
            up = int(top[a, b]) if clear[a, b] else nat
            if up > t:
                col[t + 1 - lo:up + 1 - lo] = air
            if (t != nat or clear[a, b]) and tuft[a, b] and t + 1 - lo < col.shape[0]:
                if t != nat:
                    col[t + 1 - lo] = tall
        return v
