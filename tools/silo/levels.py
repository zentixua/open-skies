"""Canon special levels of a silo, furnished over the generic residential levels built by silo.Silo.level.

Level list and room descriptions from explorethesilo.com (show canon, novels where marked), condensed in
/mnt/project-files/silo/canon-levels-explorethesilo.md. Angles are degrees in the silo frame (x east, z south),
radii in blocks from the axis; each level has 4 clear rows (y .. y + 3) over its floor at y - 1.
"""
from __future__ import annotations

import math

import numpy as np

TAU = 2 * math.pi
GOLDEN = math.radians(137.5)          # bridge rotation per level, as silo.GOLDEN
AIR = "minecraft:air"


class Furnisher:
    def __init__(self, silo):
        self.silo, self.s, self.v = silo, silo.s, silo.v

    # helpers ----------------------------------------------------------------------------------------------------
    def sector(self, a0: float, a1: float, r0: float, r1: float) -> np.ndarray:
        return self.silo.sector(math.radians(a0), math.radians(a1)) & self.silo.ring(r0, r1)

    def hall(self, n: int, a0: float, a1: float, r0: float, r1: float, floor: str | None = None,
             walls: str | None = None, rows: int = 4) -> np.ndarray:
        """Clear a sector of level n into one room; optionally new floor and a wall around its edge."""
        y = self.silo.level_y(n)
        m = self.sector(a0, a1, r0, r1)
        self.v.mask(y, y + rows - 1, m, AIR)
        if floor:
            self.v.mask(y - 1, y - 1, m, floor)
        if walls:
            inner = self.sector(a0 + 1.5 * 57.3 / r1, a1 - 1.5 * 57.3 / r1, r0 + 1, r1 - 1)
            self.v.mask(y, y + rows - 1, m & ~inner, walls)
        return m

    def at(self, r: float, a: float) -> tuple[int, int]:
        return self.silo.polar(r, math.radians(a))

    def put(self, n: int, r: float, a: float, dy: int, state: str) -> None:
        x, z = self.at(r, a)
        self.v.set(x, self.silo.level_y(n) + dy, z, state)

    def ceiling_lights(self, n: int, m: np.ndarray, state: str, every: int = 5) -> None:
        y = self.silo.level_y(n) + 3
        grid = ((self.silo.X % every) == 0) & ((self.silo.Z % every) == 0) & m
        self.v.mask(y, y, grid, state)

    def facing(self, a_deg: float, outward: bool = True) -> str:
        f = self.silo.facing_radial(math.radians(a_deg))
        if outward:
            return f
        return {"east": "west", "west": "east", "north": "south", "south": "north"}[f]

    # levels -----------------------------------------------------------------------------------------------------
    def all(self) -> None:
        self.judicial(13)
        self.managers_row(15)
        self.it(19)
        self.watcher_room(20)
        self.checkpoint(30)
        self.medical(50)
        self.medical(62)
        self.bazaar(100)
        self.deputy_station(105)
        self.farm(122)
        self.barricade(130)
        self.mechanical(140)
        self.workshop(144)
        self.generator_extras()
        self.digger_camp_and_door()

    def judicial(self, n: int) -> None:
        """Seclusion holding: concrete corridor on steel grate, sealed doors along one wall, cold light; a cell."""
        y = self.silo.level_y(n)
        m = self.hall(n, 0, 120, 31, 43, floor="minecraft:waxed_weathered_copper_grate", walls="minecraft:gray_concrete")
        corridor = self.sector(1, 119, 32, 35)
        cells = m & ~corridor & ~self.sector(1, 119, 35, 36)
        self.v.mask(y, y + 3, self.sector(1, 119, 35, 36), "minecraft:gray_concrete")
        self.v.mask(y, y + 3, cells, "minecraft:gray_concrete")
        for a in range(8, 116, 12):
            x, z = self.at(35.5, a)
            self.v.set(x, y, z, "minecraft:iron_block")
            self.v.set(x, y + 1, z, "minecraft:iron_block")
            self.v.set(x, y + 2, z, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
            hx, hz = self.at(38.5, a)
            self.v.box(hx - 1, y, hz - 1, hx + 1, y + 3, hz + 1, AIR)
            self.v.set(hx, y + 3, hz, "minecraft:iron_bars")
        self.ceiling_lights(n, corridor, "minecraft:pearlescent_froglight", 6)

    def managers_row(self, n: int) -> None:
        """Better apartments: carpet, shelves, plants."""
        y = self.silo.level_y(n)
        for b in range(self.s.bays):
            a = (b + 0.5) * 360 / self.s.bays
            room = self.sector(a - 9, a + 9, 31, 42)
            self.v.mask(y - 1, y - 1, room, "minecraft:dark_oak_planks")
            for k in (-6, 6):
                self.put(n, 41.5, a + k, 0, "minecraft:bookshelf")
                self.put(n, 41.5, a + k, 1, "minecraft:bookshelf")
            self.put(n, 36, a, 0, "minecraft:potted_azalea_bush")
            self.put(n, 33, a - 4, 0, "minecraft:red_carpet")
            self.put(n, 33, a + 4, 0, "minecraft:red_carpet")

    def it(self, n: int) -> None:
        """IT: round office under radiating lights, the server hall, and the Vault."""
        y = self.silo.level_y(n)
        office = self.hall(n, 20, 160, 18, 43, floor="minecraft:polished_andesite", walls="minecraft:light_gray_concrete")
        # radiating ceiling light from one point
        cx, cz = self.at(30, 90)
        for k in range(12):
            ang = k * TAU / 12
            for t in range(2, 12):
                x, z = cx + int(round(t * math.cos(ang))), cz + int(round(t * math.sin(ang)))
                if 0 <= x < self.v.size[0] and 0 <= z < self.v.size[2] and office[x, z]:
                    self.v.set(x, y + 3, z, "minecraft:pearlescent_froglight" if t % 3 == 0 else "minecraft:smooth_quartz")
        for r in (22, 26, 34, 38):
            for a in range(28, 156, 9):
                f = self.facing(a, outward=False)
                self.put(n, r, a, 0, "minecraft:spruce_slab[type=top]")
                self.put(n, r, a, 1, "minecraft:black_stained_glass_pane")
                self.put(n, r + 1, a, 0, f"minecraft:spruce_stairs[facing={f}]")
        # server hall: racks of lit lamps powered from behind
        hall = self.hall(n, 165, 290, 18, 43, floor="minecraft:polished_deepslate", walls="minecraft:gray_concrete")
        for r in (22, 26, 30, 34, 38):
            for a in np.arange(170, 286, 360 / (TAU * r) * 1.0):
                x, z = self.at(r, a)
                if not hall[x, z]:
                    continue
                self.v.box(x, y, z, x, y + 2, z, "minecraft:polished_blackstone")
                self.v.set(x, y + 1, z, "minecraft:redstone_lamp[lit=true]")
                self.v.set(x, y + 3, z, "minecraft:redstone_block")
                self.v.set(x, y + 2, z, "minecraft:redstone_lamp[lit=true]")
        # the Vault: steel walls, a round door, the things that do not exist
        vault = self.hall(n, 300, 340, 31, 43, floor="minecraft:iron_block", walls="minecraft:iron_block")
        dx, dz = self.at(31.5, 320)
        for oy in range(0, 4):
            for o in (-1, 0, 1):
                xx, zz = self.at(31.5, 320 + o * 2.2)
                self.v.set(xx, y + oy, zz, "minecraft:waxed_copper_block" if oy in (0, 3) or o else "minecraft:waxed_oxidized_copper")
        for a, r in ((310, 40), (320, 41), (330, 40)):
            self.put(n, r, a, 0, "minecraft:chest")
        self.put(n, 36, 320, 0, "minecraft:lectern")
        self.ceiling_lights(n, vault, "minecraft:pearlescent_froglight", 5)

    def watcher_room(self, n: int) -> None:
        """A janitorial closet that leads on into the hidden Watcher Room: a wall of feeds."""
        y = self.silo.level_y(n)
        closet = self.hall(n, 196, 204, 31, 34, floor="minecraft:stone_bricks", walls="minecraft:light_gray_concrete")
        self.put(n, 32.5, 200, 0, "minecraft:cauldron")
        self.put(n, 33.2, 198, 0, "minecraft:barrel")
        room = self.hall(n, 188, 212, 35, 43, floor="minecraft:polished_deepslate", walls="minecraft:gray_concrete")
        self.v.mask(y, y, self.sector(199, 201, 33, 36), AIR)
        self.v.mask(y + 1, y + 1, self.sector(199, 201, 33, 36), AIR)
        wall = self.sector(189, 211, 42, 43)
        self.v.mask(y + 1, y + 3, wall, "minecraft:black_stained_glass")
        self.v.mask(y + 3, y + 3, self.sector(189, 211, 41, 42), "minecraft:redstone_block")
        self.v.mask(y + 2, y + 2, self.sector(189, 211, 41, 42), "minecraft:redstone_lamp[lit=true]")
        for a in (194, 200, 206):
            self.put(n, 39, a, 0, "minecraft:dark_oak_slab[type=top]")

    def checkpoint(self, n: int) -> None:
        """Judicial checkpoint at the landing: a gate across the bridge and a guard desk."""
        a = math.degrees((n * GOLDEN) % TAU)
        y = self.silo.level_y(n)
        gate = self.sector(a - 8, a + 8, 13, 14.5)
        self.v.mask(y, y + 2, gate, "minecraft:iron_bars")
        for o in (-12, 12):
            self.put(n, 16, a + o, 0, "minecraft:polished_deepslate")
            self.put(n, 16, a + o, 1, "minecraft:lantern")

    def medical(self, n: int) -> None:
        """Mids Medical: white wards, rows of beds, clean cold light."""
        y = self.silo.level_y(n)
        ward = self.hall(n, 30, 150, 18, 43, floor="minecraft:white_concrete", walls="minecraft:white_concrete")
        for r in (24, 31, 38):
            for a in range(36, 146, 8):
                f = self.facing(a)
                self.put(n, r, a, 0, f"minecraft:white_bed[facing={f},part=head]")
                ox, oz = {"east": (-1, 0), "west": (1, 0), "south": (0, -1), "north": (0, 1)}[f]
                x, z = self.at(r, a)
                self.v.set(x + ox, y, z + oz, f"minecraft:white_bed[facing={f},part=foot]")
        self.put(n, 20, 90, 0, "minecraft:brewing_stand")
        self.put(n, 20, 95, 0, "minecraft:white_concrete")
        self.ceiling_lights(n, ward, "minecraft:pearlescent_froglight", 4)

    def bazaar(self, n: int) -> None:
        """The Bazaar (novels): the whole level one market of family stalls under canopies."""
        y = self.silo.level_y(n)
        market = self.hall(n, 0, 360, 18, 43, floor="minecraft:spruce_planks")
        # keep the rooms' back wall as the outer wall
        self.v.mask(y, y + 3, self.silo.ring(42, 43), "minecraft:light_gray_concrete")
        colours = ["red", "orange", "yellow", "lime", "cyan", "blue", "purple", "brown", "white", "green"]
        k = 0
        for r in (22, 29, 36):
            step = 360 / int(TAU * r / 6)
            for a in np.arange(0, 360, step):
                x, z = self.at(r, a)
                c = colours[(k * 7 + self.s.number) % len(colours)]
                k += 1
                for ox, oz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    self.v.set(x + ox, y, z + oz, "minecraft:spruce_fence")
                    self.v.set(x + ox, y + 1, z + oz, "minecraft:spruce_fence")
                self.v.box(x - 1, y + 2, z - 1, x + 1, y + 2, z + 1, f"minecraft:{c}_wool")
                self.v.set(x, y, z, ("minecraft:barrel[facing=up]", "minecraft:chest", "minecraft:composter",
                                     "minecraft:smoker", "minecraft:loom")[k % 5])
                self.v.set(x + 1, y + 3, z, "minecraft:lantern[hanging=true]")
        self.ceiling_lights(n, market, "minecraft:ochre_froglight", 7)

    def deputy_station(self, n: int) -> None:
        y = self.silo.level_y(n)
        m = self.hall(n, 60, 90, 31, 43, floor="minecraft:polished_andesite", walls="minecraft:light_gray_concrete")
        self.v.mask(y, y + 3, self.sector(80, 89, 37, 42) & ~self.sector(81, 88, 38, 41), "minecraft:iron_bars")
        self.put(n, 34, 70, 0, "minecraft:dark_oak_planks")
        self.put(n, 34, 70, 1, "minecraft:lantern")
        self.ceiling_lights(n, m, "minecraft:pearlescent_froglight", 5)

    def farm(self, n: int) -> None:
        """Lower Mids Farm: hydroponic rows under grow lights across the whole level."""
        y = self.silo.level_y(n)
        farm = self.hall(n, 0, 360, 18, 42, floor="minecraft:dirt")
        crops = ["minecraft:wheat[age=7]", "minecraft:carrots[age=7]", "minecraft:potatoes[age=7]", "minecraft:beetroots[age=3]"]
        X, Z = self.silo.X, self.silo.Z
        water = farm & ((X % 5) == 0)
        land = farm & ~water
        self.v.mask(y - 1, y - 1, water, "minecraft:water")
        self.v.mask(y - 1, y - 1, land, "minecraft:farmland[moisture=7]")
        for i, c in enumerate(crops):
            self.v.mask(y, y, land & ((Z // 6) % 4 == i), c)
        self.v.mask(y + 3, y + 3, farm & ((X % 5) == 0) & ((Z % 3) == 0), "minecraft:verdant_froglight")

    def barricade(self, n: int) -> None:
        """The barricade at the landing: junk piled across the bridge."""
        a = math.degrees((n * GOLDEN) % TAU)
        y = self.silo.level_y(n)
        m = self.sector(a - 14, a + 14, 13, 17)
        junk = ["minecraft:barrel[facing=up]", "minecraft:cobblestone_wall", "minecraft:iron_bars",
                "minecraft:oak_planks", "minecraft:scaffolding[distance=0,bottom=false]", "minecraft:anvil[facing=north]"]
        xs, zs = np.nonzero(m)
        for i, (x, z) in enumerate(zip(xs, zs)):
            for dy in range(0, 2 + (i % 2)):
                self.v.set(x, y + dy, z, junk[(i * 3 + dy) % len(junk)])

    def mechanical(self, n: int) -> None:
        """Mechanical: hot, loud pipes and furnaces through the rooms."""
        y = self.silo.level_y(n)
        m = self.hall(n, 90, 270, 18, 43, floor="minecraft:waxed_weathered_copper_grate", walls="minecraft:gray_concrete")
        for r in (21, 27, 33, 39):
            ring = self.silo.ring(r, r + 1) & m
            self.v.mask(y + 3, y + 3, ring, "minecraft:waxed_weathered_cut_copper")
        for a in range(100, 265, 15):
            self.put(n, 41, a, 0, "minecraft:blast_furnace[facing=" + self.facing(a, False) + "]")
            self.put(n, 41, a + 5, 0, "minecraft:furnace[facing=" + self.facing(a, False) + "]")
            self.put(n, 24, a, 0, "minecraft:waxed_weathered_copper")
            self.put(n, 24, a, 1, "minecraft:chain[axis=y]")
            self.put(n, 24, a, 2, "minecraft:chain[axis=y]")
        self.ceiling_lights(n, m, "minecraft:verdant_froglight", 6)

    def workshop(self, n: int) -> None:
        """Walker's electronics workshop: a cluttered bench room nobody has left in decades."""
        m = self.hall(n, 150, 175, 31, 43, floor="minecraft:spruce_planks", walls="minecraft:gray_concrete")
        things = ["minecraft:smithing_table", "minecraft:crafting_table", "minecraft:lectern", "minecraft:barrel[facing=up]",
                  "minecraft:copper_bulb[lit=true]", "minecraft:lightning_rod", "minecraft:target",
                  "minecraft:dropper[facing=up]"]
        i = 0
        for a in np.arange(152, 174, 2.0):
            for r in (41, 33):
                self.put(n, r, a, 0, things[i % len(things)])
                i += 1
        for a in (156, 163, 170):
            self.put(n, 37, a, 3, "minecraft:lantern[hanging=true]")

    def generator_extras(self) -> None:
        """Steam main from the wall to the turbine, and the hatch to the pressure chamber."""
        silo, v = self.silo, self.v
        yf = silo.yi(silo.gen_floor_rel)
        a = math.radians(120)
        for t in range(24, 42):
            x, z = silo.polar(t, a)
            v.box(x, yf + 3, z - 1, x, yf + 5, z + 1, "minecraft:waxed_weathered_copper")
        hx, hz = silo.polar(26, math.radians(140))
        v.box(hx - 1, yf - 1, hz - 1, hx + 1, yf - 1, hz + 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")

    def digger_camp_and_door(self) -> None:
        """George's camp inside the digger body; across the water a tunnel ends at a huge metal door."""
        silo, v = self.silo, self.v
        floor = silo.yi(silo.void_floor_rel)
        c = silo.R
        v.set(c + 2, floor + 3, c, "minecraft:red_bed[facing=east,part=head]")
        v.set(c + 1, floor + 3, c, "minecraft:red_bed[facing=east,part=foot]")
        v.set(c - 2, floor + 3, c + 1, "minecraft:chest")
        v.set(c - 2, floor + 3, c - 1, "minecraft:lantern")
        v.set(c, floor + 3, c + 2, "minecraft:lectern")
        a = math.radians(30)
        for t in range(int(self.s.void_radius) - 2, silo.R):
            x, z = silo.polar(t, a)
            v.box(x - 2, floor + 3, z - 2, x + 2, floor + 7, z + 2, AIR)
            v.box(x - 2, floor + 2, z - 2, x + 2, floor + 2, z + 2, "minecraft:polished_deepslate")
        x, z = silo.polar(silo.R - 1, a)
        v.box(x - 3, floor + 2, z - 3, x + 3, floor + 8, z + 3, "minecraft:iron_block")
        v.box(x - 1, floor + 4, z - 1, x + 1, floor + 6, z + 1, "minecraft:waxed_oxidized_copper")
