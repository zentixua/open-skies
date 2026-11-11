"""The ground above one silo: bowl, berm, the open-cut exit ramp to the airlock door, the sensor mast, and the blend
into the surrounding terrain.

Built after the silo volume. The silo leaves its top dirt at grade - 1; here the bowl floor (top block) is grade - 1
too, a berm rings it (Daniel climbs one to see the horizon in S3E9), and the ground eases back to the natural
terrain by the blend radius, so the site reads as land shaped long ago, not a stamp. Trees inside the clear radius
are removed; water outside the berm stays as it was. The ramp runs straight out along the airlock angle from the
door in the shell, flat for an apron and then rising at 1 in 4 until it meets the ground, between concrete
retaining walls.
"""
from __future__ import annotations

import math

import numpy as np

from heights import MISSING
from silo import AIRLOCK_ANGLE, Silo
from volume import Volume

GRASS = "minecraft:grass_block"
DIRT = "minecraft:dirt"
COARSE = "minecraft:coarse_dirt"
GRAVEL = "minecraft:gravel"
CONCRETE = "minecraft:light_gray_concrete"
CONCRETE_B = "minecraft:polished_andesite"
CONCRETE_C = "minecraft:andesite"
FRAME = "minecraft:polished_deepslate"
RAMP = "minecraft:smooth_stone"
RAMP_SLAB = "minecraft:smooth_stone_slab[type=bottom]"
AIR = "minecraft:air"
WATER = "minecraft:water"


