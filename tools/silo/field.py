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
from surface import hash01, smooth
from volume import Volume

SIGMA = 40.0          # metres of the low-pass
MAX_CHANGE = 9        # blocks the plain may move the natural ground
CORE, EDGE = 150.0, 240.0
TREES_OUT = 0.5       # plain weight above which trees are cleared
SHORE = 8             # shaped ground within this many blocks of remaining water stays above its surface
FILL = 0.35           # plain weight above which water is filled
TOWN_KEEP = 12        # blocks around a town chunk left untouched


def dilate_max(a: np.ndarray, r: int) -> np.ndarray:
    """Maximum over a (2r+1)-square neighbourhood, by r 3x3 steps."""
    out = a.copy()
    for _ in range(r):
        p = np.pad(out, 1, mode="edge")
        out = np.max(np.stack([p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)]), axis=0)
    return out


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
    return np.where(den > 1e-3, num / np.maximum(den, 1e-6), np.nan)


class Field:
    def __init__(self, layout_path: str, world: str, cache_dir: str):
        self.layout = json.load(open(layout_path))
        self.silos = [s for s in self.layout["silos"] if not s.get("unplaced")]
        xs = [s["x"] for s in self.silos] + [s["ring"][0] for s in self.silos if "ring" in s]
        zs = [s["z"] for s in self.silos] + [s["ring"][1] for s in self.silos if "ring" in s]
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
        wet = known & (self.water > MISSING)
        land = known & ~wet
        g = np.where(known, self.ground, 0).astype(float)
        smooth_g = gaussian_conv(g, land.astype(float), SIGMA)
        X = np.arange(self.nx)[:, None] + self.x0
        Z = np.arange(self.nz)[None, :] + self.z0
        d = np.full((self.nx, self.nz), 1e9)
        for s in self.silos:            # the plain reaches out from each shaft and from its ring (crater)
            d = np.minimum(d, np.hypot(X - s["x"], Z - s["z"]))
            if "ring" in s:
                d = np.minimum(d, np.hypot(X - s["ring"][0], Z - s["ring"][1]))
        rag = 30 * (hash01(X // 24, Z // 24, 7) - 0.5) + 12 * (hash01(X // 7, Z // 7, 9) - 0.5)
        w = 1 - smooth(CORE, EDGE, d + rag)
        # Zearth's own towns and villages stay as built: the plain fades out before them
        towns = self.layout.get("towns", [])
        if towns:
            dt = np.full((self.nx, self.nz), 1e9)
            for tx, tz in towns:
                if self.x0 - 100 <= tx <= self.x0 + self.nx + 100 and self.z0 - 100 <= tz <= self.z0 + self.nz + 100:
                    dt = np.minimum(dt, np.maximum(np.abs(X - tx), np.abs(Z - tz)) - 8)
            w = w * smooth(TOWN_KEEP, TOWN_KEEP + 48, dt)
        self.weight, self.dist = w, d
        # land eases toward the low-passed ground; water inside the plain is filled to it
        # far from any land (open water) the fill comes up to a block above the water
        smooth_g = np.where(np.isnan(smooth_g), np.where(wet, self.water + 1.0, g), smooth_g)
        plain = np.where(land, g + w * np.clip(smooth_g - g, -MAX_CHANGE, MAX_CHANGE), smooth_g)
        self.filled = wet & (w > FILL)
        # banks hold the water that stays: shaped ground near it stays a block above its surface
        wl = dilate_max(np.where(wet & ~self.filled, self.water, MISSING), SHORE)
        plain = np.where(wl > MISSING, np.maximum(plain, wl + 1), plain)
        shaped = known & (w > 0.02) & (land | self.filled)
        self.height = np.where(shaped, np.round(plain), self.ground).astype(np.int32)
        self.shaped = shaped

    def slice(self, x: int, z: int, radius: int):
        """For surface.Site around x, z: plain height, water that stays, highest block, original ground, plain weight
        (0 at Zearth's towns, which no site may touch)."""
        i, k = x - radius - self.x0, z - radius - self.z0
        n = 2 * radius + 1
        sl = (slice(i, i + n), slice(k, k + n))
        water = np.where(self.filled[sl], MISSING, self.water[sl])
        top = np.maximum(self.top[sl], np.where(self.filled[sl], self.water[sl], MISSING))
        return self.height[sl], water, top, self.ground[sl], self.weight[sl]

    def tiles(self, size: int = 128, skip_site: float = 100, gaps: int | None = None):
        """Plain tiles, nearest to Silo 1 first: (name, Volume) without columns a silo site rebuilds anyway.

        With gaps (the sites' half-size, surface.Site.radius) only the columns the first pass skipped as near a
        shaft or ring but that no site square covers: the ring sits 115.5 m out along the tunnel, so its 100 m
        circle reaches past the 190 m site square and left forest and water there."""
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
            v = self.tile(i, k, size, skip_site, gaps)
            if v is not None:
                yield f"{'gap' if gaps else 'plain'}_{self.x0 + i}_{self.z0 + k}", v

    def tile(self, i: int, k: int, size: int, skip_site: float, gaps: int | None = None) -> Volume | None:
        sl = (slice(i, i + size), slice(k, k + size))
        w, h, n, top = self.weight[sl], self.height[sl], self.ground[sl], self.top[sl]
        dist, filled, ws = self.dist[sl], self.filled[sl], self.water[sl]
        if gaps is None:
            work = self.shaped[sl] & (dist > skip_site)
        else:
            X = np.arange(h.shape[0])[:, None] + self.x0 + i
            Z = np.arange(h.shape[1])[None, :] + self.z0 + k
            site = np.zeros(h.shape, bool)
            for s in self.silos:
                site |= (np.abs(X - s["x"]) <= gaps) & (np.abs(Z - s["z"]) <= gaps)
            work = self.shaped[sl] & (dist <= skip_site) & ~site
        if not work.any():
            return None
        clear = work & (w > TREES_OUT)
        lo = int(np.minimum(h, n)[work].min()) - 3
        hi = int(np.maximum(np.maximum(np.where(clear, top, h), np.maximum(h, n)), ws)[work].max()) + 1
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
            if t != nat or filled[a, b]:
                col[min(t, nat) - 2 - lo:t - lo] = dirt
                col[t - lo] = grass
            up = int(top[a, b]) if clear[a, b] else nat
            if filled[a, b]:
                up = max(up, int(ws[a, b]))        # the water above the new ground goes
            if up > t:
                col[t + 1 - lo:up + 1 - lo] = air
            if (t != nat or clear[a, b]) and tuft[a, b] and t + 1 - lo < col.shape[0]:
                if t != nat:
                    col[t + 1 - lo] = tall
        return v
