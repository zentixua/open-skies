"""The opening-day set at Silo 1 (S3E09, 2052): stage, stretch tents, chairs, the founders' plaque, carts and crates.

Sources: /mnt/project-files/silo/frames/s3e09/ and its notes.md (frames named by number below).
- Placement (03, the 2052 aerial frame zoomed): a cluster of white tents in the north half of Silo 1's bowl. The
  larger one is at the north; four smaller ones (west, south-west, south-east, east) stand on a ring of ~11 m round a
  dark centre, taken here as the seated audience. Its centre is ~21 m north and ~3 m west of the ring centre. Three
  small tents stand ~28 m west, a little south of centre. A straight path runs due south from the cluster, over the
  south berm, to a pale apron ~50 m wide on the ring path.
- Plot (RU wiki "Прощай"): the stage stands next to Silo 1.
- Stage (11, 12, 13):
  - a portal of bent dark-brown wooden ribs under a white fabric roof on silver box truss;
  - a curtain, and three light-wood vertical-slat back panels, the middle one with the gold sun emblem in a ring;
  - a dark wood lectern;
  - a floor ~0.9 m high (one block), with steps at both front corners;
  - slatted light-wood planters of pink and white flowers along the front;
  - white banners with the gold emblem at both sides;
  - a ~14 m opening between the truss towers.
- Tents and seats (14, 15): cream-white stretch tents on timber poles (eaves ~2.5 m, peaks 4-5 m) and long rows of
  grey folding chairs; the berm right behind the tents.
- Backstage (17): stacks of pale grey crates on dollies, a dark golf cart. Plaque (19, 20): a slanted metal plate on a
  waist-high stand, a white-canopied cart near it.

Ours (no frame gives it):
- The tent size (7 x 7) and the 12 m ring radius, fitted inside the floor (r 30).
- The audience centre 21 m north, so the stage's back reaches r 33 at the berm's foot.
- The number of chair rows.
- Where the plaque, carts and crates stand.
- The flower species.
- Each block standing for a material (bent wood = stripped dark oak, fabric = white wool, slats = bamboo planks,
  truss = iron bars).

build(ring_x, ring_z, floor_y) gives the set as a Volume in world coordinates; the floor's top block is floor_y and
nothing is placed in it. ground_paths(ring_x, ring_z) gives the path and apron columns, for the live laying in
paths.py (they cross the berm, whose heights only the world knows). Kept clear: the portal leaves (x ring-6..ring+7,
z ring-4..ring+4) and the camera block (x ring+10..ring+15, z ring-4..ring+4).
"""
from __future__ import annotations

import math

from volume import Volume
from silo1 import emblem

NORTH = -1                     # -z is north

FLOOR_R = 30                   # surface.Site.floor_r: the level floor
PORTAL = (-6, 7, -4, 4)        # x0, x1, z0, z1 relative to the ring centre
CAMERA = (10, 15, -4, 4)

C = (-3, -21)                  # audience centre (03), relative to the ring centre
TENT_RING = 12
TENTS = {"W": 270, "SW": 225, "SE": 135, "E": 90}   # bearings from north, clockwise (03)
SMALL_TENTS = [(-28, 2), (-28, 6), (-25, 4)]          # the three to the west (03)

# materials
RIB = "minecraft:stripped_dark_oak_wood"
DECK = "minecraft:dark_oak_planks"
DECK_EDGE = "minecraft:dark_oak_slab[type=top]"
SLAT = "minecraft:bamboo_planks"
CURTAIN = "minecraft:orange_terracotta"
GOLD = "minecraft:gold_block"
FABRIC = "minecraft:white_wool"
TRUSS = "minecraft:iron_bars"
LAMP = "minecraft:lantern[hanging=true]"
BANNER = "minecraft:white_concrete"
POLE = "minecraft:spruce_fence"
CHAIR = "minecraft:polished_andesite_stairs[facing=south,half=bottom]"   # back to the south: seated facing the stage
SOIL = "minecraft:moss_block"
FLOWERS = ["minecraft:pink_tulip", "minecraft:allium", "minecraft:oxeye_daisy", "minecraft:white_tulip",
           "lilac", "peony"]                                              # pink spikes and white heads (11, 13)
CRATE = "minecraft:light_gray_concrete"
AIR = "minecraft:air"


def _in(dx, dz, box):
    return box[0] <= dx <= box[1] and box[2] <= dz <= box[3]


