"""An Almighty bot walks a built silo the way a player would: from the outer ring path through the berm's cut, over
the bowl past the camera block, down the slot, the ramps, the airlock, level 1 to the gallery, then down the stair
core a few levels. The route below the surface is the shortest walk over the generated volume (walk.py's graph,
the same silo regenerated in world coordinates); the bot gets it as walk_to waypoints and walks it with its own keys.

  uv run --with httpx --with numpy --with scipy bot_walk.py LAYOUT.json DONE.json SILO [--levels 4]

Needs ALMIGHTY_URL / ALMIGHTY_TOKEN_FILE. Prints each leg and the bot's position; exit 1 when the bot stops more
than 3 blocks from where a leg should end.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from build_live import Bridge  # noqa: E402
import walk as W  # noqa: E402
from silo import CAMERA, EXIT_X, Silo, Spec  # noqa: E402
from tunnels import TURNS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("layout"); ap.add_argument("done"); ap.add_argument("silo", type=int)
ap.add_argument("--levels", type=int, default=4, help="walk down to this level's gallery")
a = ap.parse_args()
L = json.load(open(a.layout)); D = json.load(open(a.done))
s = next(x for x in L["silos"] if x["number"] == a.silo)
cx, cz, grade, k = s["x"], s["z"], D[f"silo{a.silo}"]["grade"], TURNS[s["dir"]]


def world(fx: float, fz: float) -> tuple[float, float]:
    """Silo frame (way in due west) -> world, k clockwise quarter turns (turn.py: (x, z) -> (-z, x))."""
    x, z = fx, fz
    for _ in range(k % 4):
        x, z = -z, x
    return cx + x, cz + z


# the volume and its walk graph, in world rows (Silo built at its real place, frame not turned)
if a.silo == 1:
    from silo1 import Silo1 as cls
else:
    cls = Silo
sil = cls(Spec(number=a.silo), 0, grade, 0)
vol = sil.build()
w = W.Walk(vol.ids, vol.palette)
R = sil.R
X_, H_, Z_ = w.shape
oy = vol.origin[1]

# graph edges as in Walk.components, kept as a sparse matrix
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import breadth_first_order  # noqa: E402

node, feet, free = w.node, w.feet, w.free
idx = np.flatnonzero(node.ravel()); pos = np.full(node.size, -1, np.int64); pos[idx] = np.arange(idx.size)
rows, cols = [], []
for dx, dz in ((1, 0), (0, 1)):
    for dy in (-1, 0, 1):
        ya0, ya1 = max(0, -dy), H_ - max(0, dy)
        A = (slice(0, X_ - dx), slice(ya0, ya1), slice(0, Z_ - dz))
        B = (slice(dx, X_), slice(ya0 + dy, ya1 + dy), slice(dz, Z_))
        ok = node[A] & node[B] & (np.abs(feet[A] - feet[B]) <= 1.0 + 1e-3)   # a step or a jump, as walk.py
        xa, ya, za = np.nonzero(ok)
        ia = (xa + A[0].start) * H_ * Z_ + (ya + A[1].start) * Z_ + (za + A[2].start)
        ib = ia + dx * H_ * Z_ + dy * Z_ + dz
        rows += [pos[ia], pos[ib]]; cols += [pos[ib], pos[ia]]
cl = w.climb & node                     # ladders and scaffolding: the node right over it, as walk.py
m = node[:, :-1, :] & node[:, 1:, :] & (cl[:, :-1, :] | cl[:, 1:, :])
xa, ya, za = np.nonzero(m)
ia = xa * H_ * Z_ + ya * Z_ + za
rows += [pos[ia], pos[ia + Z_]]; cols += [pos[ia + Z_], pos[ia]]
r = np.concatenate(rows); c = np.concatenate(cols)
G = coo_matrix((np.ones(r.size, np.int8), (r, c)), shape=(idx.size, idx.size)).tocsr()


def nearest(fx, fz, y_world):
    """Node nearest the frame point at about that height (feet within 2)."""
    i0, k0 = int(round(fx)) + R, int(round(fz)) + R
    best = None
    for di in range(-4, 5):
        for dk in range(-4, 5):
            i, kk = i0 + di, k0 + dk
            for j in range(max(0, y_world - oy - 2), min(H_, y_world - oy + 3)):
                if 0 <= i < X_ and 0 <= kk < Z_ and node[i, j, kk]:
                    d = di * di + dk * dk + (j + oy - y_world) ** 2
                    if best is None or d < best[0]:
                        best = (d, i * H_ * Z_ + j * Z_ + kk)
    if best is None:
        raise SystemExit(f"no node near {fx},{fz} y {y_world}")
    return pos[best[1]]


start = nearest(EXIT_X, 0, grade + 1)
goal = nearest(-(sil.s.r_atrium + 2.5), 0, sil.level_y(a.levels) + oy)
order, pred = breadth_first_order(G, start, directed=False, return_predecessors=True)
if pred[goal] < 0 and goal != start:
    raise SystemExit(f"silo {a.silo}: level {a.levels}'s gallery is not reachable from the stair head")
path = [goal]
while path[-1] != start:
    path.append(pred[path[-1]])
path.reverse()
cells = []
for p in path:
    flat = idx[p]; i, rem = divmod(flat, H_ * Z_); j, kk = divmod(rem, Z_)
    cells.append((i - R + 0.5, j + oy, kk - R + 0.5))
# waypoints: where the walk turns, and at least every 6 blocks
way = [cells[0]]
for q in range(1, len(cells) - 1):
    a0, a1, a2 = cells[q - 1], cells[q], cells[q + 1]
    turn = (a1[0] - a0[0], a1[2] - a0[2]) != (a2[0] - a1[0], a2[2] - a1[2])
    if turn or math.hypot(a1[0] - way[-1][0], a1[2] - way[-1][2]) >= 6:
        way.append(a1)
way.append(cells[-1])
# the surface: ring path on the cut side (frame +x) -> through the cut -> over the bowl to the pad -> round the camera
# block to the stair head
cam_back = CAMERA[1]
surface = [(110, 0), (60, 0), (0, 0), (cam_back + 5, 0), (cam_back + 3, 4.5), (EXIT_X + 0.5, 4.5),
           (EXIT_X + 0.5, 0.5)]
legs = [("surface", [(*world(x + 0.5, z + 0.5), grade + 1) for x, z in surface])]
legs.append(("down", [(*world(x, z), y) for x, y, z in way[1:]]))

if os.environ.get("DRY"):
    for leg, pts in legs:
        print(leg, len(pts), [tuple(round(v, 1) for v in p) for p in pts[:6]], "...", [tuple(round(v, 1) for v in p) for p in pts[-3:]])
    print("ys", [round(c[1]) for c in way[::max(1, len(way) // 20)]])
    sys.exit(0)
os.environ.setdefault("ALMIGHTY_URL", "http://10.0.6.2:25654")
br = Bridge()
name = f"walker{a.silo}"
x0, z0, _ = legs[0][1][0]
area = br.call("area.prepare", {"from": [int(cx) - 140, int(cz) - 140], "to": [int(cx) + 140, int(cz) + 140],
                                "ttl_seconds": 900, "wait": 50})
fail = False
try:
    try:
        br.call("bot.remove", {"name": name})
    except Exception:
        pass
    br.call("bot.spawn", {"name": name, "pos": [x0, grade + 8, z0], "gamemode": "survival"})
    time.sleep(3)
    for leg, pts in legs:
        print(f"{leg}: {len(pts)} waypoints", flush=True)
        for q, (x, z, y) in enumerate(pts):
            acts = [{"walk_to": [x, z], "within": 0.25}]
            if q + 1 < len(pts) and pts[q + 1][2] < y - 2:
                acts.append({"wait": 20 + 4 * int(y - pts[q + 1][2])})     # down a ladder or a drop: let it land
            res = br.call("bot.act", {"name": name, "actions": acts, "replace": True, "wait": 50})
            st = br.call("bot", {"name": name})
            p = st.get("body", st).get("pos") or st.get("pos")
            d = math.hypot(p[0] - x, p[2] - z)
            if d > 3:
                print(f"  STUCK at {[round(v, 1) for v in p]} going to {round(x, 1)},{round(z, 1)} "
                      f"(leg {leg} waypoint {q}): {str(res)[:200]}", flush=True)
                fail = True
                break
        if fail:
            break
        print(f"  reached {[round(v, 1) for v in p]}", flush=True)
    if not fail:
        print(f"silo {a.silo}: PASS, from the ring path to level {a.levels}'s gallery (y {round(p[1], 1)})")
finally:
    try:
        br.call("bot.remove", {"name": name})
    except Exception:
        pass
    br.call("area.release", {"id": area["id"]})
sys.exit(1 if fail else 0)
