"""The ground above one silo and the way in, to the explorethesilo.com 3D model (silo3d.js, "THE WAY IN" and
"THE GROUND OUTSIDE"; numbers there in metres, here blocks).

Along the tunnel axis, s blocks out from the shell (the model's s from the shaft wall):
  s 0-10   the Sheriff's Station (desk, holding cell)
  s 10     inner thick door; s 10-20 the airlock chamber; s 20 outer thick door (both rectangular)
  s 20-76  the ramp, 7 wide, climbing to the crater floor (model: 60 m for 15 m; here 56 for 6..26, the floor's
           height over the outer door)
  s 63-76  the stair head, open to the sky between curbs (S3E09 06, 07, 09; the model's flush leaves seal it later)
  s 53-60  the sensor block 3 behind the portal: walls leaning in, a thick cap slab overhanging all round, an alcove
           facing the portal with a pale stone cone on three round steps and the camera on top
Each silo's entrance sits in its own crater: a flat floor to 30 from the portal, a berm 2 over the plain at 42, back
to the plain by 64 (model: SITE_FLOOR 30, SITE_RIM 42, SITE_OUT 64, berm 1.6, floor 2.2 under the plain).

Deviation: the model's tunnel bends 8 degrees and leaves at 210 degrees; here it runs straight out due west, so the
tunnel, portal and block are block-aligned rectangles rather than staircased diagonals.
"""
from __future__ import annotations

import math

import numpy as np

from heights import MISSING
from silo import Silo
from volume import Volume

