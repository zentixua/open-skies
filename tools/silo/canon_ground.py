"""What the show's 2052 aerial shows on the ground, mapped onto our world: trees, water and pale ground (gravel,
roads), per 4 m cell, through the frame's homography (canon/fit.json Hf1920, ground in canon units -> pixels of
aerial2052-1920.jpg) and the layout's own frame (Silo 1, rotation, edge).

Classes from colour (Lab of the 3x3-blurred frame), chosen by clustering the frame and checking each mask on it:
- trees: dark, less yellow than grass (b < 137, L < 90, a < 126), or locally darker than their surroundings with a
  leafy texture (the sunlit groves); berm shadows (thin arcs on each ring's berm) are dropped;
- water: blue (H 88-115 in OpenCV's HSV, S > 60) and smooth (the hazy far forest is as blue, but leafy);
- pale: low saturation, bright (paths, gravel, roads, roofs).

  uv run --with numpy --with opencv-python-headless canon_ground.py AERIAL.jpg LAYOUT.json OUT.npz [--png P]

OUT.npz: tree, water, pale (fraction of the cell's pixels, 0-1), seen (the cell is inside the frame), x0, z0, cell.
"""
from __future__ import annotations

import argparse
import json
import math
import os

import cv2
import numpy as np

import canon_check

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("aerial"); ap.add_argument("layout"); ap.add_argument("out")
ap.add_argument("--cell", type=int, default=4)
ap.add_argument("--margin", type=float, default=1500, help="metres beyond the outermost rings")
ap.add_argument("--png")
ap.add_argument("--reach", type=float, default=420, help="water and pale ground only within this of a ring centre")
ap.add_argument("--tree-reach", type=float, default=1500, help="trees within this of a ring centre")
a = ap.parse_args()
Hf = np.array(json.load(open(os.path.join(HERE, "canon", "fit.json")))["Hf1920"])
im = cv2.imread(a.aerial)
lab = cv2.cvtColor(cv2.blur(im, (3, 3)), cv2.COLOR_BGR2LAB).astype(float)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
Lc, Ac, Bc = lab[..., 0], lab[..., 1], lab[..., 2]
hp = g - cv2.GaussianBlur(g, (0, 0), 2)
tex = np.sqrt(cv2.blur(hp * hp, (9, 9)))
rel = cv2.blur(g, (3, 3)) / (cv2.blur(g, (101, 101)) + 1)
tree = ((Bc < 137) & (Lc < 90) & (Ac < 126)) | ((rel < 0.82) & (tex > 4.5) & (Ac < 128))
tree = cv2.morphologyEx(tree.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
# the far forest is as blue as the ponds in the haze; ponds are smooth, the forest leafy
water = ((hsv[..., 0] > 88) & (hsv[..., 0] < 115) & (hsv[..., 1] > 60) & (tex < 3.5)).astype(np.uint8)
water = cv2.morphologyEx(water, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
pale = ((hsv[..., 1] < 60) & (hsv[..., 2] > 150)).astype(np.uint8)
H_, W_ = g.shape

L = json.load(open(a.layout))
one_s = next(s for s in L["silos"] if s["number"] == 1)
one = tuple(one_s["ring"]); rot, edge = L["rotation_deg"], L["spacing"]
xs = [s["x"] for s in L["silos"]]; zs = [s["z"] for s in L["silos"]]
x0, x1 = int(min(xs) - a.margin), int(max(xs) + a.margin)
z0, z1 = int(min(zs) - a.margin), int(max(zs) + a.margin)
C = a.cell
gx = np.arange(x0, x1, C) + C / 2; gz = np.arange(z0, z1, C) + C / 2
WX, WZ = np.meshgrid(gx, gz, indexing="ij")
out = {k: np.zeros(WX.shape, np.float32) for k in ("tree", "water", "pale", "dark")}
darkness = np.clip((95 - Lc) / 45, 0, 1).astype(np.float32)      # 0 bright grass .. 1 the darkest canopy
seen = np.zeros(WX.shape, bool)
# 3 x 3 samples per cell
c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
n = 0
for ox in (-C / 3, 0, C / 3):
    for oz in (-C / 3, 0, C / 3):
        dx, dz = (WX + ox - one[0]) / edge, (WZ + oz - one[1]) / edge
        u, v = dx * c + dz * s, -dx * s + dz * c
        q = Hf @ np.stack([u.ravel(), v.ravel(), np.ones(u.size)])
        px, py = (q[0] / q[2]).reshape(u.shape), (q[1] / q[2]).reshape(u.shape)
        ok = (q[2].reshape(u.shape) > 0) & (px >= 0) & (px < W_ - 1) & (py >= 0) & (py < H_ - 1)
        ix, iy = np.clip(px.astype(int), 0, W_ - 1), np.clip(py.astype(int), 0, H_ - 1)
        for k, m in (("tree", tree), ("water", water), ("pale", pale)):
            out[k] += np.where(ok, m[iy, ix], 0)
        out["dark"] += np.where(ok, darkness[iy, ix] * tree[iy, ix], 0)
        seen |= ok
        n += 1
for k in out:
    out[k] /= n
out["dark"] = np.where(out["tree"] > 0, out["dark"] / np.maximum(out["tree"], 1e-6), 0)
# berm shadows: thin dark arcs on each ring's berm read as trees; the frame shows no trees on the bowl floors and only
# lone ones on the crests, so drop tree cells within the berm and bowl (r < 82) unless part of a grove reaching out
r_min = np.full(WX.shape, 1e9)
for s_ in L["silos"]:
    r_min = np.minimum(r_min, np.hypot(WX - s_["ring"][0], WZ - s_["ring"][1]))
out["tree"][r_min < 82] = 0
# only the complex and its edge: beyond, the frame's hazy far forest reads as water, and Zearth's own land stays
for k in ("water", "pale"):
    out[k][r_min > a.reach] = 0
for k in ("tree", "dark"):                     # the forest round the field: as far as the frame sees it well
    out[k][r_min > a.tree_reach] = 0
np.savez_compressed(a.out, **out, seen=seen, x0=x0, z0=z0, cell=C)
print(f"grid {WX.shape} from {x0},{z0} cell {C}: tree {float((out['tree'] > 0.5).sum() * C * C) / 1e4:.1f} ha, "
      f"water {float((out['water'] > 0.5).sum() * C * C) / 1e4:.1f} ha, seen {float(seen.sum() * C * C) / 1e6:.1f} km2")
if a.png:
    rgb = np.zeros(WX.shape + (3,), np.uint8); rgb[:] = (110, 150, 70)
    rgb[~seen] = (40, 40, 40)
    rgb[out["pale"] > 0.5] = (220, 210, 170)
    rgb[out["tree"] > 0.5] = (30, 80, 30)
    rgb[out["water"] > 0.5] = (60, 100, 200)
    for s_ in L["silos"]:
        i, k = int((s_["ring"][0] - x0) / C), int((s_["ring"][1] - z0) / C)
        cv2.circle(rgb, (i, k), int(110 / C), (255, 255, 255), 1)
    cv2.imwrite(a.png, cv2.cvtColor(rgb.transpose(1, 0, 2).copy(), cv2.COLOR_RGB2BGR))