class Event:
    def __init__(self, ring_x: int, ring_z: int, floor_y: int):
        self.rx, self.rz, self.fy = ring_x, ring_z, floor_y
        self.R = 40
        self.v = Volume((ring_x - self.R, floor_y, ring_z - self.R), (2 * self.R + 1, 16, 2 * self.R + 1))

    # world <-> local: dx, dz relative to the ring centre, h blocks over the floor's top block
    def put(self, dx: int, h: int, dz: int, state: str) -> None:
        if _in(dx, dz, PORTAL) or _in(dx, dz, CAMERA):
            raise ValueError(f"{dx},{dz} is kept clear")
        self.v.set(dx + self.R, h, dz + self.R, state)

    def build(self) -> Volume:
        self.stage()
        for name, b in TENTS.items():
            a = math.radians(b)
            self.stretch_tent(round(C[0] + TENT_RING * math.sin(a)), round(C[1] - TENT_RING * math.cos(a)))
        self.chairs()
        for x, z in SMALL_TENTS:
            self.gazebo(x, z)
        self.plaque(1, -7)
        self.crates(11, -17)
        self.cart(10, -14, canopy=False)       # the dark cart backstage (17)
        self.cart(4, -9, canopy=True)          # the white-canopied cart by the plaque (19)
        return self.v

    # the stage -------------------------------------------------------------------------------------------------
    def stage(self) -> None:
        cx = C[0]
        x0, x1 = cx - 8, cx + 8              # 17 wide: the truss towers stand on its corners
        zb, zf = -31, -26                     # back (against the berm's foot) and front edge
        # the deck, one block high, cleared above to the roof (the berm's foot rises less than a block here)
        for x in range(x0, x1 + 1):
            for z in range(zb, zf + 1):
                self.put(x, 1, z, DECK)
                for h in range(2, 12):
                    self.put(x, h, z, AIR)
        # steps up at both front corners, planters between them (11)
        for x in list(range(x0, x0 + 3)) + list(range(x1 - 2, x1 + 1)):
            self.put(x, 1, zf + 1, "minecraft:birch_stairs[facing=north,half=bottom]")
        for i, x in enumerate(range(x0 + 3, x1 - 2)):
            self.put(x, 1, zf + 2, SLAT)       # the box's slatted front
            self.put(x, 1, zf + 1, SOIL)
            f = FLOWERS[(i * 7 + 3) % len(FLOWERS)]
            if f in ("lilac", "peony"):
                self.put(x, 2, zf + 1, f"minecraft:{f}[half=lower]")
                self.put(x, 3, zf + 1, f"minecraft:{f}[half=upper]")
            else:
                self.put(x, 2, zf + 1, f)
        # curtain over the whole back, slat panels before it: middle 7 x 7 with the emblem, sides 4 x 4 (11)
        for x in range(x0 + 1, x1):
            for h in range(2, 10):
                self.put(x, h, zb, CURTAIN)
        for p0, p1, top in ((cx - 3, cx + 3, 8), (x0 + 2, x0 + 5, 5), (x1 - 5, x1 - 2, 5)):
            for x in range(p0, p1 + 1):
                for h in range(2, top + 1):
                    self.put(x, h, zb + 1, SLAT)
        e = emblem(7)
        for j, row in enumerate(e):
            for i, ch in enumerate(row):
                if ch == "#":
                    self.put(cx - 3 + i, 8 - j, zb + 1, GOLD)
        self.put(cx + 4, 2, zb + 3, "minecraft:lectern[facing=south]")
        # the ribs: three arches across the stage, bent dark wood, springing from the deck's sides (11, 12)
        for z, half in ((zf, 7), (zf - 2, 6), (zf - 4, 5)):      # narrowing to the back, so they fan in the frame
            for (x, h) in self.arch(half, 9):
                self.put(cx + x, 1 + h, z, RIB)
        # fabric roof over the ribs, a block out at the sides; truss towers at the four corners (11)
        for x in range(x0, x1 + 1):
            for z in range(zb, zf + 1):
                self.put(x, 11, z, FABRIC)
        for x in (x0, x1):
            for z in (zb, zf):
                for h in range(2, 11):
                    self.put(x, h, z, TRUSS)
        for x in range(x0 + 2, x1 - 1, 2):                     # the lighting row under the front edge
            self.put(x, 10, zf - 1, LAMP)
        # banners: white, the gold emblem near the top, outside the towers (11)
        for bx in (x0 - 3, x1 + 1):
            for x in range(bx, bx + 3):
                for h in range(1, 8):
                    self.put(x, h, zf, BANNER)
            for (i, j) in ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)):
                self.put(bx + i, 6 - j, zf, GOLD)
            self.put(bx + 1, 5, zf, "minecraft:raw_gold_block")

    @staticmethod
    def arch(half: int, rise: int) -> list[tuple[int, int]]:
        """Cells of a 4-connected half-ellipse from (-half, 0) over (0, rise) to (half, 0)."""
        cells = set()
        prev = None
        for k in range(0, 721):
            a = math.pi * k / 720
            p = (round(-half * math.cos(a)), round(rise * math.sin(a)))
            if prev is not None and p[0] != prev[0] and p[1] != prev[1]:
                cells.add((prev[0], p[1]))      # step corner, so the rib reads as one piece
            cells.add(p)
            prev = p
        return sorted(cells)

    # the tents -------------------------------------------------------------------------------------------------
    def stretch_tent(self, x: int, z: int) -> None:
        """Cream-white fabric pulled up on a tall centre pole, eaves on corner poles (14, 15): 7 x 7."""
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                d = max(abs(dx), abs(dz))
                h = 5 if d == 0 else 4 if d == 1 else 3     # peak ~4.5 m, eaves ~2.5 m over the floor
                self.put(x + dx, h, z + dz, FABRIC)
        for dx, dz in ((-3, -3), (-3, 3), (3, -3), (3, 3)):
            for h in (1, 2):
                self.put(x + dx, h, z + dz, POLE)
        for h in range(1, 5):
            self.put(x, h, z, POLE)

    def gazebo(self, x: int, z: int) -> None:
        """A small white tent: 3 x 3 roof on four white posts."""
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                self.put(x + dx, 3, z + dz, FABRIC)
        for dx, dz in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            for h in (1, 2):
                self.put(x + dx, h, z + dz, "minecraft:birch_fence")

    # seats, plaque, carts, crates ------------------------------------------------------------------------------
    def chairs(self) -> None:
        """Grey folding chairs in rows facing the stage, an aisle down the middle (11, 14)."""
        for z in (-22, -20, -18):
            for x in range(C[0] - 6, C[0] + 7):
                if x != C[0]:
                    self.put(x, 1, z, CHAIR)

    def plaque(self, x: int, z: int) -> None:
        """The founders' plaque: a slanted metal plate on a waist-high stand, read from the path to the west (19, 20)."""
        for dz in (-1, 1):
            self.put(x, 1, z + dz, "minecraft:polished_deepslate_wall")
        self.put(x, 1, z, "minecraft:polished_deepslate_wall")
        for dz in (-1, 0, 1):
            self.put(x, 2, z + dz, "minecraft:waxed_cut_copper_stairs[facing=east,half=bottom]")

    def crates(self, x: int, z: int) -> None:
        """Pale grey crates stacked on dollies (17)."""
        for dx in (0, 1):
            self.put(x + dx, 1, z, "minecraft:iron_trapdoor[half=bottom,open=false]")
            for h in (2, 3):
                self.put(x + dx, h, z, CRATE)

    def cart(self, x: int, z: int, canopy: bool) -> None:
        """A golf cart, 2 wide and 3 long, pointing north: dark body, seat, a white roof on posts when canopy."""
        for dx in (0, 1):
            for dz in (0, 1, 2):
                self.put(x + dx, 1, z + dz, "minecraft:black_concrete" if dz else "minecraft:polished_blackstone_slab[type=bottom]")
            self.put(x + dx, 2, z + 1, "minecraft:black_wool")
            if canopy:
                self.put(x + dx, 2, z, "minecraft:iron_bars")
                self.put(x + dx, 2, z + 2, "minecraft:iron_bars")
                for dz in (0, 1, 2):
                    self.put(x + dx, 3, z + dz, "minecraft:smooth_quartz_slab[type=bottom]")