def smooth(e0: float, e1: float, x):
    t = np.clip((np.asarray(x, float) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hash01(x, z, salt=0):
    h = (np.asarray(x, np.int64) * 73856093) ^ (np.asarray(z, np.int64) * 19349663) ^ (salt * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


class Site:
    radius = 112          # volume half-size
    clear = 96            # trees removed inside this radius
    bowl = 34             # flat floor
    berm_in, berm_crest, berm_out = 46, 54, 70
    berm_height = 7
    blend_in, blend_out = 70, 108
    ramp_half = 3.5
    apron = 52            # the ramp is flat from the door out to this distance
    slope = 4.0           # blocks along per block up

    def __init__(self, silo: Silo, ground: np.ndarray, water: np.ndarray, top: np.ndarray):
        """ground/water/top: heights.read_area arrays over [cx - radius, cx + radius] in x and z."""
        self.silo = silo
        R = self.radius
        self.cx = silo.origin[0] + silo.R
        self.cz = silo.origin[2] + silo.R
        self.grade = silo.surface_y
        self.walk = silo.origin[1] + silo.level_y(1)          # world y of the level-1 walking surface
        n = 2 * R + 1
        ax = np.arange(n) - R
        self.X, self.Z = np.meshgrid(ax, ax, indexing="ij")
        self.r = np.hypot(self.X, self.Z)
        self.theta = np.arctan2(self.Z, self.X)
        a = AIRLOCK_ANGLE
        self.along = self.X * math.cos(a) + self.Z * math.sin(a)
        self.lat = -self.X * math.sin(a) + self.Z * math.cos(a)
        g = ground.astype(float)
        self.known = ground > MISSING
        self.nat = np.where(self.known, g, self.grade - 1)
        self.water = water
        self.top = np.where(top > MISSING, top, self.nat)

    # height field ----------------------------------------------------------------------------------------------
    def target(self) -> np.ndarray:
        r, th = self.r, self.theta
        seed = self.silo.s.number
        crest = self.berm_height + 1.2 * np.sin(3 * th + seed) + 0.7 * np.sin(7 * th + 2.1 * seed)
        berm = crest * smooth(self.bowl, self.berm_in, r) * (1 - smooth(self.berm_crest, self.berm_out, r))
        w = smooth(self.blend_in, self.blend_out, r)
        t = (1 - w) * (self.grade - 1 + berm) + w * self.nat
        return np.round(t).astype(int)

    def ramp_floor(self) -> np.ndarray:
        """Top block of the ramp floor (float, for slabs) along the airlock axis."""
        return (self.walk - 1) + np.maximum(0, self.along - self.apron) / self.slope

    # volume ----------------------------------------------------------------------------------------------------
    def build(self) -> Volume:
        R = self.radius
        T = self.target()
        f = self.ramp_floor()
        fi = np.floor(f).astype(int)
        # the ramp runs while it is below the shaped ground on its axis
        axis = (np.abs(self.lat) < 0.5) & (self.along > self.apron)
        s_end = float(self.along[axis & (fi >= T)].min()) if np.any(axis & (fi >= T)) else float(R)
        ramp_zone = (self.along >= 45) & (self.along <= s_end + 1)
        ramp = ramp_zone & (np.abs(self.lat) <= self.ramp_half)
        wall = ramp_zone & (np.abs(self.lat) > self.ramp_half) & (np.abs(self.lat) <= self.ramp_half + 1)
        y_lo = self.walk - 4
        y_hi = int(max(self.top[self.r <= self.clear].max(), T.max(), self.grade + 12)) + 2
        v = Volume((self.cx - R, y_lo, self.cz - R), (2 * R + 1, y_hi - y_lo + 1, 2 * R + 1))
        ids = v.ids
        oy = y_lo
        grass, dirt, coarse, gravel, air, water = (v.id(s) for s in (GRASS, DIRT, COARSE, GRAVEL, AIR, WATER))
        conc = [v.id(CONCRETE), v.id(CONCRETE_B), v.id(CONCRETE_C)]
        noise = hash01(self.X + self.cx, self.Z + self.cz, self.silo.s.number)
        H = ids.shape[1]
        for i in range(ids.shape[0]):
            for k in range(ids.shape[2]):
                r = self.r[i, k]
                if r > R:
                    continue
                t, n = int(T[i, k]), int(round(self.nat[i, k]))
                ws = int(self.water[i, k])
                inside = r <= self.clear
                if not inside and t == n:
                    continue
                col = ids[i, :, k]
                lo = max(0, min(t, n) - 3 - oy)
                # ground: dirt below the surface, a surface block on top
                col[lo:max(0, t - oy)] = dirt
                if 0 <= t - oy < H:
                    if r <= self.bowl and noise[i, k] < 0.35:
                        col[t - oy] = coarse
                    elif r <= self.bowl and noise[i, k] > 0.93:
                        col[t - oy] = gravel
                    else:
                        col[t - oy] = grass
                # above: air (trees and cut ground) or the old water body where it stays above the new ground
                above_top = max(int(self.top[i, k]), n) if inside else n
                a0 = max(0, t + 1 - oy)
                a1 = min(H, above_top + 1 - oy)
                if a1 > a0:
                    col[a0:a1] = air
                if ws > t and not inside:
                    col[a0:min(H, ws + 1 - oy)] = water
        # ramp: floor, half steps, open cut above, retaining walls with a curb
        for i, k in zip(*np.nonzero(ramp | wall)):
            col = ids[i, :, k]
            fl = int(fi[i, k])
            surface = int(max(T[i, k], self.nat[i, k]))
            if ramp[i, k]:
                col[max(0, fl - 1 - oy):fl - oy] = conc[0]
                col[fl - oy] = v.id(RAMP)
                col[fl + 1 - oy:min(H, surface + 3 - oy)] = air
                if f[i, k] - fl >= 0.5:
                    col[fl + 1 - oy] = v.id(RAMP_SLAB)
            else:
                top_wall = min(H - 1, max(surface, fl + 2) + 1 - oy)
                for y in range(max(0, fl - 1 - oy), top_wall + 1):
                    col[y] = conc[0] if hash01(i, y, k) < 0.75 else conc[1 + int(hash01(k, y, i) > 0.6)]
        self.portal(v)
        self.mast(v, int(T[R, R]))
        return v

    def portal(self, v: Volume) -> None:
        """Concrete headwall over the shell at the end of the cut, a steel frame around the airlock door."""
        R = self.radius
        oy = v.origin[1]
        face = (self.along >= 45) & (self.along < 47) & (np.abs(self.lat) <= self.ramp_half + 1)
        door = np.abs(self.lat) < 2.6
        frame = (np.abs(self.lat) >= 2.6) & (np.abs(self.lat) < 3.6)
        for i, k in zip(*np.nonzero(face)):
            col = v.ids[:, :, :][i, :, k]
            for y in range(self.walk - 1, self.grade + 2):
                if door[i, k] and self.walk <= y <= self.walk + 3:
                    continue                                   # the silo's own outer door (iron) stays
                if (frame[i, k] and self.walk <= y <= self.walk + 4) or (door[i, k] and y == self.walk + 4):
                    col[y - oy] = v.id(FRAME)
                else:
                    col[y - oy] = v.id(CONCRETE)
        # two work lamps flush in the headwall beside the frame
        for side in (-4.2, 4.2):
            for i, k in zip(*np.nonzero(face & (np.abs(self.lat - side) < 0.5))):
                v.ids[i, self.walk + 3 - oy, k] = v.id("minecraft:pearlescent_froglight")
                break

    def mast(self, v: Volume, t: int) -> None:
        """The sensor mast over the silo axis: the cafeteria wallscreen's camera."""
        R = self.radius
        oy = v.origin[1]
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in (t + 1, t + 2):
                    v.ids[R + dx, y - oy, R + dz] = v.id(CONCRETE)
        for y in range(t + 3, t + 9):
            v.ids[R, y - oy, R] = v.id("minecraft:polished_deepslate_wall")
        v.ids[R, t + 9 - oy, R] = v.id("minecraft:observer[facing=down]")
        v.ids[R, t + 10 - oy, R] = v.id("minecraft:lightning_rod")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v.ids[R + dx, t + 9 - oy, R + dz] = v.id("minecraft:tinted_glass")
