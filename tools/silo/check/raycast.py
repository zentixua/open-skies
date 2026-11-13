"""A perspective view of the world's top surface (a scan from top.py) for comparing with a film frame when the bridge's
`see` cannot reach far enough (it draws ~100 blocks): rays march over the heightfield (crowns stand 6 m over the
ground they cover), each hit coloured by its top block and shaded by the surface normal (sun from the north-west,
35 degrees up) with distance haze.

  uv run --with numpy --with pillow raycast.py SCAN.npz OUT.png --at x y z --yaw DEG --pitch DEG [--fov 60] [--size 960x540]

yaw/pitch as Minecraft: yaw 0 looks +z (south), 90 looks -x; pitch > 0 looks down.
"""
import argparse
import math

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("scan"); ap.add_argument("out")
ap.add_argument("--at", nargs=3, type=float, required=True)
ap.add_argument("--yaw", type=float, required=True); ap.add_argument("--pitch", type=float, default=0)
ap.add_argument("--fov", type=float, default=60); ap.add_argument("--size", default="960x540")
ap.add_argument("--far", type=float, default=900)
a = ap.parse_args()
W, H = (int(v) for v in a.size.split("x"))
d = np.load(a.scan, allow_pickle=True)
G, GY, CAN = d["ground"], d["gy"].astype(np.float32), d["canopy"]
X0, Z0 = int(d["x0"]), int(d["z0"])
names = list(d["names"])
PAL = {"grass_block": (110, 160, 60), "dirt": (134, 96, 67), "coarse_dirt": (120, 85, 58), "dirt_path": (148, 120, 74),
       "water": (64, 100, 196), "sand": (219, 207, 163), "gravel": (150, 142, 136), "stone": (122, 122, 122),
       "smooth_sandstone": (222, 212, 175), "white_terracotta": (205, 178, 160), "smooth_stone": (170, 170, 170), "smooth_stone_slab": (170, 170, 170),
       "polished_andesite": (140, 142, 140), "polished_andesite_stairs": (140, 142, 140),
       "light_gray_concrete": (155, 155, 150), "gray_concrete": (90, 92, 96), "white_concrete": (220, 222, 222),
       "moss_block": (89, 109, 45), "clay": (160, 165, 178), "polished_blackstone": (45, 42, 48)}
pal = np.zeros((len(names) + 1, 3), np.float32)
for i, n in enumerate(names):
    b = n.split(":")[-1]
    c = PAL.get(b)
    if c is None:
        c = (120, 90, 55) if b.endswith(("_log", "_wood")) else ((55, 110, 40) if b.endswith("_leaves") else (150, 150, 150))
    pal[i] = c
known = GY > -9000
Hh = np.where(known, GY, np.median(GY[known])) + np.where(CAN, 6.0, 0.0)
gx, gz = np.gradient(Hh)
az, alt = math.radians(315), math.radians(35)
lx, lz, ly = math.cos(alt) * math.cos(az), math.cos(alt) * math.sin(az), math.sin(alt)
shade = np.clip((-gx * lx - gz * lz + ly) / np.sqrt(gx * gx + gz * gz + 1) / ly, 0.4, 1.3).astype(np.float32)
col = pal[np.clip(G, 0, len(names) - 1)] * shade[..., None]
col[CAN] = col[CAN] * 0.5 + np.array([25, 55, 22], np.float32) * 0.5
# rays
yaw, pitch = math.radians(a.yaw), math.radians(a.pitch)
fwd = np.array([-math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
right = np.array([-math.cos(yaw), 0.0, -math.sin(yaw)])
up = np.cross(right, fwd)
f = 0.5 * W / math.tan(math.radians(a.fov) / 2)
u, v = np.meshgrid(np.arange(W) - W / 2 + 0.5, np.arange(H) - H / 2 + 0.5)
dirs = fwd[None, None, :] * f + right[None, None, :] * u[..., None] - up[None, None, :] * v[..., None]
dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
ox, oy, oz = a.at
img = np.zeros((H, W, 3), np.float32)
hit = np.zeros((H, W), bool)
t = np.full((H, W), 0.5, np.float32)
sky = np.array([175, 195, 215], np.float32)
while True:
    act = ~hit & (t < a.far)
    if not act.any():
        break
    px = ox + dirs[..., 0] * t; py = oy + dirs[..., 1] * t; pz = oz + dirs[..., 2] * t
    ix = np.floor(px).astype(int) - X0; iz = np.floor(pz).astype(int) - Z0
    inside = (ix >= 0) & (ix < Hh.shape[0]) & (iz >= 0) & (iz < Hh.shape[1])
    ixc, izc = np.clip(ix, 0, Hh.shape[0] - 1), np.clip(iz, 0, Hh.shape[1] - 1)
    h = Hh[ixc, izc] + 1.0
    new = act & inside & (py <= h)
    if new.any():
        haze = np.clip(t[new] / a.far, 0, 1)[:, None] ** 1.3
        img[new] = col[ixc[new], izc[new]] * (1 - haze * 0.6) + sky * haze * 0.6
        hit |= new
    t = np.where(act, t + np.maximum(0.25, t * 0.004), t)
img[~hit] = sky
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(a.out)
print(a.out, W, H)
