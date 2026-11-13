"""One silo of the Silo series at 1:1, generated block by block (SPEC-1to1.md, Artem's decision 12.11.2026).

Sizes and their sources are in SPEC-1to1.md and canon/official-layout.md (the production's own plan, BFDG t2014s;
the built set, t2163s; the dome, t2240s; levels of 6, BFDG 28:10). 1 block = 1 m.

Plan of a level, radii from the shaft axis:
  r 0-1.5    solid concrete core (the plan's stair core, about 1/5 of the open shaft)
  r 1.5-3.5  the spiral flight, 2 wide, wound round the core; its solid parapet at r 3.5-4.5
  r 4.5-8.5  the landing ring round the stair, a parapet on each edge
  r 8.5-19.5 the open atrium, crossed by two radial bridges about 135 degrees apart (plan t2014s)
  r 19.5-24  the gallery street, 4 wide: a 1.1 m parapet on its edge between big round columns with light collars
  r 24-25    the two-storey facades (bays.FACADES), broken by alleys
  r 25-60    flat modules: front flats on the gallery, back flats on an inner ring alley, an outer ring of flats
             between two ring alleys; radial alleys 4 wide join the gallery to both ring alleys (BFDG t3452s, S2 ew)
  r 60-62    the shaft's concrete wall (Ø≈120 from the bowl, SPEC section 2)
A level is 6 blocks: the gallery floor, a 3-row lower storey (doors 2) and a 2-row upper storey (BFDG 28:10: two
levels in a 12.2 m stage). 144 levels; the open atrium ends at the top in a coffered dome (BFDG t2240s).

Local frame: x, z centred on the silo axis (index R), y index 0 at the bottom of the digger void. World y of an
index is origin_y + index. Level n (1..144) has its walking surface at Y1 - 6 * (n - 1). Level 1's specials (the
cafeteria, the sheriff's office, the holding cells, the airlock and the ramp) are laid out with the way in due west;
build_live turns the finished volume to the silo's own side.

Interiors from the explorethesilo.com model: bay facades (bays.py), the canon rooms (levels.py), the generator hall,
digger void and tunnel (machines.py); after them connect.py gives panes, bars, fences and walls their connections and
drops halves a room cut off, and lighting.py puts invisible light wherever a monster could spawn.
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
    pitch: int = 6                    # blocks per level: floor 1 + lower storey 3 + upper storey 2 (BFDG 28:10)
    r_newel: float = 1.5              # solid stair core (plan t2014s: core ≈ 1/5 of the open shaft)
    r_flight: float = 3.5             # flight 2 wide (≈ 1.8-2 m by a person)
    r_stair_wall: float = 4.5         # the flight's solid parapet
    r_landing: float = 8.5            # landing ring round the stair core, outer edge
    r_atrium: float = 19.5            # gallery edge: the open atrium is Ø≈40 (SPEC 2)
    r_column: float = 1.5             # big round columns on the gallery edge (Ø3, t2163s)
    columns: int = 15                 # 24 degrees apart: an 8 m scallop between them
    r_facade: float = 24.0            # gallery street 4 wide (t2163s)
    r_ring1: tuple = (39.0, 44.0)     # inner ring alley (wall, alley, wall): 4 wide
    r_ring2: tuple = (50.0, 55.0)     # outer ring alley
    r_split: float = 32.0             # wall between the front flats (on the gallery) and the back flats
    r_inner_wall: float = 60.0        # inside face of the shaft wall: Ø≈120 (SPEC 2)
    r_outer: float = 62.0
    bays: int = 18
    alley_every: int = 3              # one radial alley every third bay, six per level
    alley_half: float = 2.0           # alleys 4 wide (S2 ew t0660s: 3-5)
    flats_out: int = 36               # outer flats: one per 10 degrees
    level1_depth: int = 15            # level 1 under the bowl floor (SPEC 5: 13-17)
    dome_rise: int = 7                # the coffered dome over the atrium
    gen_height: int = 16              # generator hall below level 144
    slab: int = 9                     # "thirty feet" of concrete above the digger void
    void_height: int = 44
    void_radius: float = 52.0
    margin: int = 3


SCREEN_ARC = math.radians(70)

# palette -------------------------------------------------------------------------------------------------------------
CONCRETE = "minecraft:light_gray_concrete"
CONCRETE_DARK = "minecraft:gray_concrete"
SHELL = "minecraft:polished_andesite"
FLOOR = "minecraft:polished_andesite"
FLOOR_DEEP = "minecraft:polished_deepslate"
SLAB_FLOOR = "minecraft:smooth_stone"
STEEL = "minecraft:polished_deepslate"
STEEL_SLAB_B = "minecraft:polished_deepslate_slab[type=bottom,waterlogged=false]"
RUST = "minecraft:waxed_weathered_cut_copper"
RAIL = "minecraft:iron_bars"
GRATE = "minecraft:waxed_weathered_copper_grate"
ROCK = "minecraft:deepslate"
STONE = "minecraft:stone"
AIR = "minecraft:air"
LAMP_WARM = "minecraft:ochre_froglight"
LAMP_COOL = "minecraft:pearlescent_froglight"
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
# store rooms' stacked crates: a block with no block entity. Barrels are containers (one block entity each); Silo 1's
# storage levels alone held 97 739 of them (12.11 offline build), weight in every chunk load and save for nothing seen
STOCK = "minecraft:stripped_spruce_wood[axis=y]"
SACK = "minecraft:brown_wool"
DRUM = "minecraft:cauldron"
HANG = "minecraft:lantern[hanging=true,waterlogged=false]"
CHAIN = "minecraft:chain[axis=y,waterlogged=false]"
DIRS = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
OPP = {"east": "west", "west": "east", "south": "north", "north": "south"}

# Level 1 and the way in, silo frame with the way in due west (x east, z south). Positions are ours: no frame or
# plan shows how the cafeteria, the sheriff's office and the airlock sit on level 1 (SPEC 8); the sizes are the
# show's: the hall Ø≈28 with a 5 m ceiling (BFDG t2375s), the airlock door ≈2.4 (t2756s), the ramp 30-50 long
# climbing toward the centre to a slot at 0-1/2 of the bowl's radius (SPEC 5).
HALL = (-40, 0, 14)                   # cafeteria centre x, z and radius (inside of its wall)
HALL_DOOR = (-30, -10)                # its second entrance (north-east), toward the sheriff's office
OFFICE = (-28, -32, 6)                # the sheriff's office, round: centre x, z, radius
CELLS_X = (-41, -39)                  # holding cells, interior x range, west of the office's vestibule
CELLS_Z = ((-38, -36), (-34, -32), (-30, -28))
LOCK = (-47, -43)                     # airlock chamber x range on cell 3's lane
TURN_X = (-50, -49)                   # the ramp's U-turn
# The way up (Artem 13.11: the slot sits on one of the ring's axes, centred, the camera straight behind it). Three
# runs, 3 wide inside: the lower ramp east along LOW_Z out of the U-turn, a crossing north-to-south along CROSS_X over
# the cafeteria's roof onto the axis, and the upper ramp east along the axis to the steps of the slot.
LOW_Z = (-23, -21)                    # lower ramp interior z
LOW_X = (-48, -36)                    # lower ramp: from the U-turn to the crossing (level 1 -> +6)
CROSS_X = (-36, -34)                  # crossing interior x (+6 -> +8; its floor stays over level 1's ceiling)
RAMP_Z = (-1, 1)                      # the upper ramp and the slot: on the axis, centred
RAMP_X = (-34, -28)                   # upper ramp: from the crossing to where the steps begin (+8 -> +10)
STEPS = 6                             # the slot's steps, one block each
EXIT_X = RAMP_X[1] + STEPS            # last step, on the bowl floor: r 22, under half the bowl's radius (27)
CAMERA = (EXIT_X + 2, EXIT_X + 3, -2, 2)   # the camera block straight behind the stair head on the axis, facing down
                                      # the steps (S3E09 07): x0 (its face, toward the slot), x1 (back), z0, z1
                                      # (≈4.4 x 2.4 m); from the cut one sees its back with the stair hidden (05)


class Silo:
    def __init__(self, spec: Spec, center_x: int, surface_y: int, center_z: int):
        self.s = s = spec
        self.R = R = int(math.ceil(s.r_outer)) + s.margin
        self.depth_levels = (LEVELS - 1) * s.pitch
        # vertical layout from the top: grade (bowl floor) -> earth and cap over the dome -> level 1 -> levels ->
        # generator -> slab -> void
        self.grade_rel = 0
        self.Y1_rel = -s.level1_depth
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
        self.r = np.hypot(self.X, self.Z)
        self.theta = np.mod(np.arctan2(self.Z, self.X), TAU)
        self.col_step = TAU / s.columns
        self.walk_ignore_boxes: list[tuple[int, int, int, int, int, int]] = []
        self._plan()

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

    def off(self, a: float) -> np.ndarray:
        """Angle of every column from bearing a, 0..pi."""
        return np.abs(((self.theta - a + math.pi) % TAU) - math.pi)

    def lane(self, a: float, half: float) -> np.ndarray:
        """Columns within `half` of the ray from the axis along bearing a."""
        d = self.off(a)
        return (d < math.pi / 2) & (self.r * np.sin(d) < half)

    def polar(self, r: float, a: float) -> tuple[int, int]:
        return self.R + int(round(r * math.cos(a))), self.R + int(round(r * math.sin(a)))

    def at(self, x: int, z: int) -> tuple[int, int]:
        """Volume column of silo-frame offsets (x east, z south)."""
        return self.R + x, self.R + z

    @staticmethod
    def facing_radial(a: float) -> str:
        """Horizontal facing pointing outward along angle a (x east, z south)."""
        c, s = math.cos(a), math.sin(a)
        if abs(c) >= abs(s):
            return "east" if c > 0 else "west"
        return "south" if s > 0 else "north"

    # plan: the 2D masks every level shares ---------------------------------------------------------------------
    def bay_center(self, b: int) -> float:
        """Bearing (radians, silo frame) of bay b's centre: the model's (b + 0.5) * 20 degrees turned by FRAME_DEG."""
        return math.radians((b + 0.5) * BAY_ARC_DEG + FRAME_DEG)

    def bridge_angles(self, n: int) -> tuple[float, float]:
        """The two bridges of level n, about 135 degrees apart (plan t2014s), turning by the model's 137.5 degrees a
        level, each landing in the scallop between two gallery columns."""
        st = self.col_step
        snap = lambda a: ((math.floor((a % TAU) / st) + 0.5) * st) % TAU
        a = snap(n * GOLDEN)
        return a, snap(a + math.radians(135))

    def alley_bays(self, n: int) -> list[int]:
        """Bays opening into a radial alley on level n: every third, shifted level by level, never the special bay of
        a room level or the cafeteria's side of level 1."""
        k = n % self.s.alley_every
        out = [b for b in range(self.s.bays) if b % self.s.alley_every == k]
        if n in ROOM_LEVELS:
            out = [b for b in out if b != ROOM_BAY]
        if n == 1:                                       # the cafeteria and the way in face west
            out = [b for b in out if abs(((self.bay_center(b) - math.pi + math.pi) % TAU) - math.pi) > math.radians(70)]
        return out

    def _plan(self) -> None:
        s = self.s
        r = self.r
        self.core = r < s.r_newel
        self.flight = self.ring(s.r_newel, s.r_flight)
        self.stair_wall = self.ring(s.r_flight, s.r_stair_wall)
        self.landing = self.ring(s.r_stair_wall, s.r_landing)
        self.gallery = self.ring(s.r_atrium, s.r_facade)
        cols = np.zeros_like(self.core)
        self.column_centres = []
        for k in range(s.columns):
            a = k * self.col_step
            px, pz = (s.r_atrium + 0.5) * math.cos(a), (s.r_atrium + 0.5) * math.sin(a)
            cols |= np.hypot(self.X - px, self.Z - pz) < s.r_column
            self.column_centres.append((px, pz))
        self.columns = cols
        self.facade_ring = self.ring(s.r_facade, s.r_facade + 1.0)
        # front-wall cells of each bay with their position across the model's bay (u, metres)
        self.bay_cells: list[list[tuple[int, int, float, float]]] = [[] for _ in range(s.bays)]
        for x, z in zip(*np.nonzero(self.facade_ring)):
            th = float(self.theta[x, z])
            m = (math.degrees(th) - FRAME_DEG) % 360.0
            b = int(m // BAY_ARC_DEG) % s.bays
            u = (m - (b + 0.5) * BAY_ARC_DEG) / BAY_ARC_DEG * BAY_W
            self.bay_cells[b].append((int(x), int(z), u, th))
        for c in self.bay_cells:
            c.sort(key=lambda t: t[2])
        self._templates = {}

    def template(self, n: int) -> dict:
        """Walls, open space, flats and doors behind the gallery for level n's alley pattern (shared by every level
        with the same alleys)."""
        alleys = tuple(self.alley_bays(n))
        reserved = self.reserved(n)
        key = (alleys, n if reserved.any() else 0)
        if key in self._templates:
            return self._templates[key]
        s, r = self.s, self.r
        zone = self.ring(s.r_facade + 1.0, s.r_inner_wall)
        lanes = np.zeros_like(zone)
        for b in alleys:
            lanes |= self.lane(self.bay_center(b), s.alley_half)
        r1a, r1b = s.r_ring1[0] + 1, s.r_ring1[1] - 1
        r2a, r2b = s.r_ring2[0] + 1, s.r_ring2[1] - 1
        ring1 = self.ring(r1a, r1b)
        ring2 = self.ring(r2a, r2b)
        open_ = ((lanes & self.ring(s.r_facade, r2b)) | ring1 | ring2) & ~reserved
        walls = zone & ~open_
        # flats: cut the solid zone into cells by rings and radial walls
        thin = lambda r0: self.ring(r0, r0 + 1.0)
        cut = thin(s.r_split) | thin(s.r_ring1[0]) | thin(s.r_ring1[1] - 1) | thin(s.r_ring2[0]) | thin(s.r_ring2[1] - 1)
        for b in range(s.bays):
            edge = self.bay_center(b) - math.radians(BAY_ARC_DEG / 2)
            cut |= (np.abs(np.sin(self.theta - edge)) * r < 0.5) & (np.cos(self.theta - edge) > 0) & self.ring(s.r_facade, s.r_ring1[1])
        for k in range(s.flats_out):
            a = k * TAU / s.flats_out + 0.05
            cut |= (np.abs(np.sin(self.theta - a)) * r < 0.5) & (np.cos(self.theta - a) > 0) & self.ring(s.r_ring1[1], s.r_inner_wall)
        # a wall wherever a lane borders solid ground
        inner = walls & ~cut & ~reserved
        # label the flats (4-connected)
        from scipy import ndimage
        lab, nlab = ndimage.label(inner)
        # every flat needs at least 2 x 2 cells; tiny bits become wall
        sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, nlab + 1))
        for i, sz in enumerate(sizes, 1):
            if sz < 6:
                inner[lab == i] = False
        lab, nlab = ndimage.label(inner)
        flats = [{"label": i, "cells": np.argwhere(lab[sl] == i) + [sl[0].start, sl[1].start], "door": None,
                  "open": False} for i, sl in enumerate(ndimage.find_objects(lab), 1)]
        # the open space reached from the gallery; a stretch of alley cut off from it (level 1's halls cross the ring
        # alleys) joins the graph like a flat and gets a door of its own
        reach, nreach = ndimage.label(open_ | self.gallery)
        main = np.bincount(reach[self.gallery & (reach > 0)]).argmax()
        access = reach == main
        for k in range(1, nreach + 1):
            if k == main:
                continue
            i = len(flats) + 1
            lab[reach == k] = i
            flats.append({"label": i, "cells": np.argwhere(reach == k), "door": None, "open": True})
        self._doors(flats, lab, access)
        # a flat the tree cannot reach (a sliver boxed in by level 1's halls) is not left as a sealed void: solid wall
        for f in flats:
            if f["door"] is None:
                inner[tuple(f["cells"].T)] = False
                open_[tuple(f["cells"].T)] = False
        flats = [f for f in flats if f["door"] is not None]
        t = {"walls": zone & ~inner & ~open_, "open": open_ & zone, "flats": flats, "lab": lab, "lanes": lanes,
             "ring1": ring1, "ring2": ring2}
        self._templates[key] = t
        return t

    def reserved(self, n: int) -> np.ndarray:
        """Columns of level n its own halls take (level 1's cafeteria, sheriff's office, cells, airlock and lower
        ramp; the special levels' rooms), kept out of the flats and alleys so no flat or alley is left cut off behind
        a hall's wall. Found by drawing the halls once on an empty volume and noting where they write in the level's
        two walking rows."""
        if not hasattr(self, "_footprints"):
            real = self.v
            self.v = Volume(real.origin, real.size)
            try:
                self.level_one()
                self.specials()
                ids = self.v.ids
                self._footprints = {}
                for k in range(1, LEVELS + 1):
                    y = self.level_y(k)
                    self._footprints[k] = (ids[:, y:y + 2, :] != 0).any(axis=1)
            finally:
                self.v = real
        return self._footprints[n] & self.ring(self.s.r_facade + 1.0, self.s.r_inner_wall)

    def specials(self) -> None:
        """The canon special levels' rooms (levels.Furnisher), drawn over the finished levels."""
        from levels import Furnisher
        Furnisher(self).all()


    def _doors(self, flats: list[dict], lab: np.ndarray, access: np.ndarray) -> None:
        """One door per flat, chosen so every flat is reached: the flats and the open space (gallery, alleys) are a
        graph, a door through a wall is an edge, and the doors are a spanning tree grown from the open space (Prim).
        A flat's best door opens straight onto the open space through a straight wall (walls on both sides along it)
        near the middle of its frontage; where diagonal walls step, the door goes through a corner or through two
        wall cells; a flat with no frontage at all opens into a neighbouring flat that already has its way out."""
        n = lab.shape[0]
        wall = (lab == 0) & ~access
        cands: dict[int, list] = {f["label"]: [] for f in flats}
        for f in flats:
            i = f["label"]
            cx, cz = f["cells"].mean(axis=0)
            for x, z in f["cells"]:
                for dx, dz, facing in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
                    run = []
                    for k in (1, 2, 3):
                        wx, wz = x + k * dx, z + k * dz
                        if not (0 <= wx < n and 0 <= wz < n):
                            break
                        if wall[wx, wz]:
                            run.append((int(wx), int(wz)))
                            continue
                        if not run:
                            break
                        to = 0 if access[wx, wz] else int(lab[wx, wz])
                        if to == i:
                            break
                        sx, sz = -dz, dx                            # along the wall, beside the first door cell
                        w0x, w0z = run[0]
                        square = all(wall[w0x + a * sx, w0z + a * sz] for a in (1, -1))
                        rank = (0 if to == 0 else 3) + (0 if len(run) == 1 and square else 1 if len(run) == 1 else 2)
                        d = (x - cx) ** 2 + (z - cz) ** 2
                        cands[i].append((rank, d, to, run, facing, (int(x), int(z)), (int(wx), int(wz))))
                        break
        done = {0}
        todo = {f["label"]: f for f in flats}
        while todo:
            best = None
            for i in todo:
                for c in cands[i]:
                    if c[2] in done and (best is None or c[:2] < best[1][:2]):
                        best = (i, c)
            if best is None:
                break                                               # walled in for good: walk.py reports it
            i, (rank, d, to, run, facing, inside, outside) = best
            todo.pop(i)["door"] = (run[0], facing, inside, outside, run[1:])
            done.add(i)
        # furniture keeps clear of both ends of every door, including the doors of flats that open into this one
        by_label = {f["label"]: f for f in flats}
        for f in flats:
            f.setdefault("clear", set())
        for f in flats:
            if f["door"] is None:
                continue
            inside, outside = f["door"][2], f["door"][3]
            around = lambda c: {(c[0] + a, c[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
            f["clear"] |= around(inside)
            to = int(lab[outside])
            if to in by_label:
                by_label[to]["clear"] |= around(outside)

    # build ----------------------------------------------------------------------------------------------------------
    def build(self) -> Volume:
        s, v = self.s, self.v
        top = self.yi(0)
        # rock around and below everything inside the footprint; earth over the cap; the site blends the outside
        v.mask(0, top - 1, self.r < self.R, ROCK)
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
        import connect
        connect.tidy(v)
        connect.connect(v)
        import lighting
        void_top = self.yi(self.void_top_rel)
        self.lights = lighting.light_up(v, lambda y: 3 if y < void_top else 12)
        return v

    def shell(self) -> None:
        s, v = self.s, self.v
        y_top = self.level_y(1) + s.pitch                  # the cap over level 1
        y_bot = self.yi(self.gen_floor_rel) - 1
        v.mask(y_bot, y_top, self.ring(s.r_inner_wall, s.r_outer), SHELL)
        v.mask(y_bot + 1, self.level_y(1) + s.pitch - 2, self.r < s.r_inner_wall, AIR)
        v.mask(self.level_y(1) + s.pitch - 1, y_top, self.r < s.r_outer, CONCRETE)
        # the gallery columns run from the bottom level up to the dome's springing
        v.mask(self.level_y(LEVELS) - 1, self.level_y(1) + s.pitch - 2, self.columns, CONCRETE)

    # levels ---------------------------------------------------------------------------------------------------------
    def level(self, n: int) -> None:
        s, v = self.s, self.v
        y = self.level_y(n)
        deep = n > 120
        t = self.template(n)
        floor = FLOOR_DEEP if deep else FLOOR
        wall_state = CONCRETE_DARK if deep else (MEDICAL_WALL if dressing_for(n) == "medical" else CONCRETE)
        lamp = lamp_for(n)
        # floors: landing, gallery and everything behind it; the next level's floor is this level's ceiling
        v.mask(y - 1, y - 1, (self.ring(s.r_stair_wall, s.r_landing) | self.ring(s.r_atrium, s.r_inner_wall)) & ~self.columns,
               floor)
        v.mask(y, y + s.pitch - 2, t["walls"], wall_state)
        v.mask(y, y + s.pitch - 2, self.facade_ring, wall_state)
        # gallery: parapet on the edge between the columns, a light collar round each column at the top row
        v.mask(y, y, self.ring(s.r_atrium, s.r_atrium + 1.0) & ~self.columns, PARAPET)
        v.mask(y + s.pitch - 2, y + s.pitch - 2, self.columns, lamp)
        # landing ring: parapets on both edges, open toward the flight where it lands and at the bridges
        v.mask(y, y, self.ring(s.r_stair_wall, s.r_stair_wall + 1.0) & ~self.stair_gate(n), PARAPET)
        v.mask(y, y, self.ring(s.r_landing - 1.0, s.r_landing), PARAPET)
        for a in self.bridge_angles(n):
            self.bridge(y, a)
        self.facades(n, y, t, wall_state, lamp)
        self.flats(n, y, t, lamp, wall_state)
        self.alley_lights(n, y, t, lamp)
        # the gallery's own light: hanging fittings under the soffit, one per bay, clear of the parapet
        for b in range(s.bays):
            x, z = self.polar(s.r_facade - 1.2, self.bay_center(b))
            if v.get(x, y + 3, z) == AIR:
                v.set(x, y + 3, z, HANG)
                v.set(x, y + 4, z, CHAIN)
            self.walkway_props(n, y, b, wall_state)

    def stair_angle(self, n: int) -> float:
        return (n * GOLDEN) % TAU

    def stair_gate(self, n: int) -> np.ndarray:
        """Where level n's landing opens onto the flight: the 30 degrees after the stair angle, where the flight runs
        down from the landing's floor. Before the stair angle the flight is a whole turn (4.3 blocks) lower: closed."""
        d = ((self.theta - self.stair_angle(n) + math.pi) % TAU) - math.pi
        return (d >= 0) & (d < math.radians(30))

    def bridge(self, y: int, a: float) -> None:
        s, v = self.s, self.v
        d = self.off(a)
        lateral = d * self.r
        front = d < math.pi / 2
        span = (lateral < 1.6) & front & self.ring(s.r_landing - 1.0, s.r_atrium + 1.0)
        v.mask(y - 1, y - 1, span, GRATE)
        rails = (np.abs(lateral - 2.0) < 0.5) & front & self.ring(s.r_landing, s.r_atrium)
        v.mask(y, y, rails, PARAPET)
        gap = (lateral < 1.6) & front & (self.ring(s.r_atrium, s.r_atrium + 1.0) | self.ring(s.r_landing - 1.0, s.r_landing))
        v.mask(y, y, gap & ~self.columns, AIR)

    def steel_door(self, y: int, cells: list[tuple[int, int]], facing: str, plates: bool = True) -> None:
        """Iron door (one or a pair) facing `facing`, opened by heavy pressure plates on both sides."""
        v = self.v
        fx, fz = DIRS[facing]
        rx, rz = -fz, fx
        if len(cells) == 2:
            (x0, z0), (x1, z1) = cells
            if (x1 - x0) * rx + (z1 - z0) * rz < 0:
                cells = [cells[1], cells[0]]
        for i, (x, z) in enumerate(cells):
            hinge = "left" if (len(cells) == 1 or i == 0) else "right"
            for half, dy in (("lower", 0), ("upper", 1)):
                v.set(x, y + dy, z, f"minecraft:iron_door[facing={facing},half={half},hinge={hinge},open=false,powered=false]")
            if plates:
                for k in (1, -1):
                    px, pz = x + k * fx, z + k * fz
                    if v.get(px, y, pz) == AIR and (px, pz) not in cells:
                        v.set(px, y, pz, PLATE)

    def facades(self, n: int, y: int, t: dict, wall_state: str, lamp: str) -> None:
        s, v = self.s, self.v
        alleys = set(self.alley_bays(n))
        self.facade_entries: set[tuple[int, int]] = set()     # first cell behind each facade door (flat_door)
        for b in range(s.bays):
            if b in alleys:
                self.alley_portal(y, b)
            else:
                self.facade(n, y, b, variant_for(n, b), wall_state, lamp)

    def alley_portal(self, y: int, b: int) -> None:
        """The alley's opening in the facade: 4 wide, 4 high, the top corners rounded (everything is round, Tyldum)."""
        v = self.v
        for x, z, u, th in self.bay_cells[b]:
            lat = abs(self.r[x, z] * math.sin(th - self.bay_center(b)))
            if lat < self.s.alley_half:
                top = 3 if lat < self.s.alley_half - 1 else 2
                for dy in range(top + 1):
                    v.set(x, y + dy, z, AIR)

    def facade(self, n: int, y: int, b: int, variant: str, wall_state: str, lamp: str) -> None:
        """One bay's face on the gallery, rasterised from the model's BAY builder (bays.FACADES) over the facade's five
        rows: the lower storey (rows 0-2) and the upper storey (rows 3-4)."""
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
        if not doors:                                   # every front flat opens on the gallery
            ci = min(range(len(us)), key=lambda i: abs(us[i] - (HW * 0.55)))
            doors.append([ci])
            grid[(ci, 0)] = grid[(ci, 1)] = "DOOR"
        for kind, x0, x1, y0, y1 in later:
            cols = cols_of(us, x0, x1)
            if kind == "shop":
                mids = [i for i in cols if abs(us[i]) <= 1.1] or [min(cols, key=lambda i: abs(us[i]))]
            for ci in cols:
                for row in rows_of(y0, y1, 5, 2.0):
                    if grid.get((ci, row)) == "DOOR":
                        continue
                    if kind == "pilaster":
                        grid.setdefault((ci, row), PILASTER)
                        continue
                    if kind in ("window", "slit", "glazed"):
                        st = PANE
                    elif kind == "grate":
                        st = GRATE if deep else GRATE_UP
                    elif kind == "chute":
                        st = "minecraft:hopper[enabled=true,facing=down]"
                    elif kind == "leaf":
                        st = "minecraft:iron_block"
                    else:
                        st = AIR if ci in mids else PANE
                    grid[(ci, row)] = st
        # upper storey: small windows over the lower storey's openings (oby0Dk/52-54)
        for ci in range(1, len(cells) - 1, 3):
            grid.setdefault((ci, 3), PANE)
        for (ci, row), st in grid.items():
            if st != "DOOR":
                v.set(cells[ci][0], y + row, cells[ci][1], st)
        for cols in doors:
            a = sum(cells[ci][3] for ci in cols) / len(cols)
            facing = self.facing_radial(a + math.pi)
            fx, fz = DIRS[facing]
            if len(cols) == 2:
                (x0, z0), (x1, z1) = [cells[ci][:2] for ci in cols]
                if (x1 - x0) * fx + (z1 - z0) * fz != 0:        # a pair one behind the other (stepped facade): the
                    cols = [min(cols, key=lambda ci: self.r[cells[ci][0], cells[ci][1]])]   # front leaf alone
            # where the round facade steps, it is two cells thick along the door's axis: open the cell behind too
            for ci in cols:
                bx, bz = cells[ci][0] - fx, cells[ci][1] - fz
                if self.facade_ring[bx, bz]:
                    v.set(bx, y, bz, AIR)
                    v.set(bx, y + 1, bz, AIR)
                    bx, bz = bx - fx, bz - fz
                self.facade_entries.add((int(bx), int(bz)))
            self.steel_door(y, [(cells[ci][0], cells[ci][1]) for ci in cols], facing)
        for u in spec.get("lamps", ()):
            ci = min(range(len(us)), key=lambda i: abs(us[i] - u))
            for row in (2, 3, 1):
                if (ci, row) not in grid:
                    v.set(cells[ci][0], y + row, cells[ci][1], lamp)
                    grid[(ci, row)] = lamp
                    break
        if "stoop" in spec:
            door_cols = {ci for cols in doors for ci in cols}
            for ci, (x, z, u, th) in enumerate(cells):
                if ci in door_cols:
                    continue
                fx, fz = self.polar(self.s.r_facade - 0.5, th)
                if v.get(fx, y, fz) == AIR:
                    v.set(fx, y, fz, STOOP)

    def flats(self, n: int, y: int, t: dict, lamp: str, wall_state: str) -> None:
        """Every flat: its door onto the gallery or an alley, a lamp, and on residential levels a home to live in
        (rug, table and chairs, a kitchen counter, a bed, a chest; poorer in the Down Deep). The front flats' doors
        are in the facade (facade())."""
        v = self.v
        dress = dressing_for(n)
        poor = region(n) == "deep"
        for f in t["flats"]:
            if f["open"]:                                       # a cut-off stretch of alley: only its door
                if f["door"]:
                    self.flat_door(y, f["door"], wall_state)
                continue
            cells = f["cells"]
            cx, cz = cells.mean(axis=0)
            k = int(np.argmin(((cells - [cx, cz]) ** 2).sum(axis=1)))
            lx, lz = cells[k]
            v.set(int(lx), y + self.s.pitch - 2, int(lz), lamp)
            if f["door"]:
                self.flat_door(y, f["door"], wall_state, cells)
            if dress in ("residential", "admin") and not (n in ROOM_LEVELS):
                self.home(n, y, f, poor)
            elif n > 1 and dress not in ("residential", "admin"):
                self.store(n, y, f)

    def flat_door(self, y: int, door: tuple, wall_state: str, cells: np.ndarray | None = None) -> None:
        """A flat's way out (template()._doors). Through the facade the facade's own door serves, if one of the
        bay's doors opens into this flat; otherwise this one is cut."""
        v = self.v
        (wx, wz), facing, inside, outside, through = door
        if self.r[wx, wz] < self.s.r_facade + 1.0 and cells is not None:
            if any((int(x), int(z)) in self.facade_entries for x, z in cells):
                return
        for tx, tz in through:                                  # the rest of a thick (stepped) wall: a short passage
            for dy in (0, 1):
                v.set(tx, y + dy, tz, AIR)
        self.steel_door(y, [(wx, wz)], facing)
        if v.get(wx, y + 2, wz) == AIR:
            v.set(wx, y + 2, wz, wall_state)

    def home(self, n: int, y: int, f: dict, poor: bool) -> None:
        v = self.v
        L = n - 1
        rnd = lambda k: seeded(L, f["label"], 500 + k)
        cells = [tuple(map(int, c)) for c in f["cells"]]
        if len(cells) < 9:
            return
        cellset = set(cells)
        door = f["door"]
        near_door = self.keep_clear(f)
        if door:
            ix, iz = door[2]
            near_door |= {(ix + a, iz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        def wall_n(c):
            return sum((c[0] + dx, c[1] + dz) not in cellset for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        free = [c for c in cells if c not in near_door and v.get(c[0], y, c[1]) == AIR]
        if not free:
            return
        wood = ("spruce", "oak", "dark_oak", "birch")[int(rnd(0) * 4)] if not poor else "spruce"
        rug = ("red", "brown", "green", "blue", "orange", "cyan", "light_gray")[int(rnd(1) * 7)]
        bed = ("light_gray", "white", "gray", "brown", "blue")[int(rnd(2) * 5)]
        dpos = np.array(door[2]) if door else np.array(cells[0])
        far = sorted(free, key=lambda c: -((c[0] - dpos[0]) ** 2 + (c[1] - dpos[1]) ** 2))
        used = set()
        # bed in the far corner along a wall
        for c in far[:12]:
            for facing, (dx, dz) in DIRS.items():
                foot = (c[0] - dx, c[1] - dz)
                head_wall = (c[0] + dx, c[1] + dz) not in cellset
                if head_wall and foot in cellset and foot not in near_door and v.get(foot[0], y, foot[1]) == AIR:
                    v.set(c[0], y, c[1], f"minecraft:{bed}_bed[facing={facing},occupied=false,part=head]")
                    v.set(foot[0], y, foot[1], f"minecraft:{bed}_bed[facing={facing},occupied=false,part=foot]")
                    used |= {c, foot}
                    side = (c[0] + dz, c[1] + dx)
                    if side in cellset and v.get(side[0], y, side[1]) == AIR:
                        v.set(side[0], y, side[1], CRATE if poor else f"minecraft:{wood}_planks")
                        v.set(side[0], y + 1, side[1], "minecraft:lantern[hanging=false,waterlogged=false]")
                        used.add(side)
                    break
            else:
                continue
            break
        # kitchen counter along a wall: two to four blocks
        kitchen = [f"minecraft:smoker[facing=north,lit=false]", "minecraft:cauldron", CRATE, f"minecraft:{wood}_planks"]
        if poor:
            kitchen = ["minecraft:furnace[facing=north,lit=false]", CRATE]
        wall_cells = [c for c in far[len(far) // 3:] if wall_n(c) >= 1 and c not in used]
        for j, c in enumerate(wall_cells[: len(kitchen)]):
            v.set(c[0], y, c[1], kitchen[j])
            used.add(c)
        # table with chairs in the middle
        mid = [c for c in free if wall_n(c) == 0 and c not in used]
        if mid:
            c = mid[len(mid) // 2]
            if not poor:
                for a in (-1, 0, 1):
                    for b in (-1, 0, 1):
                        cc = (c[0] + a, c[1] + b)
                        if cc in cellset and cc not in used and cc not in near_door and v.get(cc[0], y, cc[1]) == AIR:
                            v.set(cc[0], y, cc[1], f"minecraft:{rug}_carpet")
            v.set(c[0], y, c[1], f"minecraft:{wood}_fence[east=false,north=false,south=false,waterlogged=false,west=false]")
            v.set(c[0], y + 1, c[1], f"minecraft:{wood}_pressure_plate[powered=false]")
            for facing, (dx, dz) in DIRS.items():
                cc = (c[0] + dx, c[1] + dz)
                if cc in cellset and cc not in near_door and rnd(10 + dx * 3 + dz) < (0.45 if poor else 0.8):
                    st = v.get(cc[0], y, cc[1])
                    if st == AIR or (st or "").endswith("_carpet"):
                        v.set(cc[0], y, cc[1], f"minecraft:{wood}_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]")
        if rnd(20) < 0.6:
            for c in far[5:]:
                if c not in used and wall_n(c) >= 1 and v.get(c[0], y, c[1]) == AIR:
                    v.set(c[0], y, c[1], "minecraft:chest[facing=north,type=single,waterlogged=false]")
                    break

    def store(self, n: int, y: int, f: dict) -> None:
        """Department levels: the flats are store rooms and workshops: crates along the walls."""
        v = self.v
        cells = [tuple(map(int, c)) for c in f["cells"]]
        cellset = set(cells)
        door = f["door"]
        near = self.keep_clear(f)
        if door:
            ix, iz = door[2]
            near |= {(ix + a, iz + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        for i, c in enumerate(cells):
            if c in near or i % 3:
                continue
            if any((c[0] + dx, c[1] + dz) not in cellset for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                if v.get(c[0], y, c[1]) == AIR:
                    v.set(c[0], y, c[1], STOCK)

    def alley_lights(self, n: int, y: int, t: dict, lamp: str) -> None:
        """Lamps in the alleys' ceilings every few blocks (S2 alleys: lanterns and a lit lattice overhead)."""
        v = self.v
        m = t["open"] & ((self.X + self.Z * 3) % 7 == 0)
        v.mask(y + self.s.pitch - 2, y + self.s.pitch - 2, m, lamp)

    def walkway_props(self, n: int, y: int, b: int, wall_state: str) -> None:
        """The model's per-bay dressing on the gallery (buildWindow), placed only where it leaves a way past."""
        v, s = self.v, self.s
        if n == 1 or (n in ROOM_LEVELS and b == ROOM_BAY) or b in self.alley_bays(n):
            return
        L, dress, reg = n - 1, dressing_for(n), region(n)
        r = seeded(L, b, 400)
        u = (seeded(L, b, 401) - 0.5) * BAY_ARC_DEG * 0.6
        th = self.bay_center(b) + math.radians(u)
        x, z = self.polar(s.r_facade - 0.5, th)
        if v.get(x, y, z) != AIR or v.get(x, y - 1, z) not in (FLOOR, FLOOR_DEEP):
            return
        if any(v.get(x + dx, y, z + dz) == PLATE for dx, dz in DIRS.values()):
            return
        if dress == "farming":
            v.set(x, y, z, "minecraft:flowering_azalea")
            v.set(x, y - 1, z, MOSS)
        elif dress == "bazaar":
            v.set(x, y, z, CRATE if r < 0.5 else SACK)
        elif dress == "mechanical":
            v.set(x, y, z, DRUM if r < 0.5 else "minecraft:smithing_table")
        elif dress == "recycling":
            v.set(x, y, z, "minecraft:dried_kelp_block" if r < 0.5 else SACK)
        elif dress == "residential" and r < (0.15 if reg == "deep" else 0.35):
            v.set(x, y, z, "minecraft:potted_azalea_bush" if r < 0.2 else CRATE)

    # the stair ------------------------------------------------------------------------------------------------------
    def stair(self) -> None:
        """One uniform helix round the solid core from level 1 down to the generator hall floor; level n is reached
        at its stair angle n * 137.5 degrees. Solid parapet on the flight's outer edge (plan t2014s)."""
        s, v = self.s, self.v
        per_turn = s.pitch / (1 + GOLDEN / TAU)        # drop per full turn
        y1 = self.level_y(1)
        y_bottom = self.yi(self.gen_floor_rel)
        top_idx = self.level_y(1) + s.pitch - 2
        v.mask(y_bottom, top_idx, self.core, CONCRETE)
        a1 = GOLDEN % TAU
        gates: dict[int, np.ndarray] = {}
        for m, solid in ((self.flight, True), (self.stair_wall, False)):
            xs, zs = np.nonzero(m)
            for x, z in zip(xs, zs):
                t = ((self.theta[x, z] - a1) % TAU) / TAU
                while True:
                    surf = y1 - t * per_turn
                    if surf < y_bottom - 0.01:
                        break
                    q = round(surf * 2) / 2
                    if solid:
                        if q == int(q):
                            v.set(x, int(q) - 1, z, STEEL)
                        else:
                            v.set(x, int(math.floor(q)), z, STEEL_SLAB_B)
                    else:
                        # the parapet stands on the helix at the flight's own tread height, open where the flight
                        # meets a level's landing (stair_gate); there its base is the floor between landing and flight
                        yb = int(math.floor(q))
                        lvl = (y1 - yb) / s.pitch
                        v.set(x, yb - 1, z, CONCRETE)
                        n = int(round(lvl)) + 1
                        if abs(lvl - round(lvl)) * s.pitch > 0.6 or not gates.setdefault(n, self.stair_gate(n))[x, z]:
                            v.set(x, yb, z, PARAPET)
                    t += 1

    def dome(self) -> None:
        """The dome over the atrium (BFDG t2240s, "dome at top of SHAFT for Main Lighting"): a shallow spherical cap
        springing from the gallery edge, its inside cut into oval coffers by ribs, a lit rig hanging from the crown."""
        s, v = self.s, self.v
        base = self.level_y(1) + s.pitch - 1            # level 1's ceiling row
        rs = s.r_atrium + 0.5
        h = s.dome_rise
        Rs = (rs * rs + h * h) / (2 * h)                # sphere radius through the springing and the crown
        cy = base + h - Rs                              # sphere centre (index units)
        inside = self.r < rs
        v.mask(base, base + h + 1, inside, CONCRETE)
        lat_step, n_mer = 1.6, 24
        for y in range(base, base + h + 1):
            yy = y + 0.5 - cy
            if yy >= Rs:
                continue
            rr = math.sqrt(max(0.0, Rs * Rs - yy * yy))
            hollow = self.r < rr - 0.5
            v.mask(y, y, hollow & inside, AIR)
            shell = (self.r >= rr - 0.5) & (self.r < rr + 0.7) & inside
            # coffers: between meridian ribs every 15 degrees and parallels every ~1.6 m of height
            mer = (np.mod(self.theta, TAU / n_mer) > 0.06 * TAU / n_mer * 6)
            par = (y - base) % 2 == 1
            v.mask(y, y, shell & mer & par, "minecraft:white_concrete")
            v.mask(y, y, shell & mer & par & (np.mod(self.theta + TAU / (2 * n_mer), TAU / n_mer) < TAU / n_mer * 0.35), LAMP_COOL)
        # crown: an oculus of light, and the rig: a ring of lamps hanging on chains
        v.mask(base + h, base + h + 1, self.r < 2.5, LAMP_COOL)
        rig_y = base + h - 3
        for k in range(12):
            x, z = self.polar(4.0, k * TAU / 12)
            for yy in range(rig_y + 1, base + h + 1):
                if v.get(x, yy, z) == AIR:
                    v.set(x, yy, z, CHAIN)
            v.set(x, rig_y, z, "minecraft:sea_lantern")

    # level 1 --------------------------------------------------------------------------------------------------------
    def level_one(self) -> None:
        """Rooms first, then the openings between them: a later room's wall must never close an earlier doorway."""
        self.openings = []
        self.cafeteria()
        self.sheriff()
        self.way_out()
        for carve in self.openings:
            carve()

    def disc(self, cx: float, cz: float, r: float) -> np.ndarray:
        return np.hypot(self.X - cx, self.Z - cz) < r

    def rect(self, x0: int, x1: int, z0: int, z1: int) -> np.ndarray:
        return (self.X >= x0) & (self.X <= x1) & (self.Z >= z0) & (self.Z <= z1)

    def cafeteria(self) -> None:
        """Level 1's cafeteria, its own round hall behind the gallery (BFDG t2338s option 03, t2375s model, 39:19:
        no columns): Ø28, a few steps down from an oval portal, a 5 m ceiling of concentric rings and radial beams
        round a flower-shaped light, the curved screen with oval ends on the far wall opposite the portal (40:34),
        the serving counter along the wall between the two entrances."""
        s, v = self.s, self.v
        y = self.level_y(1)
        hx, hz, hr = HALL
        hall = self.disc(hx, hz, hr)
        wall = self.disc(hx, hz, hr + 1.2) & ~hall
        fl = y - 1                                       # walking row inside: one step down from the gallery
        v.mask(fl - 1, y + 4, wall, CONCRETE)
        v.mask(fl, y + 3, hall, AIR)
        v.mask(fl - 1, fl - 1, hall, "minecraft:polished_andesite")
        v.mask(y + 4, y + 4, hall, "minecraft:white_concrete")
        dx, dz = self.X - hx, self.Z - hz
        d = np.hypot(dx, dz)
        ang = np.mod(np.arctan2(dz, dx), TAU)            # hall-local bearing: 0 east (the portal), pi west (screen)
        offa = lambda a: np.abs(((ang - a + math.pi) % TAU) - math.pi)
        # ceiling: concentric rings and radial beams, the flower over the middle
        beams = (np.mod(ang, TAU / 12) < 0.09) & (d > 3.2)
        rings = (np.abs(d - 6.5) < 0.5) | (np.abs(d - 10.5) < 0.5)
        v.mask(y + 4, y + 4, hall & (beams | rings), "minecraft:smooth_stone")
        petal_a = np.mod(ang, TAU / 8) - TAU / 16
        petal = (d >= 1.0) & (d < 3.6) & (np.abs(petal_a) * np.maximum(d, 1) < 1.1 - 0.25 * np.abs(d - 2.3))
        v.mask(y + 4, y + 4, hall & petal, LAMP_COOL)
        v.mask(y + 4, y + 4, hall & (d < 1.0), "minecraft:sea_lantern")
        v.mask(y + 3, y + 3, hall & (d < 0.8), "minecraft:end_rod[facing=down]")
        # wall panelling and sconces
        face = hall & (d >= hr - 1.0)
        v.mask(fl, y + 3, face, "minecraft:dark_oak_planks")
        v.mask(y + 1, y + 1, face & (np.mod(ang, TAU / 20) < 0.12), "minecraft:shroomlight")
        # the screen on the far wall: 70 degrees of arc, rows 1-3 over the floor, oval ends in black
        screen = face & (offa(math.pi) < SCREEN_ARC / 2)
        ends = face & (offa(math.pi) >= SCREEN_ARC / 2) & (offa(math.pi) < SCREEN_ARC / 2 + 0.08)
        v.mask(fl + 1, y + 2, screen, "minecraft:gray_stained_glass")
        v.mask(fl + 1, y + 2, ends, "minecraft:black_concrete")
        v.mask(fl, fl, screen, "minecraft:black_concrete")
        v.mask(y + 3, y + 3, screen, "minecraft:black_concrete")
        # the oval portal from the gallery and the half steps down
        portal = (np.abs(self.Z - hz) <= 2) & (self.X <= -int(s.r_facade) + 1) & (self.X >= hx + hr - 1)
        v.mask(y, y + 2, portal, AIR)
        v.mask(y + 3, y + 3, portal & (np.abs(self.Z - hz) <= 1), AIR)
        v.mask(y - 1, y - 1, portal, "minecraft:polished_andesite")
        v.mask(fl, fl, portal & (self.X == hx + hr - 1), STOOP)
        # the second entrance, north-east, and its passage to the sheriff's office (passing under the ramp)
        ex, ez = HALL_DOOR
        ox, oz, orr = OFFICE
        # it runs from inside the panelling to inside the office's round wall; carved in level_one() after every room
        # of level 1 stands, so neither the hall's panelling nor the office's wall ring closes it again
        pas = (np.abs(self.X - ex) <= 1) & (self.Z <= ez + 4) & (self.Z >= oz + orr - 1) & (d >= hr - 1.0)
        sides = (np.abs(self.X - ex) == 2) & (self.Z <= ez) & (self.Z >= oz + orr) & (d >= hr + 1.0)

        def passage() -> None:
            v.mask(y - 1, y + 3, sides | (pas & (d >= hr + 1.2)), CONCRETE)
            v.mask(y, y + 2, pas, AIR)
            v.mask(y - 1, y - 1, pas & (d >= hr), "minecraft:polished_andesite")
            v.mask(fl, fl, pas & (d < hr), STOOP)
            v.mask(y + 3, y + 3, pas & (self.X == ex) & (self.Z % 4 == 0) & (d >= hr + 1.2), "minecraft:sea_lantern")
        self.openings.append(passage)
        # the serving counter on the arc between the two entrances
        door_a = math.atan2(ez - hz, ex - hx) % TAU
        counter = hall & (np.abs(d - (hr - 2.5)) < 0.5) & (ang > door_a + 0.2) & (ang < TAU - 0.2)
        v.mask(fl, fl, counter, "minecraft:spruce_slab[type=top,waterlogged=false]")
        xs, zs = np.nonzero(counter)
        for i, (x, z) in enumerate(zip(xs, zs)):
            if i % 3 == 0:
                v.set(x, fl + 1, z, "minecraft:lantern[hanging=false,waterlogged=false]")
        # tables 0.8 x 1.6 set tangentially in rings with chairs both sides (60-70 tables, t2375s), clear of the
        # aisles from the two entrances, the counter and the screen's foot
        aisle = lambda a, r: min(abs(((a - g + math.pi) % TAU) - math.pi) * r for g in (0.0, door_a)) < 2.5
        rr = 4.5
        while rr < hr - 3.5:
            count = int(TAU * rr / 3.4)
            for k in range(count):
                a = (k + 0.5) * TAU / count
                if aisle(a, rr) or (rr > hr - 6 and abs(((a - math.pi + math.pi) % TAU) - math.pi) < SCREEN_ARC / 2):
                    continue
                for sg in (-0.4, 0.4):
                    X_, Z_ = self.at(int(round(hx + rr * math.cos(a + sg / rr))), int(round(hz + rr * math.sin(a + sg / rr))))
                    v.set(X_, fl, Z_, "minecraft:spruce_slab[type=top,waterlogged=false]")
                for sd in (-1, 1):
                    X_, Z_ = self.at(int(round(hx + (rr + sd) * math.cos(a))), int(round(hz + (rr + sd) * math.sin(a))))
                    if v.get(X_, fl, Z_) == AIR:
                        back = self.facing_radial(a if sd > 0 else a + math.pi)
                        v.set(X_, fl, Z_, f"minecraft:oak_stairs[facing={back},half=bottom,shape=straight,waterlogged=false]")
            rr += 3.6

    def sheriff(self) -> None:
        """The sheriff's office (BFDG 44:08, EN wiki): round, concentric circles in the floor, desks round the middle,
        entered through the cafeteria; the holding cells on the same floor along one wall, behind barred fronts."""
        v = self.v
        y = self.level_y(1)
        ox, oz, orr = OFFICE
        room = self.disc(ox, oz, orr + 0.5)
        wall = self.disc(ox, oz, orr + 1.7) & ~room
        vest = self.rect(CELLS_X[1] + 2, ox - orr + 1, CELLS_Z[0][0], CELLS_Z[-1][1])     # in front of the cells
        cells = np.zeros_like(room)
        for z0, z1 in CELLS_Z:
            cells |= self.rect(CELLS_X[0], CELLS_X[1], z0, z1)
        block = self.rect(CELLS_X[0] - 1, ox, CELLS_Z[0][0] - 1, CELLS_Z[-1][1] + 1) | wall
        v.mask(y - 1, y + 4, block, CONCRETE)
        v.mask(y, y + 3, room | vest | cells, AIR)
        v.mask(y - 1, y - 1, room | vest, "minecraft:polished_andesite")
        v.mask(y - 1, y - 1, cells, "minecraft:white_glazed_terracotta[facing=north]")
        dd = np.hypot(self.X - ox, self.Z - oz)
        v.mask(y - 1, y - 1, room & ((np.abs(dd - 2.5) < 0.5) | (np.abs(dd - 4.5) < 0.5)), "minecraft:polished_blackstone")
        v.mask(y + 3, y + 3, room & (np.abs(dd - 3) < 0.6), LAMP_COOL)
        # desks round the middle, a chair behind each, facing out
        for k in range(6):
            a = k * TAU / 6 + 0.3
            X_, Z_ = self.at(int(round(ox + 2.0 * math.cos(a))), int(round(oz + 2.0 * math.sin(a))))
            v.set(X_, y, Z_, "minecraft:dark_oak_slab[type=top,waterlogged=false]")
            if k % 2 == 0:
                v.set(X_, y + 1, Z_, "minecraft:lantern[hanging=false,waterlogged=false]")
            X_, Z_ = self.at(int(round(ox + 1.0 * math.cos(a))), int(round(oz + 1.0 * math.sin(a))))
            if v.get(X_, y, Z_) == AIR:
                v.set(X_, y, Z_, f"minecraft:spruce_stairs[facing={OPP[self.facing_radial(a)]},half=bottom,shape=straight,waterlogged=false]")
        # barred fronts with a cell door; a bunk in each
        fx = CELLS_X[1] + 1
        for z0, z1 in CELLS_Z:
            for z in range(z0, z1 + 1):
                X_, Z_ = self.at(fx, z)
                for dy in range(3):
                    v.set(X_, y + dy, Z_, RAIL)
            X_, Z_ = self.at(fx, (z0 + z1) // 2)
            for half, dy in (("lower", 0), ("upper", 1)):
                v.set(X_, y + dy, Z_, f"minecraft:iron_door[facing=west,half={half},hinge=left,open=false,powered=false]")
            v.set(X_ + 1, y, Z_, PLATE)
            v.set(X_ - 1, y, Z_, PLATE)
            bx, bz = self.at(CELLS_X[0], z0)
            v.set(bx, y, bz, "minecraft:gray_bed[facing=west,occupied=false,part=head]")
            v.set(bx + 1, y, bz, "minecraft:gray_bed[facing=west,occupied=false,part=foot]")
            X_, Z_ = self.at(CELLS_X[0] + 1, z1)
            v.set(X_, y + 3, Z_, "minecraft:sea_lantern")

    def way_out(self) -> None:
        """Holding cell 3 -> the airlock (a thick door ≈2.4 m at each end, BFDG 46:23; "these two big sliding doors
        each weigh 25 tons", S3E09: here each is a pair of iron leaves in a steel frame) -> a U-turn -> the ribbed ramp
        (LOW, CROSS, then up the axis) -> a slot with steps on the ring's axis, opening on the bowl floor inside half
        its radius (SPEC 5, S1E02 #25/#27, S3E09 #77). The slot's curb and the camera block are surface.py's."""
        v = self.v
        y = self.level_y(1)
        grade = self.yi(0)                               # the bowl floor's top block; its walking surface is grade + 1
        z0, z1 = CELLS_Z[-1]
        lock = self.rect(LOCK[0], LOCK[1], z0, z1)
        turn = self.rect(TURN_X[0], TURN_X[1], z0, LOW_Z[1])
        v.mask(y - 1, y + 4, self.rect(TURN_X[0] - 1, LOCK[1] + 1, z0 - 1, LOW_Z[1] + 1), CONCRETE)
        v.mask(y, y + 2, lock | turn, AIR)
        v.mask(y - 1, y - 1, lock | turn, "minecraft:polished_andesite")
        v.mask(y + 3, y + 3, lock & ((self.X % 2) == 0) & (self.Z == (z0 + z1) // 2), "minecraft:sea_lantern")
        # the thick doors: steel frames round a 2 x 2 opening, the leaves a pair of iron doors
        for dx in (LOCK[1] + 1, LOCK[0] - 1):
            v.mask(y - 1, y + 3, self.rect(dx, dx, z0 - 1, z1 + 1), "minecraft:iron_block")
            v.mask(y, y + 1, self.rect(dx, dx, z0 + 1, z1), AIR)
            self.steel_door(y, [self.at(dx, z0 + 1), self.at(dx, z0 + 2)], "west")
        ceil1 = y + self.s.pitch - 1                     # level 1's ceiling row: the upper runs never dig below it
        top = grade + 1 - STEPS                          # walking surface where the steps begin
        lz, cx = (LOW_Z[0] + LOW_Z[1]) // 2, (CROSS_X[0] + CROSS_X[1]) // 2
        # the centre line: (x, z, walking surface, along, kind); along is the run's axis ("x" or "z")
        line = []
        for x in range(LOW_X[0], cx):
            line.append((x, lz, y + 6 * (x - LOW_X[0]) / (cx - LOW_X[0]), "x", "low"))
        for z in range(lz, 0):
            line.append((cx, z, y + 6 + 2 * (z - lz) / (0 - lz), "z", "up"))
        for x in range(cx, RAMP_X[1] + 1):
            line.append((x, 0, y + 8 + (top - y - 8) * (x - cx) / (RAMP_X[1] - cx), "x", "up"))
        for x in range(RAMP_X[1] + 1, EXIT_X + 1):
            line.append((x, 0, top + (x - RAMP_X[1]), "x", "step"))
        inner = {}                                       # (x, z) -> (k, half, roof, kind, along, i)
        for i, (x, z, surf, along, kind) in enumerate(line):
            q = round(surf * 2) / 2
            k = int(math.floor(q))
            half = kind != "step" and q - k >= 0.5
            roof = grade + 1 if kind == "step" else min(k + (1 if half else 0) + 3, grade - 1)
            w = range(LOW_Z[0], LOW_Z[1] + 1) if kind == "low" else \
                (range(CROSS_X[0], CROSS_X[1] + 1) if along == "z" else range(RAMP_Z[0], RAMP_Z[1] + 1))
            for o in w:
                c = (o, z) if along == "z" else (x, o)
                if c not in inner:
                    inner[c] = (k, half, roof, kind, along, i)
        walls = {}
        for (x, z), (k, half, roof, kind, along, i) in inner.items():
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c = (x + dx, z + dz)
                    if c in inner or c[0] < LOW_X[0]:            # the west end opens into the U-turn
                        continue
                    lo = max(y - 1, k - 3) if kind == "low" else max(ceil1, k - 3)
                    hi = grade if kind == "step" else roof
                    o = walls.get(c)
                    walls[c] = (min(lo, o[0]), max(hi, o[1])) if o else (lo, hi)
        for (x, z), (lo, hi) in walls.items():
            X_, Z_ = self.at(x, z)
            for yy in range(lo, hi + 1):
                v.set(X_, yy, Z_, CONCRETE)
        for (x, z), (k, half, roof, kind, along, i) in inner.items():
            X_, Z_ = self.at(x, z)
            lo = max(y - 1, k - 3) if kind == "low" else max(ceil1, k - 3)
            hi = grade if kind == "step" else roof
            for yy in range(lo, hi + 1):
                v.set(X_, yy, Z_, CONCRETE if (yy < k or (yy == roof and kind != "step")) else AIR)
            if kind == "step":
                v.set(X_, k - 1, Z_, "minecraft:smooth_stone_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
                continue
            rib = ((z if along == "z" else x) % 2) == 0
            v.set(X_, k - 1, Z_, "minecraft:waxed_cut_copper" if rib else "minecraft:smooth_stone")
            if half:
                v.set(X_, k, Z_, "minecraft:waxed_cut_copper_slab[type=bottom,waterlogged=false]" if rib else STOOP)
            # lights: a sea lantern in the roof over the run's middle, every third block
            mid = (z == (LOW_Z[0] + LOW_Z[1]) // 2) if kind == "low" else \
                (x == cx if along == "z" else z == 0)
            if mid and i % 3 == 1 and roof < grade:
                v.set(X_, roof, Z_, "minecraft:sea_lantern")
        self.exit_cells = [(x, z) for x in range(RAMP_X[1] + 1, EXIT_X + 1) for z in range(RAMP_Z[0] - 1, RAMP_Z[1] + 2)]

    def keep_clear(self, f: dict) -> set[tuple[int, int]]:
        """Cells of a flat that furniture leaves free: both ends of its doors (the template's "clear") and the first
        cell behind a facade door that opens into it."""
        out = set(f.get("clear", ()))
        for x, z in getattr(self, "facade_entries", ()):
            out |= {(x + a, z + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        return out

    def door_plates(self) -> None:
        """Every iron door that leads through (open on both sides) gets its heavy plate on each side where the floor
        is free: a hall carved after the levels (Silo 1's cryo halls, the farms) must not leave a door that opens
        only one way."""
        v = self.v
        for i, st in enumerate(list(v.palette)):
            if not st.startswith("minecraft:iron_door") or "half=lower" not in st:
                continue
            fx, fz = DIRS[st.split("facing=")[1].split(",")[0].rstrip("]")]
            for x, y, z in zip(*np.nonzero(v.ids == i)):
                ends = [(x + k * fx, z + k * fz) for k in (1, -1)]
                if not all(v.get(px, y, pz) in (AIR, PLATE) for px, pz in ends):
                    continue                                   # a sealed hatch, or something stands there
                for px, pz in ends:
                    if v.get(px, y, pz) == AIR and v.get(px, y - 1, pz) not in (None, AIR):
                        v.set(px, y, pz, PLATE)

    def walk_ignore(self) -> list[tuple[int, int, int, int, int, int]]:
        """Boxes (silo frame x, row index, z; inclusive) whose unreachable standing places walk.py does not report:
        things built to bar the way, like the barricade on level 130."""
        return list(getattr(self, "walk_ignore_boxes", []))

    def walk_targets(self) -> dict[str, tuple[int, int, int]]:
        """Places walk.py requires reachable that its room check does not cover (silo frame x, row index, z)."""
        m = self.machines()
        out = {}
        if hasattr(m, "camp_at"):
            out["George's camp"] = m.camp_at
        return out

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
        X, Z = np.meshgrid(np.arange(x0, x1 + 1), np.arange(z0, z1 + 1), indexing="ij")
        inside = (np.abs(X) <= self.R) & (np.abs(Z) <= self.R)
        vol.ids.transpose(0, 2, 1)[inside] = 0
        return vol
