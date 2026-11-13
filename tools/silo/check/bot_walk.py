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
    """Silo-frame point -> world: its block (floor) turned k quarters as turn.turn_volume turns blocks (integer
    (x, z) -> (-z, x) about the shaft column), then that block's centre."""
    x, z = fx, fz
    for _ in range(k % 4):
        x, z = 1 - z, x            # a block's centre (b + 0.5) lands on the turned block's centre
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
cl = w.climb & node & (os.environ.get("NOCLIMB") is None)   # ladders and scaffolding (NOCLIMB: stairs only)
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
# doorways: a double iron door's open leaves lie along its outer jambs, a single one along a jamb; the bot goes
# through the middle of the doorway (between the leaves), so path cells in a door are moved onto that centre line
door_ids = {i for i, st in enumerate(vol.palette) if "iron_door" in st or "_door[" in st}
door = np.isin(vol.ids, list(door_ids)).any(axis=1)          # [x, z]
fixed = []
for q, (x, y, z) in enumerate(cells):
    i, kk = int(math.floor(x)) + R, int(math.floor(z)) + R
    if 0 <= i < door.shape[0] and 0 <= kk < door.shape[1] and door[i, kk]:
        # the doorway runs across the walk: its cells are the door cells in line with this one, across the walk
        if q + 1 < len(cells):
            dx_, dz_ = cells[q + 1][0] - cells[q - 1][0], cells[q + 1][2] - cells[q - 1][2]
        else:
            dx_, dz_ = 1, 0
        if abs(dx_) >= abs(dz_):        # walking along x: the doorway spans z
            ks = [kk + d for d in range(-2, 3) if 0 <= kk + d < door.shape[1] and door[i, kk + d]]
            z = (min(ks) + max(ks) + 1) / 2 - R
        else:
            is_ = [i + d for d in range(-2, 3) if 0 <= i + d < door.shape[0] and door[i + d, kk]]
            x = (min(is_) + max(is_) + 1) / 2 - R
        fixed.append((x, y, z, True))
    else:
        fixed.append((x, y, z, False))
cells_d = fixed
# waypoints: where the walk turns, at least every 6 blocks, and a block before, in and after every doorway
way = [cells[0]]
for q in range(1, len(cells) - 1):
    a0, a1, a2 = cells[q - 1], cells[q], cells[q + 1]
    turn = (a1[0] - a0[0], a1[2] - a0[2]) != (a2[0] - a1[0], a2[2] - a1[2])
    if False:
        pass
    elif turn or math.hypot(a1[0] - way[-1][0], a1[2] - way[-1][2]) >= 6:
        way.append(a1)
way.append(cells[-1])
# the surface: ring path on the cut side (frame +x) -> through the cut -> over the bowl to the pad -> round the camera
# block to the stair head
cam_back = CAMERA[1]
surface = [(110, 0), (60, 0), (0, 0), (cam_back + 5, 0), (cam_back + 3, 4.5), (EXIT_X + 0.5, 4.5),
           (EXIT_X + 0.5, 0.5)]
if a.silo == 1:          # Silo 1's cut is where the opening-day path leaves due south: frame -z after its two turns
    surface = [(0, -110), (0, -40), (-10, -10), (EXIT_X + 0.5, -4.5), (EXIT_X + 0.5, 0.5)]
legs = [("surface", [(*world(x + 0.5, z + 0.5), grade + 1) for x, z in surface])]
legs.append(("down", [(*world(x, z), y) for x, y, z in way[1:]]))

