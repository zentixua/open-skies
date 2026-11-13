"""Canon special levels of a silo, furnished from the explorethesilo.com model over the levels built by silo.Silo.level.

Source: silo3d.js (explorethesilo.com, taken apart for private use with Artem's permission): ROOM_BUILDERS it,
watcher, market, judicial, workshop (room-local metres: x across the bay, z into the rock from ROOM_Z0), the sheriff's
station by the airlock, dressingFor/variantFor (bays.py). Level list: levels.js (canon: true only).

Rooms stand behind the special bay (bays.ROOM_BAY, bearing 0, so a room's depth runs along world +x and its x across
along world +z) at 1 m = 1 block in plan; heights fall into the level's four clear rows (1 m each). Room-local x, s
(depth from the room's front wall) map to cells by cell(): d = 18 + floor(s) from the axis, c = floor(x + W/2) - W//2.
Where the model's rooms chain deeper than the 26 blocks between the shaft wall (r 17) and the shell (r 43), the chain
is folded sideways and the fold is named at the room. The 1:1 silo's facade stands at r 24 (silo.Spec.r_facade), so
every d here is moved out by SHIFT; rooms keep the model's four clear rows, and the level's fifth row over them is
closed as their ceiling. Model colours are matched to the nearest vanilla block.
"""
from __future__ import annotations

import math

import numpy as np

TAU = 2 * math.pi
GOLDEN = math.radians(137.5)          # bridge rotation per level, as silo.GOLDEN
AIR = "minecraft:air"
DIRS = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}   # world (dx, dz): east = +d, south = +c
OPP = {"east": "west", "west": "east", "south": "north", "north": "south"}
PLATE = "minecraft:heavy_weighted_pressure_plate[power=0]"
SLAB_TOP = "minecraft:spruce_slab[type=top,waterlogged=false]"
SEA = "minecraft:sea_lantern"
HANG = "minecraft:lantern[hanging=true,waterlogged=false]"
LANTERN = "minecraft:lantern[hanging=false,waterlogged=false]"

# Terracotta and concrete colours (block top textures, averaged) for matching model colours.
TERRACOTTA = {"white": (209, 178, 161), "orange": (161, 83, 37), "yellow": (186, 133, 35), "light_gray": (135, 107, 98),
              "cyan": (86, 91, 91), "blue": (74, 59, 91), "brown": (77, 51, 35), "green": (76, 83, 42), "red": (143, 61, 46),
              "gray": (57, 42, 35), "lime": (103, 117, 53), "purple": (118, 70, 86), "magenta": (149, 88, 108),
              "pink": (161, 78, 78), "light_blue": (113, 108, 137), "black": (37, 22, 16)}


def nearest(rgb, table: dict) -> str:
    return min(table, key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb, table[k])))


def stairs(facing: str) -> str:
    return f"minecraft:spruce_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]"


