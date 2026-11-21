"""Preview images of a generated volume: vertical sections and horizontal slices (for checking, not for players)."""
import hashlib
import sys

import numpy as np
from PIL import Image

KNOWN = {
    "air": None, "<keep>": None, "water": (60, 90, 200), "deepslate": (55, 55, 60), "dirt": (120, 85, 55),
    "light_gray_concrete": (190, 190, 185), "gray_concrete": (110, 110, 112), "polished_andesite": (150, 152, 150),
    "polished_deepslate": (70, 70, 75), "iron_bars": (200, 60, 60), "ochre_froglight": (255, 220, 120),
    "pearlescent_froglight": (250, 220, 240), "verdant_froglight": (200, 250, 180),
}


def color(state: str):
    name = state.split("[", 1)[0].replace("minecraft:", "")
    if name in KNOWN:
        return KNOWN[name]
    h = hashlib.md5(name.encode()).digest()
    return (60 + h[0] % 170, 60 + h[1] % 170, 60 + h[2] % 170)


def lut(vol):
    t = np.zeros((len(vol.palette), 3), dtype=np.uint8)
    alpha = np.zeros(len(vol.palette), dtype=bool)
    for i, st in enumerate(vol.palette):
        c = color(st)
        if c is not None:
            t[i] = c
            alpha[i] = True
    return t, alpha


def section_xy(vol, z, path, y0=0, y1=None, scale=1):
    t, a = lut(vol)
    ids = vol.ids[:, y0:y1, z]                      # [x, y]
    img = np.full(ids.shape + (3,), 255, np.uint8)
    img[a[ids]] = t[ids][a[ids]]
    img = np.flipud(img.transpose(1, 0, 2))
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)


def slice_y(vol, y, path, scale=4):
    t, a = lut(vol)
    ids = vol.ids[:, y, :]
    img = np.full(ids.shape + (3,), 255, np.uint8)
    img[a[ids]] = t[ids][a[ids]]
    img = img.transpose(1, 0, 2)
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)
