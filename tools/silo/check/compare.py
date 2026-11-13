"""Built silo positions read from the world, against the show.

  uv run --with numpy --with scipy --with pillow compare.py SCAN.npz LAYOUT.json OUTDIR [--plaque P] [--frame F]

SCAN.npz: top ground per column (v2paths/top.py: ground, gy, canopy, names, x0, z0) over the whole complex.
Ring paths are found in the world itself (circle Hough transform over the path blocks); their centres are the
built ring centres, and each canon silo takes the nearest one. Writes positions.json, check.txt (canon_check against
canon/fit.json), top.png (colour top-down, green = canon, red = built), plaque.png and frame2052.png (the image
with green = canon, red = built through Hp / Hf), and frame2052-side.png: our ground warped into the 2052 frame's
camera by Hf, beside the frame itself.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import signal


def signal_fft(img, k):
    return signal.fftconvolve(img, k[::-1, ::-1], mode="same")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import canon_check  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("scan"); ap.add_argument("layout"); ap.add_argument("out")
ap.add_argument("--plaque"); ap.add_argument("--frame")
ap.add_argument("--min-cover", type=float, default=0.5, help="share of a 110 m circle that must be path")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
d = np.load(a.scan, allow_pickle=True)
G, GY, CAN = d["ground"], d["gy"].astype(float), d["canopy"]
X0, Z0 = int(d["x0"]), int(d["z0"])
names = list(d["names"])
L = json.load(open(a.layout))
one_s = next(s for s in L["silos"] if s["number"] == 1)
one = tuple(one_s["ring"]); rot, edge = L["rotation_deg"], L["spacing"]
canon_w = {n: canon_check.to_world(u, one, rot, edge) for n, u in canon_check.GROUND.items()}

# built rings: the ring path (paths.RING_PATH_R, smooth sandstone or dirt path) found by a circle Hough transform
# over the path columns; the bowls themselves are too shallow (floor ~3 below a plain that rolls +-2) to segment
known = GY > -9000
level = float(np.median(GY[known]))
PATHB = {i for i, n in enumerate(names) if n.split(":")[-1] in ("smooth_sandstone", "dirt_path")}
mask = np.isin(G, list(PATHB)).astype(np.float32)
R = 110
yy, xx = np.mgrid[-R - 3:R + 4, -R - 3:R + 4]
ring = (np.abs(np.hypot(xx, yy) - R) <= 1.5).astype(np.float32)
acc = signal_fft(mask, ring) / ring.sum()
bowls = []
work = acc.copy()
while True:
    i, k = np.unravel_index(np.argmax(work), work.shape)
    if work[i, k] < a.min_cover:
        break
    # refine to the centroid of the accumulator peak (sub-block)
    win = acc[max(i - 3, 0):i + 4, max(k - 3, 0):k + 4]
    wi, wk = np.mgrid[max(i - 3, 0):i + 4, max(k - 3, 0):k + 4][:, :win.shape[0], :win.shape[1]]
    w = np.clip(win - win.max() * 0.8, 0, None)
    bowls.append((X0 + (wi * w).sum() / w.sum() + 0.5, Z0 + (wk * w).sum() / w.sum() + 0.5, float(work[i, k])))
    work[max(i - 150, 0):i + 151, max(k - 150, 0):k + 151] = 0
pos = {}
for n, (cx, cz) in canon_w.items():
    b = min(bowls, key=lambda b: math.hypot(b[0] - cx, b[1] - cz))
    pos[n] = (round(b[0], 1), round(b[1], 1))
json.dump({str(n): v for n, v in sorted(pos.items())}, open(os.path.join(a.out, "positions.json"), "w"), indent=0)
res = canon_check.check(L, pos)
bad = [r for r in res if r[1] > 10]
with open(os.path.join(a.out, "check.txt"), "w") as f:
    f.write(f"plain level y {level:.0f}; {len(bowls)} ring paths found in the world\n")
    for n, e, g, u in sorted(res):
        f.write(f"silo {n:2d}: built {pos[n][0]:7.1f},{pos[n][1]:7.1f}  canon {canon_w[n][0]:7.1f},{canon_w[n][1]:7.1f}  off {e:6.1f} m\n")
    f.write(f"{len(res) - len(bad)}/{len(res)} within 10 m; worst {res[0][1]:.1f} m (silo {res[0][0]})\n")
print(open(os.path.join(a.out, "check.txt")).read().splitlines()[-1], f"({len(bowls)} bowls)")

# colour top-down -------------------------------------------------------------------------------------------------
PAL = {"grass_block": (95, 159, 53), "dirt": (134, 96, 67), "coarse_dirt": (120, 85, 58), "podzol": (90, 66, 40),
       "dirt_path": (148, 120, 74), "water": (64, 100, 196), "ice": (160, 190, 235), "sand": (219, 207, 163),
       "gravel": (136, 126, 120), "stone": (122, 122, 122), "smooth_sandstone": (224, 214, 170),
       "smooth_stone": (155, 155, 155), "smooth_stone_slab": (155, 155, 155), "moss_block": (89, 109, 45),
       "andesite": (136, 136, 138), "diorite": (188, 188, 190), "granite": (153, 114, 99), "deepslate": (80, 80, 86)}


def col(n):
    b = n.split(":")[-1]
    if b in PAL:
        return PAL[b]
    for suf, c in (("_planks", (160, 130, 82)), ("_log", (120, 90, 55)), ("_leaves", (55, 120, 40)),
                   ("_slab", (150, 150, 150)), ("_stairs", (150, 120, 80)), ("_concrete", (180, 180, 180))):
        if b.endswith(suf):
            return c
    return (150, 150, 150)


nx, nz = G.shape
rgb = np.zeros((nx, nz, 3), np.uint8)
for gi in np.unique(G):
    if gi >= 0:
        rgb[G == gi] = col(names[gi])
S = np.where(known, GY, level)
gx, gz = np.gradient(S)
f = rgb.astype(float) * np.clip(1.0 + 0.11 * (gx + gz), 0.72, 1.28)[..., None]
f[CAN] = f[CAN] * 0.6 + np.array([30, 70, 25]) * 0.4
RGB = np.clip(f, 0, 255).astype(np.uint8)          # [x, z]

sc = 0.5
top = Image.fromarray(RGB.transpose(1, 0, 2)).resize((int(nx * sc), int(nz * sc)), Image.LANCZOS)
dr = ImageDraw.Draw(top)
for n in canon_w:
    gx_, gz_ = (canon_w[n][0] - X0) * sc, (canon_w[n][1] - Z0) * sc
    bx, bz = (pos[n][0] - X0) * sc, (pos[n][1] - Z0) * sc
    dr.line([gx_, gz_, bx, bz], fill=(255, 255, 0), width=2)
    dr.ellipse([gx_ - 7, gz_ - 7, gx_ + 7, gz_ + 7], outline=(0, 255, 0), width=3)
    dr.ellipse([bx - 4, bz - 4, bx + 4, bz + 4], fill=(255, 40, 40))
    dr.text((gx_ + 9, gz_ - 7), str(n), fill=(255, 255, 255))
top.save(os.path.join(a.out, "top.png"))


def overlay(path, H, out, side=None):
    im = Image.open(path).convert("RGB")
    dr = ImageDraw.Draw(im)
    for n in canon_w:
        g = canon_check.proj(H, canon_check.GROUND[n])
        b = canon_check.proj(H, canon_check.to_canon(*pos[n], one, rot, edge))
        dr.line([*g, *b], fill=(255, 255, 0), width=2)
        dr.ellipse([g[0] - 7, g[1] - 7, g[0] + 7, g[1] + 7], outline=(0, 255, 0), width=3)
        dr.ellipse([b[0] - 4, b[1] - 4, b[0] + 4, b[1] + 4], fill=(255, 40, 40))
        dr.text((g[0] + 8, g[1] - 14), str(n), fill=(255, 255, 255))
    im.save(os.path.join(a.out, out))
    if not side:
        return
    # our ground seen by the frame's camera: every frame pixel -> canon units (Hf^-1) -> world -> top-down colour
    W_, H_ = im.size
    Hi = np.linalg.inv(H)
    u, v = np.meshgrid(np.arange(W_) + 0.5, np.arange(H_) + 0.5)
    q = Hi @ np.stack([u.ravel(), v.ravel(), np.ones(u.size)])
    cu, cv = q[0] / q[2], q[1] / q[2]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    wx = one[0] + edge * (cu * c - cv * s); wz = one[1] + edge * (cu * s + cv * c)
    ix, iz = np.floor(wx - X0).astype(int), np.floor(wz - Z0).astype(int)
    ok = (q[2] > 0) & (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
    sky = np.zeros((u.size, 3), np.uint8); sky[:] = (170, 190, 210)
    sky[ok] = RGB[ix[ok], iz[ok]]
    ours = Image.fromarray(sky.reshape(H_, W_, 3))
    both = Image.new("RGB", (W_ * 2 + 10, H_), (255, 255, 255))
    both.paste(Image.open(path).convert("RGB"), (0, 0)); both.paste(ours, (W_ + 10, 0))
    dr = ImageDraw.Draw(both)
    dr.text((10, 10), "show (2052)", fill=(255, 255, 255)); dr.text((W_ + 20, 10), "our world, same camera", fill=(0, 0, 0))
    both.save(os.path.join(a.out, side))


if a.plaque:
    overlay(a.plaque, canon_check.HP, "plaque.png")
if a.frame:
    overlay(a.frame, canon_check.HF, "frame2052.png", side="frame2052-side.png")
sys.exit(1 if bad else 0)
