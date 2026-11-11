"""Silo 1, the control silo: the same shell as the other forty-nine, fitted out for the Project's staff.

Facts and their sources: /mnt/project-files/silo/silo1-canon.md (S3E09-S3E10 frames from the English and Russian
fan wikis, recaps, summaries of Shift). Only what differs from silo.Silo is here:

- a fast lift in the core instead of the spiral stair (show S3E10, Shift); the car is parked on level 1;
- level 1 cafeteria: long tables, pendant discs, radial ceiling coffers, a wallscreen showing old-world forest (not
  the outside) and food dispensers marked CIBUM instead of a kitchen;
- the operations room (round, big screen, podium and two tiers of consoles, ring-and-slot ceiling);
- the leaders' rooms (director's salon, Victor's office, Troy's office) in warm wood and lamps;
- staff quarters, then unlit storage for most of the depth (Russian fan wiki, from S3E10);
- cryo halls at the bottom: pods in rows under a gallery that leads to the lift, orange wall slots, ceiling discs,
  the wake pod under hanging linear lamps with the Project's emblem behind it.

Level numbers are not given by any source (only "upper" and "lower" levels); ours are in OPS, LEADERS, QUARTERS and
CRYO. The surface is unchanged: nothing shows Silo 1 different outside.

Not canon, for vanilla play: the lift cannot move, so a service ladder on one core column with a step to each walkway
keeps every level reachable on foot; invisible light blocks (level 7) keep the dark storage levels free of mob spawns.
"""
from __future__ import annotations

import math

import numpy as np

import silo as base
from silo import AIR, COLUMN_ANGLES, GOLDEN, LEVELS, TAU, Silo, Spec

OPS = (2, 3)                 # double-height operations room, floor of level 3 (ours: "upper levels")
LEADERS = 4                  # director, Victor, Troy (ours)
QUARTERS = (5, 6)            # staff quarters (ours; a shift is a few dozen people)
CRYO = [(n, n + 1) for n in range(131, LEVELS, 2)]   # (gallery level, pod level) pairs (ours: "lower levels")
LADDER_COLUMN = 64           # degrees: the core column that carries the service ladder

# palette: smooth, cool, dark blue-grey; LED edges; warm wood only in the leaders' rooms
WALL = "minecraft:light_gray_concrete"
DARK = "minecraft:gray_concrete"
PANEL = "minecraft:white_concrete"
INK = "minecraft:black_concrete"
METAL = "minecraft:iron_block"
FLOOR = "minecraft:smooth_stone"
LED = "minecraft:sea_lantern"
WARM = "minecraft:ochre_froglight"
DISC = "minecraft:pearlescent_froglight"
GLASS_BLUE = "minecraft:light_blue_stained_glass"
GRATE = base.GRATE
WOOD = "minecraft:dark_oak_planks"
TABLE = "minecraft:dark_oak_slab[type=top,waterlogged=false]"
NO_SPAWN = "minecraft:light[level=7,waterlogged=false]"
LADDER_STEP = "minecraft:polished_deepslate_slab[type=top,waterlogged=false]"

# Block mosaics sampled from S3E10 frames (exposure normalised, nearest vanilla colour in CIELAB, silhouettes in
# front of the screen skipped): the cafeteria screen (forest under sky, frame "Виктор и Трой в кафе", crop
# 470,300-1215,555) and the operations screen (drone feed of a crater with HUD, frame "Оперативная комната", crop
# 680,263-1315,538). Rows top to bottom.
MOSAIC = {
    "a": "white_concrete", "b": "light_gray_concrete", "e": "light_blue_concrete", "f": "cyan_concrete",
    "g": "green_concrete", "j": "white_terracotta", "k": "light_gray_terracotta", "l": "cyan_terracotta",
    "m": "light_blue_terracotta", "n": "green_terracotta", "o": "lime_terracotta", "u": "moss_block",
    "w": "calcite", "x": "tuff", "y": "stone", "G": "smooth_sandstone", "J": "light_blue_wool",
}
CAFE_SCREEN = [
    "JJeeJaaaaaaaaaaJJJJJJJJJJaayfflfflllllll",
    "JJJJJJJJJJJaaaJJJJJJJJJaaaabnxlxbnnbxnnn",
    "gffbffbffffffffffbbffffbnnoognllnnggggnn",
    "uuggffugffuuuugguuuggggggguugnlgnngggnnn",
    "ggfnffggguuuugnggguggllgnugnnnnggnnnnnnn",
    "ngnnfnnnggugngggguuggllgngngnnggnnnggnnn",
    "lnnnnnlllgggnggnggggggnnnnnnnnnnnnnkklll",
]
OPS_SCREEN = [
    "mmybjjjjbjbbym",
    "myjbybjjjbjbby",
    "myyyajjGjjbbyy",
    "mmyyawjjjjyymm",
    "myybaaajjyymmm",
    "yyybyyyyyyyymm",
]


