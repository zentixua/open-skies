"""Can a silo's camera see the camera block of another silo in its group? (layout-facts.md: the berm hides the
silos of a group from each other.) Reads the world's heightmaps (no leaves), so run it on a saved world.
uv run --with numpy --with nbtlib los.py <world> <layout.json> <done.json>"""
import json, math, sys, os
sys.path.insert(0, os.path.expanduser('~/claude/silo-1to1/tools/silo'))
import numpy as np
from heights import read_area, MISSING
from silo import CAMERA
from tunnels import TURNS
from turn import turn_points
world, lay, done = sys.argv[1], json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))
GROUPS = [(2, 6), (7, 13), (14, 21), (22, 28), (29, 35), (36, 42), (43, 50)]   # founders' plaque hubs
S = {s['number']: s for s in lay['silos']}
def cam(n):
    s = S[n]; g = done[f'silo{n}']['grade']
    lx = (CAMERA[0] + CAMERA[1]) / 2; lz = (CAMERA[2] + CAMERA[3]) / 2
    (x, z), = turn_points([(s['x'] + lx, s['z'] + lz)], TURNS[s['dir']], s['x'], s['z'])
    return x, z, g
xs = [s['x'] for s in lay['silos']]; zs = [s['z'] for s in lay['silos']]
X0, Z0 = min(xs) - 80, min(zs) - 80
if os.path.exists('surf.npz') and os.environ.get('CACHE'):
    _d = np.load('surf.npz'); SURF = _d['surf']; water = _d['water']
else:
  ground, water, top = read_area(world, X0, Z0, max(xs) + 80 - X0, max(zs) + 80 - Z0, min_y=-896, height=1216)
  SURF = np.where(water > MISSING, water, ground) + 1        # walking / visual surface
np.savez_compressed('surf.npz', surf=SURF, water=water, x0=X0, z0=Z0)
seen, total = [], 0
for a0, a1 in GROUPS:
    ns = list(range(a0, a1 + 1)) + [1] * 0
    for i in ns:
        for j in ns:
            if i >= j: continue
            total += 1
            xa, za, ga = cam(i); xb, zb, gb = cam(j)
            x0, z0, surf = X0, Z0, SURF
            L = math.hypot(xb - xa, zb - za)
            res = []
            for (ex, ez, eg), (tx, tz, tg) in (((xa, za, ga), (xb, zb, gb)), ((xb, zb, gb), (xa, za, ga))):
                ey, ty = eg + 2.5 + float(os.environ.get('EXTRA', 0)), tg + 4.0 + float(os.environ.get('EXTRA', 0))          # sensor at g+2 (eye mid-block), target: top of the roof (g+3)
                block = None
                for k in range(1, int(L)):
                    t = k / L
                    if t * L < 6 or (1 - t) * L < 6: continue
                    px, pz = ex + t * (tx - ex), ez + t * (tz - ez)
                    h = surf[int(math.floor(px)) - x0, int(math.floor(pz)) - z0]
                    if h > ey + t * (ty - ey):
                        block = (round(px), round(pz), int(h)); break
                res.append(block)
            if res[0] is None or res[1] is None:
                seen.append((i, j, round(L), res))
print(f'{total} pairs in groups; visible camera-to-camera: {len(seen)}')
for s in seen: print('  visible', s)
