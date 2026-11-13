"""Which way each silo's tunnel runs, when the craters (the rings seen from above) stand where the show has them.

The rings in the show are the craters around each portal (explorethesilo model: crater about the portal, shaft 115.5 m
back along the tunnel). At the show's ring spacing (156 m) one shared bearing puts some tunnels into the next shaft,
so each silo picks one of four bearings (the tunnel stays block-aligned): its shaft is the ring centre minus the
reach along that bearing. Chosen so that every shaft stays clear of every other tunnel and crater floor, and shafts
stay apart.
"""
from __future__ import annotations

import math

REACH = 46 + 69.5            # shaft axis to portal centre (surface.Site: shell r 46 + portal_s 69.5)
DIRS = {"W": (-1, 0), "N": (0, -1), "E": (1, 0), "S": (0, 1)}
TURNS = {"W": 0, "N": 1, "E": 2, "S": 3}       # quarter turns clockwise (seen from above, north up) from W
SHAFT_R, TUNNEL_HALF, FLOOR_R = 46, 4, 30


def seg_dist(px, pz, sx, sz, d):
    """Point to the tunnel line of a silo with shaft sx, sz and bearing d."""
    vx, vz = px - sx, pz - sz
    t = min(max(vx * d[0] + vz * d[1], 0.0), REACH)
    return math.hypot(vx - t * d[0], vz - t * d[1])


def seg_seg(a0, a1, b0, b1):
    def pt(p, q0, q1):
        dx, dz = q1[0] - q0[0], q1[1] - q0[1]
        L = dx * dx + dz * dz
        t = 0 if L == 0 else min(max(((p[0] - q0[0]) * dx + (p[1] - q0[1]) * dz) / L, 0), 1)
        return math.hypot(p[0] - q0[0] - t * dx, p[1] - q0[1] - t * dz)
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    if (cross(a0, a1, b0) * cross(a0, a1, b1) < 0) and (cross(b0, b1, a0) * cross(b0, b1, a1) < 0):
        return 0.0
    return min(pt(a0, b0, b1), pt(a1, b0, b1), pt(b0, a0, a1), pt(b1, a0, a1))


def margin(rings, dirs, i, j):
    """Clearance between silos i and j in metres beyond what they need (negative: they collide). A shaft may lie under
    another silo's crater (2 m lower ground over its 4 m cover); it may not meet another tunnel, ramp or portal."""
    di, dj = DIRS[dirs[i]], DIRS[dirs[j]]
    si = (rings[i][0] - REACH * di[0], rings[i][1] - REACH * di[1])
    sj = (rings[j][0] - REACH * dj[0], rings[j][1] - REACH * dj[1])
    need_t = SHAFT_R + TUNNEL_HALF + 6
    return min(seg_dist(*si, *sj, dj) - need_t, seg_dist(*sj, *si, di) - need_t,
               math.dist(si, sj) - 2 * SHAFT_R - 8,
               seg_seg(si, rings[i], sj, rings[j]) - 2 * TUNNEL_HALF - 6)


def assign(rings: list[tuple[float, float]], fixed: dict[int, str] | None = None, rounds: int = 200, seed: int = 0):
    """Bearings (one of W N E S per ring) maximising the smallest clearance, then the sum of the shortfalls;
    rings[0] is Silo 1. Returns (dirs, worst)."""
    import random
    rnd = random.Random(seed)
    fixed = fixed or {}
    n = len(rings)
    near = [[j for j in range(n) if j != i and math.dist(rings[i], rings[j]) < 2 * REACH + 2 * SHAFT_R + 40]
            for i in range(n)]

    def local(dirs, i):
        ms = [margin(rings, dirs, i, j) for j in near[i]] or [1e9]
        return (min(ms), sum(min(m, 0) for m in ms))

    best_all = None
    for restart in range(30):
        dirs = [fixed.get(i, rnd.choice("WNES") if restart else "W") for i in range(n)]
        for _ in range(rounds):
            changed = False
            for i in rnd.sample(range(n), n):
                if i in fixed:
                    continue
                cur = dirs[i]
                opts = []
                for d in DIRS:
                    dirs[i] = d
                    opts.append((local(dirs, i), d != cur, d))
                opts.sort(key=lambda o: (o[0], not o[1]), reverse=True)
                dirs[i] = opts[0][2] if opts[0][0] > local(dirs[:i] + [cur] + dirs[i + 1:], i) else cur
                changed |= dirs[i] != cur
            if not changed:
                break
        worst = min(local(dirs, i)[0] for i in range(n))
        if best_all is None or worst > best_all[1]:
            best_all = (dirs[:], worst)
        if worst >= 0:
            break
    return best_all


def shafts(rings, dirs):
    return [(r[0] - REACH * DIRS[d][0], r[1] - REACH * DIRS[d][1]) for r, d in zip(rings, dirs)]
