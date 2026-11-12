"""The one tree the show keeps by Silo 18: in full leaf on opening day (S3E09 frame 10), dead and bare in the camera's
view of later years. It stands on the inner slope of the berm in front of the camera, one o'clock to someone at the
ramp's mouth looking out.

Shape and place are the explorethesilo model's (silo3d.js, THE TREE / HERO_TREE, "user, 2026-09-19, two frames from
the show"): a short flared trunk forking at 2.6 m into three wide leaning limbs that fork four times more, a leaf
clump at every twig end and fourteen filling the spread between them (buildCanopies, the living tree). Its seeded
generator is ported as is, so the limbs are the model's own; the model's world axes are turned into the site frame by
its SITE_PHI. Site frame: origin at the portal centre (our ring), +z out along the ramp, +x to the left of someone
looking out. Here: blocks relative to the trunk's base column, y 0 = the first block above the ground.

Checked against S3E09 frame 10 (the living tree on the berm behind the stair head, against a person on the crest):
about 7 m tall, a round crown about 7 m across on one leaning trunk.
"""
from __future__ import annotations

import math

HERO_TREE = (-21.0, 29.0)          # silo3d.js HERO_TREE: site frame lx, lz (m)


def _i32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x >= 1 << 31 else x


def seeded(a: int, b: int, c: int = 0) -> float:
    """silo3d.js seeded(): JavaScript int32 arithmetic."""
    h = _i32(_i32(a * 73856093) ^ _i32(b * 19349663) ^ _i32(c * 83492791) ^ 0x5F3759DF)
    h = _i32((h ^ ((h & 0xFFFFFFFF) >> 15)) * 0x85EBCA6B)
    h = _i32((h ^ ((h & 0xFFFFFFFF) >> 13)) * 0xC2B2AE35)
    return ((h ^ ((h & 0xFFFFFFFF) >> 16)) & 0xFFFFFFFF) / 4294967296


def _site_phi() -> float:
    """silo3d.js SITE_PHI = rampHeading(PORTAL_S), desktop build (18 bays)."""
    bay_arc = 2 * math.pi / 18
    airlock = (round(213 * math.pi / 180 / bay_arc - 0.5) + 0.5) * bay_arc
    kappa, let_in, added = math.radians(8) / 50, 26, 60 - 30
    ramp_len, portal_l = 20 + 60 + 0, 6.5
    s = ramp_len - portal_l
    arc = s if s <= let_in else let_in if s <= let_in + added else s - added
    return airlock + kappa * arc


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _add(a, b, k=1.0):
    return tuple(x + k * y for x, y in zip(a, b))


def model_tree():
    """The model's tree in its own world axes, about its base point: (segments [(a, b, r0, r1, depth)], leaf
    clumps [(centre, radius)]); depth 5 is the trunk, 4 the three main limbs, 0 the twigs."""
    segs, tips = [], []
    n = 0

    def bend(d, amt, k):
        j = ((seeded(k, 1, 931) - 0.5) * amt, (seeded(k, 2, 931) - 0.3) * 0.6 * amt, (seeded(k, 3, 931) - 0.5) * amt)
        return _norm(_add(d, j))

    def limb(frm, d, ln, r, depth):
        nonlocal n
        n += 1
        k = n
        mid = _add(frm, d, ln * 0.5)
        d2 = bend(d, 0.35, k)
        end = _add(mid, d2, ln * 0.5)
        rm, re = r * 0.8, r * 0.6
        segs.append((frm, mid, r, rm, depth))
        segs.append((mid, end, rm, re, depth))
        if depth == 0:
            tips.append(end)
            return
        forks = 3 if depth >= 3 else 2
        for f in range(forks):
            a = f * 2.3 + k * 1.7
            sp = 0.85 + 0.45 * seeded(k, f, 932)
            nd = _norm(_add(_add(d2, (math.cos(a) * sp, 0.0, math.sin(a) * sp)), (0.0, 0.18 + 0.2 * seeded(k, f, 934), 0.0)))
            limb(end, nd, ln * (0.55 + 0.3 * seeded(k, f, 933)), re * (0.8 if f == 0 else 0.62), depth - 1)
        if depth == 1:
            tips.append(end)

    at = (0.0, -0.25, 0.0)
    low, top = _add(at, (0.15, 1.3, 0.05)), _add(at, (0.45, 2.6, 0.15))
    segs.append((_add(at, (0, -0.2, 0)), low, 0.7, 0.5, 5))
    segs.append((low, top, 0.5, 0.42, 5))
    for dx, dy, dz, ln in ((1.1, 0.9, 0.25, 3.6), (-0.9, 1.0, 0.6, 3.1), (-0.25, 1.2, -1.0, 2.8)):
        limb(top, _norm((dx, dy, dz)), ln, 0.34, 4)
    clumps = []
    for j, tp in enumerate(tips):
        clumps.append((_add(tp, (0, 0.2, 0)), 1.05 + 0.5 * seeded(j, 1, 971)))
    c = tuple(sum(t[i] for t in tips) / len(tips) for i in range(3))
    for j in range(14):
        a, d = seeded(j, 3, 971) * 2 * math.pi, 1.5 + 3 * seeded(j, 4, 971)
        clumps.append(((c[0] + math.cos(a) * d, c[1] + (seeded(j, 5, 971) - 0.3) * 2, c[2] + math.sin(a) * d), 1.4))
    return segs, clumps


