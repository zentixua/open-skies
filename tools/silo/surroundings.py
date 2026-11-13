"""The complex's surroundings as blocks: the gate and its coach park, the perimeter roads, the railway and its yard,
and the facility yards with their hangars, tank farms, sheds and car parks. What and where come from
canon/surroundings.json (canon_surroundings.py, the show's 2052 aerial); this module only turns them into Volumes.

Each item stands on the ground it finds: an area (yard, coach park, car park) is levelled at the median of the natural
ground under it and eased back to the natural ground over APRON blocks; trees and hills above go. Buildings, tanks and
domes stand on that level. Roads and track beds follow the natural ground smoothed over ROAD_SMOOTH metres along the
line. Nothing is laid within RING_KEEP of a ring centre (the rings, their paths and the plain are site.py's and
field.py's), and items without a size in the frame are not built (canon/surroundings.json "unsized").

Run after the plain and the silos (it reads the ground they left) and before the trees:

  from surroundings import Surroundings
  vols = Surroundings(layout, ground_fn=lambda x0, z0, nx, nz: read_area(world, x0, z0, nx, nz)).volumes()

  python3 surroundings.py LAYOUT.json [--world DIR] [--png top.png]   # without --world: flat test ground

Block choices (presentation, the frame gives colours only): asphalt gray concrete, gravel yards and roads gravel,
bare strip coarse dirt, white roofs and tanks white concrete, walls light gray concrete, rails on a gravel bed.
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

from heights import MISSING
from volume import Volume

HERE = os.path.dirname(os.path.abspath(__file__))
RING_KEEP = 116          # paths.RING_PATH_R + the path's half width + 3
APRON = 6                # blocks over which a levelled area eases back to the natural ground
ROAD_SMOOTH = 31         # metres: moving average of the natural ground along a road
SHOULDER = 3             # blocks of eased ground beside a road
CHUNK = 48               # metres of centre line per road volume
AVENUE_W = 3             # paths.py axis road
CANOPY_EDGE = 4          # frame 02: the canopy's low arches stand about 2.5 people high
BAND_H = 2               # frame 02: the grey band beside the canopy, about a person high

DIRT, GRASS, AIR = "minecraft:dirt", "minecraft:grass_block", "minecraft:air"
SURFACE = {"gravel": "minecraft:gravel", "paved": "minecraft:gray_concrete", "bare": "minecraft:gravel",
           "vehicle_rows": "minecraft:gray_concrete", "road": "minecraft:gravel", "lawn": GRASS}
SURFACE_BY_ID = {"gate_forecourt": "minecraft:light_gray_concrete", "access_road": "minecraft:gray_concrete",
                 "sw_vehicle_yard": "minecraft:gravel"}
WALL, ROOF_FLAT, ROOF_WHITE = "minecraft:light_gray_concrete", "minecraft:gray_concrete", "minecraft:white_concrete"
FLOOR = "minecraft:smooth_stone"


# geometry --------------------------------------------------------------------------------------------------------

def inside(poly: np.ndarray, X: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """Even-odd point in polygon for cell centres X, Z."""
    m = np.zeros(X.shape, bool)
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        c = ((z1 > Z) != (z2 > Z)) & (X < (x2 - x1) * (Z - z1) / ((z2 - z1) if z2 != z1 else 1e-9) + x1)
        m ^= c
    return m


def densify(pts, step=1.0) -> np.ndarray:
    out = []
    for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, z1 - z0) / step))
        for t in np.arange(n) / n:
            out.append((x0 + t * (x1 - x0), z0 + t * (z1 - z0)))
    out.append(tuple(pts[-1]))
    return np.array(out, float)


def offset(pts: np.ndarray, d: float) -> np.ndarray:
    """A polyline moved d to its left (normal of the local direction)."""
    t = np.gradient(pts, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1)[:, None], 1e-9)
    return pts + d * np.c_[-t[:, 1], t[:, 0]]


def cell_path(pts: np.ndarray) -> list[tuple[int, int]]:
    """4-connected cells along a dense polyline (diagonals become a staircase, as vanilla rails need)."""
    out: list[tuple[int, int]] = []
    for x, z in pts:
        c = (int(math.floor(x)), int(math.floor(z)))
        if out and c == out[-1]:
            continue
        if out and abs(c[0] - out[-1][0]) + abs(c[1] - out[-1][1]) == 2:
            out.append((c[0], out[-1][1]))
        if not out or c != out[-1]:
            out.append(c)
    return out


def rail_shape(prev, cur, nxt, hp, hc, hn) -> str:
    def d(a, b):
        return (b[0] - a[0], b[1] - a[1])
    name = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}
    ends = {name[d(cur, o)] for o in (prev, nxt) if o is not None}
    if nxt is not None and hn > hc:
        return "ascending_" + name[d(cur, nxt)]
    if prev is not None and hp > hc:
        return "ascending_" + name[d(cur, prev)]
    if ends <= {"east", "west"}:
        return "east_west"
    if ends <= {"north", "south"}:
        return "north_south"
    a = "south" if "south" in ends else "north"
    b = "east" if "east" in ends else "west"
    return f"{a}_{b}"


def smoothstep(x):
    t = np.clip(x, 0, 1)
    return t * t * (3 - 2 * t)


# the module ------------------------------------------------------------------------------------------------------

class Surroundings:
    def __init__(self, layout: dict, ground_fn, source: str | None = None):
        """layout: layout.json (silos with rings, rotation_deg, spacing, gate). ground_fn(x0, z0, nx, nz) ->
        (ground, water, top) as heights.read_area: natural ground (trees removed), water surface or MISSING, top."""
        self.layout = layout
        self.src = json.load(open(source or os.path.join(HERE, "canon", "surroundings.json")))
        one = next(s for s in layout["silos"] if s["number"] == 1)
        self.one = tuple(one["ring"])
        r = math.radians(layout["rotation_deg"])
        self.cs, self.sn = math.cos(r), math.sin(r)
        self.k = layout["spacing"] / self.src["edge_m"]
        self.rings = np.array([s["ring"] for s in layout["silos"] if not s.get("unplaced")], float)
        self.ground_fn = ground_fn
        self.done: dict[tuple[int, int], int] = {}     # finished surface height per column, for what stands on it
        self.skipped: list[str] = []

    def w(self, p) -> tuple[float, float]:
        """Canon metres (x east, z south of Silo 1) -> world x, z."""
        x, z = p[0] * self.k, p[1] * self.k
        return self.one[0] + x * self.cs - z * self.sn, self.one[1] + x * self.sn + z * self.cs

    def wl(self, pts) -> np.ndarray:
        return np.array([self.w(p) for p in pts], float)

    # ground ----------------------------------------------------------------------------------------------------
    def area(self, x0, z0, x1, z1):
        """Grids over the inclusive cell box: X, Z (cell centres), ground, water, top, keep (near a ring)."""
        nx, nz = x1 - x0 + 1, z1 - z0 + 1
        g, wtr, top = self.ground_fn(x0, z0, nx, nz)
        X, Z = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(z0, z1 + 1) + 0.5, indexing="ij")
        keep = np.zeros(X.shape, bool)
        for rx, rz in self.rings:
            if abs(rx - (x0 + x1) / 2) < nx / 2 + RING_KEEP and abs(rz - (z0 + z1) / 2) < nz / 2 + RING_KEEP:
                keep |= np.hypot(X - rx, Z - rz) < RING_KEEP
        return X, Z, g, wtr, top, keep

    def column(self, v: Volume, i: int, k: int, g: int, h: int, top: int, surf: str) -> None:
        """One column of v (local i, k): ground from g to h, surface block at h, air above up to top."""
        y0 = v.origin[1]
        for y in range(min(g, h) + 1, h):
            v.set(i, y - y0, k, DIRT)
        if h < g:
            for y in range(h + 1, g + 1):
                v.set(i, y - y0, k, AIR)
        v.set(i, h - y0, k, surf)
        if h - 1 > g or h < g:
            v.set(i, h - 1 - y0, k, DIRT)
        for y in range(h + 1, max(top, g) + 1):
            v.set(i, y - y0, k, AIR)

    def level_area(self, poly_w: np.ndarray, surf: str, extra_h: int = 0, level: int | None = None):
        """Level a polygon (world) with an eased apron. Returns (volume, level, mask, X, Z) or None."""
        x0, z0 = np.floor(poly_w.min(0)).astype(int) - APRON - 1
        x1, z1 = np.ceil(poly_w.max(0)).astype(int) + APRON + 1
        X, Z, g, wtr, top, keep = self.area(x0, z0, x1, z1)
        m = inside(poly_w, X, Z) & ~keep
        known = g > MISSING
        if not (m & known).any():
            return None
        fin = np.array([[self.done.get((x0 + i, z0 + k), MISSING) for k in range(X.shape[1])] for i in range(X.shape[0])])
        base = np.where(fin > MISSING, fin, g)
        if level is None:
            level = int(round(float(np.median(base[m & known]))))
        from scipy import ndimage
        d = ndimage.distance_transform_edt(~m)
        apron = (d > 0) & (d <= APRON) & known & ~keep & (fin == MISSING)
        lo = int(min(level, base[(m | apron) & known].min())) - 2
        hi = int(max(level + extra_h, top[(m | apron) & known].max())) + 2
        v = Volume((int(x0), lo, int(z0)), (X.shape[0], hi - lo + 1, X.shape[1]))
        for i, k in zip(*np.nonzero((m | apron) & known)):
            if m[i, k]:
                h, s = level, surf
            else:
                t = float(smoothstep(d[i, k] / (APRON + 1)))
                h, s = int(round(level + t * (base[i, k] - level))), GRASS
            water = wtr[i, k] > MISSING
            self.column(v, i, k, int(base[i, k]), h, int(top[i, k]) if not water else int(wtr[i, k]), s)
            if water:                     # a pond or river under a yard is filled
                for y in range(int(base[i, k]) + 1, h):
                    v.set(i, y - lo, k, DIRT)
            self.done[(int(x0 + i), int(z0 + k))] = h
        return v, level, m, X, Z

    # items -----------------------------------------------------------------------------------------------------
    def volumes(self) -> list[Volume]:
        items = self.src["items"]
        order = ["gravel", "bare", "vehicle_rows", "paved", "lawn", "road", "rail", "round_pad", "band", "shed",
                 "barrel_hall", "tank", "dome", "mast", "canopy"]
        out: list[Volume] = []
        for kind in order:
            for it in items:
                if it["kind"] != kind:
                    continue
                fn = getattr(self, "b_" + kind, None)
                vs = fn(it) if fn else None
                if not vs:
                    self.skipped.append(it["id"])
                    continue
                out += [v for v in vs if v is not None]
        self.skipped += [it["id"] for it in items if it["kind"] not in order]
        out += self.avenue()
        return out

    def _area(self, it, polys=None):
        surf = SURFACE_BY_ID.get(it["id"], SURFACE.get(it["kind"], "minecraft:gravel"))
        vs = []
        for q in polys or ([it["poly"]] if "poly" in it else it.get("polys", [])):
            r = self.level_area(self.wl(q), surf)
            if r:
                vs.append(r[0])
        return vs

    b_gravel = b_bare = b_paved = _area

    def b_vehicle_rows(self, it):
        if it["id"] == "se_stacks":       # objects inside the gravel yard; single vehicles are not resolved
            return None
        return self._area(it)

    def b_lawn(self, it):
        a, b = it["axes_m"]
        c = it["centre"]
        t = math.radians(it["angle_deg"])
        poly = [(c[0] + a / 2 * math.cos(s) * math.cos(t) - b / 2 * math.sin(s) * math.sin(t),
                 c[1] + a / 2 * math.cos(s) * math.sin(t) + b / 2 * math.sin(s) * math.cos(t)) for s in np.linspace(0, 2 * math.pi, 72, endpoint=False)]
        return self._area(it, [poly])

    def line_cells(self, pts_w: np.ndarray, half: float, shoulder: int):
        """Per chunk of centre line: (X, Z, g, wtr, top, keep, dist, h_line) with h_line the smoothed ground of the
        nearest centre-line sample."""
        dense = densify(pts_w)
        # natural ground along the line, one sample per metre
        x0, z0 = np.floor(dense.min(0)).astype(int) - 2
        x1, z1 = np.ceil(dense.max(0)).astype(int) + 2
        G, WT, _ = self.ground_fn(int(x0), int(z0), int(x1 - x0 + 1), int(z1 - z0 + 1))
        hs = []
        for p in dense:
            i, k = int(math.floor(p[0])), int(math.floor(p[1]))
            f = self.done.get((i, k))
            if f is not None:
                hs.append(f)
                continue
            g, wt = G[i - x0, k - z0], WT[i - x0, k - z0]
            hs.append(int(max(g, wt + 1)) if g > MISSING else np.nan)
        hs = np.array(hs, float)
        ok = ~np.isnan(hs)
        if not ok.any():
            return
        hs = np.interp(np.arange(len(hs)), np.nonzero(ok)[0], hs[ok])
        ker = np.ones(ROAD_SMOOTH) / ROAD_SMOOTH
        hs = np.convolve(np.pad(hs, ROAD_SMOOTH // 2, mode="edge"), ker, mode="valid")
        for s in range(0, len(dense), CHUNK):
            seg = dense[max(0, s - 2):s + CHUNK + 2]
            hseg = hs[max(0, s - 2):s + CHUNK + 2]
            r = half + shoulder + 1
            a0, b0 = np.floor(seg.min(0) - r).astype(int)
            a1, b1 = np.ceil(seg.max(0) + r).astype(int)
            X, Z, g, wtr, top, keep = self.area(a0, b0, a1, b1)
            dd = np.hypot(X[..., None] - seg[:, 0], Z[..., None] - seg[:, 1])
            j = dd.argmin(-1)
            yield X, Z, g, wtr, top, keep, dd.min(-1), np.round(hseg[j]).astype(int), (a0, b0)

    def b_road(self, it):
        width = it.get("width_m", 7) * self.k
        half = width / 2
        surf = SURFACE_BY_ID.get(it["id"], SURFACE["road"])
        vs = []
        for X, Z, g, wtr, top, keep, dist, hl, (a0, b0) in self.line_cells(self.wl(it["line"]), half, SHOULDER):
            on = (dist <= half) & (g > MISSING) & ~keep
            sh = (dist > half) & (dist <= half + SHOULDER) & (g > MISSING) & ~keep
            if not (on | sh).any():
                continue
            fin = np.array([[self.done.get((a0 + i, b0 + k), MISSING) for k in range(X.shape[1])] for i in range(X.shape[0])])
            lo = int(min(hl[on | sh].min(), g[on | sh].min())) - 2
            hi = int(max(hl[on | sh].max(), top[on | sh].max())) + 2
            v = Volume((int(a0), lo, int(b0)), (X.shape[0], hi - lo + 1, X.shape[1]))
            for i, k in zip(*np.nonzero(on | sh)):
                if fin[i, k] > MISSING and not on[i, k]:
                    continue                  # a yard's own surface stays
                base = int(fin[i, k]) if fin[i, k] > MISSING else int(g[i, k])
                if on[i, k]:
                    h, s = int(hl[i, k]), surf
                    if it["id"] == "access_road" and dist[i, k] < 0.5:
                        s = "minecraft:yellow_concrete"   # frame 02: a yellow centre line
                else:
                    t = float(smoothstep((dist[i, k] - half) / (SHOULDER + 1)))
                    h, s = int(round(hl[i, k] + t * (base - hl[i, k]))), GRASS
                self.column(v, i, k, base, h, int(max(top[i, k], wtr[i, k])), s)
                self.done[(int(a0 + i), int(b0 + k))] = h
            vs.append(v)
        return vs

    def b_rail(self, it):
        n = it.get("tracks", 1)
        sp = it.get("track_spacing_m", 4.5) * self.k
        pts = densify(self.wl(it["line"]), 0.5)
        vs = []
        for t in range(n):
            line = offset(pts, (t - (n - 1) / 2) * sp)
            # the bed: gravel 3 wide on the smoothed ground
            for X, Z, g, wtr, top, keep, dist, hl, (a0, b0) in self.line_cells(line[::2], 1.5, 1):
                on = (dist <= 1.5) & (g > MISSING) & ~keep
                if not on.any():
                    continue
                lo = int(min(hl[on].min(), g[on].min())) - 2
                hi = int(max(hl[on].max() + 1, top[on].max())) + 2
                v = Volume((int(a0), lo, int(b0)), (X.shape[0], hi - lo + 1, X.shape[1]))
                for i, k in zip(*np.nonzero(on)):
                    base = self.done.get((int(a0 + i), int(b0 + k)), int(g[i, k]))
                    self.column(v, i, k, base, int(hl[i, k]), int(max(top[i, k], wtr[i, k])), "minecraft:gravel")
                    self.done[(int(a0 + i), int(b0 + k))] = int(hl[i, k])
                vs.append(v)
            # the rails on top, one per cell of a 4-connected path
            cells = [c for c in cell_path(line) if not (np.hypot(self.rings[:, 0] - c[0], self.rings[:, 1] - c[1]) < RING_KEEP).any()]
            hs = [self.done.get(c) for c in cells]
            for s in range(0, len(cells), 256):
                part = [(c, h) for c, h in zip(cells[s:s + 256], hs[s:s + 256]) if h is not None]
                if not part:
                    continue
                xs = [c[0] for c, _ in part]; zs = [c[1] for c, _ in part]; ys = [h for _, h in part]
                v = Volume((min(xs), min(ys) + 1, min(zs)), (max(xs) - min(xs) + 1, max(ys) - min(ys) + 2, max(zs) - min(zs) + 1))
                for j in range(s, min(s + 256, len(cells))):
                    c, h = cells[j], hs[j]
                    if h is None:
                        continue
                    pv = cells[j - 1] if j > 0 else None
                    nx = cells[j + 1] if j + 1 < len(cells) else None
                    hp = hs[j - 1] if pv is not None and hs[j - 1] is not None else h
                    hn = hs[j + 1] if nx is not None and hs[j + 1] is not None else h
                    v.set(c[0] - v.origin[0], h + 1 - v.origin[1], c[1] - v.origin[2],
                          f"minecraft:rail[shape={rail_shape(pv, c, nx, hp, h, hn)},waterlogged=false]")
                vs.append(v)
        return vs

    # things standing on the levelled ground -----------------------------------------------------------------------
    def stand(self, poly_w: np.ndarray, height: int):
        """Volume over a footprint standing on its finished level (levels it first if nothing has)."""
        r = self.level_area(poly_w, FLOOR, extra_h=height)
        if r is None:
            return None
        v, level, m, X, Z = r
        return v, level, m, X, Z

    def b_shed(self, it):
        if "height_m" not in it:
            return None
        hgt = max(3, int(round(it["height_m"] * self.k)))
        poly = self.wl(it["poly"])
        r = self.stand(poly, hgt)
        if r is None:
            return None
        v, level, m, X, Z = r
        from scipy import ndimage
        edge = m & ~ndimage.binary_erosion(m)
        # a door 4 wide, 4 high, in the middle of the first long side
        e = [np.linalg.norm(poly[(i + 1) % 4] - poly[i]) for i in range(4)]
        a = int(np.argmax(e))
        mid = (poly[a] + poly[(a + 1) % 4]) / 2
        door = np.hypot(X - mid[0], Z - mid[1]) <= 2.2
        y0 = v.origin[1]
        for i, k in zip(*np.nonzero(m)):
            for y in range(level + 1, level + hgt):
                wall = edge[i, k] and not (door[i, k] and y <= level + 4)
                v.set(i, y - y0, k, WALL if wall else AIR)
            v.set(i, level + hgt - y0, k, ROOF_FLAT)
        return [v]

    def b_barrel_hall(self, it):
        if "height_m" not in it:
            return None
        poly = self.wl(it["poly"])
        e = [np.linalg.norm(poly[(i + 1) % 4] - poly[i]) for i in range(4)]
        a = int(np.argmax(e))
        p0, p1 = poly[a], poly[(a + 1) % 4]
        ax = (p1 - p0) / np.linalg.norm(p1 - p0)            # the barrel's axis: along the long side
        nrm = np.array([-ax[1], ax[0]])
        width = abs(float((poly[(a + 2) % 4] - p0) @ nrm))
        length = float(np.linalg.norm(p1 - p0))
        hgt = max(4, int(round(it["height_m"] * self.k)))
        r = self.stand(poly, hgt)
        if r is None:
            return None
        v, level, m, X, Z = r
        side = np.sign(float((poly[(a + 2) % 4] - p0) @ nrm)) or 1.0
        s = ((X - p0[0]) * nrm[0] + (Z - p0[1]) * nrm[1]) * side          # across, 0..width
        ln = (X - p0[0]) * ax[0] + (Z - p0[1]) * ax[1]                     # along, 0..length
        u = np.clip(2 * s / max(width, 1) - 1, -1, 1)
        roof = level + np.round(hgt * np.sqrt(np.clip(1 - u * u, 0, 1))).astype(int)
        roof = np.where(m, np.maximum(roof, level + 1), 0)
        end = m & ((ln < 1) | (ln > length - 1))
        door = end & (ln > length / 2) & (np.abs(u) < 0.45)               # one end open: a hangar door
        y0 = v.origin[1]
        for i, k in zip(*np.nonzero(m)):
            top = int(roof[i, k])
            nb = [roof[i + di, k + dk] for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= i + di < m.shape[0] and 0 <= k + dk < m.shape[1] and m[i + di, k + dk]]
            low = min([top] + [int(b) for b in nb]) if len(nb) == 4 else level + 1
            for y in range(level + 1, top + 1):
                if y >= low:
                    st = ROOF_WHITE
                elif end[i, k] and not (door[i, k] and y <= level + 0.6 * hgt):
                    st = WALL
                else:
                    st = AIR
                v.set(i, y - y0, k, st)
        return [v]

    def _round(self, it, solid_top):
        if "height_m" not in it or "diameter_m" not in it:
            return None
        hgt = max(2, int(round(it["height_m"] * self.k)))
        rad = it["diameter_m"] * self.k / 2
        vs = []
        for p in it["points"]:
            c = np.array(self.w(p))
            poly = np.array([c + rad * np.array([math.cos(t), math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
            r = self.stand(poly, hgt)
            if r is None:
                continue
            v, level, m, X, Z = r
            rr = np.hypot(X - c[0], Z - c[1])
            if solid_top:                         # tank: wall ring, flat top
                top = np.full(rr.shape, level + hgt)
            else:                                 # dome: a spherical cap of the given rise
                R = (rad * rad + hgt * hgt) / (2 * hgt)
                top = level + np.round(np.sqrt(np.clip(R * R - rr * rr, 0, None)) - (R - hgt)).astype(int)
                top = np.maximum(top, level + 1)
            y0 = v.origin[1]
            for i, k in zip(*np.nonzero(m)):
                nb = [top[i + di, k + dk] for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= i + di < m.shape[0] and 0 <= k + dk < m.shape[1] and m[i + di, k + dk]]
                low = min([int(top[i, k])] + [int(b) for b in nb]) if len(nb) == 4 else level + 1
                for y in range(level + 1, int(top[i, k]) + 1):
                    v.set(i, y - y0, k, ROOF_WHITE if (y >= low or y == top[i, k]) else AIR)
            vs.append(v)
        return vs

    def b_tank(self, it):
        return self._round(it, True)

    def b_dome(self, it):
        return self._round(it, False)

    def b_mast(self, it):
        hs = it.get("heights_m") or []
        vs = []
        for p, h in zip(it["points"], hs):
            if h is None:
                continue
            x, z = (int(math.floor(c)) for c in self.w(p))
            base = self.done.get((x, z))
            if base is None:
                g, _, _ = self.ground_fn(x, z, 1, 1)
                base = int(g[0, 0])
            hgt = int(round(h * self.k))
            v = Volume((x - 1, base, z - 1), (3, hgt + 2, 3))
            v.box(0, 0, 0, 2, 0, 2, FLOOR)
            v.box(1, 1, 1, 1, hgt - 1, 1, "minecraft:iron_bars")
            v.set(1, hgt, 1, "minecraft:sea_lantern")
            vs.append(v)
        return vs or None

    def b_round_pad(self, it):
        rad = it["diameter_m"] * self.k / 2
        vs = []
        for p in it["points"]:
            c = np.array(self.w(p))
            poly = np.array([c + rad * np.array([math.cos(t), math.sin(t)]) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
            r = self.level_area(poly, "minecraft:white_concrete")
            if r is None:
                continue
            v, level, m, X, Z = r
            dark = m & (np.hypot(X - c[0], Z - c[1]) < rad / 2)      # frame 01: white ring, dark centre
            for i, k in zip(*np.nonzero(dark)):
                v.set(i, level - v.origin[1], k, "minecraft:gray_concrete")
            vs.append(v)
        return vs

    def b_band(self, it):
        a, b = (np.array(self.w(p)) for p in it["line"])
        can = next(i for i in self.src["items"] if i["id"] == "gate_canopy")
        c0, c1 = (np.array(self.w(p)) for p in can["line"])
        gap = np.linalg.norm(c1 - c0) / 2 + 2
        mid = (c0 + c1) / 2
        pts = densify([tuple(a), tuple(b)], 0.5)
        x0, z0 = np.floor(pts.min(0)).astype(int)
        x1, z1 = np.ceil(pts.max(0)).astype(int)
        G, _, _ = self.ground_fn(int(x0), int(z0), int(x1 - x0 + 1), int(z1 - z0 + 1))
        vs = []
        for x, z in pts:
            if math.hypot(x - mid[0], z - mid[1]) < gap:
                continue                   # the canopy stands in the band's middle
            xi, zi = int(math.floor(x)), int(math.floor(z))
            base = self.done.get((xi, zi), int(G[xi - x0, zi - z0]))
            if base <= MISSING:
                continue
            if vs and vs[-1][:2] == (xi, zi):
                continue
            vs.append((xi, zi, base))
        if not vs:
            return None
        xs = [p[0] for p in vs]; zs = [p[1] for p in vs]; ys = [p[2] for p in vs]
        v = Volume((min(xs), min(ys) + 1, min(zs)), (max(xs) - min(xs) + 1, max(ys) - min(ys) + BAND_H + 1, max(zs) - min(zs) + 1))
        for x, z, base in vs:
            v.box(x - v.origin[0], base + 1 - v.origin[1], z - v.origin[2], x - v.origin[0], base + BAND_H - v.origin[1], z - v.origin[2], "minecraft:polished_andesite")
        return [v]

    def b_canopy(self, it):
        """White tensile canopy: `peaks` square modules in a row along its line (module depth = module width: frame 02
        shows each as a four-sided tent; its depth is not measurable), each rising from CANOPY_EDGE at its rim to the
        measured height at its peak, on posts at the module corners."""
        if "height_m" not in it:
            return None
        a, b = (np.array(self.w(p)) for p in it["line"])
        n = it.get("peaks", 5)
        L = float(np.linalg.norm(b - a))
        ax = (b - a) / L
        nrm = np.array([-ax[1], ax[0]])
        mw = L / n
        poly = np.array([a - nrm * mw / 2, b - nrm * mw / 2, b + nrm * mw / 2, a + nrm * mw / 2])
        hgt = int(round(it["height_m"] * self.k))
        r = self.level_area(poly, "minecraft:light_gray_concrete", extra_h=hgt)
        if r is None:
            return None
        v, level, m, X, Z = r
        along = (X - a[0]) * ax[0] + (Z - a[1]) * ax[1]
        across = (X - a[0]) * nrm[0] + (Z - a[1]) * nrm[1]
        j = np.clip(np.floor(along / mw), 0, n - 1)
        cu = along - (j + 0.5) * mw
        q = np.maximum(np.abs(cu), np.abs(across)) / (mw / 2)        # 0 at a peak, 1 at the module's rim
        top = level + CANOPY_EDGE + np.round((hgt - CANOPY_EDGE) * (1 - np.clip(q, 0, 1)) ** 1.6).astype(int)
        post = (np.abs(np.abs(cu) - mw / 2) < 0.8) & (np.abs(np.abs(across) - mw / 2) < 0.8)
        y0 = v.origin[1]
        for i, k in zip(*np.nonzero(m)):
            nb = [top[i + di, k + dk] for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= i + di < m.shape[0] and 0 <= k + dk < m.shape[1] and m[i + di, k + dk]]
            low = min([int(top[i, k])] + [int(x) for x in nb])
            for y in range(level + 1, int(top[i, k]) + 1):
                if y >= low:
                    v.set(i, y - y0, k, "minecraft:white_wool")
                elif post[i, k]:
                    v.set(i, y - y0, k, WALL)
        return [v]

    def avenue(self) -> list[Volume]:
        """The axis road from layout's gate on to the canopy (paths.py lays it from Silo 1 to layout's gate; the
        frame has the canopy farther north, see canon/surroundings.json gate_note)."""
        can = next((i for i in self.src["items"] if i["id"] == "gate_canopy"), None)
        if can is None:
            return []
        c = np.mean([self.w(p) for p in can["line"]], axis=0)
        g = np.array(self.layout["gate"], float)
        if np.linalg.norm(c - g) < 2:
            return []
        vs = []
        for X, Z, gg, wtr, top, keep, dist, hl, (a0, b0) in self.line_cells(np.array([g, c]), AVENUE_W / 2, 1):
            on = (dist <= AVENUE_W / 2) & (gg > MISSING) & ~keep
            if not on.any():
                continue
            lo = int(min(hl[on].min(), gg[on].min())) - 2
            hi = int(max(hl[on].max(), top[on].max())) + 2
            v = Volume((int(a0), lo, int(b0)), (X.shape[0], hi - lo + 1, X.shape[1]))
            for i, k in zip(*np.nonzero(on)):
                key = (int(a0 + i), int(b0 + k))
                if key in self.done:
                    continue                    # forecourt or band already there
                self.column(v, i, k, int(gg[i, k]), int(hl[i, k]), int(max(top[i, k], wtr[i, k])), "minecraft:smooth_sandstone")
            vs.append(v)
        return vs


# offline check -------------------------------------------------------------------------------------------------------

def flat_ground(level=70):
    def fn(x0, z0, nx, nz):
        X, Z = np.meshgrid(np.arange(x0, x0 + nx), np.arange(z0, z0 + nz), indexing="ij")
        g = (level + 3 * np.sin(X / 40.0) + 2 * np.cos(Z / 55.0)).round().astype(np.int32)
        return g, np.full(g.shape, MISSING, np.int32), g + 12          # a 12-block forest over it
    return fn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--world", help="world dir for heights.read_area; without it a rolling test ground")
    ap.add_argument("--png", help="top-down map of what was generated")
    a = ap.parse_args()
    layout = json.load(open(a.layout))
    if a.world:
        from heights import read_area
        fn = lambda x0, z0, nx, nz: read_area(a.world, x0, z0, nx, nz, min_y=-896, height=1216)
    else:
        fn = flat_ground()
    s = Surroundings(layout, fn)
    vols = s.volumes()
    blocks = sum(int((v.ids != 0).sum()) for v in vols)
    states = sorted({st for v in vols for st in v.used_states()})
    print(f"{len(vols)} volumes, {blocks} blocks set; not built: {', '.join(s.skipped)}")
    print("states:", ", ".join(states))
    if a.png:
        import cv2
        xs = [v.origin[0] for v in vols] + [v.origin[0] + v.size[0] for v in vols]
        zs = [v.origin[2] for v in vols] + [v.origin[2] + v.size[2] for v in vols]
        X0, Z0 = min(xs + [int(r[0]) - 150 for r in s.rings]), min(zs + [int(r[1]) - 150 for r in s.rings])
        X1, Z1 = max(xs + [int(r[0]) + 150 for r in s.rings]), max(zs + [int(r[1]) + 150 for r in s.rings])
        sc = 2
        img = np.full(((Z1 - Z0) // sc + 1, (X1 - X0) // sc + 1, 3), (60, 110, 60), np.uint8)
        col = {"gravel": (150, 150, 150), "gray_concrete": (70, 70, 70), "white_concrete": (250, 250, 250),
               "white_wool": (255, 255, 255), "light_gray_concrete": (190, 190, 190), "coarse_dirt": (90, 120, 150),
               "rail": (20, 40, 110), "smooth_sandstone": (170, 210, 220), "yellow_concrete": (0, 220, 240),
               "polished_andesite": (140, 140, 140), "iron_bars": (0, 0, 255), "sea_lantern": (0, 0, 255)}
        for v in vols:
            pal = [None] + [next((c for k, c in col.items() if p.split("[")[0].endswith(k)), None) for p in v.palette[1:]]
            ids = v.ids
            for i in range(0, v.size[0], sc):
                for k in range(0, v.size[2], sc):
                    nz = np.nonzero(ids[i, :, k])[0]
                    for y in nz[::-1]:
                        c = pal[ids[i, y, k]]
                        if c is not None:
                            img[(v.origin[2] + k - Z0) // sc, (v.origin[0] + i - X0) // sc] = c
                            break
        for rx, rz in s.rings:
            cv2.circle(img, (int((rx - X0) / sc), int((rz - Z0) / sc)), int(110 / sc), (200, 230, 200), 1)
        g = layout["gate"]
        cv2.circle(img, (int((g[0] - X0) / sc), int((g[1] - Z0) / sc)), 6, (255, 0, 255), 2)
        cv2.imwrite(a.png, img)
        print(a.png, img.shape)


if __name__ == "__main__":
    main()
