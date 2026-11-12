"""The shaft face of a level: eighteen bay facades and the walkway in front of them, from the explorethesilo.com model.

Source: silo3d.js (explorethesilo.com three.js model, taken apart for private use with Artem's permission):
variantFor, the BAY.* facade builders in buildInterior, dressingFor and the per-bay dressing in buildWindow, seeded.
Level data: levels.js. Only canon levels (canon: true) get a department's dressing; the model's filler departments
(canon: false: farms, clinics, water treatment, supply depots invented to fill the list) stay residential here.

Mapping into Minecraft. The model's shaft wall stands at radius 30 with eighteen 10.47 m bays on 10 m levels; ours
is radius 17 with 5-block levels (4 clear rows), so each facade is drawn on its bay's ~6 blocks of wall: positions
across the bay scale with the bay, model heights 0-10 m fall into the four rows (row k takes 2.5k..2.5k+2.5 m), and
every opening keeps at least one block. Doors are always two rows (a Minecraft door). Things standing proud of the
face (stoops, balcony decks) go on the walkway's outer row. Bearings: the silo frame is the model's turned by
FRAME_DEG, so the model's airlock bay (210 degrees) lands at 180 as in silo.AIRLOCK_ANGLE.
"""
from __future__ import annotations

import math

TAU = 2 * math.pi
FRAME_DEG = -30.0                         # silo bearing = model bearing + FRAME_DEG
BAYS = 18
BAY_ARC_DEG = 360.0 / BAYS
BAY_W = 30 * TAU / BAYS                   # model bay width at SHAFT_RADIUS 30: 10.47 m
HW = BAY_W / 2
SIGN_BAY = round(BAYS / 3)                # model: the bay that carries a department's door and plaque
ROOM_BAY = 1                              # model uses SIGN_BAY - 1 (in its camera's view); here the bay at bearing 0,
                                          # so the rooms behind it are square to the world grid


def to_i32(x: float) -> int:
    x = int(math.trunc(x)) & 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


def imul(a: int, b: int) -> int:
    return to_i32((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF))


def seeded(a: float, b: float, c: float = 0) -> float:
    """silo3d.js seeded(a, b, c), bit for bit (checked against node)."""
    h = to_i32(a * 73856093) ^ to_i32(b * 19349663) ^ to_i32(c * 83492791) ^ 0x5f3759df
    h = to_i32(h)
    h = imul(h ^ ((h & 0xFFFFFFFF) >> 15), 0x85ebca6b)
    h = imul(h ^ ((h & 0xFFFFFFFF) >> 13), 0xc2b2ae35)
    return ((h ^ ((h & 0xFFFFFFFF) >> 16)) & 0xFFFFFFFF) / 4294967296


# Canon levels (levels.js, canon: true), number -> (name, department). Everything else is residential.
CANON = {
    1: ("The Top", "Sheriff's Department"), 13: ("Judicial", "Judicial"), 14: ("Residential", None),
    15: ("Manager's Row", "Administration"), 17: ("Residential", None), 19: ("IT", "IT"),
    20: ("Recycling and the Watcher Room", "Recycling"), 30: ("Checkpoint", "Judicial"), 31: ("Residential", None),
    36: ("Residential", None), 42: ("Residential", None), 45: ("Residential", None), 47: ("The Great Stair", None),
    50: ("Mids Medical", "Medical"), 52: ("Residential", None), 62: ("Mids Medical", "Medical"),
    100: ("The Bazaar", "Supply"), 105: ("Deputy Station", "Sheriff's Department"), 120: ("The Rail", None),
    122: ("Lower Mids Farm", "Farming"), 124: ("Residential", None), 130: ("The Barricade", None),
    140: ("Mechanical", "Mechanical"), 144: ("The Bottom", "Mechanical"),
}
ROOM_LEVELS = {13, 19, 20, 100, 105, 144}   # model ROOM_LEVELS (indices 12, 18, 19, 99, 143) + the deputy station


