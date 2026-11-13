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

- the operator room at Silo 1's end of the line to Silo 18's server-room console: the "Algorithm" Bernard talks to is
  the voice of Silo 1's staff (Artem, 12.11 20:16; S2/S3).

At 1:1 (SPEC-1to1.md) Silo 1 has the same shaft, gallery, flats and level 1 as the others; only the fittings differ.

Not canon, for vanilla play: the lift cannot move, so a service ladder down the lift's outer wall, through a hatch in
each landing, keeps every level reachable on foot; invisible light blocks (level 7) keep the dark storage levels free
of mob spawns.
"""
from __future__ import annotations

import math

import numpy as np

import silo as base
from silo import AIR, GOLDEN, LEVELS, TAU, Silo, Spec

OPS = (2, 3)                 # double-height operations room, floor of level 3 (ours: "upper levels")
LEADERS = 4                  # director, Victor, Troy (ours)
QUARTERS = (5, 6)            # staff quarters (ours; a shift is a few dozen people)
CRYO = [(n, n + 1) for n in range(131, LEVELS, 2)]   # (gallery level, pod level) pairs (ours: "lower levels")
OPERATOR = 2                 # the operator room's level (ours)
LADDER_DEG = 64              # bearing of the service ladder on the lift's outer wall

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
        v.mask(self.level_y(1) + s.pitch + 1, top - 1, self.r < self.R, "minecraft:dirt")
        self.shell()
        for n in range(LEVELS, 0, -1):
            self.level(n)
        self.stair()
        self.dome()
        self.level_one()
        self.generator_hall()
        self.digger_void()
        self.specials()
        self.door_plates()
        import connect                          # panes, bars and wall parapets join up; orphan halves go
        connect.tidy(v)
        connect.connect(v)
        self.no_spawn_lights()
        self.service_ladder()
        import lighting
        void_top = self.yi(self.void_top_rel)
        self.lights = lighting.light_up(v, lambda y: 3 if y < void_top else 12)
        return v

    def specials(self) -> None:
        """Silo 1's own halls instead of the canon special levels of the other silos."""
        self.operations_room()
        self.operator_room()
        self.leaders()
        for upper, lower in CRYO:
            self.cryo_hall(upper, lower, wake=(upper, lower) == CRYO[0])

    # helpers -----------------------------------------------------------------------------------------------------
    def lateral(self, a: float) -> tuple[np.ndarray, np.ndarray]:
        d = self.off(a)
        return d * self.r, d

    def arc_cells(self, r: float, a0: float, a1: float, cx: float = 0.0, cz: float = 0.0) -> list[tuple[int, int]]:
        """Columns of the ring [r, r + 1) round (cx, cz) between angles a0 and a1 (radians), counter-clockwise."""
        dx, dz = self.X - cx, self.Z - cz
        d = np.hypot(dx, dz)
        ang = np.mod(np.arctan2(dz, dx) - a0, TAU)
        m = (d >= r) & (d < r + 1) & (ang < (a1 - a0) % TAU)
        xs, zs = np.nonzero(m)
        order = np.argsort(ang[xs, zs])
        return [(int(xs[i]), int(zs[i])) for i in order]

    @staticmethod
    def opposite(f: str) -> str:
        return {"east": "west", "west": "east", "north": "south", "south": "north"}[f]

    # levels: same construction, Silo 1 contents and light --------------------------------------------------------
    def level(self, n: int) -> None:
        super().level(n)
        s, v, y = self.s, self.v, self.level_y(n)
        # gallery lanterns: cold soul light instead of warm flame (all levels; the storage levels keep only these)
        walk = self.ring(s.r_atrium, s.r_facade)
        sl = v.ids[:, y:y + s.pitch, :]
        lantern = v.index.get(base.HANG)
        if lantern is not None:
            sl[(sl == lantern) & walk[:, None, :]] = v.id("minecraft:soul_lantern[hanging=true,waterlogged=false]")

    def home(self, n: int, y: int, f: dict, poor: bool) -> None:
        """Staff quarters: two white beds and a cool light; leaders' and operations levels: a desk; the rest of the
        depth is unlit storage (Russian fan wiki, from S3E10)."""
        v = self.v
        cells = [tuple(map(int, c)) for c in f["cells"]]
        if n in QUARTERS:
            super().home(n, y, f, False)
            return
        if n in OPS or n == LEADERS or n == OPERATOR:
            clear = self.keep_clear(f)
            free = [c for c in cells if c not in clear]
            if len(cells) > 6 and free:
                c = free[len(free) // 2]
                v.set(c[0], y, c[1], TABLE)
                v.set(c[0], y + 1, c[1], GLASS_BLUE)
            return
        if any(n in pair for pair in CRYO):
            return
        self.store(n, y, f)
        # storage is unlit: the flat's lamp goes (no_spawn_lights keeps it free of mobs)
        for c in cells:
            if v.get(c[0], y + self.s.pitch - 2, c[1]) == base.lamp_for(n):
                v.set(c[0], y + self.s.pitch - 2, c[1], AIR)

    # lift ----------------------------------------------------------------------------------------------------------
    def stair(self) -> None:
        """The core: a lift shaft (car about 4.5 m across, S3E10) in a thick wall, closed doors facing each level's
        landing, the car parked at level 1."""
        s, v = self.s, self.v
        r_car, r_wall = 2.5, s.r_stair_wall
        y_floor = self.yi(self.gen_floor_rel) - 1            # the shaft runs on down to the generator hall floor
        top = self.level_y(1) + s.pitch - 2
        v.mask(y_floor, top, self.ring(r_car, r_wall), WALL)
        v.mask(y_floor + 1, top, self.r < r_car, AIR)
        # the shaft under the parked car is closed on every level (lift doors shut): nobody is meant to stand in it
        self.walk_ignore_boxes.append((-3, y_floor, -3, 3, self.level_y(1) - 2, 3))
        v.mask(y_floor, y_floor, self.r < r_car, base.FLOOR_DEEP)
        for n in range(1, LEVELS + 1):
            y = self.level_y(n)
            lat, d = self.lateral(self.stair_angle(n))
            front = d < math.pi / 2
            door = (lat < 1.6) & front & self.ring(r_car, r_wall)
            v.mask(y, y + 2, door, AIR)
            leaf = door & self.ring(r_wall - 1, r_wall)
            v.mask(y, y + 2, leaf, AIR if n == 1 else METAL)
            v.mask(y + 3, y + 3, (lat < 0.6) & front & self.ring(r_wall - 1, r_wall), LED)   # call light
        y1 = self.level_y(1)
        v.mask(y1 - 1, y1 - 1, self.r < r_car, DARK)
        v.mask(y1 - 1, y1 - 1, self.ring(r_car - 0.8, r_car), LED)
        v.mask(y1 + 3, y1 + 3, self.ring(1.0, r_car), LED)
        v.mask(y1 + 3, y1 + 3, self.r < 1.0, PANEL)
        v.mask(y1 + 4, y1 + 4, self.r < r_car, WALL)

    def service_ladder(self) -> None:
        """Not canon: a ladder down the lift's outer wall, through a hatch in each level's landing, to the generator
        hall floor (the only way below level 144: the lift car is parked at level 1)."""
        s, v = self.s, self.v
        a = math.radians(LADDER_DEG)
        c, sn = math.cos(a), math.sin(a)
        if abs(c) >= abs(sn):
            step, facing = ((1, 0), "east") if c > 0 else ((-1, 0), "west")
        else:
            step, facing = ((0, 1), "south") if sn > 0 else ((0, -1), "north")
        # the first cell outside the lift wall along the bearing
        k = 1
        while math.hypot(k * step[0], k * step[1]) < s.r_stair_wall:
            k += 1
        lx, lz = self.R + k * step[0], self.R + k * step[1]
        bottom = self.yi(self.gen_floor_rel)                  # on down the shaft into the generator hall
        for y in range(bottom, self.level_y(1) + 1):
            v.set(lx, y, lz, f"minecraft:ladder[facing={facing},waterlogged=false]")

    # level 1 ----------------------------------------------------------------------------------------------------
    def cafeteria(self) -> None:
        """Silo 1's cafeteria: the same hall; long dark tables, pendant discs, the wallscreen showing old-world
        forest (S3E10), food dispensers marked CIBUM along the counter's arc instead of a kitchen."""
        super().cafeteria()
        s, v = self.s, self.v
        y = self.level_y(1)
        fl = y - 1
        hx, hz, hr = base.HALL
        hall = self.disc(hx, hz, hr - 1.0)
        v.mask(fl, y + 2, hall, AIR)
        v.mask(fl - 1, fl - 1, self.disc(hx, hz, hr), DARK)
        door_a = math.atan2(base.HALL_DOOR[1] - hz, base.HALL_DOOR[0] - hx) % TAU
        # long tables in tangential rows, chairs both sides, clear of the two entrances
        for rr in (4.5, 8.5):
            n_seg = int(TAU * rr / 7)
            for i in range(n_seg):
                a0 = i * TAU / n_seg
                for t in np.arange(0, 4.5 / rr, 0.5 / rr):
                    ang = a0 + t
                    if min(abs(((ang - g + math.pi) % TAU) - math.pi) * rr for g in (0.0, door_a, math.pi)) < 2.5:
                        continue
                    x, z = self.at(int(round(hx + rr * math.cos(ang))), int(round(hz + rr * math.sin(ang))))
                    v.set(x, fl, z, TABLE)
                    if int(t * rr) % 2 == 0:
                        for off, outward in ((1.2, True), (-1.2, False)):
                            xx, zz = self.at(int(round(hx + (rr + off) * math.cos(ang))), int(round(hz + (rr + off) * math.sin(ang))))
                            if v.get(xx, fl, zz) == AIR:
                                f = self.facing_radial(ang)
                                if not outward:
                                    f = self.opposite(f)
                                v.set(xx, fl, zz, f"minecraft:birch_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
        # pendant discs over the tables
        for rr in (6.5, 10.5):
            count = int(TAU * rr / 6)
            for i in range(count):
                x, z = self.at(int(round(hx + rr * math.cos((i + 0.5) * TAU / count))), int(round(hz + rr * math.sin((i + 0.5) * TAU / count))))
                v.set(x, y + 3, z, "minecraft:chain[axis=y,waterlogged=false]")
                v.set(x, y + 2, z, DISC)
        # the wallscreen: the forest mosaic over the screen's arc, rounded ends in black
        cells = self.arc_cells(hr - 1, math.pi - base.SCREEN_ARC / 2, math.pi + base.SCREEN_ARC / 2, hx + 0.5, hz + 0.5)
        cells = [c for c in cells if c[0] - self.R <= hx]
        rows = CAFE_SCREEN
        h_scr = 3
        w = len(cells)
        for i, (x, z) in enumerate(cells):
            col = int(i * len(rows[0]) / max(1, w))
            for j in range(h_scr):
                state = "minecraft:" + MOSAIC[rows[2 * j][col]]
                corner = (i in (0, w - 1)) and j in (0, h_scr - 1)
                v.set(x, fl + h_scr - j, z, INK if corner else state)
        # food dispensers along the counter's arc: LED band, lit window, dark body, cyan CIBUM header
        disp = self.arc_cells(hr - 3, door_a + 0.2, TAU - 0.2, hx + 0.5, hz + 0.5)
        for i, (x, z) in enumerate(disp):
            v.set(x, fl, z, AIR)
        disp = self.arc_cells(hr - 1, door_a + 0.2, TAU - 0.2, hx + 0.5, hz + 0.5)
        for i, (x, z) in enumerate(disp):
            ang = math.atan2(z - self.R - hz, x - self.R - hx)
            if i % 2:
                for dy in range(4):
                    v.set(x, fl + dy, z, INK)
                continue
            v.set(x, fl, z, LED)
            v.set(x, fl + 1, z, DISC)
            v.set(x, fl + 2, z, INK)
            v.set(x, fl + 3, z, LED)
            inward = self.opposite(self.facing_radial(ang))
            sx, sz = self.at(int(round(hx + (hr - 2) * math.cos(ang))), int(round(hz + (hr - 2) * math.sin(ang))))
            if v.get(sx, fl + 3, sz) == AIR:
                v.set(sx, fl + 3, sz, f"minecraft:dark_oak_wall_sign[facing={inward},waterlogged=false]", {
                    "id": "minecraft:sign", "is_waxed": True,
                    "front_text": {"messages": ['"CIBUM"', '""', '""', '""'], "color": "cyan", "has_glowing_text": True},
                    "back_text": {"messages": ['""', '""', '""', '""'], "color": "black", "has_glowing_text": False}})

    # operations room ------------------------------------------------------------------------------------------------
    def operations_room(self) -> None:
        """Round room over levels 2-3 at bearing 0: big screen on the far wall, central podium with a console, three
        consoles left and right on a raised ring edged with light, ceiling rings and radial slots (S3E10)."""
        s, v = self.s, self.v
        lo, hi = self.level_y(OPS[1]), self.level_y(OPS[0]) + s.pitch - 2      # floor row .. top air row
        rc = s.r_facade + 12
        ox, oz = self.polar(rc, 0.0)
        dx, dz = self.X - (ox - self.R), self.Z - (oz - self.R)
        d = np.hypot(dx, dz)
        room, wall = d < 10, (d >= 10) & (d < 11)
        v.mask(lo - 1, hi + 1, wall | room, WALL)
        v.mask(lo, hi, room, AIR)
        v.mask(lo - 1, lo - 1, room, FLOOR)
        door = (np.abs(self.Z) <= 1) & (self.X > 0) & (self.r >= s.r_facade - 0.5) & (d < 10.5)
        v.mask(lo, lo + 2, door, AIR)
        v.mask(lo - 1, lo - 1, door, FLOOR)
        tier = (d >= 5) & (d < 8.5) & (np.abs(dz) >= 3)
        v.mask(lo, lo, tier, DARK)
        v.mask(lo, lo, (d >= 5) & (d < 5.8) & (np.abs(dz) >= 3), LED)
        for side in (-1, 1):
            for ddx in (-3, 0, 3):
                x, z = ox + ddx, oz + side * 6
                v.set(x, lo + 1, z, TABLE)
                v.set(x, lo + 2, z + side, GLASS_BLUE)
                v.set(x, lo + 1, z + side, INK)
        v.box(ox + 1, lo, oz - 1, ox + 3, lo, oz + 1, LED)
        v.box(ox + 2, lo + 1, oz - 1, ox + 2, lo + 1, oz + 1, TABLE)
        v.box(ox + 3, lo + 1, oz - 1, ox + 3, lo + 2, oz + 1, GLASS_BLUE)
        sx = ox + 7
        w, h = len(OPS_SCREEN[0]), len(OPS_SCREEN)
        z0, y0 = oz - w // 2, lo + 2
        v.box(sx + 1, y0 - 1, z0 - 1, ox + 10, hi, z0 + w, WALL)        # up to the ceiling: no ledge behind it
        v.box(sx, y0 - 1, z0 - 1, sx, y0 + h, z0 + w, INK)
        v.box(sx, y0 + h + 1, z0 - 1, sx, hi, z0 + w, WALL)
        for j, row in enumerate(OPS_SCREEN):
            for i, ch in enumerate(row):
                v.set(sx, y0 + h - 1 - j, z0 + i, "minecraft:" + MOSAIC[ch])
        ang = np.mod(np.arctan2(dz, dx), TAU)
        v.mask(hi, hi, (d >= 1.5) & (d < 2.5), LED)
        v.mask(hi, hi, (d >= 8) & (d < 9), PANEL)
        v.mask(hi, hi, (d >= 3.5) & (d < 7) & (np.mod(ang + TAU / 16, TAU / 8) < 0.12), LED)

    def operator_room(self) -> None:
        """Silo 1's end of the line Bernard hears as the "Algorithm" (Artem, 12.11 20:16; S2 ew t1126s shows only
        Silo 18's end): a small round room off the level 2 gallery with one operator's console under a voice grille,
        a dark screen and a sign. Its look is ours: nothing shows it."""
        s, v = self.s, self.v
        y = self.level_y(OPERATOR)
        a = math.radians(60)
        ox, oz = self.polar(s.r_facade + 7, a)
        dx, dz = self.X - (ox - self.R), self.Z - (oz - self.R)
        d = np.hypot(dx, dz)
        room = d < 4.5
        v.mask(y - 1, y + 4, d < 5.6, WALL)
        v.mask(y, y + 3, room, AIR)
        v.mask(y - 1, y - 1, room, DARK)
        v.mask(y + 3, y + 3, (d >= 2) & (d < 3), LED)
        lane = self.lane(a, 1.0) & self.ring(s.r_facade - 0.5, s.r_facade + 4)
        v.mask(y, y + 2, lane, AIR)
        v.mask(y - 1, y - 1, lane, FLOOR)
        fx, fz = self.polar(s.r_facade + 0.5, a)
        self.steel_door(y, [(fx, fz)], self.facing_radial(a + math.pi))
        # console on the far side facing in: desk, screen, the grille the voice comes through
        far = self.facing_radial(a)
        cx, cz = self.polar(s.r_facade + 10, a)
        v.set(cx, y, cz, TABLE)
        v.set(cx, y + 1, cz, "minecraft:daylight_detector[inverted=false,power=0]")
        bx, bz = self.polar(s.r_facade + 11, a)
        v.set(bx, y + 1, bz, INK)
        v.set(bx, y + 2, bz, GLASS_BLUE)
        v.set(bx, y + 3, bz, "minecraft:waxed_copper_grate")
        hx, hz = self.polar(s.r_facade + 9, a)
        v.set(hx, y, hz, f"minecraft:dark_oak_stairs[facing={far},half=bottom,shape=straight,waterlogged=false]")
        sx, sz = self.polar(s.r_facade + 10, a + 0.12)
        v.set(sx, y + 2, sz, f"minecraft:dark_oak_wall_sign[facing={self.opposite(far)},waterlogged=false]", {
            "id": "minecraft:sign", "is_waxed": True,
            "front_text": {"messages": ['""', '"LINE 18"', '""', '""'], "color": "cyan", "has_glowing_text": True},
            "back_text": {"messages": ['""', '""', '""', '""'], "color": "black", "has_glowing_text": False}})

    # leaders --------------------------------------------------------------------------------------------------------
    def leaders(self) -> None:
        """Level 4: the director's salon (white sofas, lamps, dark shelving), Victor's office (desk, banker's lamp,
        bookshelves) and Troy's office (long desk, niche shelves), each in one front flat (S3E10)."""
        s, v = self.s, self.v
        y = self.level_y(LEADERS)
        for b, kind in ((2, "director"), (3, "victor"), (4, "troy")):
            a = self.bay_center(b)
            half = math.radians(10) - 0.5 / s.r_facade
            front = (self.off(a) < half) & self.ring(s.r_facade + 1, s.r_split)
            v.mask(y, y + 3, front, AIR)
            v.mask(y - 1, y - 1, front, WOOD)
            shelf = (self.off(a) < half - 0.03) & self.ring(s.r_split - 1, s.r_split)
            v.mask(y, y + 2, shelf, "minecraft:bookshelf")
            x, z = self.polar(s.r_facade + 4, a)
            if kind == "director":
                for k in (-0.22, 0.22):
                    ang = a + k * math.radians(20)
                    xs, zs = self.polar(s.r_facade + 4, ang)
                    f = self.facing_radial(ang + (math.pi / 2 if k > 0 else -math.pi / 2))
                    v.set(xs, y, zs, f"minecraft:quartz_stairs[facing={f},half=bottom,shape=straight,waterlogged=false]")
                v.set(x, y, z, TABLE)
                for k in (-0.35, 0.35):
                    xl, zl = self.polar(s.r_facade + 6, a + k * math.radians(20))
                    v.set(xl, y, zl, "minecraft:spruce_fence[waterlogged=false]")
                    v.set(xl, y + 1, zl, "minecraft:lantern[hanging=false,waterlogged=false]")
            else:
                v.set(x, y, z, TABLE)
                xx, zz = self.polar(s.r_facade + 4, a + 0.05)
                v.set(xx, y, zz, TABLE)
                v.set(x, y + 1, z, "minecraft:lantern[hanging=false,waterlogged=false]" if kind == "victor" else GLASS_BLUE)
                xc, zc = self.polar(s.r_facade + 5.2, a)
                f = self.facing_radial(a)
                v.set(xc, y, zc, f"minecraft:dark_oak_stairs[facing={self.opposite(f)},half=bottom,shape=straight,waterlogged=false]")
            v.set(x, y + 3, z, WARM)

    # cryo -------------------------------------------------------------------------------------------------------------
    def cryo_hall(self, upper: int, lower: int, wake: bool = False) -> None:
        """Two levels opened into one hall: pods in rows on the lower floor, the upper level keeps only a gallery
        with a solid parapet along the atrium side; orange wall slots, ceiling discs (S3E10)."""
        s, v = self.s, self.v
        yl, yu = self.level_y(lower), self.level_y(upper)
        top = yu + s.pitch - 2
        hall = self.ring(s.r_facade + 1, s.r_inner_wall)
        gallery_out = s.r_facade + 3
        v.mask(yl, top, hall, AIR)
        v.mask(yl - 1, yl - 1, hall, FLOOR)
        v.mask(yu, top, self.ring(s.r_facade, s.r_facade + 1), AIR)
        v.mask(yu - 1, yu - 1, self.ring(s.r_facade, gallery_out), FLOOR)
        v.mask(yu, yu, self.ring(gallery_out - 1, gallery_out), WALL)
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
        face = self.ring(s.r_inner_wall, s.r_inner_wall + 1)            # flush in the shell: no ledge to stand on
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
        cx, cz = self.polar(s.r_facade + 9, a)
        v.box(cx - 3, y, cz - 2, cx + 3, y + 2, cz + 2, AIR)
        v.box(cx - 2, y, cz - 1, cx + 2, y, cz + 1, LED)
        v.box(cx - 1, y + 1, cz, cx + 1, y + 1, cz, "minecraft:white_carpet")
        for dz in (-1, 1):
            v.box(cx - 2, y + 4, cz + dz, cx + 2, y + 4, cz + dz, "minecraft:end_rod[facing=east]")
        e = emblem(9)
        pz = cz + 4
        v.box(cx - 5, y, pz, cx + 5, y + 8, pz, PANEL)
        for j, row in enumerate(e):
            for i, ch in enumerate(row):
                if ch == "#":
                    v.set(cx - 4 + i, y + 8 - j, pz, INK)

    # mobs -----------------------------------------------------------------------------------------------------------
    def no_spawn_lights(self) -> None:
        """Invisible level-7 light blocks every 4 blocks at knee height behind the gallery: the storage levels stay
        dark to the eye, but no mob spawns there (vanilla spawns need block light 0)."""
        s, v = self.s, self.v
        grid = (np.mod(self.X, 4) == 0) & (np.mod(self.Z, 4) == 0) & self.ring(s.r_atrium, s.r_inner_wall)
        air = v.index.get(AIR)
        light = v.id(NO_SPAWN)
        for n in range(1, LEVELS + 1):
            yy = self.level_y(n) + 1
            row = v.ids[:, yy, :]
            row[grid & (row == air)] = light