# S3E09 frame 10 (808x335; the tree beside a woman of ~1.7 m = 25 px on the crest just behind it): the living tree is
# ~6.4 m from its foot to the crown top (94 px), the crown ~7.3 m across the view (107 px), and the crown's middle
# stands ~1.5 m to the right of the foot (22 px): the trunk leans that way. The model's tree (present-day, dead) is
# taller and wider; the same limbs are scaled to the frame's height and leaned to its offset. The tree stands a little
# nearer than the woman, so these are upper bounds (+-15 %).
FRAME_HEIGHT, FRAME_LEAN = 6.4, 1.5
# In blocks the scaled twigs (under 0.2 m) vanish and the scaled clumps leave the crown a flat sieve: limbs are kept as
# logs down to the second fork, and every clump grows (taller than wide) into the frame's dense dome. With the limbs
# scaled to 5.8 m the built tree matches the frame: 6 blocks tall, crown rows 2-5 (the frame: crown from ~2.3 m),
# 8 across the camera's view and 9 deep, crown centre 1.3-1.5 m right of the foot.
MODEL_HEIGHT, LOG_DEPTH, LEAF_GROW = 5.8, 3, 1.2


def _site_tree():
    """The tree in the site frame (lx left, y up, lz out), fitted to frame 10: (segments, clumps)."""
    phi = _site_phi()
    sn, cs = math.sin(phi), math.cos(phi)

    def to_site(p):
        return (p[0] * sn - p[2] * cs, p[1], p[0] * cs + p[2] * sn)   # silo3d.js siteX/siteZ, about the base

    segs, clumps = model_tree()
    top = max(max(c[0][1] + 0.9 * c[1] for c in clumps), max(max(a[1], b[1]) for a, b, *_ in segs))
    k = MODEL_HEIGHT / top
    segs = [(tuple(k * v for v in to_site(a)), tuple(k * v for v in to_site(b)), k * r0, k * r1, dp)
            for a, b, r0, r1, dp in segs]
    clumps = [(tuple(k * v for v in to_site(c)), k * r) for c, r in clumps]
    mid_y = sum(c[0][1] for c in clumps) / len(clumps)
    right = -sum(c[0][0] for c in clumps) / len(clumps)             # +x is left of someone looking out
    shear = (FRAME_LEAN - right) / mid_y                            # lean to the right, growing with height

    def lean(p):
        return (p[0] - shear * max(0.0, p[1]), p[1], p[2])

    return [(lean(a), lean(b), r0, r1, dp) for a, b, r0, r1, dp in segs], [(lean(c), r) for c, r in clumps]


