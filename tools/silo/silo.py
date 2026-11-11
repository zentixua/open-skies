"""One silo of the Silo series, generated block by block.

Sources: the show and novels as collected by the fan reference explorethesilo.com (canon level list) and the
dimensions of its three.js model (atrium, stair, bridges rotating by 137.5 degrees per level, 18 bays, cafeteria
screen and airlock angles, ramp, generator, digger void). Minecraft scale: 1 block = 1 m horizontally; a level is 5
blocks (4 clear + 1 slab) instead of the model's cinematic 10 m, so 144 levels fit in about 780 blocks of depth.

Local frame: x, z centred on the silo axis (index R), y index 0 at the bottom of the digger void. World y of an
index is origin_y + index. Level n (1..144) has its walking surface at Y1 - 5 * (n - 1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from volume import Volume

TAU = 2 * math.pi
GOLDEN = math.radians(137.5)          # bridge rotation per level (explorethesilo BRIDGE_STEP)
LEVELS = 144


@dataclass
class Spec:
    number: int = 18
    pitch: int = 5                    # blocks per level
    r_newel: float = 1.5              # solid stair core
    r_stair_in: float = 1.5
    r_stair_out: float = 5.5
    r_landing: float = 7.5            # landing pad outer radius
    r_column_orbit: float = 11.0      # six core columns (explorethesilo CORE_COLUMNS, angles below)
    r_walk_in: float = 14.0           # walkway ring projecting into the atrium
    r_atrium: float = 17.0            # front wall of the rooms
    r_corridor_in: float = 28.0
    r_corridor_out: float = 30.0
    r_inner_wall: float = 43.0        # back wall of the rooms
    r_outer: float = 46.0             # outside of the concrete shell
    bays: int = 18
    cafe_height: int = 10             # level 1 cafeteria clear height
    cap: int = 3                      # concrete cap above level 1
    cover: int = 12                   # earth over the cap up to grade (the bowl floor)
    gen_height: int = 16              # generator hall below level 144
    slab: int = 9                     # "thirty feet" of concrete above the digger void
    void_height: int = 44
    void_radius: float = 44.0
    margin: int = 6


COLUMN_ANGLES = [64, 110, 158, 202, 250, 296]
SCREEN_ANGLE, SCREEN_ARC = math.radians(170), math.radians(54)
AIRLOCK_ANGLE = math.radians(213)

# palette -------------------------------------------------------------------------------------------------------------
CONCRETE = "minecraft:light_gray_concrete"
CONCRETE_DARK = "minecraft:gray_concrete"
SHELL = "minecraft:polished_andesite"
FLOOR = "minecraft:polished_andesite"
FLOOR_DEEP = "minecraft:polished_deepslate"
SLAB_FLOOR = "minecraft:smooth_stone"
STEEL = "minecraft:polished_deepslate"
STEEL_SLAB_B = "minecraft:polished_deepslate_slab[type=bottom]"
STEEL_SLAB_T = "minecraft:polished_deepslate_slab[type=top]"
RUST = "minecraft:waxed_weathered_cut_copper"
RAIL = "minecraft:iron_bars"
GRATE = "minecraft:waxed_weathered_copper_grate"
ROCK = "minecraft:deepslate"
STONE = "minecraft:stone"
AIR = "minecraft:air"
LAMP_WARM = "minecraft:ochre_froglight"
LAMP_COOL = "minecraft:pearlescent_froglight"
LAMP_DEEP = "minecraft:verdant_froglight"
WATER = "minecraft:water"


class Silo:
    def __init__(self, spec: Spec, center_x: int, surface_y: int, center_z: int):
        self.s = s = spec
        self.R = R = int(math.ceil(s.r_outer)) + s.margin
        self.depth_levels = (LEVELS - 1) * s.pitch
        # vertical layout from the top: grade (bowl floor) -> cover -> cap -> cafeteria -> levels -> generator -> slab -> void
        self.grade_rel = 0
        top_of_cap = -s.cover
        self.Y1_rel = top_of_cap - s.cap - s.cafe_height    # level 1 walking surface relative to grade
        self.y144_rel = self.Y1_rel - self.depth_levels
        self.gen_floor_rel = self.y144_rel - s.pitch - s.gen_height
        self.void_top_rel = self.gen_floor_rel - 1 - s.slab
        self.void_floor_rel = self.void_top_rel - s.void_height
        bottom_rel = self.void_floor_rel - 3
        height = -bottom_rel + 1
        self.origin = (center_x - R, surface_y + bottom_rel, center_z - R)
        self.v = Volume(self.origin, (2 * R + 1, height, 2 * R + 1))
        self.surface_y = surface_y
        self.yi_grade = -bottom_rel                     # index of the grade row
        n = 2 * R + 1
        ax = np.arange(n) - R
        self.X, self.Z = np.meshgrid(ax, ax, indexing="ij")
        self.r = np.hypot(self.X + 0.5 - 0.5, self.Z)   # block centres measured from the axis column
        self.theta = np.mod(np.arctan2(self.Z, self.X), TAU)

    # coordinates -------------------------------------------------------------------------------------------------
    def yi(self, rel: int) -> int:
        return self.yi_grade + rel

    def level_y(self, n: int) -> int:
        """Index of the walking surface (first air row) of level n."""
        return self.yi(self.Y1_rel - (n - 1) * self.s.pitch)

    def ring(self, r0: float, r1: float) -> np.ndarray:
        return (self.r >= r0) & (self.r < r1)

    def sector(self, a0: float, a1: float) -> np.ndarray:
        a0, a1 = a0 % TAU, a1 % TAU
        if a0 <= a1:
            return (self.theta >= a0) & (self.theta < a1)
        return (self.theta >= a0) | (self.theta < a1)

    def polar(self, r: float, a: float) -> tuple[int, int]:
        return self.R + int(round(r * math.cos(a))), self.R + int(round(r * math.sin(a)))

    # build ----------------------------------------------------------------------------------------------------------
    def build(self) -> Volume:
        s, v = self.s, self.v
        top = self.yi(0)
        # rock around and below everything inside the footprint; the site generator blends the outside
        v.mask(0, top - 1, self.r < self.R, ROCK)
        v.mask(self.yi(-s.cover // 2), top - 1, self.r < self.R, "minecraft:dirt")
        self.shell()
        for n in range(LEVELS, 0, -1):
            self.level(n)
        self.stair()
        self.cafeteria()
        self.generator_hall()
        self.digger_void()
        return v

    def shell(self) -> None:
        s, v = self.s, self.v
        y_top = self.level_y(1) + s.cafe_height + s.cap - 1
        y_bot = self.yi(self.gen_floor_rel) - 1
        v.mask(y_bot, y_top, self.ring(s.r_inner_wall, s.r_outer), SHELL)
        # open atrium through all levels (floors and walkways are added per level)
        v.mask(y_bot + 1, self.level_y(1) + s.cafe_height - 1, self.r < s.r_inner_wall, AIR)
        # cap
        v.mask(self.level_y(1) + s.cafe_height, y_top, self.r < s.r_outer, CONCRETE)

    def level(self, n: int) -> None:
        s, v = self.s, self.v
        y = self.level_y(n)
        deep = n > 120
        floor = FLOOR_DEEP if deep else FLOOR
        # floor slab under rooms and walkway
        v.mask(y - 1, y - 1, self.ring(s.r_walk_in, s.r_inner_wall), floor)
        # walkway edge railing
        edge = self.ring(s.r_walk_in, s.r_walk_in + 1.0)
        v.mask(y, y, edge, RAIL)
        # front wall of the rooms with doors, bay walls, corridor walls
        front = self.ring(s.r_atrium, s.r_atrium + 1.0)
        back_of_front = self.ring(s.r_corridor_in - 1.0, s.r_corridor_in)
        corr_out = self.ring(s.r_corridor_out, s.r_corridor_out + 1.0)
        bay_arc = TAU / s.bays
        offset = n * GOLDEN
        walls = np.zeros_like(front)
        for b in range(s.bays):
            a = b * bay_arc
            d = np.abs(((self.theta - a + math.pi) % TAU) - math.pi) * self.r
            walls |= (d < 0.5) & self.ring(s.r_atrium, s.r_inner_wall)
            mid = a + bay_arc / 2
            dm = np.abs(((self.theta - mid + math.pi) % TAU) - math.pi) * self.r
            walls |= (dm < 0.5) & self.ring(s.r_corridor_out, s.r_inner_wall)
        wall_state = CONCRETE_DARK if deep else CONCRETE
        for dy in range(s.pitch - 1):
            v.mask(y + dy, y + dy, front | back_of_front | corr_out | walls, wall_state)
        # doors: one per bay in the front wall, one per room into the corridor
        for b in range(s.bays):
            a = (b + 0.5) * bay_arc
            for rr in (s.r_atrium + 0.5, s.r_corridor_in - 0.5):
                self.door(y, rr, a)
            for k in (0.25, 0.75):
                self.door(y, s.r_corridor_out + 0.5, (b + k) * bay_arc)
            self.room_contents(n, y, b)
        # lamps on the walkway ceiling, one per bay front
        for b in range(s.bays):
            a = (b + 0.5) * bay_arc
            x, z = self.polar(s.r_atrium - 1.2, a)
            v.set(x, y + s.pitch - 2, z, "minecraft:lantern[hanging=true]")
            v.set(x, y + s.pitch - 1, z, "minecraft:chain[axis=y]") if s.pitch > 4 else None
        # bridge from the landing to the walkway
        self.bridge(n, y)

    def door(self, y: int, r: float, a: float) -> None:
        x, z = self.polar(r, a)
        facing = self.facing_radial(a)
        self.v.set(x, y, z, f"minecraft:iron_door[facing={facing},half=lower,hinge=left,open=false]")
        self.v.set(x, y + 1, z, f"minecraft:iron_door[facing={facing},half=upper,hinge=left,open=false]")
        self.v.set(x, y + 2, z, AIR) if self.v.get(x, y + 2, z) == CONCRETE else None

    @staticmethod
    def facing_radial(a: float) -> str:
        """Horizontal facing pointing outward along angle a (x east, z south)."""
        c, s = math.cos(a), math.sin(a)
        if abs(c) >= abs(s):
            return "east" if c > 0 else "west"
        return "south" if s > 0 else "north"

    def bridge(self, n: int, y: int) -> None:
        s, v = self.s, self.v
        a = (n * GOLDEN) % TAU
        d = np.abs(((self.theta - a + math.pi) % TAU) - math.pi)
        lateral = d * self.r
        span = (lateral < 1.6) & (d < math.pi / 2) & self.ring(s.r_stair_out, s.r_walk_in + 1.0)
        v.mask(y - 1, y - 1, span, GRATE)
        rails = (np.abs(lateral - 2.0) < 0.5) & (d < math.pi / 2) & self.ring(s.r_landing, s.r_walk_in)
        v.mask(y, y, rails, RAIL)
        # gap in the walkway railing where the bridge lands
        gap = (lateral < 1.6) & (d < math.pi / 2) & self.ring(s.r_walk_in, s.r_walk_in + 1.0)
        v.mask(y, y, gap, AIR)
        pad = (d < math.radians(26)) & self.ring(s.r_stair_out, s.r_landing)
        v.mask(y - 1, y - 1, pad, GRATE)

    def stair(self) -> None:
        """One uniform helix through the whole silo; level n is reached at angle n * 137.5 degrees."""
        s, v = self.s, self.v
        per_turn = s.pitch / (1 + GOLDEN / TAU)        # drop per full turn
        y1 = self.level_y(1)
        y_bottom = self.level_y(LEVELS)
        annulus = self.ring(s.r_stair_in, s.r_stair_out)
        newel = self.r < s.r_newel
        top_idx = self.level_y(1) + s.cafe_height - 1
        v.mask(self.yi(self.gen_floor_rel), top_idx, newel, STEEL)
        xs, zs = np.nonzero(annulus)
        a1 = GOLDEN % TAU                               # angle of level 1
        for x, z in zip(xs, zs):
            th = self.theta[x, z]
            # cumulative turns from level 1 to this column's first pass
            t0 = ((th - a1) % TAU) / TAU
            t = t0
            while True:
                surf = y1 - t * per_turn
                if surf < y_bottom - 0.01:
                    break
                q = round(surf * 2) / 2
                if q == int(q):
                    v.set(x, int(q) - 1, z, STEEL)
                else:
                    v.set(x, int(math.floor(q)), z, STEEL_SLAB_B)
                t += 1
        # outer handrail following the helix
        rail = self.ring(s.r_stair_out, s.r_stair_out + 1.0)
        xs, zs = np.nonzero(rail)
        for x, z in zip(xs, zs):
            th = self.theta[x, z]
            t = ((th - a1) % TAU) / TAU
            while True:
                surf = y1 - t * per_turn
                if surf < y_bottom - 0.01:
                    break
                yb = int(math.floor(surf))
                if v.get(x, yb - 1, z) != GRATE:
                    v.set(x, yb, z, RAIL)
                t += 1
        # six core columns between stair and walkway
        for deg in COLUMN_ANGLES:
            cx, cz = self.polar(s.r_column_orbit, math.radians(deg))
            v.box(cx - 1, self.yi(self.gen_floor_rel), cz - 1, cx + 1, top_idx, cz + 1, CONCRETE)

    def room_contents(self, n: int, y: int, b: int) -> None:
        """Furnish one bay of a residential level (special levels override in their own builders)."""
        s, v = self.s, self.v
        bay_arc = TAU / s.bays
        a = (b + 0.5) * bay_arc
        lamp = LAMP_DEEP if n > 120 else (LAMP_COOL if n > 49 else LAMP_WARM)
        # ceiling lamps in front room, back rooms
        for r in (s.r_atrium + 5, s.r_corridor_out + 6):
            for k in ((0.0,) if r < s.r_corridor_in else (-0.25, 0.25)):
                x, z = self.polar(r, a + k * bay_arc)
                v.set(x, y + s.pitch - 2, z, lamp)
        # beds and a table in each back room
        for k in (-0.25, 0.25):
            ang = a + k * bay_arc
            x, z = self.polar(s.r_inner_wall - 2.5, ang)
            facing = self.facing_radial(ang)
            v.set(x, y, z, f"minecraft:light_gray_bed[facing={facing},part=head]", {"id": "minecraft:bed"})
            dx, dz = {"east": (-1, 0), "west": (1, 0), "south": (0, -1), "north": (0, 1)}[facing]
            v.set(x + dx, y, z + dz, f"minecraft:light_gray_bed[facing={facing},part=foot]", {"id": "minecraft:bed"})
        x, z = self.polar(s.r_atrium + 6, a)
        v.set(x, y, z, "minecraft:spruce_fence")
        v.set(x, y + 1, z, "minecraft:spruce_pressure_plate")

    def cafeteria(self) -> None:
        """Level 1: the dining hall around the stair head, the wallscreen, the airlock passage."""
        s, v = self.s, self.v
        y = self.level_y(1)
        h = s.cafe_height
        # clear the rooms of level 1 to make one hall up to r_inner_wall, keep walkway floor
        hall = self.ring(s.r_walk_in, s.r_inner_wall)
        v.mask(y, y + h - 1, hall, AIR)
        v.mask(y - 1, y - 1, hall, "minecraft:polished_andesite")
        # tables in rings
        for r in (22, 28, 34, 40):
            count = int(TAU * r / 6)
            for i in range(count):
                a = (i + 0.5) * TAU / count
                if abs(((a - SCREEN_ANGLE + math.pi) % TAU) - math.pi) < SCREEN_ARC / 2 + 0.1 and r > 36:
                    continue
                x, z = self.polar(r, a)
                v.set(x, y, z, "minecraft:dark_oak_fence")
                v.set(x, y + 1, z, "minecraft:dark_oak_pressure_plate")
                for off in (-1, 1):
                    xx, zz = self.polar(r + off, a)
                    v.set(xx, y, zz, "minecraft:dark_oak_stairs[facing=north]")
        # wallscreen on the outer wall
        screen = self.sector(SCREEN_ANGLE - SCREEN_ARC / 2, SCREEN_ANGLE + SCREEN_ARC / 2) & self.ring(s.r_inner_wall - 1, s.r_inner_wall)
        v.mask(y + 2, y + h - 2, screen, "minecraft:gray_stained_glass")
        v.mask(y + 1, y + 1, screen, "minecraft:black_concrete")
        v.mask(y + h - 1, y + h - 1, screen, "minecraft:black_concrete")
        # ceiling lamps
        for r in (20, 26, 32, 38):
            count = int(TAU * r / 7)
            for i in range(count):
                x, z = self.polar(r, (i + 0.25) * TAU / count)
                v.set(x, y + h - 1, z, LAMP_WARM)
        # airlock passage through the shell toward the ramp
        a = AIRLOCK_ANGLE
        corridor = (np.abs(((self.theta - a + math.pi) % TAU) - math.pi) * self.r < 2.6) & self.ring(s.r_inner_wall - 1, self.R + 1)
        v.mask(y, y + 3, corridor, AIR)
        v.mask(y - 1, y - 1, corridor, "minecraft:polished_andesite")
        for rr, label in ((s.r_inner_wall + 0.5, "inner"), (s.r_outer - 0.5, "outer")):
            ring = (np.abs(((self.theta - a + math.pi) % TAU) - math.pi) * self.r < 2.6) & self.ring(rr - 0.5, rr + 0.5)
            v.mask(y, y + 3, ring, "minecraft:iron_block")

    def generator_hall(self) -> None:
        s, v = self.s, self.v
        yf = self.yi(self.gen_floor_rel)
        v.mask(yf - 1, yf - 1, self.r < s.r_inner_wall, FLOOR_DEEP)
        v.mask(yf, self.yi(self.y144_rel) - 2, self.ring(0, s.r_inner_wall) & ~(self.r < s.r_newel), AIR)
        # turbine casing at 120 degrees, radius 16
        cx, cz = self.polar(16, math.radians(120))
        for dx in range(-7, 8):
            for dz in range(-4, 5):
                for dy in range(0, 7):
                    if (dz * dz) / 16 + ((dy - 3) ** 2) / 9 <= 1.0:
                        v.set(cx + dx, yf + dy, cz + dz, "minecraft:waxed_weathered_copper" if abs(dx) < 6 else STEEL)
        # control room raised over the floor
        rx, rz = self.polar(34, math.radians(300))
        v.box(rx - 5, yf + 5, rz - 4, rx + 5, yf + 5, rz + 4, STEEL)
        v.box(rx - 5, yf + 6, rz - 4, rx + 5, yf + 9, rz + 4, "minecraft:gray_stained_glass")
        v.box(rx - 4, yf + 6, rz - 3, rx + 4, yf + 9, rz + 3, AIR)
        for dy in range(4):
            v.mask(yf + 1, yf + 1, self.ring(s.r_inner_wall - 3, s.r_inner_wall - 2) & (np.mod(self.theta * 8 / math.pi, 1) < 0.15), LAMP_DEEP)

    def digger_void(self) -> None:
        s, v = self.s, self.v
        top = self.yi(self.void_top_rel)
        floor = self.yi(self.void_floor_rel)
        r = self.r
        dome = np.clip(1 - (r / s.void_radius) ** 2, 0, 1)
        for yy in range(floor, top):
            frac = (yy - floor) / (top - floor)
            m = r < s.void_radius * (1.0 if frac < 0.8 else math.sqrt(max(0.0, 1 - ((frac - 0.8) / 0.2) ** 2)))
            v.mask(yy, yy, m, AIR)
        v.mask(floor, floor + 2, r < s.void_radius, WATER)
        # central unit of the digging machine with eight arms of three drills each
        cyl = r < 9
        v.mask(floor, top - 6, cyl, "minecraft:waxed_weathered_copper")
        v.mask(floor + 3, top - 6, r < 7, AIR)
        for k in range(8):
            a = k * TAU / 8
            for t in range(9, int(s.void_radius) - 6):
                x, z = self.polar(t, a)
                v.box(x, top - 10, z, x, top - 8, z, STEEL)
            for t in (20, 30, 40):
                x, z = self.polar(t, a)
                v.box(x - 1, top - 16, z - 1, x + 1, top - 11, z + 1, "minecraft:waxed_exposed_copper")
                v.set(x, top - 17, z, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down]")
        v.mask(top - 4, top - 1, self.ring(s.void_radius - 4, s.void_radius), "minecraft:waxed_weathered_copper")
