"""The ground over one silo at 1:1 (SPEC-1to1.md section 1): the bowl, its berm, the ring path, the slot and camera.

About the shaft axis, which is the ring's centre (construction S3E07 #2, S3E08 #8: the bore in the middle of a round pit):
  r 0-55     the bowl floor, level, 2 under the plain (Ø110: S3E09 frame 05, people on the far berm 27 px)
  r 55-77    the inner bank up to the crest, 4 over the floor (frame 10); crest Ø≈155 (floor/crest 0.71)
  r 77-100   the outer bank back down to the plain
  r 110      the ring path, 3 wide, on the plain (Ø≈220: crest/path 0.70, aerials 01, 03; frame 05: two side by side)
On some rings the berm is cut where the path comes in (aerials ×4): a gap along the ring's own bearing.

The way out (silo.way_out) ends in a slot with steps on the bowl floor at about half its radius (SPEC 1, frames
05-07); here: a pale curb flush with the lawn round the slot, and beside it the camera block (≈4.4 x 2.4 m, S3E09 07:
two piers, a dark recess, a thin roof slab; the sensor on a cone looking over the steps).

The banks are mown lawn (S3E09 05, 10, 23). Each contour waves a little (an earth bank, not an amphitheatre; shader
frames 03, 07c, 11 of 1112d): the inner bank and crest take the ground found up to WOBBLE blocks in or out along their
radius, two slow waves round the ring, different for each silo; lone one-column pillars and pits left by a diagonal
contour go to their neighbours' level. Risers stay grass (the Fast Better Grass pack draws grass on every side); where
a riser is 2-3 deep the block under the top one is moss, not dirt (banks.py, round 5 on 25567).

The site is laid in the silo's own frame (way in due west, silo.py) and build_offline turns it like the silo.
"""
from __future__ import annotations

import math

import numpy as np

from heights import MISSING
from silo import CAMERA, EXIT_X, PORTAL_X, RAMP_Z, Silo
from volume import Volume

GRASS = "minecraft:grass_block"
DIRT = "minecraft:dirt"
MOSS = "minecraft:moss_block"
AIR = "minecraft:air"
WATER = "minecraft:water"
CONCRETE = "minecraft:light_gray_concrete"
RIM = "minecraft:smooth_stone"
DARK = "minecraft:polished_blackstone"
PATH = "minecraft:smooth_sandstone"       # S3E09 05: pale beige compacted fine gravel, flush with the lawn
PATH_DULL = "minecraft:white_terracotta"  # mixed in (3 of 5 columns): smooth sandstone alone read bright cream from the
                                          # air (13.11 Photon shot); the show's paths are a muted beige-grey


def path_state(x: int, z: int) -> str:
    """The path block for world column x, z: a stable speckle of white terracotta and smooth sandstone."""
    h = ((x * 73856093) ^ (z * 19349663)) & 0xFFFF
    return PATH_DULL if h % 5 < 3 else PATH
STEP = "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]"


def smooth(e0: float, e1: float, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hash01(x, z, salt=0):
    """Stable pseudo-random 0..1 per integer position (wrapping 64-bit arithmetic)."""
    with np.errstate(over="ignore"):
        h = (np.asarray(x, np.int64).astype(np.uint64) * np.uint64(73856093)) ^ \
            (np.asarray(z, np.int64).astype(np.uint64) * np.uint64(19349663)) ^ np.uint64(salt * 83492791)
        h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177)
        return ((h ^ (h >> np.uint64(16))) & np.uint64(0xFFFF)) / 65535.0


