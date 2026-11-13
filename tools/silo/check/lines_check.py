"""The built straight paths against their measurement on the 2052 aerial (canon/lines.json): along each measured line
(axis, founders' lines, north cross) the nearest path block in the world must lie within --tol (12 m: the frame's
homography error at most); also the axis must be one straight line through Silo 1's centre (within 2 blocks).

  uv run --with numpy lines_check.py SCAN.npz LAYOUT.json [--tol 12]
"""
import argparse, json, math, os, sys
import numpy as np
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("scan"); ap.add_argument("layout"); ap.add_argument("--tol", type=float, default=12)
a = ap.parse_args()
d = np.load(a.scan, allow_pickle=True); G = d["ground"]; X0, Z0 = int(d["x0"]), int(d["z0"]); names = list(d["names"])
L = json.load(open(a.layout)); meas = json.load(open(os.path.join(HERE, "..", "canon", "lines.json")))
one = next(s for s in L["silos"] if s["number"] == 1)["ring"]
rot = math.radians(L["rotation_deg"]); cs, sn = math.cos(rot), math.sin(rot); e = L["spacing"]
W = lambda p: (one[0] + p[0] * e * cs - p[1] * e * sn, one[1] + p[0] * e * sn + p[1] * e * cs)
path_ids = [i for i, n in enumerate(names) if n.split(":")[-1] in ("smooth_sandstone", "dirt_path", "gravel")]
mask = np.isin(G, path_ids)
dist = ndimage.distance_transform_edt(~mask)
bad = []
for l in meas["lines"]:
    p0, p1 = W(l["from"]), W(l["to"])
    ds = []
    for t in np.linspace(0.05, 0.95, 60):
        x, z = p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])
        i, k = int(x) - X0, int(z) - Z0
        if 0 <= i < dist.shape[0] and 0 <= k < dist.shape[1]:
            ds.append(dist[i, k])
    worst = max(ds) if ds else float("inf")
    ok = worst <= a.tol
    print(f"{'ok  ' if ok else 'FAIL'} {l['name']:14s} worst {worst:5.1f} m, median {np.median(ds):4.1f} m over {len(ds)} samples")
    if not ok:
        bad.append(l["name"])
sys.exit(1 if bad else 0)