def blocks(out: tuple[int, int], wood: str = "oak"):
    """{(dx, dy, dz): block} about the trunk's base column, for a site whose ramp runs out along `out` (a unit
    (x, z) step: W (-1, 0), N (0, -1), E (1, 0), S (0, 1))."""
    ox, oz = out
    lx_v = (oz, -ox)                            # +x of the site frame: left of someone looking out

    def to_world(p):
        return (p[2] * ox + p[0] * lx_v[0], p[1], p[2] * oz + p[0] * lx_v[1])

    segs, clumps = _site_tree()
    logs: dict = {}
    for a, b, r0, r1, dp in segs:
        if dp < LOG_DEPTH:                     # twigs: inside the crown, finer than a block
            continue
        a, b = to_world(a), to_world(b)
        d = tuple(y - x for x, y in zip(a, b))
        ln = math.sqrt(sum(c * c for c in d))
        axis = "xyz"[max(range(3), key=lambda i: abs(d[i]))]
        steps = max(1, int(ln * 4))
        for i in range(steps + 1):
            t = i / steps
            p = _add(a, d, t)
            r = r0 + (r1 - r0) * t
            reach = max(0.0, r - 0.3)           # thin limbs: one block; the flared foot: its disc
            span = int(math.ceil(reach))
            for ddx in range(-span, span + 1):
                for ddz in range(-span, span + 1):
                    for ddy in range(-span, span + 1):
                        if ddx * ddx + ddy * ddy + ddz * ddz <= reach * reach + 1e-9:
                            cell = (math.floor(p[0] + ddx), math.floor(p[1] + ddy), math.floor(p[2] + ddz))
                            logs.setdefault(cell, axis)
    leaves = set()
    for cpos, r in clumps:
        cx, cy, cz = to_world(cpos)
        rx, ry = LEAF_GROW * 1.25 * r, LEAF_GROW * 1.6 * r   # the model's cards (1.6 r squares over +-r/2), grown
        for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
            for z in range(math.floor(cz - rx), math.ceil(cz + rx) + 1):
                for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
                    q = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 + ((z + 0.5 - cz) / rx) ** 2
                    if q <= 1:
                        leaves.add((x, y, z))
    out_blocks = {cell: f"minecraft:{wood}_leaves[persistent=true]" for cell in leaves}
    for cell, axis in logs.items():
        if cell[1] >= -1:
            out_blocks[cell] = f"minecraft:{wood}_log[axis={axis}]"
    return out_blocks


def place(ring: tuple[float, float], out: tuple[int, int]) -> tuple[int, int]:
    """World column of the trunk's base for a ring (portal centre) and its ramp's outward step."""
    lx, lz = HERO_TREE
    ox, oz = out
    return (int(math.floor(ring[0] + lz * ox + lx * oz)), int(math.floor(ring[1] + lz * oz - lx * ox)))


if __name__ == "__main__":
    import sys
    b = blocks((-1, 0))
    xs = [c[0] for c in b]; ys = [c[1] for c in b]; zs = [c[2] for c in b]
    logs = sum(1 for v in b.values() if "_log" in v)
    print(f"{len(b)} blocks ({logs} logs), x {min(xs)}..{max(xs)}, y {min(ys)}..{max(ys)}, z {min(zs)}..{max(zs)}")
    if len(sys.argv) > 1:
        from PIL import Image
        S = 16
        for name, (i, j, flip) in {"front": (2, 1, False), "side": (0, 1, False), "top": (0, 2, False)}.items():
            u0, u1 = min(c[i] for c in b), max(c[i] for c in b)
            v0, v1 = min(c[j] for c in b), max(c[j] for c in b)
            img = Image.new("RGB", ((u1 - u0 + 1) * S, (v1 - v0 + 1) * S), (200, 220, 235))
            px = img.load()
            order = sorted(b.items(), key=lambda kv: kv[0][3 - i - j] if name != "top" else kv[0][1])
            for c, st in order:
                col = (110, 80, 50) if "_log" in st else (70, 130, 50)
                u = c[i] - u0
                v = (v1 - c[j]) if name != "top" else (c[j] - v0)
                for a in range(S):
                    for bb in range(S):
                        px[u * S + a, v * S + bb] = col
            img.save(f"{sys.argv[1]}-{name}.png")