def dressing_for(n: int) -> str:
    """silo3d.js dressingFor, on canon levels only."""
    e = CANON.get(n)
    if not e:
        return "residential"
    name, d = e
    low = name.lower()
    if "cafeteria" in low:
        return "cafeteria"
    if "bazaar" in low:
        return "bazaar"
    return {"Farming": "farming", "Mechanical": "mechanical", "Supply": "supply", "IT": "it", "Medical": "medical",
            "Judicial": "judicial", "Recycling": "recycling", "Administration": "admin"}.get(d, "residential")


SHARE = [("windowsA", 0.30), ("windowsB", 0.50), ("door", 0.68), ("shop", 0.78), ("louvre", 0.88), ("balcony", 1.0)]


def variant_for(n: int, b: int) -> str:
    """silo3d.js variantFor(level index n - 1, bay b)."""
    L = n - 1
    if n in ROOM_LEVELS and b == ROOM_BAY:
        return "roomDoor"
    dress, r = dressing_for(n), seeded(L, b)
    signed = b == SIGN_BAY and n in CANON
    if dress == "farming":
        return "farm"
    if dress == "mechanical":
        return "mech" if r < 0.55 else "louvre" if r < 0.8 else "door"
    if dress == "it":
        return "itDoor" if b == SIGN_BAY else "it"
    if dress == "medical":
        return "medical" if signed or r < 0.6 else "windowsB"
    if dress == "judicial":
        return "judicialDoor" if b == SIGN_BAY else "judicialWall"
    if dress == "recycling":
        return "recycling" if r < 0.6 else "louvre"
    if dress == "bazaar":
        return "shop" if r < 0.75 else "door"
    if dress == "admin":
        return "admin" if signed or r < 0.8 else "windowsA"
    if signed:
        return "door"
    for k, s in SHARE:
        if r < s:
            return k
    return "windowsA"


def _rect(cx, w, y0, y1):
    return (cx - w / 2, cx + w / 2, y0, y1)


# Facade openings per variant, model metres: (kind, x0, x1, y0, y1), x across the bay from its centre, y up from the
# deck (BAY.* in buildInterior). Kinds: door, window, shop, grate (louvre panel, vent grille, louvred recess), slit,
# chute, glazed, pilaster, leaf (the monumental door above a man's height). Plus stoops in front and wall lamps.
def _vent(cx, cy, r=0.45):
    return ("grate", cx - r, cx + r, cy - r, cy + r)