def build(ring_x: int, ring_z: int, floor_y: int) -> Volume:
    return Event(ring_x, ring_z, floor_y).build()


def ground_paths(ring_x: int, ring_z: int) -> tuple[set, set]:
    """(path, apron) columns in world x, z: the aisle and the straight path due south from the audience, over the
    south berm, to the pale apron on the ring path (03). The apron is ~50 m along the ring path; its depth (16 m) is ours."""
    path, apron = set(), set()
    for z in range(-23, 66):
        for x in (C[0] - 1, C[0], C[0] + 1):
            if z <= -17 and x != C[0]:
                continue                           # one block wide between the chair rows
            if not _in(x, z, PORTAL):
                path.add((ring_x + x, ring_z + z))
    for x in range(-25, 26):
        for z in range(40, 72):
            r = math.hypot(x, z)
            if 56 <= r <= 72:
                apron.add((ring_x + x, ring_z + z))
    return path - apron, apron


if __name__ == "__main__":
    import sys
    from check_states import load, problem
    v = build(0, 0, 70)
    blocks = load()
    bad = [(s, problem(s, blocks)) for s in v.used_states() if problem(s, blocks)]
    print(f"{len(v.used_states())} states, {int((v.ids != 0).sum())} positions, {len(bad)} errors")
    for s, p in bad:
        print(" ", s, p)
    sys.exit(1 if bad else 0)