GRASS = "minecraft:grass_block"
DIRT = "minecraft:dirt"
COARSE = "minecraft:coarse_dirt"
AIR = "minecraft:air"
WATER = "minecraft:water"
CONCRETE = "minecraft:light_gray_concrete"
CONCRETE_B = "minecraft:polished_andesite"
CONCRETE_C = "minecraft:andesite"
PLATE = "minecraft:gray_concrete"
SEAM = "minecraft:polished_deepslate"
RIM = "minecraft:smooth_stone"
DOOR = "minecraft:iron_block"
FLOOR = "minecraft:smooth_stone"
STEP = "minecraft:smooth_stone_slab[type=bottom]"
DARK = "minecraft:polished_blackstone"
PALE = "minecraft:calcite"
LAMP = "minecraft:pearlescent_froglight"


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
    radius = 190                 # volume half-size around the shaft axis
    shaft_zone = 120             # the plain skipped 100 around each shaft (and Silo 1 had an older open cut to ~115)
    # the way in (s from the shell's outer face)
    station, inner_door, outer_door = 10, 10, 20
    slope_run, rise = 56, 14
    half = 3                     # tunnel interior: |l| <= 3 (7 wide)
    room = 5                     # tunnel clear height
    portal_l = 13                # leaves along the ramp, ending at its head
    portal_half = 4              # leaves across: |l| <= 4 (laps onto the walls)
    # the sensor block (s measured back from the portal)
    # the camera block at the frames' size (S3E09 07: >= 3.4 m wide, roof top 2.4-3 m against a 1.65 m guide;
    # 05: ~3 m wide, ~2 m tall from behind), not the explorethesilo model's 12.8 m
    block_gap, block_depth, alcove_depth = 3, 4, 2
    block_half, alcove_half = 2, 1
    # the crater, about the portal centre
    floor_r, rim_r, out_r = 30, 42, 64
    floor_drop, berm = 2, 2

    def __init__(self, silo: Silo, ground: np.ndarray, water: np.ndarray, top: np.ndarray, bed: np.ndarray | None = None,
                 weight: np.ndarray | None = None, old_cut_deg: float | None = None, neighbours=()):
        """neighbours: (shaft x, z[, quarter turns]) of the other silos, in this site's own frame (tunnel due west);
        a neighbour turned k quarters clockwise runs its tunnel W, N, E or S for k = 0..3 (build_live turns the
        inputs and the result for a silo that is not due west). The ground each site lays is its own cell (columns
        nearer its shaft-to-portal line than any other silo's), and their craters are kept."""
        """ground/water/top/bed over [axis - radius, axis + radius] in x and z, as field.Field.slice gives them:
        ground is the plain, bed the original ground under it."""
        self.silo = silo
        R = self.radius
        self.cx = silo.origin[0] + silo.R
        self.cz = silo.origin[2] + silo.R
        self.grade = silo.surface_y
        self.walk = silo.origin[1] + silo.level_y(1)         # stand y of level 1
        self.s_shell = int(math.ceil(silo.s.r_outer))          # s = 0 at the shell's outer face, due west
        self.ramp_end = self.outer_door + self.slope_run       # the head of the ramp
        self.portal_s = self.ramp_end - self.portal_l / 2      # portal centre
        n = 2 * R + 1
        ax = np.arange(n) - R
        self.X, self.Z = np.meshgrid(ax, ax, indexing="ij")
        self.s = -self.X - self.s_shell                         # along the tunnel, out from the shell
        self.l = self.Z                                         # across it
        self.d_axis = np.hypot(self.X, self.Z)
        px = -(self.s_shell + self.portal_s)
        self.d_portal = np.hypot(self.X - px, self.Z)
        known = ground > MISSING
        self.plain = np.where(known, ground, self.grade - 1).astype(float)
        self.water = water
        self.top = np.where(top > MISSING, top, self.plain)
        self.bed = np.where(bed > MISSING, bed, self.plain) if bed is not None else self.plain
        self.p_portal = float(self.plain[R + int(px), R])
        # the ramp climbs from the outer door to the crater floor (the model: "climbing to the crater floor"), so
        # its rise is the floor's height over the door, not a fixed 14: the shaft's grade (its own 34 m round) and
        # the portal's plain 115 m out differ by up to ~10, and a fixed rise left the head above or below the floor
        # (Silo 18 on 25567: head 4 over the bowl, under the camera block). Kept within 6..26 (slabs climb 0.5 a
        # block at most); outside that the crater floor follows the ramp instead.
        base = self.walk - 1
        floor = int(round(self.p_portal - self.floor_drop))
        self.rise = min(26, max(6, floor - base))
        self.p_portal = float(base + self.rise + self.floor_drop)
        # the stair is open to the sky until the floor is 3.5 under the lawn (2.5 clear over a half step under the
        # ground's own slab): 13 at Silo 1's rise of 15, longer on a gentler ramp (Silo 18, rise 10: 20)
        self.open_l = max(self.portal_l, math.ceil(3.5 * self.slope_run / self.rise))
        self.old_cut_deg = old_cut_deg      # an earlier draft's open cut along this bearing, to be filled
        self.keep = (weight <= 0.05) if weight is not None else np.zeros(ground.shape, bool)   # towns: never touched
        reach = self.s_shell + self.portal_s
        bearing = ((-1, 0), (0, -1), (1, 0), (0, 1))      # W N E S: tunnel direction after 0..3 quarter turns
        def seg_dist(ax, az, k=0):          # distance to a silo's shaft-to-portal line (relative shaft position)
            dx, dz = bearing[k % 4]
            t = np.clip(((self.X - ax) * dx + (self.Z - az) * dz) / reach, 0, 1)
            return np.hypot(self.X - (ax + t * reach * dx), self.Z - (az + t * reach * dz))
        own = seg_dist(0, 0)
        self.own_line = own
        self.cell = np.ones_like(own, bool)
        self.neighbour_portals = []
        for nb in neighbours:
            nx_, nz_ = nb[0], nb[1]
            k = nb[2] if len(nb) > 2 else 0
            ax, az = nx_ - self.cx, nz_ - self.cz
            if (ax, az) == (0, 0) or math.hypot(ax, az) > 2 * R + 2 * self.out_r:
                continue
            self.cell &= own <= seg_dist(ax, az, k)
            dx, dz = bearing[k % 4]
            qx, qz = ax + reach * dx, az + reach * dz           # its portal
            pi, pk = R + int(round(qx)), R + int(round(qz))
            if 0 <= pi < n and 0 <= pk < n:
                self.neighbour_portals.append((np.hypot(self.X - qx, self.Z - qz), float(self.plain[pi, pk])))

    # heights ---------------------------------------------------------------------------------------------------
    def crater(self, d: np.ndarray, p_floor: float, ground: np.ndarray) -> np.ndarray:
        """Ground with one crater about a portal at distance d: level floor, berm ring, back to the plain."""
        prof = np.where(d <= self.floor_r, -self.floor_drop,
                        np.where(d <= self.rim_r,
                                 -self.floor_drop + (self.floor_drop + self.berm) * smooth(self.floor_r, self.rim_r, d),
                                 self.berm * (1 - smooth(self.rim_r, self.out_r, d))))
        w = smooth(self.floor_r, self.out_r, d)               # the floor is level, the rim follows the plain
        return (1 - w) * p_floor + w * ground + prof - ground   # the change it makes

    def target(self) -> np.ndarray:
        """Top block of the finished ground: the plain, with every crater nearby (this silo's and its neighbours',
        so a site never flattens the next one's)."""
        t = self.plain + self.crater(self.d_portal, self.p_portal, self.plain)
        for d, p in self.neighbour_portals:
            t = t + self.crater(d, p, self.plain)
        return np.round(t).astype(int)

    def floor_top(self, s: np.ndarray) -> np.ndarray:
        """Top block of the tunnel floor (float: half steps become slabs)."""
        return (self.walk - 1) + np.clip(s - self.outer_door, 0, self.slope_run) * self.rise / self.slope_run

    # volume ----------------------------------------------------------------------------------------------------
    def build(self) -> Volume:
        R = self.radius
        T = self.target()
        f = self.floor_top(self.s)
        fi = np.floor(f).astype(int)
        # every column within 100 of any shaft is some site's (the plain skipped those): a cell's reach of 150 from
        # its own shaft-to-portal line covers it, and the whole crater
        zone = ((self.own_line <= 150) | (self.d_axis <= self.shaft_zone)) & self.cell & ~self.keep
        tunnel = (self.s >= -3) & (self.s <= self.ramp_end) & (np.abs(self.l) <= self.half + 1)
        y_lo = min(self.walk - 3, int(self.bed[zone].min()) - 4)
        y_hi = int(max(self.top[zone].max(), T[zone].max(), self.grade + 12)) + 2
        v = Volume((self.cx - R, y_lo, self.cz - R), (2 * R + 1, y_hi - y_lo + 1, 2 * R + 1))
        ids, oy, H = v.ids, y_lo, v.size[1]
        grass, dirt, coarse, air, water = (v.id(s) for s in (GRASS, DIRT, COARSE, AIR, WATER))
        noise = hash01(self.X + self.cx, self.Z + self.cz, self.silo.s.number)
        floor_zone = self.d_portal <= self.floor_r + 4
        clear_top = self.grade + 12          # also takes away anything an earlier pass raised here
        for i, k in zip(*np.nonzero(zone)):
            t = int(T[i, k])
            n = int(round(self.plain[i, k]))
            col = ids[i, :, k]
            lo = max(0, min(t, n, int(self.bed[i, k])) - 3 - oy)
            col[lo:max(0, t - oy)] = dirt
            # 2052 (the opening day, S3E09): the aerial frame shows every floor grassed like the plain; the model's
            # bleached floor is the later wasteland
            col[t - oy] = grass
            a0, a1 = t + 1 - oy, min(H, max(int(self.top[i, k]), n, clear_top) + 1 - oy)
            if a1 > a0:
                col[a0:a1] = air
            ws = int(self.water[i, k])
            if ws > t:
                col[a0:min(H, ws + 1 - oy)] = water
        if self.old_cut_deg is not None:
            a = math.radians(self.old_cut_deg)
            along = self.X * math.cos(a) + self.Z * math.sin(a)
            across = -self.X * math.sin(a) + self.Z * math.cos(a)
            cut = (np.abs(across) <= 6) & (along >= 44) & (along <= self.shaft_zone + 4) & ~tunnel
            stone = v.id("minecraft:stone")
            for i, k in zip(*np.nonzero(cut)):
                t = int(T[i, k])
                ids[i, max(0, self.walk - 3 - oy):max(0, t - 3 - oy), k] = stone
                ids[i, max(0, t - 3 - oy):max(0, t - oy), k] = dirt
        self.tunnel(v, T, f, fi, tunnel)
        self.portal(v, T)
        self.block(v, T)
        return v

    def tunnel(self, v: Volume, T, f, fi, mask) -> None:
        oy = v.origin[1]
        ids = v.ids
        conc = [v.id(CONCRETE), v.id(CONCRETE_B), v.id(CONCRETE_C)]
        air, dirt, floor, step = v.id(AIR), v.id(DIRT), v.id(FLOOR), v.id(STEP)
        door, lamp = v.id(DOOR), v.id(LAMP)
        for i, k in zip(*np.nonzero(mask)):
            s, l = int(self.s[i, k]), int(self.l[i, k])
            col = ids[i, :, k]
            fl, t = int(fi[i, k]), int(T[i, k])
            roof = min(fl + self.room + 1, t)          # under the crater floor the roof is the ground's own slab
            inside = abs(l) <= self.half and s >= -3          # from the shell's own doorway (r 43) outward
            # slip-formed pours: the wall concrete varies in bands of two rows
            for y in range(fl - 1, roof + 1):
                band = conc[0] if hash01(s // 3, y // 2, 11) < 0.7 else conc[1 + int(hash01(s, y, 13) > 0.5)]
                col[y - oy] = band
            if inside:
                col[fl - oy] = floor
                if f[i, k] - fl >= 0.5:
                    col[fl + 1 - oy] = step
                    col[fl + 2 - oy:roof - oy] = air
                else:
                    col[fl + 1 - oy:roof - oy] = air
                if s % 7 == 3 and l == 0 and roof - 1 > fl + 2:
                    col[roof - oy] = lamp
                if s in (self.inner_door, self.outer_door):
                    # the thick door stands open: its leaf drawn back into a steel frame round the opening
                    if abs(l) == self.half:
                        col[fl + 1 - oy:fl + 5 - oy] = door
                    else:
                        col[fl + 5 - oy] = door
            # backfill above the roof up to the ground (an earlier open cut here is closed again)
            if roof < t:
                col[roof + 1 - oy:t - oy] = dirt
            # and below the floor: an earlier ramp at a lower rise left its air there
            if s >= 0 and fl - 1 > self.walk - 2:
                col[self.walk - 2 - oy:fl - 1 - oy] = dirt
        self.station_room(v, fi)

    def station_room(self, v: Volume, fi) -> None:
        """Sheriff's Station in the first ten blocks: a desk, a holding cell on the south side."""
        oy, R = v.origin[1], self.radius
        def at(s, l, dy, state):
            i = R - (self.s_shell + s)
            v.set(i, int(fi[i, R + l]) + 1 + dy - oy, R + l, state)
        for s in (3, 4):
            at(s, -2, 0, "minecraft:dark_oak_planks")
        at(3, -2, 1, "minecraft:lantern")
        at(5, -3, 0, "minecraft:dark_oak_stairs[facing=south]")
        for s in range(5, 10):
            at(s, 1, 0, "minecraft:iron_bars"); at(s, 1, 1, "minecraft:iron_bars"); at(s, 1, 2, "minecraft:iron_bars")
        at(8, 3, 0, "minecraft:gray_bed[facing=west,part=head]")
        at(9, 3, 0, "minecraft:gray_bed[facing=west,part=foot]")

    def portal(self, v: Volume, T) -> None:
        """The open stair head over the last open_l blocks of the ramp, a pale concrete curb round it."""
        oy, R = v.origin[1], self.radius
        s0 = self.ramp_end - self.open_l
        for s in range(s0 - 1, self.ramp_end + 2):
            for l in range(-self.portal_half - 1, self.portal_half + 2):
                i, k = R - (self.s_shell + s), R + l
                t = int(T[i, k])
                rim = s in (s0 - 1, self.ramp_end + 1) or abs(l) == self.portal_half + 1
                if rim:
                    v.set(i, t - oy, k, RIM)
                    continue
                # opening day (S3E09 06, 07, 09): the stair head is an open trench between concrete curbs flush
                # with the lawn, roofed further down; the model's flush leaves are the sealed silo of later years
                if abs(l) > self.half:
                    v.set(i, t - oy, k, RIM)
                    continue
                fl = int(math.floor(self.floor_top(np.array(float(s)))))
                for y in range(fl + 1 + (1 if self.floor_top(np.array(float(s))) - fl >= 0.5 else 0), t + 1):
                    v.set(i, y - oy, k, AIR)

    def block(self, v: Volume, T) -> None:
        """The camera block (S3E09 07, 08): two thick light concrete piers with sloped outer faces, a dark recessed
        back wall, a thin flat roof slab cantilevered over them; in front, on a stepped plinth, a truncated concrete
        cone carrying the sensor, looking out over the stair."""
        oy, R = v.origin[1], self.radius
        face = self.ramp_end - self.open_l - self.block_gap          # s of the open face
        back = face - self.block_depth + 1
        i_of = lambda s: R - (self.s_shell + s)
        t = int(T[i_of(face), R])
        put = lambda s, l, y, st: v.set(i_of(s), y - oy, R + l, st)
        for s in range(back, face + 1):
            for l in range(-self.block_half, self.block_half + 1):
                for dy in (1, 2):
                    recess = abs(l) <= self.alcove_half and s > face - self.alcove_depth
                    if recess:
                        put(s, l, t + dy, AIR)
                    elif abs(l) <= self.alcove_half:
                        put(s, l, t + dy, DARK)                      # the recessed back wall, dark grey
                    else:
                        put(s, l, t + dy, CONCRETE)
                # the piers' sloped outer faces
                for sd in (-1, 1):
                    put(s, sd * (self.block_half + 1), t + 1,
                        f"minecraft:andesite_stairs[facing={'south' if sd < 0 else 'north'},half=bottom]")
        # the roof: one thin slab, overhanging the front and the sides
        for s in range(back, face + 2):
            for l in range(-self.block_half - 1, self.block_half + 2):
                put(s, l, t + 3, STEP)
        # the plinth (stepped), the cone, the sensor, in front of the recess under the roof's lip
        mz = face
        for l in range(-1, 2):
            for s in range(mz - 1, mz + 2):
                if (s, l) != (mz, 0):
                    put(s, l, t + 1, STEP)
        put(mz, 0, t + 1, "minecraft:andesite_wall")                 # the truncated cone
        put(mz, 0, t + 2, "minecraft:observer[facing=west]")         # the sensor, looking out over the stair
