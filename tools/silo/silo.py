"""One silo of the Silo series, generated block by block.

Sources: the show and novels as collected by the fan reference explorethesilo.com (canon level list) and the
dimensions of its three.js model (atrium, stair, bridges rotating by 137.5 degrees per level, 18 bays, cafeteria
screen and airlock angles, ramp, generator, digger void). Minecraft scale: 1 block = 1 m horizontally; a level is 5
blocks (4 clear + 1 slab) instead of the model's cinematic 10 m, so 144 levels fit in about 780 blocks of depth.

Local frame: x, z centred on the silo axis (index R), y index 0 at the bottom of the digger void. World y of an
index is origin_y + index. Level n (1..144) has its walking surface at Y1 - 5 * (n - 1).

Interiors from the model: bay facades and walkway dressing (bays.py), the canon rooms (levels.py), the generator
hall, digger void and tunnel (machines.py); after them connect.py gives panes, bars, fences and walls their
connections and drops halves a room cut off, and lighting.py puts invisible light wherever a monster could spawn.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from bays import (BAY_ARC_DEG, BAY_W, FACADES, FRAME_DEG, HW, ROOM_BAY, ROOM_LEVELS, cols_of, dressing_for,
                  lamp_for, region, rows_of, seeded, variant_for)
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
    cover: int = 4                    # earth over the cap up to grade (the bowl floor); the exit ramp climbs cover+cap+cafe
    gen_height: int = 16              # generator hall below level 144
    slab: int = 9                     # "thirty feet" of concrete above the digger void
    void_height: int = 44
    void_radius: float = 44.0
    margin: int = 6


COLUMN_ANGLES = [64, 110, 158, 202, 250, 296]
SCREEN_ANGLE, SCREEN_ARC = math.radians(140), math.radians(54)
# The model has the airlock at 210 degrees with the screen just to its left (170); here both turn by 30 so the way in
# runs due west and the tunnel, portal and sensor block are block-aligned (surface.py).
AIRLOCK_ANGLE = math.radians(180)

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
PARAPET = "minecraft:andesite_wall"
PANE = "minecraft:glass_pane"
GRATE_UP = "minecraft:waxed_copper_grate"
PILASTER = "minecraft:polished_andesite"
PLATE = "minecraft:heavy_weighted_pressure_plate[power=0]"
STOOP = "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]"
MEDICAL_WALL = "minecraft:white_concrete"
MOSS = "minecraft:moss_block"
LEAVES = "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"
CRATE = "minecraft:barrel[facing=up,open=false]"
SACK = "minecraft:brown_wool"
DRUM = "minecraft:cauldron"


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
        self._bays()

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
        from levels import Furnisher
        Furnisher(self).all()
        import connect
        connect.tidy(v)
        connect.connect(v)
        import lighting
        void_top = self.yi(self.void_top_rel)
        self.lights = lighting.light_up(v, lambda y: 3 if y < void_top else 12)
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

    # levels ---------------------------------------------------------------------------------------------------------
    def bay_center(self, b: int) -> float:
        """Bearing (radians, silo frame) of bay b's centre: the model's (b + 0.5) * 20 degrees turned by FRAME_DEG."""
        return math.radians((b + 0.5) * BAY_ARC_DEG + FRAME_DEG)

    def _bays(self) -> None:
        """Front-wall cells of each bay with their position across the model's bay (u, metres), and the walls."""
        s = self.s
        front = self.ring(s.r_atrium, s.r_atrium + 1.0)
        self.bay_cells: list[list[tuple[int, int, float, float]]] = [[] for _ in range(s.bays)]
        for x, z in zip(*np.nonzero(front)):
            th = float(self.theta[x, z])
            m = (math.degrees(th) - FRAME_DEG) % 360.0
            b = int(m // BAY_ARC_DEG) % s.bays
            u = (m - (b + 0.5) * BAY_ARC_DEG) / BAY_ARC_DEG * BAY_W
            self.bay_cells[b].append((int(x), int(z), u, th))
        for c in self.bay_cells:
            c.sort(key=lambda t: t[2])
        walls = front | self.ring(s.r_corridor_in - 1.0, s.r_corridor_in) | self.ring(s.r_corridor_out, s.r_corridor_out + 1.0)
        for b in range(s.bays):
            edge = self.bay_center(b) - math.radians(BAY_ARC_DEG / 2)
            d = np.abs(((self.theta - edge + math.pi) % TAU) - math.pi) * self.r
            walls |= (d < 0.5) & self.ring(s.r_atrium, s.r_inner_wall)
            dm = np.abs(((self.theta - self.bay_center(b) + math.pi) % TAU) - math.pi) * self.r
            walls |= (dm < 0.5) & self.ring(s.r_corridor_out, s.r_inner_wall)
        self.wall_mask = walls

    def level(self, n: int) -> None:
        s, v = self.s, self.v
        y = self.level_y(n)
        deep = n > 120
        v.mask(y - 1, y - 1, self.ring(s.r_walk_in, s.r_inner_wall), FLOOR_DEEP if deep else FLOOR)
        # walkway parapet: the model's solid 1.1 m concrete parapet (WALK_PARAPET) as one wall block
        v.mask(y, y, self.ring(s.r_walk_in, s.r_walk_in + 1.0), PARAPET)
        wall_state = CONCRETE_DARK if deep else (MEDICAL_WALL if dressing_for(n) == "medical" else CONCRETE)
        v.mask(y, y + s.pitch - 2, self.wall_mask, wall_state)
        for b in range(s.bays):
            a = self.bay_center(b)
            self.steel_door(y, [self.polar(s.r_corridor_in - 0.5, a)], a, s.r_corridor_in - 0.5)
            for k in (-0.25, 0.25):
                ak = a + k * math.radians(BAY_ARC_DEG)
                self.steel_door(y, [self.polar(s.r_corridor_out + 0.5, ak)], ak, s.r_corridor_out + 0.5)
            self.facade(n, y, b, variant_for(n, b), wall_state)
            self.room_contents(n, y, b)
            self.walkway_props(n, y, b, wall_state)
            # the walkway's own light: one hanging fitting per bay, clear of the parapet
            x, z = self.polar(s.r_atrium - 1.2, a)
            if v.get(x, y + 2, z) == AIR:
                v.set(x, y + 2, z, "minecraft:lantern[hanging=true,waterlogged=false]")
                v.set(x, y + 3, z, "minecraft:chain[axis=y,waterlogged=false]")
        self.bridge(n, y)

    def steel_door(self, y: int, cells: list[tuple[int, int]], a: float, r: float) -> None:
        """Iron door (one or a pair) in a ring wall at radius r, opened by heavy pressure plates on both sides."""
        v = self.v
        facing = self.facing_radial(a + math.pi)            # faces the axis
        fx, fz = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}[facing]
        rx, rz = -fz, fx                                     # right hand when looking along facing
        if len(cells) == 2:
            (x0, z0), (x1, z1) = cells
            if (x1 - x0) * rx + (z1 - z0) * rz < 0:
                cells = [cells[1], cells[0]]
        for i, (x, z) in enumerate(cells):
            hinge = "left" if (len(cells) == 1 or i == 0) else "right"
            for half, dy in (("lower", 0), ("upper", 1)):
                v.set(x, y + dy, z, f"minecraft:iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")
            ang = math.atan2(z - self.R, x - self.R)
            for rr in (r - 1.0, r + 1.0):
                px, pz = self.polar(rr, ang)
                if v.get(px, y, pz) == AIR and (px, pz) not in cells:
                    v.set(px, y, pz, PLATE)

    def facade(self, n: int, y: int, b: int, variant: str, wall_state: str) -> None:
        """One bay's face on the walkway, rasterised from the model's BAY builder (bays.FACADES)."""
        v = self.v
        cells = self.bay_cells[b]
        if not cells:
            return
        us = [c[2] for c in cells]
        spec = FACADES[variant]
        deep = n > 120
        grid: dict[tuple[int, int], str] = {}
        doors: list[list[int]] = []
        later = []
        for kind, x0, x1, y0, y1 in spec["open"]:
            if kind == "door":
                mid = (x0 + x1) / 2
                cols = sorted(sorted(cols_of(us, x0, x1), key=lambda i: abs(us[i] - mid))[:2])
                doors.append(cols)
                for ci in cols:
                    grid[(ci, 0)] = grid[(ci, 1)] = "DOOR"
            else:
                later.append((kind, x0, x1, y0, y1))
        for kind, x0, x1, y0, y1 in later:
            cols = cols_of(us, x0, x1)
            if kind == "shop":
                mids = [i for i in cols if abs(us[i]) <= 1.1] or [min(cols, key=lambda i: abs(us[i]))]
            for ci in cols:
                for row in rows_of(y0, y1):
                    while grid.get((ci, row)) == "DOOR" and row < 3:
                        row += 1
                    if kind == "pilaster":
                        grid.setdefault((ci, row), PILASTER)
                        continue
                    if grid.get((ci, row)) == "DOOR":
                        continue
                    if kind in ("window", "slit", "glazed"):
                        st = PANE
                    elif kind == "grate":
                        st = GRATE if deep else GRATE_UP
                    elif kind == "chute":
                        st = "minecraft:hopper[enabled=true,facing=down]"
                    elif kind == "leaf":
                        st = "minecraft:iron_block"
                    else:                                    # shop front: open between the mullions, glazed beside
                        st = AIR if ci in mids else PANE
                    grid[(ci, row)] = st
        for (ci, row), st in grid.items():
            if st != "DOOR":
                x, z = cells[ci][0], cells[ci][1]
                v.set(x, y + row, z, st)
        for cols in doors:
            a = sum(cells[ci][3] for ci in cols) / len(cols)
            self.steel_door(y, [(cells[ci][0], cells[ci][1]) for ci in cols], a, self.s.r_atrium + 0.5)
        lamp = lamp_for(n)
        for u in spec.get("lamps", ()):
            ci = min(range(len(us)), key=lambda i: abs(us[i] - u))
            for row in (1, 2, 3):
                if (ci, row) not in grid:
                    v.set(cells[ci][0], y + row, cells[ci][1], lamp)
                    grid[(ci, row)] = lamp
                    break
        if "stoop" in spec:                                   # a raised step along the face (windowsB, balcony)
            door_cols = {ci for cols in doors for ci in cols}
            for ci, (x, z, u, th) in enumerate(cells):
                if ci in door_cols:
                    continue
                fx, fz = self.polar(self.s.r_atrium - 0.5, th)
                if v.get(fx, y, fz) == AIR:
                    v.set(fx, y, fz, STOOP)

    def walk_cell(self, b: int, px: float, pz: float) -> tuple[int, int, float]:
        """Walkway cell in front of bay b at the model's (across px, out from the wall pz) position."""
        th = self.bay_center(b) + math.radians(px / BAY_W * BAY_ARC_DEG)
        rr = self.s.r_atrium - (0.5 if pz < 1.4 else 1.5)
        x, z = self.polar(rr, th)
        return x, z, th

    def walkway_props(self, n: int, y: int, b: int, wall_state: str) -> None:
        """The model's per-bay dressing on the walkway (buildWindow), placed only where it leaves a way past."""
        v, s = self.v, self.s
        if n == 1 or (n in ROOM_LEVELS and b == ROOM_BAY):
            return
        L, dress, reg = n - 1, dressing_for(n), region(n)
        r = seeded(L, b, 400)
        px = -HW + 1.2 + (2 * HW - 2.4) * seeded(L, b, 401)
        pz = 1.0 + 1.2 * seeded(L, b, 402)
        rot = seeded(L, b, 403) * 0.6 - 0.3

        def free(x, z, th) -> bool:
            if v.get(x, y, z) != AIR or v.get(x, y - 1, z) not in (FLOOR, FLOOR_DEEP):
                return False
            for rr in (s.r_atrium - 0.5, s.r_atrium - 1.5):  # keep the other walkway row open at this bearing
                ox, oz = self.polar(rr, th)
                if (ox, oz) != (x, z) and v.get(ox, y, oz) != AIR:
                    return False
            return True

        def put(px_, pz_, state, floor=None, above=None):
            x, z, th = self.walk_cell(b, px_, pz_)
            if not free(x, z, th):
                return
            v.set(x, y, z, state)
            if floor:
                v.set(x, y - 1, z, floor)
            if above:
                v.set(x, y + 3, z, above)

        inward = lambda th, turn=0.0: self.facing_radial(th + math.pi + turn)
        _, _, th0 = self.walk_cell(b, px, pz)
        if dress == "farming":
            for bx in (-2.7, 2.7):
                put(bx, 1.75, LEAVES, floor=MOSS, above=lamp_for(n))
            if seeded(L, b, 10) < 0.8:
                put(px * 0.55, 2.45, "minecraft:flowering_azalea", floor=MOSS)
            put(px, 2.65, "minecraft:fern", floor=MOSS)
            put(-px * 0.8, 2.55, "minecraft:fern", floor=MOSS)
        elif dress == "bazaar":
            for sx in (-2.8, 2.8):
                h = seeded(L, b, 15 if sx > 0 else 16)
                colour = "red" if h < 0.33 else "orange" if h < 0.66 else "yellow"
                x, z, th = self.walk_cell(b, sx, 1.0)
                if free(x, z, th):
                    v.set(x, y, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
                    v.set(x, y + 2, z, f"minecraft:{colour}_wool")
            put(px, 2.55, CRATE)
            if seeded(L, b, 17) < 0.6:
                put(-px * 0.7, 2.5, SACK)
        elif dress == "mechanical":
            if r < 0.5:
                put(px, pz, DRUM)
            elif r < 0.75:
                put(px, 0.5, "minecraft:smithing_table")
            else:
                put(px, pz, f"minecraft:blast_furnace[facing={inward(th0)},lit=false]")
            if b % 3 == 0:
                x, z, _ = self.walk_cell(b, px, 0.7)
                if v.get(x, y + 3, z) == AIR:
                    v.set(x, y + 3, z, "minecraft:chain[axis=y,waterlogged=false]")
        elif dress == "recycling":
            put(px, pz, "minecraft:dried_kelp_block" if r < 0.5 else SACK)
        elif dress in ("residential",):
            if seeded(L, b, 33) < 0.3:                        # notice board on the wall, 2.4 m up
                x, z, th = self.walk_cell(b, px * 0.5, 0.1)
                wx, wz = self.polar(s.r_atrium + 0.5, th)
                if v.get(x, y + 1, z) == AIR and v.get(wx, y + 1, wz) == wall_state:
                    v.set(x, y + 1, z, f"minecraft:spruce_wall_sign[facing={inward(th)},waterlogged=false]")
            if seeded(L, b, 34) < (0.12 if reg == "deep" else 0.3):
                put(px, 1.5 + 0.6 * seeded(L, b, 35), f"minecraft:spruce_stairs[facing={inward(th0, rot * 3)},half=bottom,shape=straight,waterlogged=false]")
            if r < 0.45:
                if reg == "deep":
                    put(px, pz, DRUM if r < 0.28 else f"minecraft:blast_furnace[facing={inward(th0)},lit=false]")
                else:
                    put(px, pz, "minecraft:potted_azalea_bush" if r < 0.25 else CRATE)

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
        # solid parapets each side (model PARAPET_HEIGHT 1.05), as on the walkway
        rails = (np.abs(lateral - 2.0) < 0.5) & (d < math.pi / 2) & self.ring(s.r_landing, s.r_walk_in)
        v.mask(y, y, rails, PARAPET)
        # gap in the walkway parapet where the bridge lands
        gap = (lateral < 1.6) & (d < math.pi / 2) & self.ring(s.r_walk_in, s.r_walk_in + 1.0)
        v.mask(y, y, gap, AIR)
        pad = (d < math.radians(26)) & self.ring(s.r_stair_out, s.r_landing)
        v.mask(y - 1, y - 1, pad, GRATE)

    def stair(self) -> None:
        """One uniform helix from level 1 down to the generator hall floor (the model's stair reaches the generator
        room); level n is reached at angle n * 137.5 degrees."""
        s, v = self.s, self.v
        per_turn = s.pitch / (1 + GOLDEN / TAU)        # drop per full turn
        y1 = self.level_y(1)
        y_bottom = self.yi(self.gen_floor_rel)
        annulus = self.ring(s.r_stair_in, s.r_stair_out)
        newel = self.r < s.r_newel
        top_idx = self.level_y(1) + s.cafe_height - 1
        v.mask(self.yi(self.gen_floor_rel), top_idx, newel, STEEL)
        xs, zs = np.nonzero(annulus)
        a1 = GOLDEN % TAU                               # angle of level 1
        for x, z in zip(xs, zs):
            th = self.theta[x, z]
            t = ((th - a1) % TAU) / TAU
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
        # six core columns between stair and walkway, from level 144's floor up (the hall below is open)
        for deg in COLUMN_ANGLES:
            cx, cz = self.polar(s.r_column_orbit, math.radians(deg))
            v.box(cx - 1, self.level_y(LEVELS) - 1, cz - 1, cx + 1, top_idx, cz + 1, CONCRETE)

    def room_contents(self, n: int, y: int, b: int) -> None:
        """A bay behind the face: lamps in the front room, corridor and back rooms, and a home to live in.
        The model has no rooms behind its facades (a lit plane 2 m in). Homes follow the show's lived-in silo
        apartments: a front room with a rug, a table and chairs and a kitchen counter against the corridor wall
        (stove, sink, shelves); two back bedrooms with a bed, a nightstand with a light and a chest. Deeper down
        (the Down Deep) the homes are poorer: no rug, fewer things. Department levels keep only their lamps."""
        s, v = self.s, self.v
        arc = math.radians(BAY_ARC_DEG)
        a = self.bay_center(b)
        lamp = lamp_for(n)
        x, z = self.polar(s.r_atrium + 5, a)
        v.set(x, y + s.pitch - 2, z, lamp)
        x, z = self.polar((s.r_corridor_in + s.r_corridor_out) / 2, a)
        v.set(x, y + s.pitch - 2, z, lamp)
        for k in (-0.25, 0.25):
            x, z = self.polar(s.r_corridor_out + 6, a + k * arc)
            v.set(x, y + s.pitch - 2, z, lamp)
        if dressing_for(n) not in ("residential", "admin") or (n in ROOM_LEVELS and b == ROOM_BAY):
            return
        L, reg = n - 1, region(n)
        rnd = lambda k: seeded(L, b, 500 + k)
        poor = reg == "deep"
        wood = ("spruce", "oak", "dark_oak", "birch")[int(rnd(0) * 4)] if not poor else "spruce"
        rug = ("red", "brown", "green", "blue", "orange", "cyan", "light_gray")[int(rnd(1) * 7)]
        bed = ("light_gray", "white", "gray", "brown", "blue")[int(rnd(2) * 5)]
        floor_ok = (FLOOR, FLOOR_DEEP)
        doors = [self.polar(s.r_corridor_in - 0.5, a)] + [self.polar(s.r_corridor_out + 0.5, a + k * arc)
                                                           for k in (-0.25, 0.25)]

        def cell(r: float, t: float) -> tuple[int, int]:
            """r out from the axis, t blocks across the bay (positive clockwise)."""
            return self.polar(r, a + t / r)

        def clear(x: int, z: int, h: int = 1) -> bool:
            if any(abs(x - dx) + abs(z - dz) <= 1 for dx, dz in doors):
                return False
            return all(v.get(x, y + k, z) == AIR for k in range(h)) and v.get(x, y - 1, z) in floor_ok

        def put(r, t, state, dy=0, h=1) -> tuple[int, int] | None:
            x, z = cell(r, t)
            if not clear(x, z, max(h, dy + 1)):
                return None
            v.set(x, y + dy, z, state)
            return x, z

        def facing_to(x0, z0, x1, z1) -> str:
            dx, dz = x1 - x0, z1 - z0
            if abs(dx) >= abs(dz):
                return "east" if dx > 0 else "west"
            return "south" if dz > 0 else "north"

        # front room: rug, table, chairs round it
        rt, tt = s.r_atrium + 5.5, (rnd(3) - 0.5) * 2.0
        tx, tz = cell(rt, tt)
        if not poor:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if clear(tx + dx, tz + dz):
                        v.set(tx + dx, y, tz + dz, f"minecraft:{rug}_carpet")
        if clear(tx, tz) or v.get(tx, y, tz) == f"minecraft:{rug}_carpet":
            v.set(tx, y, tz, f"minecraft:{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
            v.set(tx, y + 1, tz, f"minecraft:{wood}_pressure_plate[powered=false]")
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if rnd(10 + dx * 3 + dz) < (0.45 if poor else 0.8):
                    cx, cz = tx + dx, tz + dz
                    st = v.get(cx, y, cz)
                    if st == AIR or (st or "").endswith("_carpet"):
                        if v.get(cx, y - 1, cz) in floor_ok:
                            f = facing_to(cx, cz, tx, tz)
                            back = {"east": "west", "west": "east", "south": "north", "north": "south"}[f]
                            v.set(cx, y, cz, f"minecraft:{wood}_stairs[facing={back},half=bottom,shape=straight,"
                                             "waterlogged=false]")
        # kitchen counter along the corridor wall, either side of its door
        rk = s.r_corridor_in - 1.5
        side = 1 if rnd(4) < 0.5 else -1
        kx, kz = cell(rk, 0)
        inward = facing_to(kx, kz, *self.polar(s.r_atrium, a))
        kitchen = [f"minecraft:smoker[facing={inward},lit=false]", "minecraft:cauldron",
                   f"minecraft:barrel[facing=up,open=false]", f"minecraft:{wood}_planks"]
        if poor:
            kitchen = [f"minecraft:furnace[facing={inward},lit=false]", "minecraft:barrel[facing=up,open=false]"]
        for j, st in enumerate(kitchen):
            got = put(rk, side * (2 + j), st)
            if got and j == len(kitchen) - 1 and not poor:
                v.set(got[0], y + 1, got[1], "minecraft:potted_red_tulip" if rnd(5) < 0.5 else "minecraft:lantern[hanging=false,waterlogged=false]")
        if not poor and rnd(6) < 0.7:                         # shelves on the other side of the door
            put(rk, -side * 2, "minecraft:bookshelf")
            put(rk, -side * 3, "minecraft:bookshelf")
        # back bedrooms
        for k in (-0.25, 0.25):
            ang = a + k * arc
            hx, hz = self.polar(s.r_inner_wall - 2.5, ang)
            facing = self.facing_radial(ang)
            dx, dz = {"east": (-1, 0), "west": (1, 0), "south": (0, -1), "north": (0, 1)}[facing]
            if clear(hx, hz) and clear(hx + dx, hz + dz):
                v.set(hx, y, hz, f"minecraft:{bed}_bed[facing={facing},occupied=false,part=head]")
                v.set(hx + dx, y, hz + dz, f"minecraft:{bed}_bed[facing={facing},occupied=false,part=foot]")
                # nightstand beside the head, with a lamp on it; a chest at the foot
                for nx, nz in ((hx + dz, hz + dx), (hx - dz, hz - dx)):
                    if clear(nx, nz, 2):
                        v.set(nx, y, nz, "minecraft:barrel[facing=up,open=false]" if poor else f"minecraft:{wood}_planks")
                        v.set(nx, y + 1, nz, "minecraft:lantern[hanging=false,waterlogged=false]")
                        break
                fx, fz = hx + 2 * dx, hz + 2 * dz
                if rnd(20 + int(k * 4)) < 0.6 and clear(fx, fz):
                    v.set(fx, y, fz, f"minecraft:chest[facing={self.facing_radial(ang + math.pi)},type=single,waterlogged=false]")
                if not poor:
                    for cx, cz in ((hx + 3 * dx, hz + 3 * dz), (hx + 3 * dx + dz, hz + 3 * dz + dx)):
                        if clear(cx, cz):
                            v.set(cx, y, cz, f"minecraft:{rug}_carpet")

    def cafeteria(self) -> None:
        """Level 1, the cafeteria (model: CAFE_FRONT, the wallscreen SCREEN_*, the ceiling flower, the panelling):
        tables 0.8 x 1.6 m set tangentially, 3 m apart along rows, four chairs each, dark panelling with sconces
        every 18 degrees off the screen, the wallscreen 54 degrees wide from 2.6 m up, and lit petals in the ceiling
        between ribs about 15 degrees apart round a lit boss. The model lays tables only on the camera's side
        (128-232 degrees, a render economy); here they fill the floor, clear of the aisles to the bridge and the
        airlock and of the screen's foot."""
        s, v = self.s, self.v
        y = self.level_y(1)
        h = s.cafe_height
        hall = self.ring(s.r_walk_in, s.r_inner_wall)
        v.mask(y, y + h - 1, hall, AIR)
        v.mask(y - 1, y - 1, hall, "minecraft:polished_andesite")
        v.mask(y, y, self.ring(s.r_walk_in, s.r_walk_in + 1.0), PARAPET)
        self.bridge(1, y)
        th = self.theta
        off = lambda a: np.abs(((th - a + math.pi) % TAU) - math.pi)
        screen = off(SCREEN_ANGLE) < SCREEN_ARC / 2
        # panelling on the wall's inner face, the screen in its sector, sconces every 18 degrees
        face = self.ring(s.r_inner_wall - 1, s.r_inner_wall)
        v.mask(y, y + h - 1, face & ~screen, "minecraft:dark_oak_planks")
        for row in range(2, h):
            v.mask(y + row, y + row, face & screen, "minecraft:black_concrete" if row == 2 else "minecraft:gray_stained_glass")
        posts = (off(SCREEN_ANGLE) >= SCREEN_ARC / 2) & (off(SCREEN_ANGLE) < SCREEN_ARC / 2 + math.radians(2.5))
        v.mask(y + 1, y + h - 1, self.ring(s.r_inner_wall - 2, s.r_inner_wall) & posts, "minecraft:black_concrete")
        v.mask(y, y + 1, face & screen, "minecraft:dark_oak_planks")
        for k in range(0, 60, 3):
            a = (k + 0.5) * TAU / 60
            if abs(((a - SCREEN_ANGLE + math.pi) % TAU) - math.pi) < SCREEN_ARC / 2 + math.radians(4):
                continue
            x, z = self.polar(s.r_inner_wall - 0.5, a)
            v.set(x, y + 4, z, "minecraft:shroomlight")
        # tables: the model's rows are 3 m apart with chairs 0.62 m off the table; a block chair needs a whole block
        # beside the table, so rows here are 4 apart to leave a block to walk between the chair rows
        aisle = lambda a, r: min(abs(((a - g + math.pi) % TAU) - math.pi) * r for g in ((GOLDEN % TAU), AIRLOCK_ANGLE)) < 3.5
        r = s.r_walk_in + 2.6
        while r < s.r_inner_wall - 2.5:
            n = int(TAU * r / 3.0)
            for k in range(n):
                a = (k + 0.5) * TAU / n
                if aisle(a, r) or (r > s.r_inner_wall - 6 and abs(((a - SCREEN_ANGLE + math.pi) % TAU) - math.pi) < SCREEN_ARC / 2 + 0.05):
                    continue
                cells = {self.polar(r, a - 0.4 / r), self.polar(r, a + 0.4 / r)}
                for x, z in cells:
                    v.set(x, y, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
                for sd in (-1, 1):
                    back = self.facing_radial(a if sd > 0 else a + math.pi)
                    for dz in (-0.4, 0.4):
                        x, z = self.polar(r + sd * 1.0, a + dz / r)
                        if v.get(x, y, z) == AIR:
                            v.set(x, y, z, f"minecraft:oak_stairs[facing={back},half=bottom,shape=straight,waterlogged=false]")
            r += 4.0
        # the ceiling flower: petals between ribs about 15 degrees apart (between the core columns), round a boss
        cols = sorted(math.radians(c) for c in COLUMN_ANGLES)
        ribs = []
        for c in range(len(cols)):
            a0, a1 = cols[c], cols[(c + 1) % len(cols)] + (TAU if c == len(cols) - 1 else 0)
            nn = max(1, round((a1 - a0) / math.radians(15)) - 1)
            ribs += [a0 + (a1 - a0) * k / (nn + 1) for k in range(1, nn + 1)]
        ribs.sort()
        ceil = y + h
        r_in, r_out = 7.2, s.r_inner_wall - 2.2
        for i, a in enumerate(ribs):
            b = ribs[(i + 1) % len(ribs)] + (TAU if i == len(ribs) - 1 else 0)
            mid, gap, ln = (a + b) / 2, b - a, r_out - r_in
            hw = min(1.6, max(0.4, (r_in + ln * 0.6) * gap * 0.5 - 0.9))
            along = self.r * np.cos(th - mid) - (r_in + ln / 2)
            across = self.r * np.sin(th - mid)
            petal = (along / (ln / 2)) ** 2 + (across / hw) ** 2 <= 1.0
            v.mask(ceil, ceil, petal, "minecraft:pearlescent_froglight")
        v.mask(ceil, ceil, (self.r < 4.4) & (self.r >= s.r_newel), "minecraft:pearlescent_froglight")
        # airlock passage through the shell toward the ramp
        a = AIRLOCK_ANGLE
        corridor = (np.abs(((self.theta - a + math.pi) % TAU) - math.pi) * self.r < 2.6) & self.ring(s.r_inner_wall - 1, self.R + 1)
        v.mask(y, y + 3, corridor, AIR)
        v.mask(y - 1, y - 1, corridor, "minecraft:polished_andesite")
        # the doorway through the shell is open; the station and the two thick doors are in the tunnel (surface.py)

    def generator_hall(self) -> None:
        """The generator hall below level 144 (machines.Builder, from the model)."""
        self.machines().generator_hall()

    def digger_void(self) -> None:
        """The digger void under the slab and the bore out of it (machines.Builder, from the model)."""
        self.machines().digger_void()

    def machines(self):
        if not hasattr(self, "_machines"):
            from machines import Builder
            self._machines = Builder(self)
        return self._machines

    def tunnel_volume(self) -> Volume:
        """The bore beyond this silo's volume, out to its door: a separate Volume in world coordinates."""
        import machines as mc
        b = mc.bearing(mc.TUN_PHI)
        r0, r1 = self.s.void_radius - 2, self.s.void_radius - 2 + mc.TUN_LEN + 1
        hw = mc.TUN_HW + 1.5
        pts = [(r * math.cos(b) - l * math.sin(b), r * math.sin(b) + l * math.cos(b)) for r in (r0, r1) for l in (-hw, hw)]
        x0, x1 = math.floor(min(p[0] for p in pts)) - 1, math.ceil(max(p[0] for p in pts)) + 1
        z0, z1 = math.floor(min(p[1] for p in pts)) - 1, math.ceil(max(p[1] for p in pts)) + 1
        H = int(round(mc.TUN_H))
        floor = self.yi(self.void_floor_rel)
        ox, oy, oz = self.origin
        vol = Volume((ox + self.R + x0, oy + floor - 1, oz + self.R + z0), (x1 - x0 + 1, H + 4, z1 - z0 + 1))
        self.machines().tunnel_into(vol, -x0, 1, -z0)
        # leave the part inside this silo's own volume to it
        inside = np.zeros((x1 - x0 + 1, z1 - z0 + 1), dtype=bool)
        X, Z = np.meshgrid(np.arange(x0, x1 + 1), np.arange(z0, z1 + 1), indexing="ij")
        inside = (np.abs(X) <= self.R) & (np.abs(Z) <= self.R)
        vol.ids.transpose(0, 2, 1)[inside] = 0
        return vol