class Site:
    radius = 135                 # volume half-size about the shaft axis: half the ring spacing (270)
    floor_r, crest_r, out_r = 55, 77, 100
    path_r, path_half = 110, 1.5
    zone_r = 116                 # columns this site lays; the plain (field.py) lays the rest
    floor_drop, berm = 2, 2      # floor under the plain, crest over it: 4 from floor to crest
    gap_half = 4                 # berm gap: 8 wide at the bowl, easing out over 4 more each side
    wobble = 2

    def __init__(self, silo: Silo, ground: np.ndarray, water: np.ndarray, top: np.ndarray, bed: np.ndarray | None = None,
                 weight: np.ndarray | None = None, neighbours=(), paths: np.ndarray | None = None,
                 road: np.ndarray | None = None, gap_bearing: float | None = None, wobble: bool = True):
        """Grids over [axis - radius, axis + radius] in x and z, in the silo's frame: ground is the plain (field.py),
        bed the original ground under it, weight the plain's weight (0 at Zearth's towns, which no site may touch),
        paths/road the path and road columns. neighbours: (x, z) of the other shafts in this frame; the site lays only
        its own cell (columns nearer its shaft than any other). gap_bearing: the berm gap's bearing (radians, this
        frame), or None for an unbroken berm."""
        self.silo = silo
        R = self.radius
        self.cx = silo.origin[0] + silo.R
        self.cz = silo.origin[2] + silo.R
        self.grade = silo.surface_y                       # top block of the bowl floor
        n = 2 * R + 1
        ax = np.arange(n) - R
        self.X, self.Z = np.meshgrid(ax, ax, indexing="ij")
        self.d = np.hypot(self.X, self.Z)
        self.theta = np.mod(np.arctan2(self.Z, self.X), 2 * math.pi)
        known = ground > MISSING
        self.plain = np.where(known, ground, self.grade + self.floor_drop).astype(float)
        self.water = water
        self.top = np.where(top > MISSING, top, self.plain)
        self.bed = np.where(bed > MISSING, bed, self.plain) if bed is not None else self.plain
        self.keep = (weight <= 0.05) if weight is not None else np.zeros(ground.shape, bool)
        self.paths = paths if paths is not None else np.zeros(ground.shape, bool)
        self.road = road if road is not None else np.zeros(ground.shape, bool)
        self.gap_bearing = gap_bearing
        self.do_wobble = wobble
        self.cell = np.ones(ground.shape, bool)
        for nx_, nz_ in neighbours:
            ax_, az_ = nx_ - self.cx, nz_ - self.cz
            if math.hypot(ax_, az_) > 2 * R + 20:
                continue
            self.cell &= self.d <= np.hypot(self.X - ax_, self.Z - az_)
        self.zone = self.cell & (self.d <= self.zone_r) & ~self.keep
        self.number = silo.s.number

    # heights ---------------------------------------------------------------------------------------------------
    def profile(self, d: np.ndarray) -> np.ndarray:
        """Bowl, inner bank, crest and outer bank: the change from the plain."""
        P = self.plain
        floor = self.grade
        # the crest stays floor_drop + berm over the floor all round: on a rolling plain (field.UNDULATE) a crest
        # at plain + berm sank 2 lower on the plain's low side, and the camera of 17 saw 16 over it (12.11)
        crest = np.maximum(P, floor + self.floor_drop) + self.berm
        inner = floor + (crest - floor) * smooth(self.floor_r, self.crest_r, d)
        outer = P + (crest - P) * (1 - smooth(self.crest_r, self.out_r, d))
        return np.where(d <= self.floor_r, floor, np.where(d <= self.crest_r, inner, outer))

    def target(self) -> np.ndarray:
        """Top block of the finished ground."""
        d = self.d
        if self.do_wobble:
            # two slow waves round the ring, their phase drifting with the radius (banks.py --wobble)
            ph = hash01(self.number, 0, 41) * 2 * math.pi
            w = self.wobble * np.sin(2 * self.theta + ph + d * 0.21) * smooth(self.floor_r - 1, self.floor_r + 3, d) \
                * (1 - smooth(self.crest_r + 2, self.crest_r + 6, d))
            d = d + w
        T = self.profile(d)
        if self.gap_bearing is not None:
            off = np.abs(((self.theta - self.gap_bearing + math.pi) % (2 * math.pi)) - math.pi)
            lat = self.d * np.sin(np.minimum(off, math.pi / 2))
            front = off < math.pi / 2
            ramp = self.grade + (self.plain - self.grade) * smooth(self.floor_r, self.out_r, self.d)
            k = (1 - smooth(self.gap_half, self.gap_half + 4, lat)) * front
            T = np.where(k > 0, T * (1 - k) + np.minimum(T, ramp) * k, T)
        T = np.round(T).astype(int)
        return self.even(T)

    def even(self, T: np.ndarray) -> np.ndarray:
        """Lone one-column pillars and pits on the banks go to their neighbours' level."""
        bank = (self.d >= self.floor_r - 1) & (self.d <= self.out_r + 2)
        for _ in range(3):
            p = np.pad(T, 1, mode="edge")
            nb = np.stack([p[2:, 1:-1], p[:-2, 1:-1], p[1:-1, 2:], p[1:-1, :-2]])
            hi, lo = nb.max(axis=0), nb.min(axis=0)
            med = np.sort(nb, axis=0)[1:3].mean(axis=0).round().astype(int)
            fix = bank & ((T > hi) | (T < lo))
            if not fix.any():
                break
            T = np.where(fix, med, T)
        return T

    # volume ----------------------------------------------------------------------------------------------------
    def slot_cells(self) -> tuple[set, set]:
        """(open trench, curb) columns in this frame: the steps' opening (head at EXIT_X, open toward the berm) and the
        pale curb along both sides and across the closed inner end over the portal (S3E09 07)."""
        z0, z1 = RAMP_Z
        open_ = {(x, z) for x in range(EXIT_X, PORTAL_X + 1) for z in range(z0, z1 + 1)}
        curb = {(x, z) for x in range(EXIT_X, PORTAL_X + 2) for z in (z0 - 1, z1 + 1)}
        curb |= {(PORTAL_X + 1, z) for z in range(z0, z1 + 1)}
        return open_, curb

    def build(self) -> Volume:
        R = self.radius
        T = self.target()
        self.T = T
        zone = self.zone
        y_lo = int(min(self.grade - 4, self.bed[zone].min() - 4))
        y_hi = int(max(self.top[zone].max(), T[zone].max(), self.grade + 14)) + 2
        v = Volume((self.cx - R, y_lo, self.cz - R), (2 * R + 1, y_hi - y_lo + 1, 2 * R + 1))
        ids, oy, H = v.ids, y_lo, v.size[1]
        grass, dirt, moss, air, water = (v.id(s) for s in (GRASS, DIRT, MOSS, AIR, WATER))
        path = v.id(PATH)
        # the lowest neighbour of each column: a riser 2-3 deep shows the block under its top
        p = np.pad(T, 1, mode="edge")
        low = np.min(np.stack([p[2:, 1:-1], p[:-2, 1:-1], p[1:-1, 2:], p[1:-1, :-2]]), axis=0)
        open_, curb = self.slot_cells()
        clear_top = self.grade + 14
        shaft = self.silo.R
        for i, k in zip(*np.nonzero(zone)):
            x, z = i - R, k - R
            if (x, z) in open_:
                # the slot: the silo's volume holds the steps up to the bowl floor; over it, whatever the golden ground
                # had (a hill, the old surface) must go, or the opening stays roofed over (v3, 13.11)
                col = ids[i, :, k]
                a0, a1 = self.grade + 1 - oy, min(H, max(int(self.top[i, k]), int(round(self.plain[i, k])), clear_top) + 1 - oy)
                if a1 > a0:
                    col[a0:a1] = air
                continue
            t = int(T[i, k])
            nat = int(round(self.plain[i, k]))
            col = ids[i, :, k]
            # over the shaft the silo's own volume holds everything below the bowl floor
            lo = self.grade - oy if self.d[i, k] <= shaft else max(0, min(t, nat, int(self.bed[i, k])) - 3 - oy)
            col[lo:max(0, t - oy)] = dirt
            if 2 <= t - low[i, k] <= 3:
                col[max(lo, t - 1 - oy)] = moss
            if (x, z) in curb:
                col[t - oy] = v.id(RIM)
                if t + 1 - oy < H:
                    # the trench's parapet stands ≈0.5 m over the lawn (S3E09 06, 07, 10); the head end stays open
                    col[t + 1 - oy] = v.id(STEP)
            elif self.paths[i, k] or self.road[i, k]:
                col[t - oy] = v.id(path_state(self.cx - R + i, self.cz - R + k))
            else:
                col[t - oy] = grass
            a0, a1 = t + 1 - oy, min(H, max(int(self.top[i, k]), nat, clear_top) + 1 - oy)
            if a1 > a0:
                col[a0:a1] = air
            ws = int(self.water[i, k])
            if ws > t and self.d[i, k] > self.out_r:
                col[a0:min(H, ws + 1 - oy)] = water
        self.camera(v)
        return v

    def camera(self, v: Volume) -> None:
        """The camera shelter (S3E09 07, 08; s3e09-notes.md; review of 43c71ce) between the centre and the trench, its
        open front facing out toward the steps: a dark back wall, light side walls, a thin roof slab overhanging the
        front (top at 2.5 m); before it a plinth of slabs (≈0.5 m) across the whole front and a block forward, the cone
        on it (a polished andesite block) with a brass sensor (waxed copper slab) on top at 1.5 m. 5 wide in all."""
        R, oy = self.radius, v.origin[1]
        x0, x1, z0, z1 = CAMERA                             # x0: the open front (toward the trench, -x); x1: the back
        g = self.grade
        put = lambda x, y, z, st: v.set(R + x, y - oy, R + z, st)
        zc = (z0 + z1) // 2
        for dy in (1, 2):
            for z in range(z0, z1 + 1):
                put(x1, g + dy, z, DARK)                   # back wall
                for x in range(x0, x1):
                    put(x, g + dy, z, CONCRETE if z in (z0, z1) else AIR)   # side walls, open middle
        for x in range(x0 - 1, x1 + 1):                    # roof slab, overhanging the front by one
            for z in range(z0, z1 + 1):
                put(x, g + 3, z, STEP)
        for z in range(z0, z1 + 1):                        # the plinth across the whole front, one block forward
            put(x0 - 1, g + 1, z, STEP)
        for z in range(z0 + 1, z1):
            put(x0, g + 1, z, STEP)
        put(x0, g + 1, zc, "minecraft:polished_andesite")
        put(x0, g + 2, zc, "minecraft:waxed_cut_copper_slab[type=bottom,waterlogged=false]")