def emblem(n: int = 9) -> list[str]:
    """The Project's sun emblem as an n x n stencil: a ring broken at upper right and lower left, a star of twelve
    rays round a filled centre (simplified from the panel in the S3E10 wake room frame)."""
    c = (n - 1) / 2
    rows = []
    for j in range(n):
        row = ""
        for i in range(n):
            dx, dz = i - c, c - j
            d = math.hypot(dx, dz)
            a = math.degrees(math.atan2(dz, dx)) % 360
            ring = abs(d - c) < 0.55 and not (40 < a < 70 or 220 < a < 250)
            star = d < 1.2 or (1.2 <= d < c - 1.3 and min(a % 30, 30 - a % 30) < 9)
            row += "#" if ring or star else "."
        rows.append(row)
    return rows


class Silo1(Silo):
    def __init__(self, spec: Spec | None = None, center_x: int = 0, surface_y: int = 70, center_z: int = 0):
        super().__init__(spec or Spec(number=1), center_x, surface_y, center_z)

    # build -------------------------------------------------------------------------------------------------------
    def build(self):
        s, v = self.s, self.v
        top = self.yi(0)
        v.mask(0, top - 1, self.r < self.R, base.ROCK)
        v.mask(self.yi(-s.cover // 2), top - 1, self.r < self.R, "minecraft:dirt")
        self.shell()
        for n in range(LEVELS, 0, -1):
            self.level(n)
        self.stair()
        self.cafeteria()
        self.generator_hall()
        self.digger_void()
        try:                                    # turbine, control room, steam hatch: the same plant in every silo
            from levels import Furnisher
            extras = getattr(Furnisher(self), "generator_extras", None)
            if extras:
                extras()
        except ImportError:
            pass
        self.operations_room()
        self.leaders()
        for upper, lower in CRYO:
            self.cryo_hall(upper, lower, wake=(upper, lower) == CRYO[0])
        self.no_spawn_lights()
        self.service_ladder()
        return v

    # helpers -----------------------------------------------------------------------------------------------------
    def lateral(self, a: float) -> tuple[np.ndarray, np.ndarray]:
        d = np.abs(((self.theta - a + math.pi) % TAU) - math.pi)
        return d * self.r, d

    def stencil(self, cells: list[tuple[int, int, int]], rows: list[str], legend: dict[str, str]) -> None:
        for (x, y, z), ch in zip(cells, "".join(rows)):
            if ch in legend:
                self.v.set(x, y, z, legend[ch])

    def arc_cells(self, r: float, a0: float, a1: float) -> list[tuple[int, int]]:
        """Columns of the ring [r, r + 1) between angles a0 and a1 (radians), ordered counter-clockwise."""
        m = self.sector(a0, a1) & self.ring(r, r + 1)
        xs, zs = np.nonzero(m)
        ang = (self.theta[xs, zs] - a0) % TAU
        order = np.argsort(ang)
        return [(int(xs[i]), int(zs[i])) for i in order]

    # levels: same construction, Silo 1 contents and light --------------------------------------------------------
    def level(self, n: int) -> None:
        super().level(n)
        s, v, y = self.s, self.v, self.level_y(n)
        # walkway lanterns: cold soul light instead of warm flame (all levels; the storage levels keep only these)
        walk = self.ring(s.r_walk_in, s.r_atrium)
        sl = v.ids[:, y:y + s.pitch, :]
        lantern = v.index.get("minecraft:lantern[hanging=true]")
        if lantern is not None:
            sl[(sl == lantern) & walk[:, None, :]] = v.id("minecraft:soul_lantern[hanging=true,waterlogged=false]")

    def room_contents(self, n: int, y: int, b: int) -> None:
        s, v = self.s, self.v
        bay_arc = TAU / s.bays
        a = (b + 0.5) * bay_arc
        if n in QUARTERS:
            for k in (-0.25, 0.25):                      # two beds per back room, cool ceiling light
                ang = a + k * bay_arc
                x, z = self.polar(s.r_inner_wall - 2.5, ang)
                f = self.facing_radial(ang)
                v.set(x, y, z, f"minecraft:white_bed[facing={f},part=head,occupied=false]", {"id": "minecraft:bed"})
                dx, dz = {"east": (-1, 0), "west": (1, 0), "south": (0, -1), "north": (0, 1)}[f]
                v.set(x + dx, y, z + dz, f"minecraft:white_bed[facing={f},part=foot,occupied=false]", {"id": "minecraft:bed"})
                x, z = self.polar(s.r_corridor_out + 6, ang)
                v.set(x, y + s.pitch - 2, z, DISC)
            x, z = self.polar(s.r_atrium + 5, a)
            v.set(x, y + s.pitch - 2, z, LED)
        elif n in OPS or n == LEADERS:
            self.office(y, a, bay_arc)
        elif not any(n in pair for pair in CRYO) and n > 1:
            # storage: barrels along the back rooms, no lamps
            for k in (-0.3, -0.15, 0.15, 0.3):
                for rr in (s.r_inner_wall - 1.5, s.r_inner_wall - 3.5):
                    x, z = self.polar(rr, a + k * bay_arc)
                    for dy in range(2):
                        v.set(x, y + dy, z, "minecraft:barrel[facing=up,open=false]", {"id": "minecraft:barrel"})

    def office(self, y: int, a: float, bay_arc: float) -> None:
        """A staff office in the front room: desk with a screen, chair, cool light."""
        s, v = self.s, self.v
        x, z = self.polar(s.r_atrium + 6, a)
        v.set(x, y, z, TABLE)
        v.set(x, y + 1, z, GLASS_BLUE)
        xc, zc = self.polar(s.r_atrium + 4.8, a)
        if (xc, zc) != (x, z):
            v.set(xc, y, zc, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
        x, z = self.polar(s.r_atrium + 5, a)
        v.set(x, y + s.pitch - 2, z, LED)
        for k in (-0.25, 0.25):
            x, z = self.polar(s.r_corridor_out + 6, a + k * bay_arc)
            v.set(x, y + s.pitch - 2, z, LED)

    # lift ----------------------------------------------------------------------------------------------------------
    def stair(self) -> None:
        """The core: a lift shaft (car about 4.5 m across, S3E10) in a thick wall, closed doors facing each level's
        bridge, the car parked at level 1. The six core columns stay (the pillars around the car in the frame)."""
        s, v = self.s, self.v
        r_car, r_wall = 2.5, s.r_stair_out
        y_floor = self.level_y(LEVELS) - 1
        top = self.level_y(1) + s.cafe_height - 1
        v.mask(y_floor, top, self.ring(r_car, r_wall), WALL)
        v.mask(y_floor + 1, top, self.r < r_car, AIR)
        v.mask(y_floor, y_floor, self.r < r_car, base.FLOOR_DEEP)
        for n in range(1, LEVELS + 1):
            y = self.level_y(n)
            lat, d = self.lateral((n * GOLDEN) % TAU)
            front = d < math.pi / 2
            door = (lat < 1.6) & front & self.ring(r_car, r_wall)
            v.mask(y, y + 2, door, AIR)
            leaf = door & self.ring(r_wall - 1, r_wall)
            v.mask(y, y + 2, leaf, AIR if n == 1 else METAL)
            v.mask(y + 3, y + 3, (lat < 0.6) & front & self.ring(r_wall - 1, r_wall), LED)   # call light
        # the car at level 1: floor with a ring of light round it, light ring in the ceiling
        y1 = self.level_y(1)
        v.mask(y1 - 1, y1 - 1, self.r < r_car, DARK)
        v.mask(y1 - 1, y1 - 1, self.ring(r_car - 0.8, r_car), LED)
        v.mask(y1 + 3, y1 + 3, self.ring(1.0, r_car), LED)
        v.mask(y1 + 3, y1 + 3, self.r < 1.0, PANEL)
        v.mask(y1 + 4, y1 + 4, self.r < r_car, WALL)
        for deg in COLUMN_ANGLES:
            cx, cz = self.polar(s.r_column_orbit, math.radians(deg))
            v.box(cx - 1, self.yi(self.gen_floor_rel), cz - 1, cx + 1, top, cz + 1, base.CONCRETE)

    def service_ladder(self) -> None:
        """Not canon: a ladder down the outer face of one core column, a step to each level's walkway."""
        s, v = self.s, self.v
        a = math.radians(LADDER_COLUMN)
        cx, cz = self.polar(s.r_column_orbit, a)
        c, sn = math.cos(a), math.sin(a)
        if abs(c) >= abs(sn):
            step, facing = ((1, 0), "east") if c > 0 else ((-1, 0), "west")
        else:
            step, facing = ((0, 1), "south") if sn > 0 else ((0, -1), "north")
        lx, lz = cx + 2 * step[0], cz + 2 * step[1]
        bottom = self.level_y(LEVELS) - 1
        for y in range(bottom, self.level_y(1) + 1):
            v.set(lx, y, lz, f"minecraft:ladder[facing={facing},waterlogged=false]")
        for n in range(1, LEVELS + 1):
            y = self.level_y(n)
            x, z = lx + step[0], lz + step[1]
            while math.hypot(x - self.R, z - self.R) < s.r_walk_in + 1.5:
                if v.get(x, y - 1, z) in (None, AIR):
                    v.set(x, y - 1, z, LADDER_STEP)
                for dy in range(3):
                    if v.get(x, y + dy, z) == base.RAIL:
                        v.set(x, y + dy, z, AIR)
                x, z = x + step[0], z + step[1]

    # level 1 ----------------------------------------------------------------------------------------------------
    def cafeteria(self) -> None:
        super().cafeteria()
        s, v = self.s, self.v
        y, h = self.level_y(1), s.cafe_height
        hall = self.ring(s.r_walk_in + 1, s.r_inner_wall - 1)
        v.mask(y, y + h - 1, hall, AIR)                                    # drop the ring tables and warm lamps
        v.mask(y - 1, y - 1, self.ring(s.r_walk_in, s.r_inner_wall), DARK)
        screen_lo = base.SCREEN_ANGLE - base.SCREEN_ARC / 2
        screen_hi = base.SCREEN_ANGLE + base.SCREEN_ARC / 2
        airlock_lat, airlock_d = self.lateral(base.AIRLOCK_ANGLE)
        airlock = (airlock_lat < 3.6) & (airlock_d < math.pi / 2)
        # long tables in tangential rows with chairs both sides (frame: long dark tables, light chairs)
        for r in (21, 26, 31, 36):
            n_seg = int(TAU * r / 13)
            for i in range(n_seg):
                a0 = i * TAU / n_seg
                for t in np.arange(0, 9.5 / r, 0.5 / r):
                    ang = a0 + t
                    x, z = self.polar(r, ang)
                    if airlock[x, z]:
                        continue
                    v.set(x, y, z, TABLE)
                    if int(t * r) % 2 == 0:
                        for off, outward in ((1.2, True), (-1.2, False)):
                            xx, zz = self.polar(r + off, ang)
                            if v.get(xx, y, zz) == AIR:
                                f = self.facing_radial(ang)
                                if not outward:
                                    f = {"east": "west", "west": "east", "north": "south", "south": "north"}[f]
                                v.set(xx, y, zz, f"minecraft:birch_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
        # pendant discs over the tables
        for r in (23.5, 33.5):
            count = int(TAU * r / 7)
            for i in range(count):
                x, z = self.polar(r, (i + 0.5) * TAU / count)
                v.set(x, y + h - 1, z, "minecraft:chain[axis=y,waterlogged=false]")
                v.set(x, y + h - 2, z, "minecraft:chain[axis=y,waterlogged=false]")
                v.set(x, y + h - 3, z, DISC)
        # radial "flower" coffers in the ceiling round a round light (frame), clear of the screen and the airlock
        for deg in (20, 80, 240, 300):
            ca = math.radians(deg)
            ox, oz = self.polar(29, ca)
            dx, dz = self.X - (ox - self.R), self.Z - (oz - self.R)
            d = np.hypot(dx, dz)
            ang = np.mod(np.arctan2(dz, dx), TAU)
            petal = (d >= 2.5) & (d < 7.5) & (np.mod(ang, TAU / 16) < TAU / 32)
            v.mask(y + h - 1, y + h - 1, (d < 2.0), LED)
            v.mask(y + h - 1, y + h - 1, petal, PANEL)
        # the wallscreen: a mosaic of the old-world forest view (S3E10), rounded ends in black
        cells = self.arc_cells(s.r_inner_wall - 1, screen_lo, screen_hi)
        rows = CAFE_SCREEN
        h_scr = len(rows)
        y0 = y + 2
        w = len(cells)
        for i, (x, z) in enumerate(cells):
            col = int(i * len(rows[0]) / w)
            for j in range(h_scr):
                state = "minecraft:" + MOSAIC[rows[j][col]]
                corner = (i in (0, w - 1)) and j in (0, h_scr - 1)
                v.set(x, y0 + h_scr - 1 - j, z, INK if corner else state)
            v.set(x, y0 - 1, z, INK)
            v.set(x, y0 + h_scr, z, INK)
        # food dispensers along the wall (no kitchen): LED band, lit window, dark body, cyan CIBUM header
        disp = self.arc_cells(s.r_inner_wall - 1, math.radians(50), math.radians(95))
        for i, (x, z) in enumerate(disp):
            ang = self.theta[x, z]
            if i % 2:
                for dy in range(4):
                    v.set(x, y + dy, z, INK)
                continue
            v.set(x, y, z, LED)
            v.set(x, y + 1, z, DISC)
            v.set(x, y + 2, z, INK)
            v.set(x, y + 3, z, LED)
            inward = {"east": "west", "west": "east", "north": "south", "south": "north"}[self.facing_radial(ang)]
            sx, sz = self.polar(self.r[x, z] - 1, ang)
            if v.get(sx, y + 3, sz) == AIR:
                v.set(sx, y + 3, sz, f"minecraft:dark_oak_wall_sign[facing={inward},waterlogged=false]", {
                    "id": "minecraft:sign", "is_waxed": True,
                    "front_text": {"messages": ['"CIBUM"', '""', '""', '""'], "color": "cyan", "has_glowing_text": True},
                    "back_text": {"messages": ['""', '""', '""', '""'], "color": "black", "has_glowing_text": False}})
            ex, ez = self.polar(self.r[x, z] - 1, ang + 0.6 / self.r[x, z])
            if v.get(ex, y + 1, ez) == AIR:
                v.set(ex, y + 1, ez, "minecraft:end_rod[facing=up]")

    # operations room ------------------------------------------------------------------------------------------------
    def operations_room(self) -> None:
        """Round room over levels 2-3 at angle 0: big screen on the far wall, central podium with a console, three
        consoles left and right on a raised ring edged with light, ceiling rings and radial slots (S3E10)."""
        s, v = self.s, self.v
        lo, hi = self.level_y(OPS[1]), self.level_y(OPS[0]) + s.pitch - 2      # floor row .. top air row
        rc = 29.5
        ox, oz = self.polar(rc, 0.0)
        dx, dz = self.X - (ox - self.R), self.Z - (oz - self.R)
        d = np.hypot(dx, dz)
        room, wall = d < 10, (d >= 10) & (d < 11)
        v.mask(lo, hi, room, AIR)
        v.mask(lo, hi, wall, WALL)
        v.mask(lo - 1, lo - 1, room, FLOOR)
        # doorway from the level 3 walkway through the front room
        door = (np.abs(self.Z) <= 1) & (self.X > 0) & (self.r >= s.r_atrium - 0.5) & (d < 10.5)
        v.mask(lo, lo + 2, door, AIR)
        v.mask(lo - 1, lo - 1, door, FLOOR)
        # raised ring for the side consoles, its edge lit
        tier = (d >= 5) & (d < 8.5) & (np.abs(dz) >= 3)
        v.mask(lo, lo, tier, DARK)
        v.mask(lo, lo, (d >= 5) & (d < 5.8) & (np.abs(dz) >= 3), LED)
        for side in (-1, 1):
            for k, ddx in enumerate((-3, 0, 3)):
                x, z = ox + ddx, oz + side * 6
                v.set(x, lo + 1, z, TABLE)
                v.set(x, lo + 2, z + side, GLASS_BLUE)
                v.set(x, lo + 1, z + side, INK)
        # podium with the main console facing the screen
        v.box(ox + 1, lo, oz - 1, ox + 3, lo, oz + 1, LED)
        v.box(ox + 2, lo + 1, oz - 1, ox + 2, lo + 1, oz + 1, TABLE)
        v.box(ox + 3, lo + 1, oz - 1, ox + 3, lo + 2, oz + 1, GLASS_BLUE)
        # the screen on the far wall (plane x = const), framed in black
        sx = ox + 7
        w, h = len(OPS_SCREEN[0]), len(OPS_SCREEN)
        z0, y0 = oz - w // 2, lo + 2
        v.box(sx + 1, y0 - 1, z0 - 1, ox + 10, y0 + h, z0 + w, WALL)
        v.box(sx, y0 - 1, z0 - 1, sx, y0 + h, z0 + w, INK)
        for j, row in enumerate(OPS_SCREEN):
            for i, ch in enumerate(row):
                v.set(sx, y0 + h - 1 - j, z0 + i, "minecraft:" + MOSAIC[ch])
        # ceiling: lit centre ring, an outer ring, radial slots between
        ang = np.mod(np.arctan2(dz, dx), TAU)
        v.mask(hi, hi, (d >= 1.5) & (d < 2.5), LED)
        v.mask(hi, hi, (d >= 8) & (d < 9), PANEL)
        v.mask(hi, hi, (d >= 3.5) & (d < 7) & (np.mod(ang + TAU / 16, TAU / 8) < 0.12), LED)

    # leaders --------------------------------------------------------------------------------------------------------
    def leaders(self) -> None:
        """Level 4: the director's salon (white sofas, lamps, dark shelving), Victor's office (desk, banker's lamp,
        bookshelves) and Troy's office (long desk, niche shelves), each in one bay's front room (S3E10)."""
        s, v = self.s, self.v
        n, y = LEADERS, self.level_y(LEADERS)
        bay_arc = TAU / s.bays
        for b, kind in ((2, "director"), (3, "victor"), (4, "troy")):
            a = (b + 0.5) * bay_arc
            front = self.sector(b * bay_arc + 0.5 / s.r_atrium, (b + 1) * bay_arc - 0.5 / s.r_atrium) \
                & self.ring(s.r_atrium + 1, s.r_corridor_in - 1)
            v.mask(y, y + 3, front, AIR)
            v.mask(y - 1, y - 1, front, WOOD)
            # shelving on the corridor-side wall
            shelf = self.sector(b * bay_arc + 0.6 / s.r_atrium, (b + 1) * bay_arc - 0.6 / s.r_atrium) \
                & self.ring(s.r_corridor_in - 2, s.r_corridor_in - 1)
            v.mask(y, y + 2, shelf, "minecraft:bookshelf")
            door_x, door_z = self.polar(s.r_corridor_in - 1.5, a)
            for dy in range(3):
                v.set(door_x, y + dy, door_z, AIR)
            x, z = self.polar(s.r_atrium + 5, a)
            if kind == "director":
                for k in (-0.22, 0.22):
                    ang = a + k * bay_arc
                    xs, zs = self.polar(s.r_atrium + 5, ang)
                    f = self.facing_radial(ang + (math.pi / 2 if k > 0 else -math.pi / 2))
                    v.set(xs, y, zs, f"minecraft:quartz_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
                v.set(x, y, z, TABLE)
                for k in (-0.35, 0.35):
                    xl, zl = self.polar(s.r_atrium + 7, a + k * bay_arc)
                    v.set(xl, y, zl, "minecraft:spruce_fence[waterlogged=false]")
                    v.set(xl, y + 1, zl, "minecraft:lantern[hanging=false,waterlogged=false]")
            else:
                v.set(x, y, z, TABLE)
                xx, zz = self.polar(s.r_atrium + 5, a + 0.12 * bay_arc)
                v.set(xx, y, zz, TABLE)
                v.set(x, y + 1, z, "minecraft:lantern[hanging=false,waterlogged=false]" if kind == "victor" else GLASS_BLUE)
                xc, zc = self.polar(s.r_atrium + 3.8, a)
                f = self.facing_radial(a)
                v.set(xc, y, zc, f"minecraft:dark_oak_stairs[facing={self.opposite(f)},half=bottom,shape=straight,waterlogged=false]")
            xl, zl = self.polar(s.r_atrium + 5, a)
            v.set(xl, y + 3, zl, WARM)

    @staticmethod
    def opposite(f: str) -> str:
        return {"east": "west", "west": "east", "north": "south", "south": "north"}[f]

    # cryo -------------------------------------------------------------------------------------------------------------
    def cryo_hall(self, upper: int, lower: int, wake: bool = False) -> None:
        """Two levels opened into one hall: pods in rows on the lower floor, the upper level keeps only a gallery
        with a solid parapet along the atrium side; orange wall slots, ceiling discs (S3E10)."""
        s, v = self.s, self.v
        yl, yu = self.level_y(lower), self.level_y(upper)
        top = yu + s.pitch - 2
        hall = self.ring(s.r_atrium + 1, s.r_inner_wall)
        gallery_out = s.r_atrium + 3
        v.mask(yl, top, hall, AIR)
        v.mask(yl - 1, yl - 1, hall, FLOOR)
        # the upper floor stays only as the gallery, its front wall gone, a solid parapet on its edge
        v.mask(yu, top, self.ring(s.r_atrium, s.r_atrium + 1), AIR)
        v.mask(yu - 1, yu - 1, self.ring(s.r_atrium, gallery_out), FLOOR)
        v.mask(yu, yu, self.ring(gallery_out - 1, gallery_out), WALL)
        # pods: oval capsules two blocks long on a lit head, blue glass lids
        for x in range(0, 2 * self.R + 1):
            for z in range(0, 2 * self.R + 1):
                if (x - self.R) % 4 or (z - self.R) % 3:
                    continue
                rr = self.r[x, z]
                if not (gallery_out + 1.5 < rr < s.r_inner_wall - 3):
                    continue
                v.set(x, yl, z, LED)
                v.set(x + 1, yl, z, "minecraft:polished_deepslate")
                v.set(x, yl + 1, z, GLASS_BLUE)
                v.set(x + 1, yl + 1, z, GLASS_BLUE)
        # orange slots along the outer wall, two rows; round discs in the ceiling, every third one lit
        face = self.ring(s.r_inner_wall, s.r_inner_wall + 1)
        slot = face & (np.mod(self.theta * s.r_inner_wall, 4) < 2.5)
        for yy in (yl + 3, yl + 6):
            v.mask(yy, yy, slot, WARM)
        grid = (np.mod(self.X, 6) == 0) & (np.mod(self.Z, 6) == 0) & self.ring(gallery_out, s.r_inner_wall - 1)
        lit = grid & (np.mod((self.X + self.Z) // 6, 3) == 0)
        v.mask(top, top, grid & ~lit, PANEL)
        v.mask(top, top, lit, LED)
        if wake:
            self.wake_room(yl)

    def wake_room(self, y: int) -> None:
        """The wake pod on a lit oval pedestal, linear lamps hung over it, the emblem panel behind (S3E10)."""
        s, v = self.s, self.v
        a = math.radians(90)
        cx, cz = self.polar(s.r_atrium + 9, a)
        v.box(cx - 3, y, cz - 2, cx + 3, y + 2, cz + 2, AIR)
        v.box(cx - 2, y, cz - 1, cx + 2, y, cz + 1, LED)
        v.box(cx - 1, y + 1, cz, cx + 1, y + 1, cz, "minecraft:white_carpet")
        for dz in (-1, 1):
            v.box(cx - 2, y + 4, cz + dz, cx + 2, y + 4, cz + dz, "minecraft:end_rod[facing=east]")
        # emblem panel on a free-standing white wall beyond the pod
        e = emblem(9)
        pz = cz + 4
        v.box(cx - 5, y, pz, cx + 5, y + 8, pz, PANEL)
        for j, row in enumerate(e):
            for i, ch in enumerate(row):
                if ch == "#":
                    v.set(cx - 4 + i, y + 8 - j, pz, INK)

    # mobs -----------------------------------------------------------------------------------------------------------
    def no_spawn_lights(self) -> None:
        """Invisible level-7 light blocks every 4 blocks at knee height in every room ring: the storage levels stay
        dark to the eye, but no mob spawns there (vanilla spawns need block light 0)."""
        s, v = self.s, self.v
        grid = (np.mod(self.X, 4) == 0) & (np.mod(self.Z, 4) == 0) & self.ring(s.r_walk_in, s.r_inner_wall)
        air = v.index.get(AIR)
        light = v.id(NO_SPAWN)
        for n in range(1, LEVELS + 1):
            yy = self.level_y(n) + 1
            row = v.ids[:, yy, :]
            row[grid & (row == air)] = light
