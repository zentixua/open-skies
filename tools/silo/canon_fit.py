# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "scipy"]
# ///
"""Fit the canon layout (canon_layout.json) to the two images from the show: one ground layout, seen in the founders'
plaque (S3E09) and in the high oblique of the complex (Reddit frame 1). Flowers are regular hexagons of equal edge; a
homography maps the ground to each image. Points: canon/image_points.json.

  uv run tools/silo/canon_fit.py      # prints residuals and the ground, writes canon/fit.json
"""
import json, os
import numpy as np
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__))
pts = json.load(open(os.path.join(HERE, "canon", "image_points.json")))
PL = {(int(k) if k.isdigit() else k): np.array(v, float) for k, v in pts["plaque"].items()}
FR = {k: np.array(v, float) for k, v in pts["frame"].items()}
corr = {(int(k) if k.isdigit() else k): v for k, v in pts["frame_of"].items()}
flowers = {7: [8, 9, 10, 11, 12, 13], 14: [15, 17, 18, 19, 20, 21], 22: [23, 24, 25, 26, 27, 28],
           29: [30, 31, 32, 33, 34, 35], 36: [37, 38, 39, 40, 41, 42], 43: [44, 46, 47, 48, 49, 50]}
order = {}
for h, sats in flowers.items():
    order[h] = sorted(sats, key=lambda s: np.arctan2(*(PL[s] - PL[h])[::-1]))
free = [16, 45, 2, 3, 4, 5, 6]
# initial ground: plaque photo offsets, rotated so the gate is straight up (-y)
g0 = PL["gate"] - PL[1]; ang = np.arctan2(g0[0], -g0[1])
R = np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]])
def init(p): return R @ (p - PL[1]) / 110.0
def unpack(x):
    i = 0; G = {1: np.zeros(2)}
    for h in flowers:
        hx, hy, th = x[i:i + 3]; i += 3; G[h] = np.array([hx, hy])
        for k, s in enumerate(order[h]): G[s] = G[h] + np.array([np.cos(th + k * np.pi / 3), np.sin(th + k * np.pi / 3)])
    for f in free: G[f] = x[i:i + 2]; i += 2
    G["gate"] = np.array([0.0, x[i]]); i += 1
    Hp = np.append(x[i:i + 8], 1).reshape(3, 3); i += 8
    Hf = np.append(x[i:i + 8], 1).reshape(3, 3); i += 8
    return G, Hp, Hf
def proj(H, p):
    q = H @ np.array([p[0], p[1], 1.0]); return q[:2] / q[2]
def dlt(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    H = np.linalg.svd(np.array(A))[2][-1].reshape(3, 3); return H / H[2, 2]
x0 = []
for h in flowers:
    c = init(PL[h]); s0 = init(PL[order[h][0]]) - c; x0 += [c[0], c[1], np.arctan2(s0[1], s0[0])]
for f in free: x0 += list(init(PL[f]))
x0 += [init(PL["gate"])[1]]
G0, _, _ = unpack(np.r_[x0, np.zeros(16)])
keys = [k for k in PL]; Hp0 = dlt([G0[k] for k in keys], [PL[k] for k in keys])
ck = list(corr); Hf0 = dlt([G0[k] for k in ck], [FR[corr[k]] for k in ck])
x0 = np.r_[x0, Hp0.ravel()[:8], Hf0.ravel()[:8]]
def res(x):
    G, Hp, Hf = unpack(x)
    r = [(proj(Hp, G[k]) - PL[k]) / 10 for k in keys]
    r += [(proj(Hf, G[k]) - FR[corr[k]]) / 10 for k in ck]
    return np.concatenate(r)
sol = least_squares(res, x0, x_scale="jac", max_nfev=20000)
G, Hp, Hf = unpack(sol.x)
rp = np.array([np.linalg.norm(proj(Hp, G[k]) - PL[k]) for k in keys])
rf = np.array([np.linalg.norm(proj(Hf, G[k]) - FR[corr[k]]) for k in ck])
print("plaque px residual rms %.1f max %.1f (%s)" % (np.sqrt((rp ** 2).mean()), rp.max(), keys[rp.argmax()]))
print("frame  px residual rms %.1f max %.1f (%s)" % (np.sqrt((rf ** 2).mean()), rf.max(), ck[rf.argmax()]))
for k, v in sorted(zip(ck, rf), key=lambda t: -t[1])[:8]: print("  frame worst", k, round(v, 1))
for k, v in sorted(zip(keys, rp), key=lambda t: -t[1])[:8]: print("  plaque worst", k, round(v, 1))
json.dump({"ground": {str(k): v.tolist() for k, v in G.items()}, "Hp": Hp.tolist(), "Hf": Hf.tolist()}, open(os.path.join(HERE, "canon", "fit.json"), "w"))
nums = sorted(k for k in G if k != "gate")
D = np.array([[np.linalg.norm(G[a] - G[b]) for b in nums] for a in nums]); np.fill_diagonal(D, 9)
print("nearest-neighbour distances (edge units): min %.2f median %.2f" % (D.min(1).min(), np.median(D.min(1))))
print("gate distance", round(float(-G["gate"][1]), 2))
for k in nums: print(k, np.round(G[k], 2))