class Furnisher:
    def __init__(self, silo):
        self.silo, self.s, self.v = silo, silo.s, silo.v
        self.R = silo.R
        self.D = int(silo.s.r_facade) - 17                 # the model's front wall (r 17) to ours
        self.top = silo.s.pitch - 2                        # the level's highest clear row
        self.n = 1
        self.y = silo.level_y(1)

    # cells ------------------------------------------------------------------------------------------------------
    def on(self, n: int) -> "Furnisher":
        self.n, self.y = n, self.silo.level_y(n)
        return self

    @staticmethod
    def cell(x: float, s: float, W: int, d0: int = 18, cshift: int = 0) -> tuple[int, int]:
        return d0 + math.floor(s), math.floor(x + W / 2) - W // 2 + cshift

    def blk(self, d: int, c: int, dy: int, state: str) -> None:
        self.v.set(self.R + self.D + d, self.y + dy, self.R + c, state)

    def get(self, d: int, c: int, dy: int) -> str:
        return self.v.get(self.R + self.D + d, self.y + dy, self.R + c)

    def box(self, d0, d1, c0, c1, dy0, dy1, state) -> None:
        d0, d1 = sorted((d0, d1))
        c0, c1 = sorted((c0, c1))
        self.v.box(self.R + self.D + d0, self.y + dy0, self.R + c0, self.R + self.D + d1, self.y + dy1, self.R + c1, state)

    def room(self, d0, d1, c0, c1, wall: str, floor: str, rows: int = 4, ceiling: str | None = None) -> None:
        """A walled room with interior cells d0..d1 x c0..c1: walls one block thick on all sides, floor under it,
        `rows` clear rows and a ceiling filling the rest of the level's four rows."""
        far = max(math.hypot(d + self.D, c) for d in (d0 - 1, d1 + 1) for c in (c0 - 1, c1 + 1))
        if far >= self.s.r_inner_wall:
            raise ValueError(f"room reaches r {far:.1f} on level {self.n}")
        self.box(d0 - 1, d1 + 1, c0 - 1, c1 + 1, 0, self.top, wall)
        self.box(d0, d1, c0, c1, 0, rows - 1, AIR)
        if rows < 4:
            self.box(d0, d1, c0, c1, rows, 3, ceiling or wall)
        self.box(d0, d1, c0, c1, -1, -1, floor)

    def entry(self) -> None:
        """The special bay's door (BAY.roomDoor) through the shaft wall into a room whose walls rebuilt that wall."""
        self.door(17, 0, "west")

    def door(self, d: int, c: int, facing: str, width: int = 1, plates: bool = True, hinge: str = "left") -> None:
        """Iron door(s) at (d, c) facing `facing`; a pair runs to the door's right. Heavy plates open them."""
        fd, fc = DIRS[facing]
        rd, rc = -fc, fd                       # right hand when looking along facing (x east, z south)
        cells = [(d + i * rd, c + i * rc) for i in range(width)]
        for i, (dd, cc) in enumerate(cells):
            h = hinge if i == 0 else ("right" if hinge == "left" else "left")
            for half, dy in (("lower", 0), ("upper", 1)):
                self.blk(dd, cc, dy, f"minecraft:iron_door[facing={facing},half={half},hinge={h},open=false,powered=false]")
            if plates:
                for k in (1, -1):
                    pd, pc = dd + k * fd, cc + k * fc
                    if self.get(pd, pc, 0) == AIR:
                        self.blk(pd, pc, 0, PLATE)

    # levels -----------------------------------------------------------------------------------------------------
    def all(self) -> None:
        self.judicial(14)                 # "Level 14" Judicial and the Safeguard pipe (S2E10; layout-facts.md)
        self.it(19)
        self.watcher(20)
        self.checkpoint(30)
        for n in (50, 62):
            self.medical(n)
        self.filtration(55)               # "ten levels up on 55 ... water filtration" (S3E09; layout-facts.md)
        self.market(100)
        self.deputy_station(105)
        for n in (80, 122):
            self.farm(n)
        self.barricade(130)
        self.workshop(144)

    def judicial(self, n: int) -> None:
        """Judicial's Seclusion Holding (model judicial(), from the Season 2 set): a long narrow concrete corridor on
        a steel grate, round sealed hatches down the left wall, pipes along the right, cold panels overhead; at its
        end a square cell with a tiled floor, a caged door and light falling through a ceiling grille."""
        self.on(n)
        W, D = 3, 13                                         # model W 3.4, D 13, H 3.3
        dark = "minecraft:gray_concrete"
        self.room(18, 30, -1, 1, dark, "minecraft:polished_deepslate", rows=3)
        self.entry()
        self.box(18, 30, -1, 1, 0, 0, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
        for s in (2.2, 5.4, 8.6, 11.4):                      # hatches: sealed, no plates, solid behind
            d, _ = self.cell(0, s, W)
            self.blk(d, -2, 0, "minecraft:iron_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
            self.blk(d, -2, 1, "minecraft:iron_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
            self.box(d, d, -3, -3, 0, 1, dark)
        for d in range(18, 31):                              # pipes along the right wall: 2.75 / 2.98 m and 0.35 m
            self.blk(d, 1, 2, "minecraft:lightning_rod[facing=east,powered=false,waterlogged=false]")
        z = 1.2
        while z < D - 0.5:                                   # dark ribs every 1.6 m on both walls
            d, _ = self.cell(0, z, W)
            for c in (-2, 2):
                if self.get(d, c, 0) == dark:
                    self.box(d, d, c, c, 0, 2, "minecraft:polished_deepslate")
            z += 1.6
        z = 1.6
        while z < D - 1:                                     # cold panels overhead every 2.8 m
            d, _ = self.cell(0, z, W)
            self.blk(d, 0, 3, SEA)
            z += 2.8
        # the cell: CW 4.4 x CD 4.4, CH 3.6, through a narrow open door 1.5 x 2.3 at the corridor's end
        self.room(32, 35, -2, 1, dark, "minecraft:deepslate_tiles", rows=3)
        self.box(31, 31, 0, 0, 0, 1, AIR)
        self.blk(31, 0, -1, "minecraft:polished_deepslate")
        self.box(33, 34, 0, 0, 3, 3, "minecraft:iron_bars")   # the grille, and daylight-coloured light over it
        self.box(33, 34, 0, 0, 4, 4, SEA)
        self.box(33, 34, -3, -3, 0, 1, "minecraft:iron_bars")  # the caged door in the cell's left wall
        self.box(33, 34, -4, -4, 0, 1, dark)
        # the Safeguard line: where the pipes from Silo 1 enter the silo ("This is where the pipes enter each of the
        # silos", S3E08; "Level 14", S2E10). Not seen on screen in detail: a copper trunk out of the cell's back wall,
        # along the ceiling to a valve wheel (a lever on the pipe) over the corridor's end
        PIPE = "minecraft:waxed_oxidized_cut_copper"
        self.box(36, 36, 1, 1, 2, 3, PIPE)                    # through the back wall
        self.box(32, 35, 1, 1, 2, 2, PIPE)
        self.blk(31, 1, 2, "minecraft:waxed_oxidized_copper_bulb[lit=false,powered=false]")
        self.blk(31, 0, 2, "minecraft:lever[face=wall,facing=west,powered=false]")

    def it(self, n: int) -> None:
        """IT (model it()): the offices under a radiating light, the server room, the Vault, the Head of IT's office.
        The model chains offices (14 m), server room (12 m) and vault (13.4 m) straight back, 41 m; here the offices
        and the server room keep the line and the vault opens off the server room's left wall."""
        self.on(n)
        paint = "minecraft:polished_tuff"                   # wall paint 0x7c877e, grey-green
        con = "minecraft:light_gray_concrete"
        W = 15                                              # offices HW 15 x HD 14 x HH 4.6
        self.room(18, 31, -7, 7, paint, "minecraft:polished_andesite")
        self.entry()
        dc, cc = 24, 0                                      # the room's centre (zh)
        for d in (24, 25):                                  # round light 1.5 m in the centre
            for c in (-1, 0, 1):
                self.blk(d, c, 3, SEA)
        for k in range(8):                                  # eight light planes at 3.9 m between eight beams
            a = k * math.pi / 4 + math.pi / 8
            self.blk(round(dc + 0.5 + math.cos(a) * 3.9), round(math.sin(a) * 3.9), 3, SEA)
            a3 = a                                          # eight columns at 6.4 across, 6.0 deep
            self.box(round(dc + 0.5 + math.cos(a3) * 6.0), round(dc + 0.5 + math.cos(a3) * 6.0),
                     round(math.sin(a3) * 6.4), round(math.sin(a3) * 6.4), 0, 3, paint)
        for c in (-8, 8):                                   # arched recesses and round lamps on the side walls
            z = 1.2
            while z < 14 - 0.6:
                d, _ = self.cell(0, z, W)
                if not (c > 0 and abs(d - 24.5) < 1.4):
                    self.box(d, d, c, c, 0, 1, "minecraft:black_concrete")
                    dl, _ = self.cell(0, z + 0.85, W)
                    self.blk(dl, c, 3, "minecraft:shroomlight")
                z += 1.75
        for x in (-5.2, -2.9, 2.9, 5.2):                    # desks with a beige monitor, a task lamp and a chair
            for dz in (3.4, 0.4, -2.6, -5.2):
                if x > 0 and abs(dz) < 1:
                    continue
                d = 24 - round(dz)
                c0 = round(x - 0.4)
                for c in (c0, c0 + 1):
                    self.blk(d, c, 0, SLAB_TOP)
                self.blk(d, c0, 1, "minecraft:smooth_sandstone_slab[type=bottom,waterlogged=false]")
                self.blk(d, c0 + 1, 1, LANTERN)
                self.blk(d - 1, c0, 0, stairs("west"))
        # server room (S2 ew t1126s): round, tiered racks stepping up round the wall, a ring light in the ceiling, a
        # raised dais on the far side with the console Bernard uses to talk to the "Algorithm" (the line to Silo 1's
        # operator room, silo1.Silo1.operator_room). Ø11 here, through a double door in the offices' back wall.
        self.server_room()
        # the Vault, D 13.4 x 13 x H 4.4: a round stepped bowl round a lit pedestal, behind a heavy door
        self.room(29, 39, -19, -9, con, "minecraft:polished_andesite")
        vd, vc = 34, -14
        prof = [(6.3, 4), (6.02, 4), (5.72, 3), (5.42, 3), (5.1, 2), (4.78, 2), (4.5, 1)]
        for d in range(29, 40):
            for c in range(-19, -8):
                r = math.hypot(d + 0.5 - (vd + 0.5), c + 0.5 - (vc + 0.5))
                if r >= 5.2:
                    self.box(d, d, c, c, 0, 3, con)
                elif r >= 4.6:
                    self.box(d, d, c, c, 0, 1, con)         # the stepped tiers: two risers, then the wall
                elif r >= 4.1:
                    self.blk(d, c, 0, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
        for d in (vd - 1, vd, vd + 1):
            for c in (vc - 1, vc, vc + 1):
                self.blk(d, c, 3, SEA)                      # the round light 2.3 m over the middle
        self.blk(vd + 1, vc, 0, "minecraft:polished_andesite")          # the pedestal 2.7 m wide, 0.34 m high
        for c in (vc - 1, vc + 1):
            self.blk(vd + 1, c, 0, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
        self.box(vd + 2, vd + 2, vc - 1, vc + 1, 1, 2, "minecraft:light_blue_stained_glass")   # the hologram 3.7 x 2.3
        self.box(36, 37, -8, -5, 0, 2, AIR)                 # passage from the server room's left wall
        self.box(36, 37, -8, -5, -1, -1, "minecraft:polished_andesite")
        self.box(35, 38, -8, -5, 3, 3, con)
        self.box(35, 35, -8, -5, 0, 2, con)
        self.box(38, 38, -8, -5, 0, 2, con)
        self.door(36, -5, "south", width=2)
        self.blk(36, -4, 3, SEA)                            # the fitting in front of the vault door
        self.box(36, 37, -9, -9, 0, 1, AIR)
        # the Head of IT's office: corridor 2.2 x 5 off the offices' right wall, office 7.2 x 6.4 x 3.2
        self.room(24, 25, 9, 12, paint, "minecraft:polished_andesite", rows=3)
        self.door(24, 8, "north", width=2, hinge="right")
        self.room(21, 27, 14, 20, paint, "minecraft:dark_oak_planks", rows=3)
        self.door(24, 13, "north")
        for d in range(21, 28):                             # shelves of books along the back wall
            self.box(d, d, 20, 20, 0, 2, "minecraft:bookshelf")
        for c in range(15, 19):                             # and along the side
            self.box(21, 21, c, c, 0, 2, "minecraft:bookshelf")
        for d in (22, 23, 24):
            self.blk(d, 18, 0, "minecraft:dark_oak_slab[type=top,waterlogged=false]")       # the desk
        self.blk(23, 19, 0, "minecraft:spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        self.blk(22, 18, 1, LANTERN)
        for c in (15, 16, 17):                              # sofa, two armchairs and a low table on a rug
            self.blk(27, c, 0, "minecraft:dark_oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
        self.blk(25, 15, 0, "minecraft:dark_oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        self.blk(25, 17, 0, "minecraft:dark_oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        self.blk(26, 16, 0, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
        for d, c in ((25, 16), (26, 15), (26, 17)):
            self.blk(d, c, 0, "minecraft:red_carpet")
        self.blk(24, 17, 2, HANG)

    def server_room(self) -> None:
        con = "minecraft:light_gray_concrete"
        dc, cc, R = 37.5, 0.5, 5.5
        self.box(31, 44, -6, 7, 0, self.top, con)
        cells = [(d, c) for d in range(32, 44) for c in range(-5, 7) if math.hypot(d + 0.5 - dc, c + 0.5 - cc) < R]
        for d, c in cells:
            self.box(d, d, c, c, 0, 3, AIR)
            self.blk(d, c, -1, "minecraft:polished_deepslate")
        for d, c in cells:
            r = math.hypot(d + 0.5 - dc, c + 0.5 - cc)
            a = math.degrees(math.atan2(c + 0.5 - cc, d + 0.5 - dc))
            if abs(a) < 40:                                  # the dais and the console, far side
                if r >= 2.5:
                    self.blk(d, c, 0, "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
                continue
            if r >= 4.6:                                     # racks, two tiers stepping up toward the wall
                self.box(d, d, c, c, 0, 2, "minecraft:observer[facing=up,powered=false]")
                if (d + c) % 2 == 0:                         # lit rack panels (S2 ew t1126s: the racks glow)
                    self.blk(d, c, 1, "minecraft:waxed_oxidized_copper_bulb[lit=true,powered=false]")
            elif r >= 3.7 and abs(a) > 140:
                continue                                     # the way in
            elif r >= 3.7:
                self.blk(d, c, 0, "minecraft:observer[facing=up,powered=false]")
            if 2.0 <= r < 3.0:
                self.blk(d, c, 3, SEA)                       # the ring light
        self.blk(41, 0, 1, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")   # the console
        self.blk(41, 1, 1, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
        self.blk(42, 0, 2, "minecraft:daylight_detector[inverted=false,power=0]")
        self.blk(42, 0, 1, "minecraft:black_concrete")
        self.blk(42, 1, 1, "minecraft:black_concrete")
        self.blk(42, 1, 2, "minecraft:waxed_copper_grate")
        self.blk(40, 0, 1, stairs("east"))
        # the room's box (from d 31) takes the offices' last row: the way in goes through it to the door at d 32
        self.box(31, 32, 0, 1, 0, 1, AIR)
        self.door(32, 0, "west", width=2, hinge="right")

    def watcher(self, n: int) -> None:
        """Recycling's janitorial closet and, through its back door, the Watcher Room (model watcher()): two tiers of
        angled monitors on an arc of 6.2 m, a curved console desk at 5 m, swivel chairs at 3.9 m, a round light."""
        self.on(n)
        con, paint = "minecraft:light_gray_concrete", "minecraft:gray_concrete"
        self.room(18, 19, -1, 1, con, "minecraft:polished_andesite", rows=3)   # closet 3.2 x 2.4 x 3.6
        self.entry()
        for c in (-1, 1):                                   # shelves of boxes both sides at 0.9, 1.6, 2.3 m
            for d in (18, 19):
                self.blk(d, c, 0, "minecraft:barrel[facing=up,open=false]")
                self.blk(d, c, 1, SLAB_TOP)
                self.blk(d, c, 2, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        self.blk(19, -1, 0, "minecraft:cauldron")         # the mop bucket
        self.blk(18, 0, 2, HANG)
        W, R = 13, 6.2                                      # room 13.4 x 9.0 x 4.6, arc centre 1.2 m in
        self.room(21, 29, -6, 6, paint, "minecraft:polished_deepslate")
        self.blk(20, 0, 0, AIR)
        self.blk(20, 0, 1, AIR)
        cd, cc = 21 + 1.2, 0.5                              # arc centre in cell coordinates
        for d in range(21, 30):
            for c in range(-6, 7):
                dx, dz = d + 0.5 - cd, c + 0.5 - cc
                r, a = math.hypot(dx, dz), math.degrees(math.atan2(dz, dx))
                if abs(a) > 82:
                    continue
                if r >= R - 0.5 and r < R + 0.5:
                    self.blk(d, c, 2, "minecraft:gray_stained_glass")     # monitors, two tiers at 2.3 and 3.3 m
                    self.blk(d, c, 3, "minecraft:gray_stained_glass")
                    self.blk(d, c, 1, paint)
                    self.blk(d, c, 0, paint)
                elif r >= R + 0.5:
                    self.box(d, d, c, c, 0, 1, paint)
                    self.box(d, d, c, c, 2, 3, SEA)                        # the feeds' glow behind the screens
                elif 4.55 <= r < 5.65 and abs(a) < 76:
                    self.blk(d, c, 0, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")   # the desk
                    if 5.0 <= r:
                        self.blk(d, c, 1, "minecraft:daylight_detector[inverted=false,power=0]")      # consoles
                elif 1.45 <= r < 2.25:
                    self.blk(d, c, 3, SEA)                                       # the round ceiling light
        for k in range(7):                                  # swivel chairs at 3.9 m, -60..60 degrees, facing the screens
            a = math.radians(-60 + 20 * k)
            d, c = math.floor(cd + 3.9 * math.cos(a)), math.floor(cc + 3.9 * math.sin(a))
            back = self.silo.facing_radial(a + math.pi)       # the back toward the arc's centre
            self.blk(d, c, 0, stairs(back))

    def market(self, n: int) -> None:
        """The Market (model market()): a narrow alley with a long food counter under red pendant shades, and the
        Traders' Hall of six family pitches. The model's hall lies behind the alley (16 + 12.5 m); here it opens off
        the alley's left wall at its centre line."""
        self.on(n)
        con, dark = "minecraft:light_gray_concrete", "minecraft:gray_concrete"
        self.room(18, 33, -2, 1, con, "minecraft:polished_andesite")             # alley 4.2 x 16 x 4.8
        self.entry()
        for d in range(20, 32):                                                  # the counter, 1.05 m, 11 m long
            self.blk(d, 1, 0, "minecraft:stripped_spruce_wood[axis=x]")
        for d in (19, 22, 25, 28, 31):                                           # pillars every 3 m
            self.box(d, d, -2, -2, 0, 3, "minecraft:polished_andesite")
            self.box(d, d, 2, 2, 0, 3, "minecraft:polished_andesite")
        self.blk(24, 1, 1, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")  # pretzel stand
        self.blk(21, 1, 1, "minecraft:cauldron")                                # the urn with its tap
        self.blk(22, 1, 1, "minecraft:flower_pot")                              # metal cups
        for s in (2.5, 5.7, 8.9, 12.1):                                          # red shades with their bulbs
            d, _ = self.cell(0, s, 4)
            self.blk(d, -1, 3, "minecraft:red_stained_glass")
            self.blk(d, -1, 2, HANG)
        # the traders' hall TW 9 x TD 12.5 x TH 5.4: across runs along d (25..33), depth along -c from the alley
        self.room(25, 33, -15, -4, dark, "minecraft:spruce_planks")
        self.box(29, 30, -3, -3, 0, 1, AIR)                                     # doorway 1.8 x 2.6
        self.box(29, 30, -3, -3, -1, -1, "minecraft:polished_andesite")
        cloth = [(158, 92, 56), (77, 107, 87), (140, 122, 77), (115, 56, 51), (87, 92, 112), (148, 133, 107)]
        trades = ["cloth", "pots", "tools", "lamps", "boots", "jars"]
        for k in range(6):
            sd = -1 if k < 3 else 1
            c = -3 - round(2.4 + (k % 3) * 3.7)                                 # pitch centre
            wall_d = 25 if sd < 0 else 33                                        # trader's side, by the wall
            cnt_d = wall_d - sd                                                  # counter row
            colour = nearest(cloth[k], TERRACOTTA)
            for cs in (c - 1, c, c + 1):
                self.blk(cnt_d, cs, 0, "minecraft:spruce_planks")              # counter 1.0 m
                self.blk(wall_d, cs, 3, f"minecraft:{colour}_terracotta")      # awning, high at the wall
                self.blk(cnt_d, cs, 3, f"minecraft:{colour}_terracotta")
            for cs in (c - 2, c + 2):                                           # partitions 2.5 m, pillars between
                if cs >= -15:
                    self.box(cnt_d, cnt_d, cs, cs, 0, 1, "minecraft:spruce_planks")
                    self.box(wall_d, wall_d, cs, cs, 0, 3, "minecraft:polished_andesite")
            self.blk(wall_d, c, 2, HANG)                                         # the pitch's own bulb
            self.blk(wall_d, c + 1, 0, "minecraft:spruce_slab[type=bottom,waterlogged=false]")   # stool
            trade = trades[k]
            if trade == "cloth":
                for cs in (c - 1, c, c + 1):
                    self.blk(cnt_d, cs, 1, f"minecraft:{nearest(cloth[(cs + k) % 6], TERRACOTTA)}_carpet")
                for cs in (c - 1, c):
                    wb = nearest(cloth[(cs + 2) % 6], TERRACOTTA)
                    self.blk(wall_d, cs, 1, f"minecraft:{wb}_wall_banner[facing={'east' if sd < 0 else 'west'}]")
            elif trade == "pots":
                for cs in (c - 1, c, c + 1):
                    self.blk(cnt_d, cs, 1, "minecraft:flower_pot")
                self.blk(wall_d, c - 1, 0, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
            elif trade == "tools":
                self.blk(cnt_d, c, 0, "minecraft:smithing_table")
                self.blk(cnt_d, c - 1, 1, "minecraft:grindstone[face=floor,facing=north]")
                self.blk(wall_d, c - 1, 1, f"minecraft:spruce_trapdoor[facing={'east' if sd < 0 else 'west'},half=bottom,open=true,powered=false,waterlogged=false]")
            elif trade == "lamps":
                for cs in (c - 1, c, c + 1):
                    self.blk(cnt_d, cs, 1, LANTERN)
                    self.blk(cnt_d - sd, cs, 2, HANG)
            elif trade == "boots":
                for cs in (c - 1, c):
                    self.blk(wall_d, cs, 0, SLAB_TOP)
                    self.blk(wall_d, cs, 1, "minecraft:brown_carpet")
            else:
                for cs in (c - 1, c, c + 1):
                    self.blk(cnt_d, cs, 1, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
                self.blk(cnt_d - sd, c + 1, 0, "minecraft:brown_wool")       # sacks of seed
        for s in (1.4, 5.3, 9.2):                                                # string lights across the aisle
            c = -3 - round(s) - 1
            for d in (27, 29, 31):
                self.blk(d, c, 3, HANG)
        for c in range(-14, -4):                                                 # the runner down the aisle
            if self.get(29, c, 0) == AIR:
                self.blk(29, c, 0, "minecraft:brown_carpet")
        for d, c in ((27, -6), (31, -9), (27, -12)):                             # produce crates
            self.blk(d, c, 0, "minecraft:composter[level=7]")
        for d, c in ((30, -13), (28, -13)):                                      # crates in the aisle
            self.blk(d, c, 0, "minecraft:barrel[facing=up,open=false]")
        # the far end: a shop front, its shutter half up on a lit back room
        self.box(28, 30, -16, -16, 0, 0, AIR)
        self.box(28, 30, -16, -16, -1, -1, "minecraft:spruce_planks")
        self.box(28, 30, -17, -17, 0, 0, "minecraft:shroomlight")
        self.box(28, 30, -16, -16, 1, 2, "minecraft:iron_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
        for d in (30, 31):
            self.blk(d, -15, 0, "minecraft:brown_wool")                        # sacks by the shop front

    def deputy_station(self, n: int) -> None:
        """Deputy station. Canon names the level only; its room follows the model's own Sheriff's station by the
        airlock (the same department): 12.4 m wide, 10 m deep, 4.3 m high, open on to the walkway through a 3.8 x 3.0 m
        doorway; two desks with chairs on the left, the holding cell's barred front on the right, a bench in the cell,
        a noticeboard by the door, long fluorescent tubes and filing cabinets."""
        self.on(n)
        W = 12
        olive = "minecraft:green_terracotta"
        self.room(18, 27, -6, 5, olive, "minecraft:polished_deepslate")
        self.box(16, 17, -2, 1, 0, 2, AIR)                                       # the open doorway, no door
        self.box(16, 17, -2, 1, -1, -1, "minecraft:polished_deepslate")
        for s0, s1, ac, sc in ((3.4, 5.0, -2.7, 3.97), (6.3, 7.9, -2.6, 6.87)):
            for s in (s0, (s0 + s1) / 2, s1 - 0.01):
                d, c = self.cell(ac, s, W)
                self.blk(d, c, 0, SLAB_TOP)
                self.blk(d, c, 1, "minecraft:green_carpet")
            d, c = self.cell(ac + 1.4, sc + 0.23, W)
            self.blk(d, c, 0, stairs("south"))
            self.blk(self.cell(ac, s0, W)[0], self.cell(ac, s0, W)[1], 1, LANTERN)
        for d in range(19, 24):                                                  # the cell's barred front
            self.box(d, d, 2, 2, 0, 2, "minecraft:iron_bars")
        for d in range(20, 23):
            self.blk(d, 5, 0, "minecraft:spruce_slab[type=bottom,waterlogged=false]")   # bench at SW - 1
        for d in (24, 25, 26):
            self.box(d, d, -6, -6, 0, 1, "minecraft:barrel[facing=east,open=false]")    # filing cabinets
        for c in (-5, -4):
            self.blk(18, c, 1, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
        for s in (2.2, 5.0, 7.8):                                                # tubes on rods, either side
            for ac in (-2.6, 2.6):
                d, c = self.cell(ac, s, W)
                self.blk(d, c, 3, "minecraft:end_rod[facing=east]")
        for s in (1.8, 4.6, 7.4):                                                # globe lamps on the left wall
            d, _ = self.cell(0, s, W)
            self.blk(d, -7, 2, "minecraft:ochre_froglight")

    def workshop(self, n: int) -> None:
        """Walker's workshop (model workshop()): dim and cluttered, a round bench strewn with radios and test gear,
        racks against the back wall, red crates, a bank of small drawers, a desk with a green CRT, cage pendants,
        two pipes high on the left wall, a round vent and an arched dark opening."""
        self.on(n)
        W, D = 10, 9
        con = "minecraft:gray_concrete"
        self.room(18, 26, -5, 4, con, "minecraft:polished_deepslate")          # 10 x 9 x 3.8
        self.entry()
        cd, cx = 18 + 4.5, 0.0
        for d in range(18, 27):
            for c in range(-5, 5):
                if math.hypot(d + 0.5 - cd, c + 0.5 - cx) <= 1.8:
                    self.blk(d, c, 0, SLAB_TOP)                                  # bench top at 0.92 m
        self.blk(23, -1, 1, "minecraft:note_block[instrument=harp,note=0,powered=false]")   # radios
        self.blk(23, 0, 1, "minecraft:daylight_detector[inverted=false,power=0]")       # the lit meter
        self.blk(22, 1, 1, LANTERN)                                                     # desk lamp
        for c in (-3, -2):                                                       # left rack
            self.blk(26, c, 0, "minecraft:barrel[facing=west,open=false]")
            self.blk(26, c, 1, "minecraft:note_block[instrument=harp,note=0,powered=false]")
            self.blk(26, c, 2, "minecraft:jukebox[has_record=false]")
        self.blk(26, 0, 0, "minecraft:dropper[facing=west,triggered=false]")    # right rack, red crates low
        self.blk(26, 0, 1, "minecraft:note_block[instrument=harp,note=0,powered=false]")
        self.box(26, 26, 1, 1, 0, 1, "minecraft:red_concrete")
        self.box(26, 26, 0, 1, 2, 2, "minecraft:barrel[facing=west,open=false]")
        for c in (-5, -4):                                                       # tools on a board
            self.blk(26, c, 1, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
        self.blk(27, 1, 2, "minecraft:waxed_copper_grate")                     # round vent in the back wall
        for d in (24, 25):                                                       # drawer bank on the right wall
            self.box(d, d, 4, 4, 0, 2, "minecraft:chiseled_bookshelf[facing=north,slot_0_occupied=false,slot_1_occupied=false,slot_2_occupied=false,slot_3_occupied=false,slot_4_occupied=false,slot_5_occupied=false]")
        for d in (21, 22):                                                       # desk, green CRT, swivel chair
            self.blk(d, 4, 0, "minecraft:smooth_stone_slab[type=top,waterlogged=false]")
        self.blk(21, 4, 1, "minecraft:green_terracotta")
        self.blk(22, 3, 0, stairs("north"))
        for d in range(18, 27):                                                  # two pipes high on the left wall
            self.blk(d, -5, 3, "minecraft:lightning_rod[facing=east,powered=false,waterlogged=false]")
        for (x, s) in ((0, 4.5), (-1.5, 5.7), (1.6, 3.5), (-3.4, 7.0), (-2.2, 0.35)):   # cage pendants
            d, c = self.cell(x, s, W)
            if self.get(d, c, 3) == AIR:
                self.blk(d, c, 3, HANG)
        d, _ = self.cell(0, 4.5 + 0.8, W)                                        # the dark arched opening, left wall
        self.box(d - 1, d, -6, -6, 0, 1, "minecraft:black_concrete")
        self.blk(25, 4, 3, "minecraft:shroomlight")                              # the wall lamp over the drawers

    def checkpoint(self, n: int) -> None:
        """Level 30: Judicial's checkpoint on the stair (canon). A barred gate across the first bridge where it reaches
        the gallery, with a door."""
        self.on(n)
        silo, v, y = self.silo, self.v, self.y
        a = silo.bridge_angles(n)[0]
        d = np.abs(((silo.theta - a + math.pi) % TAU) - math.pi)
        gate = (np.abs(d * silo.r) < 2.6) & (d < math.pi / 2) & silo.ring(self.s.r_atrium - 2, self.s.r_atrium - 1)
        v.mask(y, y + 2, gate, "minecraft:iron_bars")
        x, z = silo.polar(self.s.r_atrium - 1.5, a)
        f = silo.facing_radial(a)
        for dy, half in ((0, "lower"), (1, "upper")):
            v.set(x, y + dy, z, f"minecraft:iron_door[facing={f},half={half},hinge=left,open=false,powered=false]")
        for k in (-1, 1):
            dx, dz = DIRS[f]
            if v.get(x + k * dx, y, z + k * dz) == AIR:
                v.set(x + k * dx, y, z + k * dz, PLATE)

    def medical(self, n: int) -> None:
        """Mids Medical: the front flats are clinics (model BAY.medical); each holds two beds."""
        self.on(n)
        silo, s = self.silo, self.s
        for b in range(s.bays):
            a = silo.bay_center(b)
            for k in (-0.22, 0.22):
                ang = a + k * math.radians(360 / s.bays)
                x, z = silo.polar(s.r_facade + 4, ang)
                f = silo.facing_radial(ang)
                dx, dz = DIRS[f]
                if self.v.get(x, self.y, z) == AIR and self.v.get(x - dx, self.y, z - dz) == AIR:
                    self.v.set(x, self.y, z, f"minecraft:white_bed[facing={f},occupied=false,part=head]")
                    self.v.set(x - dx, self.y, z - dz, f"minecraft:white_bed[facing={f},occupied=false,part=foot]")

    def filtration(self, n: int) -> None:
        """Water filtration on 55 (S3E09). Not seen on screen: the level's ring behind the facades opened into one hall
        of settling basins (water in tiled troughs between walkways) fed by copper mains along the ceiling, the stair
        and gallery passing through as on a farm level."""
        self.on(n)
        silo, s, v, y = self.silo, self.s, self.v, self.y
        top = y + s.pitch - 2
        hall = silo.ring(s.r_facade, s.r_inner_wall)
        v.mask(y, top, hall, AIR)
        v.mask(y - 1, y - 1, hall, "minecraft:smooth_stone")
        posts = silo.ring(s.r_facade, s.r_facade + 1.0) & (np.mod(silo.theta, TAU / 48) < 0.04)
        v.mask(y, top, posts, "minecraft:light_gray_concrete")
        basins = silo.ring(s.r_facade + 3, s.r_inner_wall - 2) & (np.mod(silo.theta, TAU / 24) > 0.05)
        v.mask(y - 2, y - 2, basins, "minecraft:cyan_terracotta")
        v.mask(y - 1, y - 1, basins, "minecraft:water")
        rims = silo.ring(s.r_facade + 2, s.r_facade + 3) | silo.ring(s.r_inner_wall - 2, s.r_inner_wall - 1)
        v.mask(y, y, rims & ~posts, "minecraft:polished_andesite_slab[type=bottom,waterlogged=false]")
        mains = silo.ring(s.r_inner_wall - 3, s.r_inner_wall - 2) | silo.ring(s.r_facade + 4, s.r_facade + 5)
        v.mask(top, top, mains, "minecraft:waxed_weathered_cut_copper")
        v.mask(top, top, hall & ~mains & ((silo.X % 6) == 3) & ((silo.Z % 6) == 0), SEA)

    def farm(self, n: int) -> None:
        """A farm level (Gold Derby 8:25, Valette 1x3gyL/01, 05): one tall open storey the full width of the silo behind a
        ring of columns, the stair and gallery passing through it. The sources give ≈7-8 m; ours is this level and
        the one above opened into one storey (11 clear, two of our 6-block levels), the upper level keeping its
        gallery as a balcony. Crops in rows on watered soil under grow lights, water towers among the fields."""
        self.on(n)
        silo, s, v, y = self.silo, self.s, self.v, self.y
        top = y + 2 * s.pitch - 2
        hall = silo.ring(s.r_facade, s.r_inner_wall)
        v.mask(y, top, hall, AIR)
        v.mask(y - 1, y - 1, hall, "minecraft:coarse_dirt")
        posts = silo.ring(s.r_facade, s.r_facade + 1.0) & (np.mod(silo.theta, TAU / 48) < 0.04)
        v.mask(y, top, posts, "minecraft:light_gray_concrete")
        X, Z = silo.X, silo.Z
        field = silo.ring(s.r_facade + 2, s.r_inner_wall - 1)
        water = field & ((X % 5) == 0) & ((Z % 11) != 0)
        land = field & ~water
        v.mask(y - 1, y - 1, water, "minecraft:water")
        v.mask(y - 1, y - 1, land, "minecraft:farmland[moisture=7]")
        crops = ["minecraft:wheat[age=7]", "minecraft:carrots[age=7]", "minecraft:potatoes[age=7]", "minecraft:beetroots[age=3]"]
        for i, c in enumerate(crops):
            v.mask(y, y, land & ((Z // 7) % 4 == i), c)
        v.mask(top, top, hall & ((X % 4) == 2) & ((Z % 4) == 0), "minecraft:verdant_froglight")
        for k in range(6):                                   # water towers: a tank on legs
            cx, cz = silo.polar(48, k * TAU / 6 + 0.3)
            v.box(cx - 1, y - 1, cz - 1, cx + 1, y + 4, cz + 1, "minecraft:polished_andesite")
            v.box(cx - 2, y + 5, cz - 2, cx + 2, y + 8, cz + 2, "minecraft:waxed_weathered_copper")

    def barricade(self, n: int) -> None:
        """Level 130, the barricade (canon): junk piled across the gallery where the first bridge reaches it."""
        self.on(n)
        silo, v, y = self.silo, self.v, self.y
        a = silo.bridge_angles(n)[0]
        d = np.abs(((silo.theta - a + math.pi) % TAU) - math.pi)
        m = (d * silo.r < 4) & (d < math.pi / 2) & silo.ring(self.s.r_atrium - 1, self.s.r_atrium + 2) & ~silo.columns
        junk = ["minecraft:barrel[facing=up,open=false]", "minecraft:cobblestone_wall", "minecraft:oak_planks",
                "minecraft:scaffolding[bottom=false,distance=0,waterlogged=false]", "minecraft:anvil[facing=north]",
                "minecraft:chipped_anvil[facing=east]", "minecraft:iron_bars"]
        xs, zs = np.nonzero(m)
        for i, (x, z) in enumerate(zip(xs, zs)):
            for dy in range(0, 2 + (i % 2)):
                v.set(x, y + dy, z, junk[(i * 3 + dy) % len(junk)])
        # the pile is meant to bar the way: walk.py does not ask anyone to stand on top of it
        R = silo.R
        silo.walk_ignore_boxes.append((int(xs.min()) - R, y - 1, int(zs.min()) - R, int(xs.max()) - R, y + 4,
                                       int(zs.max()) - R))
