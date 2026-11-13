"""Terrace step edges on the plain: columns whose ground differs by a block or more from the next column (x or z),
counted where the plain lies open (farther than 125 m from every ring centre, no crown over it, not a path, within 300 m of a ring and within 3 blocks of the plain's level), per km2.

  uv run --with numpy --with scipy steps_check.py SCAN.npz LAYOUT.json
"""
import json, sys
import numpy as np
from scipy import ndimage
d = np.load(sys.argv[1], allow_pickle=True)
GY = d["gy"].astype(float); CAN = d["canopy"]; G = d["ground"]; names = list(d["names"])
X0, Z0 = int(d["x0"]), int(d["z0"])
L = json.load(open(sys.argv[2]))
grass = [i for i, n in enumerate(names) if n.endswith("grass_block")]
nx, nz = GY.shape
mask = np.zeros((nx, nz), bool)
for s in L["silos"]:
    i, k = int(s["ring"][0]) - X0, int(s["ring"][1]) - Z0
    if 0 <= i < nx and 0 <= k < nz:
        mask[i, k] = True
dist = ndimage.distance_transform_edt(~mask)
level = float(np.median(GY[(dist > 125) & (dist < 300) & (GY > -9000)]))
# the plain itself: its level +-3 (beyond its edge Zearth's own relief starts, which is not the plain's)
open_ = (dist > 125) & (dist < 300) & ~CAN & np.isin(G, grass) & (GY > -9000) & (np.abs(GY - level) <= 3)
ex = np.zeros_like(open_); ez = np.zeros_like(open_)
ex[:-1] = (np.abs(np.diff(GY, axis=0)) >= 1) & open_[:-1] & open_[1:]
ez[:, :-1] = (np.abs(np.diff(GY, axis=1)) >= 1) & open_[:, :-1] & open_[:, 1:]
area_km2 = open_.sum() / 1e6
edges = int(ex.sum() + ez.sum())
print(f"open plain {area_km2:.2f} km2: {edges} step edges, {edges / max(area_km2, 1e-9):.0f} per km2 "
      f"(an edge every {1e6 / max(edges / max(area_km2, 1e-9), 1) :.0f} m2)")