if os.environ.get("DRY"):
    for leg, pts in legs:
        print(leg, len(pts), [tuple(round(v, 1) for v in p) for p in pts[:6]], "...", [tuple(round(v, 1) for v in p) for p in pts[-3:]])
    print("ys", [round(c[1]) for c in way[::max(1, len(way) // 20)]])
    print("down", [(q, tuple(round(float(v), 2) for v in p)) for q, p in enumerate(legs[1][1]) if q in range(int(os.environ.get("DQ", 8)) - 4, int(os.environ.get("DQ", 8)) + 4)])
    sys.exit(0)
os.environ.setdefault("ALMIGHTY_URL", "http://10.0.6.2:25654")
br = Bridge()
name = f"w{a.silo}x{int(time.time()) % 1000000}"     # fresh: a known bot comes back where it left
x0, z0, _ = legs[0][1][0]
area = br.call("area.prepare", {"from": [int(cx) - 140, int(cz) - 140], "to": [int(cx) + 140, int(cz) + 140],
                                "ttl_seconds": 900, "wait": 50})
fail = False
saved = []
try:
    try:
        br.call("bot.remove", {"name": name})
    except Exception:
        pass
    # Almighty's bot does not press pressure plates (13.11: on the airlock's heavy plate its power stays 0), and open
    # iron leaves stand in a 0.6-wide body's way depending on the hinges: the iron doors on the route are taken out for
    # the test, each state saved, and put back exactly after it (no block updates)
    xs_ = [p[0] for _, pts in legs for p in pts]; zs_ = [p[1] for _, pts in legs for p in pts]
    ys_ = [p[2] for _, pts in legs for p in pts]
    box = [int(min(xs_)) - 3, int(min(ys_)) - 2, int(min(zs_)) - 3, int(max(xs_)) + 3, int(max(ys_)) + 3, int(max(zs_)) + 3]
    DOORS = """import net.minecraft.core.BlockPos
import net.minecraft.core.registries.Registries
import net.minecraft.commands.arguments.blocks.BlockStateParser
def w = server.overworld(); def out = []
if (args.restore != null) {
  def look = w.holderLookup(Registries.BLOCK)
  for (e in args.restore) { w.setBlock(new BlockPos(e[0], e[1], e[2]), BlockStateParser.parseForBlock(look, e[3], false).blockState(), 18) }
  return args.restore.size()
}
for (x in args.b[0]..args.b[3]) for (y in args.b[1]..args.b[4]) for (z in args.b[2]..args.b[5]) {
  def p = new BlockPos(x, y, z); def s = w.getBlockState(p)
  if (s.getBlock() == net.minecraft.world.level.block.Blocks.IRON_DOOR) {
    def str = s.toString().replace('Block{', '').replace('}', '')
    out << [x, y, z, str]
    w.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), 18) } }
return out"""
    saved = br.call("script", {"code": DOORS, "args": {"b": box, "restore": None}, "timeout_ms": 10000})["value"]
    print("iron doors taken out for the bot (it does not press plates):", len(saved), flush=True)
    br.call("bot.spawn", {"name": name, "pos": [x0, grade + 8, z0], "gamemode": "survival"})
    time.sleep(3)
    for leg, pts in legs:
        print(f"{leg}: {len(pts)} waypoints", flush=True)
        for q, (x, z, y) in enumerate(pts):
            acts = [{"walk_to": [x, z], "within": 0.25}]
            res = br.call("bot.act", {"name": name, "actions": acts, "replace": True, "wait": 50})
            st0 = br.call("bot", {"name": name}); p = st0.get("pos")
            if math.hypot(p[0] - x, p[2] - z) > 3:
                print(f"  STUCK at {[round(v, 1) for v in p]} going to {round(x, 1)},{round(z, 1)} "
                      f"(leg {leg} waypoint {q}): {str(res)[:200]}", flush=True)
                fail = True
                break
            if q + 1 < len(pts) and pts[q + 1][2] < y - 2 and math.hypot(pts[q + 1][0] - x, pts[q + 1][1] - z) <= 1.5:
                # down a ladder: slide (≈0.15 m a tick), brake with sneak at the floor the route leaves it on, and
                # climb back a little with jump if it slid past
                target = pts[q + 1][2]
                br.call("bot.act", {"name": name, "actions": [{"release": "all"}], "replace": True, "wait": 5})
                for _ in range(80):
                    yy = br.call("bot", {"name": name})["pos"][1]
                    if abs(yy - target) <= 0.3:
                        break
                    if yy > target:
                        step = [{"release": "all"}, {"wait": max(1, min(20, int((yy - target) / 0.15) - 2))},
                                {"hold": "sneak", "ticks": 4}]
                    else:
                        step = [{"hold": "jump", "ticks": max(2, min(10, int((target - yy) / 0.12)))},
                                {"hold": "sneak", "ticks": 4}]
                    br.call("bot.act", {"name": name, "actions": step, "replace": True, "wait": 10})
                print(f"  ladder: down to y {round(br.call('bot', {'name': name})['pos'][1], 1)} (route {target})", flush=True)
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
    try:
        if saved:
            print("iron doors put back:", br.call("script", {"code": DOORS, "args": {"b": box, "restore": saved},
                                                             "timeout_ms": 10000})["value"])
    except Exception as e:
        print("could not shut the doors again:", e)
    br.call("area.release", {"id": area["id"]})
sys.exit(1 if fail else 0)
