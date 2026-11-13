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
- The tent reach (6 m from each pole) and the 12 m ring radius, fitted inside the floor (r 30).
- The audience centre 21 m north, so the stage's back reaches r 33 at the berm's foot.
- The number of chair rows.
- Where the plaque, carts and crates stand.
- The flower species.
- Each block standing for a material (bent wood = dark oak fence, roof fabric = white wool, tent fabric = smooth
  quartz slabs, slats = stripped birch, truss = iron bars, chairs = smooth stone slab and iron trapdoor).

build(ring_x, ring_z, floor_y) gives the set as a Volume in world coordinates; the floor's top block is floor_y and
nothing is placed in it. ground_paths(ring_x, ring_z) gives the path and apron columns, for the live laying in
paths.py (they cross the berm, whose heights only the world knows). Kept clear: the portal leaves (x ring-6..ring+7,
z ring-4..ring+4) and the camera block (x ring+10..ring+15, z ring-4..ring+4).
"""
from __future__ import annotations

import math

import numpy as np

from volume import Volume
from silo1 import emblem

NORTH = -1                     # -z is north

FLOOR_R = 55                   # surface.Site.floor_r: the level floor (1:1, SPEC-1to1.md)
# The set is laid out in the show's frame (03: north is toward the gate) and turned into the world by the layout's
# rotation (ROT_DEG, set by set_rotation; the complex stands at 128 degrees). Kept clear: Silo 1's slot and camera
# shelter. Its way out is build_offline.FIRST: "W" (the silo frame unturned), which puts the slot on the frame's
# south-south-east side, clear of the audience (north half), the small tents (west) and the path south.
from silo import CAMERA as _CAM, EXIT_X as _EX, PORTAL_X as _PX, RAMP_Z as _RZ  # noqa: E402
_PORTAL_W = (_EX - 1, _PX + 1, _RZ[0] - 1, _RZ[1] + 1)             # world offsets about the ring centre, curb included
_CAMERA_W = (_CAM[0] - 1, _CAM[1], _CAM[2], _CAM[3])               # roof and plinth included
ROT_DEG = 0.0
PORTAL = CAMERA = None


def _frame_box(box, pad=1):
    """A world-offset box about the ring centre as the frame's (x, z) bounding box."""
    c, s_ = math.cos(math.radians(ROT_DEG)), math.sin(math.radians(ROT_DEG))
    pts = [(x * c + z * s_, -x * s_ + z * c) for x in (box[0], box[1] + 1) for z in (box[2], box[3] + 1)]
    return (math.floor(min(p[0] for p in pts)) - pad, math.ceil(max(p[0] for p in pts)) + pad,
            math.floor(min(p[1] for p in pts)) - pad, math.ceil(max(p[1] for p in pts)) + pad)


def set_rotation(deg: float) -> None:
    global ROT_DEG, PORTAL, CAMERA
    ROT_DEG = deg
    PORTAL, CAMERA = _frame_box(_PORTAL_W), _frame_box(_CAMERA_W)


def to_world(dx: float, dz: float) -> tuple[float, float]:
    c, s_ = math.cos(math.radians(ROT_DEG)), math.sin(math.radians(ROT_DEG))
    return dx * c - dz * s_, dx * s_ + dz * c


set_rotation(0.0)
RING_PATH_R = 110              # surface.Site.path_r

C = (-3, -21)                  # audience centre (03), relative to the ring centre
TENT_RING = 12
TENTS = {"W": 270, "SW": 225, "SE": 135, "E": 90}   # bearings from north, clockwise (03)
SMALL_TENTS = [(-28, 2), (-28, 6), (-25, 4)]          # the three to the west (03)

