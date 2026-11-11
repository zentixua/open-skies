"""Interior previews of a generated silo (for checking, not for players).

plan: an architect's cut plan of one level, looking down from 1.5 blocks over its floor (row 1 where filled, else
row 0, else the floor shaded). facade: the shaft face of one level unrolled, bearing left to right, rows bottom up,
with the walkway rows under it.
"""
from __future__ import annotations

import math
import sys

import numpy as np
from PIL import Image

from preview import color

EXTRA = {
    "glass_pane": (150, 200, 230), "iron_door": (40, 60, 140), "heavy_weighted_pressure_plate": (230, 200, 60),
    "andesite_wall": (120, 130, 125), "light_gray_bed": (230, 120, 120), "iron_bars": (200, 60, 60),
    "sea_lantern": (210, 255, 255), "shroomlight": (255, 160, 70), "barrel": (140, 100, 60), "cauldron": (60, 60, 60),
    "white_concrete": (240, 240, 240), "lantern": (255, 200, 60), "waxed_weathered_copper_grate": (90, 140, 120),
    "waxed_copper_grate": (200, 120, 80), "spruce_stairs": (110, 80, 50), "potted_azalea_bush": (60, 140, 60),
}


def col(state: str):
    name = state.split("[", 1)[0].replace("minecraft:", "")
    return EXTRA.get(name, color(state))


def lut(vol):
    t = np.full((len(vol.palette), 3), 255, dtype=np.uint8)
    a = np.zeros(len(vol.palette), dtype=bool)
    for i, st in enumerate(vol.palette):
        c = col(st)
        if c is not None:
            t[i], a[i] = c, True
    return t, a


def plan(vol, y, path, scale=6, crop=None):
    t, a = lut(vol)
    r1, r0, fl = vol.ids[:, y + 1, :], vol.ids[:, y, :], vol.ids[:, y - 1, :]
    img = np.full(r0.shape + (3,), 255, np.uint8)
    m = a[fl]
    img[m] = (t[fl][m] * 0.55 + 255 * 0.45).astype(np.uint8)
    m = a[r0]
    img[m] = t[r0][m]
    m = a[r1]
    img[m] = t[r1][m]
    img = img.transpose(1, 0, 2)                    # rows = z (south down), columns = x (east right)
    if crop:
        x0, z0, x1, z1 = crop
        img = img[z0:z1, x0:x1]
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)


def facade(silo, n, path, scale=8):
    vol, y = silo.v, silo.level_y(n)
    t, a = lut(vol)
    s = silo.s
    rows = []
    for rr, dys in ((s.r_atrium + 0.5, range(3, -1, -1)), (s.r_atrium - 0.5, (0,)), (s.r_atrium - 1.5, (0,))):
        cells = []
        for k in range(int(TAU_STEPS)):
            th = k / TAU_STEPS * 2 * math.pi
            cells.append(silo.polar(rr, th))
        for dy in dys:
            rows.append([vol.ids[x, y + dy, z] for x, z in cells])
    ids = np.array(rows)
    img = np.full(ids.shape + (3,), 255, np.uint8)
    img[a[ids]] = t[ids][a[ids]]
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)


TAU_STEPS = 360


if __name__ == "__main__":
    from silo import Silo, Spec
    out = sys.argv[1]
    levels = [int(a) for a in sys.argv[2:]] or [18]
    s = Silo(Spec(number=18), 0, 70, 0)
    v = s.build()
    R = s.R
    for n in levels:
        plan(v, s.level_y(n), f"{out}/plan-{n:03d}.png")
        plan(v, s.level_y(n), f"{out}/room-{n:03d}.png", scale=14, crop=(R + 14, R - 22, R + 45, R + 23))
        facade(s, n, f"{out}/facade-{n:03d}.png", scale=4)