FACADES: dict[str, dict] = {
    "windowsA": {"open": [("window", *_rect(cx, 1.6, 4.0, 6.2)) for cx in (-3.6, -1.2, 1.2, 3.6)]
                 + [("grate", *_rect(0, 2.2, 7.75, 8.65)), _vent(-4.2, 8.3)]},
    "windowsB": {"open": [("window", *_rect(cx, 1.8, 3.6, 6.6)) for cx in (-2.8, 0.2, 3.2)] + [_vent(4.3, 8.4)],
                 "stoop": (-HW, HW)},
    "door": {"open": [("door", -1.5, 1.5, 0, 3.4), ("window", -4.6, -3.0, 4.2, 6.0), ("window", 3.0, 4.6, 4.2, 6.0),
                      ("grate", *_rect(0, 2.4, 4.2, 5.0)), _vent(0, 8.2)], "lamps": (-2.2, 2.2)},
    "shop": {"open": [("shop", -3.4, 3.4, 0, 4.4), ("window", -1.0, 1.0, 6.0, 7.6)], "lamps": (-4.3, 4.3)},
    "louvre": {"open": [("grate", -3.6, 3.6, 2.0, 8.0)]},
    "balcony": {"open": [("door", -3.4, -1.6, 0.6, 3.2), ("window", 0.8, 3.2, 4.2, 6.2), ("grate", *_rect(2.0, 2.0, 7.25, 7.95))],
                "stoop": (-HW, HW), "lamps": (-0.6,)},
    "farm": {"open": [("glazed", *_rect(cx, 3.1, 0.6, 7.0)) for cx in (-3.5, 0, 3.5)]},
    "mech": {"open": [("door", -2.0, 2.0, 0, 4.0), ("window", 3.0, 4.6, 4.6, 6.0), ("grate", *_rect(-3.6, 2.0, 4.6, 6.2)),
                      _vent(0, 7.6, 0.7)], "pipes": True, "lamps": (-3.2, 3.2)},
    "it": {"open": [("slit", 2.2, 2.5, 1.2, 2.6), _vent(-3.4, 6.2, 0.6), _vent(3.4, 6.2, 0.6)]},
    "itDoor": {"open": [("door", -1.4, 1.4, 0, 3.2), ("slit", 2.4, 2.7, 0.8, 2.6), _vent(-3.6, 6.4, 0.6)]},
    "medical": {"open": [("window", *_rect(cx, 2.8, 0.6, 4.2)) for cx in (-2.6, 0.6)] + [("door", 2.6, 4.2, 0, 3.2)],
                "lamps": (-4.4,), "cross": True},
    "judicialDoor": {"open": [("door", -1.7, 1.7, 0, 5.0), ("leaf", -1.7, 1.7, 5.0, 6.4)]
                     + [("pilaster", *_rect(x, 0.9, 0, 8.4)) for x in (-2.6, 2.6)]},
    "judicialWall": {"open": [("pilaster", *_rect(x, 0.7, 0, 9.4)) for x in (-3.5, 0, 3.5)]},
    "recycling": {"open": [("chute", -3.9, -2.1, 1.0, 2.8), ("chute", 2.1, 3.9, 1.0, 2.8)], "lamps": (-4.6, 4.6)},
    "admin": {"open": [("door", *_rect(cx, 1.6, 0, 2.6)) for cx in (-3.4, 0, 3.4)]},
    "roomDoor": {"open": [("door", -1.5, 1.5, 0, 3.4), _vent(3.6, 8.2)]
                 + [("pilaster", *_rect(x, 0.5, 0, 3.9)) for x in (-1.9, 1.9)], "lamps": (-2.6, 2.6)},
}

ROW_H = 2.5                                   # model metres per Minecraft row (10 m level -> 4 rows)


def rows_of(y0: float, y1: float, n: int = 4, row_h: float = ROW_H) -> list[int]:
    """Rows of an n-row face (row_h model metres each) that an opening from model height y0 to y1 covers."""
    rows = {k for k in range(n) if y0 <= row_h * k + row_h / 2 <= y1}
    rows.add(min(n - 1, max(0, int(((y0 + y1) / 2) // row_h))))
    return sorted(rows)


def cols_of(us: list[float], x0: float, x1: float) -> list[int]:
    """Indices of the bay's wall cells (by their model u) that an opening x0..x1 covers; never none."""
    hit = [i for i, u in enumerate(us) if x0 <= u <= x1]
    if not hit:
        mid = (x0 + x1) / 2
        hit = [min(range(len(us)), key=lambda i: abs(us[i] - mid))]
    return hit


def region(n: int) -> str:
    return "upTop" if n <= 49 else "mids" if n <= 120 else "deep"


# Lamp blocks. Model LAMP_COLOR / DEPT_LIGHT: up-top warm cream ffe9c4, mids pale grey-green dfe8d8, deep amber
# ffc48a; IT 8cb2ff, medical e2fcff, judicial c8d6ff (cold), farming b8f2ae (green), bazaar ff9448 and mechanical
# ffbc78 (warm). Nearest vanilla light blocks.
REGION_LAMP = {"upTop": "minecraft:ochre_froglight", "mids": "minecraft:pearlescent_froglight", "deep": "minecraft:shroomlight"}
DEPT_LAMP = {"it": "minecraft:sea_lantern", "medical": "minecraft:sea_lantern", "judicial": "minecraft:sea_lantern",
             "farming": "minecraft:verdant_froglight", "bazaar": "minecraft:shroomlight", "mechanical": "minecraft:shroomlight",
             "recycling": "minecraft:ochre_froglight", "admin": "minecraft:pearlescent_froglight"}


def lamp_for(n: int) -> str:
    return DEPT_LAMP.get(dressing_for(n), REGION_LAMP[region(n)])