# materials
RIB = "minecraft:dark_oak_fence"            # thin bent ribs: a fence reads as a rod, full wood as a stepped wall (08, 12.11)
DECK = "minecraft:dark_oak_planks"
DECK_EDGE = "minecraft:dark_oak_slab[type=top]"
SLAT = "minecraft:stripped_birch_log[axis=y]"   # pale timber with vertical grain (11, 13); bamboo read bright yellow
CURTAIN = "minecraft:orange_terracotta"
GOLD = "minecraft:gold_block"
FABRIC = "minecraft:white_wool"
TENT_FABRIC = "minecraft:smooth_quartz_slab"
TENT_PEAK, TENT_EAVE, TENT_REACH = 5.0, 2.0, 6     # m over the floor at the pole, at the edge; edge radius (14, 15)
TRUSS = "minecraft:iron_bars"
LAMP = "minecraft:lantern[hanging=true]"
BANNER = "minecraft:white_concrete"
POLE = "minecraft:spruce_fence"
SEAT = "minecraft:smooth_stone_slab[type=bottom]"
CHAIR_BACK = "minecraft:birch_trapdoor[facing=south,half=bottom,open=true]"  # a thin pale back on the seat's south
# (iron trapdoors in a row read as one grated wall, shader frame 08 of 1112d)
BANNER_CLOTH = ('minecraft:white_wall_banner[facing=south]{patterns:[{color:"yellow",pattern:"minecraft:flower"},'
                '{color:"yellow",pattern:"minecraft:border"}]}')         # the gold emblem on white cloth (11)
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
        self.chairs()
        for x, z in SMALL_TENTS:
            self.gazebo(x, z)
        self.plaque(1, -7)
        self.crates(-6, -8)                    # clear of the tents' fabric
        self.cart(10, -14, canopy=False)       # the dark cart backstage (17)
        self.cart(-8, -7, canopy=True)         # the white-canopied cart by the plaque (19), clear of the fabric
        self.stretch_tents([(round(C[0] + TENT_RING * math.sin(math.radians(b))),
                             round(C[1] - TENT_RING * math.cos(math.radians(b)))) for b in TENTS.values()])
        self.clear_rest()
        return self.v

    def clear_rest(self) -> None:
        """Air over the rest of the bowl floor (r <= 27, outside the portal and the camera block): a rebuilt set leaves
        nothing of an earlier one."""
        for dx in range(-27, 28):
            for dz in range(-27, 28):
                if dx * dx + dz * dz > 27 * 27:
                    continue
                if _in(dx, dz, (PORTAL[0] - 1, PORTAL[1] + 1, PORTAL[2] - 1, PORTAL[3] + 1)) or \
                        _in(dx, dz, (CAMERA[0] - 1, CAMERA[1] + 1, CAMERA[2] - 1, CAMERA[3] + 1)):
                    continue
                for h in range(1, self.v.size[1]):
                    if self.v.get(dx + self.R, h, dz + self.R) is None:
                        self.v.set(dx + self.R, h, dz + self.R, AIR)

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
            self.put(bx + 1, 6, zf + 1, BANNER_CLOTH)

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
    def stretch_tents(self, poles: list[tuple[float, float]]) -> None:
        """Cream-white stretch fabric pulled up on tall timber poles and down to short ones at the edge (14, 15): over
        each column the fabric hangs at the highest of the poles' cones (peak 5 m at the pole, 2 m at 6 m out), so
        neighbouring tents join in saddles as stretch tents do. One layer of half slabs: half-metre steps read as a
        sloping sheet; whole-block steps and stairs read as white plates (shader frames 12.11). Only empty cells."""
        def sheet(px, pz):
            best = None
            for cx, cz in poles:
                d = math.hypot(px + 0.5 - (cx + 0.5), pz + 0.5 - (cz + 0.5))
                if d <= TENT_REACH:
                    # pulled up at the pole, nearly flat towards the edge: a stretch tent's sheet is concave (14, 15);
                    # a straight cone read as a white step pyramid (shader frames 08, 09 of 1112d)
                    h = TENT_EAVE + (TENT_PEAK - TENT_EAVE) * (1 - d / TENT_REACH) ** 1.6
                    best = h if best is None else max(best, h)
            return None if best is None else math.floor(best * 2) / 2
        xs = [int(math.floor(c[0])) for c in poles]; zs = [int(math.floor(c[1])) for c in poles]
        for x in range(min(xs) - TENT_REACH - 1, max(xs) + TENT_REACH + 2):
            for z in range(min(zs) - TENT_REACH - 1, max(zs) + TENT_REACH + 2):
                h = sheet(x, z)
                if h is None or _in(x, z, PORTAL) or _in(x, z, CAMERA):
                    continue
                layer, top = int(h), h - int(h) >= 0.5
                if self.v.get(x + self.R, layer, z + self.R) is None:
                    self.put(x, layer, z, f"{TENT_FABRIC}[type={'top' if top else 'bottom'}]")
        for cx, cz in poles:
            x, z = int(math.floor(cx)), int(math.floor(cz))
            for h in list(range(1, int(TENT_PEAK))) + [int(TENT_PEAK) + 1]:   # the pole, its tip through the peak
                if self.v.get(x + self.R, h, z + self.R) is None:
                    self.put(x, h, z, POLE)
            for k in range(8):                                  # short poles round the edge, where no other tent is over
                a = k * math.pi / 4
                ex, ez = int(math.floor(cx + (TENT_REACH - 0.5) * math.cos(a))), int(math.floor(cz + (TENT_REACH - 0.5) * math.sin(a)))
                h = sheet(ex, ez)
                if h is None or h > TENT_EAVE + 0.5 or _in(ex, ez, PORTAL) or _in(ex, ez, CAMERA):
                    continue
                for hh in range(1, int(h)):
                    if self.v.get(ex + self.R, hh, ez + self.R) is None:
                        self.put(ex, hh, ez, POLE)

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
        """Grey folding chairs in long rows facing the stage, an aisle down the middle (11, 14): a half-height seat,
        and its back a thin open trapdoor standing on the seat's south edge (solid stairs read as stone blocks from
        behind, shader frame 08 of 12.11); every third seat is left out, so the rows read as chairs, not walls."""
        for z in (-22, -20, -18, -16, -14):
            for x in range(C[0] - 6, C[0] + 7):
                if x != C[0] and (x - C[0]) % 3 != 0:
                    self.put(x, 1, z, SEAT)
                    self.put(x, 1, z + 1, CHAIR_BACK)

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
    """The set in the show's frame, turned into the world by ROT_DEG (nearest-block resampling, about the ring
    centre; block facings turned by the nearest quarter)."""
    v = Event(ring_x, ring_z, floor_y).build()
    if not ROT_DEG % 360:
        return v
    from turn import turn_state
    ox, oy, oz = v.origin
    nx, ny, nz = v.size
    corners = [to_world(x - ring_x, z - ring_z) for x in (ox, ox + nx) for z in (oz, oz + nz)]
    x0 = math.floor(min(p[0] for p in corners)) + ring_x; x1 = math.ceil(max(p[0] for p in corners)) + ring_x
    z0 = math.floor(min(p[1] for p in corners)) + ring_z; z1 = math.ceil(max(p[1] for p in corners)) + ring_z
    out = Volume((x0, oy, z0), (x1 - x0 + 1, ny, z1 - z0 + 1))
    k = round(ROT_DEG / 90) % 4
    def turn_nbt(st):                                # inline {nbt} (banners) stays as it is
        head, brace, tail = st.partition("{")
        return turn_state(head, k) + brace + tail
    pal = ["<keep>"] + [turn_nbt(st) for st in v.palette[1:]]
    remap = np.array([0] + [out.id(st) for st in pal[1:]], dtype=out.ids.dtype)
    c, s_ = math.cos(math.radians(ROT_DEG)), math.sin(math.radians(ROT_DEG))
    X, Z = np.meshgrid(np.arange(x0, x1 + 1) + 0.5 - ring_x, np.arange(z0, z1 + 1) + 0.5 - ring_z, indexing="ij")
    sx = np.floor(X * c + Z * s_ + ring_x - ox).astype(int)          # frame offsets of each world column, then source
    sz = np.floor(-X * s_ + Z * c + ring_z - oz).astype(int)
    ok = (sx >= 0) & (sx < nx) & (sz >= 0) & (sz < nz)
    ii, kk = np.nonzero(ok)
    out.ids[ii, :, kk] = remap[v.ids[sx[ii, kk], :, sz[ii, kk]]]
    for (bx, by, bz), nbt in v.block_entities.items():
        wx, wz = to_world(ox + bx + 0.5 - ring_x, oz + bz + 0.5 - ring_z)
        i, kk_ = math.floor(wx + ring_x) - x0, math.floor(wz + ring_z) - z0
        if 0 <= i < out.size[0] and 0 <= kk_ < out.size[2]:
            out.block_entities[(i, by, kk_)] = nbt
    return out


def ground_paths(ring_x: int, ring_z: int) -> tuple[set, set]:
    """(path, apron) columns in world x, z: the aisle and the straight path due south from the audience, over the
    south berm, to the pale apron on the ring path (03). The apron is ~50 m along the ring path; its depth (16 m) is ours."""
    path, apron = set(), set()
    for z in range(-23, RING_PATH_R + 2):
        for x in (C[0] - 1, C[0], C[0] + 1):
            if z <= -17 and x != C[0]:
                continue                           # one block wide between the chair rows
            if not _in(x, z, PORTAL):
                path.add((x, z))
    for x in range(-25, 26):
        for z in range(RING_PATH_R - 30, RING_PATH_R + 9):
            r = math.hypot(x, z)
            if RING_PATH_R - 8 <= r <= RING_PATH_R + 8:
                apron.add((x, z))

    def world(cells_):
        out = set()
        for x, z in cells_:
            for ax in (0.25, 0.75):                  # every world column a turned frame cell touches
                for az in (0.25, 0.75):
                    wx, wz = to_world(x + ax, z + az)
                    out.add((math.floor(wx) + ring_x, math.floor(wz) + ring_z))
        return out
    path, apron = world(path), world(apron)
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
