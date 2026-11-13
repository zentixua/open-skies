"""Each ring's axis, read from the world: the slot (its open steps), the camera block (its roof slab) and the berm's
cut must lie on the ring's axis (layout "dir": the slot's side; the cut on the opposite side, Silo 1's due south).

  uv run --with numpy axis_check.py SCAN.npz LAYOUT.json POSITIONS.json

SCAN.npz: top ground per column (top.py); POSITIONS.json: the ring centres read from the world (compare.py).
Per ring: slot and camera centroids off the axis line (blocks, must be <= 1) and their bearing (degrees off the axis,
must be <= 2); the camera right behind the stair head, between it and the centre (S3E09 07); the crest at the cut at least 2 lower than the crest's median.
Exit status 1 on any failure.
"""
import json
import math
import sys

import numpy as np

d = np.load(sys.argv[1], allow_pickle=True)
G, GY = d["ground"], d["gy"].astype(float)
X0, Z0 = int(d["x0"]), int(d["z0"])
names = list(d["names"])
L = json.load(open(sys.argv[2]))
P = {int(k): v for k, v in json.load(open(sys.argv[3])).items()}
CARD = {"W": (-1, 0), "N": (0, -1), "E": (1, 0), "S": (0, 1)}
STAIR = {i for i, n in enumerate(names) if n.endswith("smooth_stone_stairs")}
SLAB = {i for i, n in enumerate(names) if n.endswith("smooth_stone_slab")}
fails = []
for s in L["silos"]:
    n = s["number"]
    cx, cz = P[n]
    ax, az = CARD[s["dir"]]                       # unit vector from the centre toward the slot
    i0, k0 = int(cx - X0), int(cz - Z0)
    sub = G[i0 - 45:i0 + 46, k0 - 45:k0 + 46]
    xs, zs = np.meshgrid(np.arange(-45, 46), np.arange(-45, 46), indexing="ij")
    along, across = xs * ax + zs * az, -xs * az + zs * ax

    def blob(ids, r0, r1):
        m = np.isin(sub, list(ids)) & (along >= r0) & (along <= r1) & (np.abs(across) <= 6)
        if m.sum() < 3:
            return None
        return float(along[m].mean()), float(across[m].mean()), int(m.sum())

    slot, cam = blob(STAIR, 15, 33), blob(SLAB, 12, 24)
    row = [f"silo {n:2d} {s['dir']}"]
    ok = True
    for nm, b in (("slot", slot), ("camera", cam)):
        if b is None:
            row.append(f"{nm} MISSING"); ok = False
            continue
        a, c, m = b
        deg = math.degrees(math.atan2(abs(c), a))
        row.append(f"{nm} at {a:4.1f} off {c:+.1f} ({deg:.1f} deg)")
        ok &= abs(c) <= 1 and deg <= 2
    if slot and cam and not (slot[0] - 8 <= cam[0] < slot[0]):
        row.append("camera not right behind the stair head"); ok = False
    # the cut: crest heights round the ring at r 62-80, the cut's bearing vs the median
    if n == 1:
        cb = math.atan2(1, 0)
    else:
        cb = math.atan2(-az, -ax)
    crest = []
    for deg in range(0, 360, 3):
        a = math.radians(deg)
        h = [GY[int(cx + r * math.cos(a)) - X0, int(cz + r * math.sin(a)) - Z0] for r in range(60, 82)]
        crest.append((deg, max(h)))
    med = float(np.median([h for _, h in crest]))
    at = min(crest, key=lambda q: abs((math.radians(q[0]) - cb + math.pi) % (2 * math.pi) - math.pi))[1]
    row.append(f"cut {med - at:+.0f} under the crest")
    ok &= med - at >= 2
    if not ok:
        fails.append(n)
    print(("ok   " if ok else "FAIL ") + "  ".join(row))
print(f"{50 - len(fails)}/50 rings on axis; failing: {fails}")
sys.exit(1 if fails else 0)
