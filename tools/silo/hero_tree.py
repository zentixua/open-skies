"""The one tree the show keeps by Silo 18: in full leaf on opening day (S3E09 frame 10), dead and bare in the camera's
view of later years. It stands on the inner slope of the berm in front of the camera, one o'clock to someone at the
ramp's mouth looking out.

Place: the explorethesilo model's (silo3d.js HERO_TREE, "user, 2026-09-19, two frames from the show"), in the site
frame: origin at the portal centre (our ring), +z out along the ramp, +x to the left of someone looking out.

Shape: S3E09 frame 10 (808x335; the tree beside a woman of ~1.7 m = 25 px on the crest just behind it). One slim
trunk leaning to the right, clear for ~1.9 m (28 px) before it forks inside the crown; a round-topped dome of a crown
~7.3 m across (107 px) and ~4.3 m tall (64 px) with a ragged underside, its middle ~1.6 m (24 px) right of the foot;
~6.4 m from foot to top (94 px). The tree stands a little nearer than the woman, so these are upper bounds (+-15 %).

The model's own tree (its seeded limb generator, ported in 5514b09) is the present-day dead tree, taller and wider:
scaled to the frame its limbs became horizontal logs under a flat leaf slab and its flared foot a 2x2 trunk (shader
frame 07c, 12.11). In blocks the frame's crown is a dome of four rows, 5, 7, 7 and 5 across, on a one-block trunk.
"""
from __future__ import annotations

import math

HERO_TREE = (-21.0, 29.0)          # silo3d.js HERO_TREE: site frame lx, lz (m)

# frame 10, in metres (site frame: +lx left of someone looking out; the frame looks out and to the right)
TRUNK_CLEAR = 1.9                  # foot to the fork, where the crown's underside starts
LEAN = 1.6                         # crown middle to the right of the foot
CROWN_W, CROWN_H = 7.3, 4.3        # across the view; foot of the crown to its top
CROWN_D = 6.6                      # along the view: unseen; a round crown a little narrower than its width (est.)
TOP_SHARE = 0.57                   # of the crown's height above its widest row: the dome is round on top, flat below


def _i32(x: int) -> int:
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x >= 1 << 31 else x


def seeded(a: int, b: int, c: int = 0) -> float:
    """Stable 0..1 per integer triple (silo3d.js seeded(), JavaScript int32 arithmetic)."""
    h = _i32(_i32(a * 73856093) ^ _i32(b * 19349663) ^ _i32(c * 83492791) ^ 0x5F3759DF)
    h = _i32((h ^ ((h & 0xFFFFFFFF) >> 15)) * 0x85EBCA6B)
    h = _i32((h ^ ((h & 0xFFFFFFFF) >> 13)) * 0xC2B2AE35)
    return ((h ^ ((h & 0xFFFFFFFF) >> 16)) & 0xFFFFFFFF) / 4294967296


def site_blocks(wood: str = "oak") -> dict:
    """{(lx, y, lz): block} in the site frame about the trunk's base column (cell 0 spans 0..1; y 0 = the first
    block above the ground)."""
    out: dict = {}
    cx, cz = 0.5 - LEAN, 0.5                     # crown middle (cell centres are at +0.5)
    rx, rz = CROWN_W / 2, CROWN_D / 2
    y0 = TRUNK_CLEAR                             # the crown's underside
    ymid = y0 + (1 - TOP_SHARE) * CROWN_H        # its widest row
    up, down = TOP_SHARE * CROWN_H, (1 - TOP_SHARE) * CROWN_H
    for y in range(int(y0), math.ceil(y0 + CROWN_H)):
        dy = y + 0.5 - ymid
        qy = (dy / (up if dy > 0 else down)) ** 2
        for lx in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
            for lz in range(math.floor(cz - rz), math.ceil(cz + rz) + 1):
                q = ((lx + 0.5 - cx) / rx) ** 2 + ((lz + 0.5 - cz) / rz) ** 2 + qy
                if q > 1:
                    continue
                # a ragged outline: the outer shell loses about half its cells (frame 10: leaf clumps with sky between)
                if q > 0.72 and seeded(lx, y, lz) < 0.45:
                    continue
                out[(lx, y, lz)] = f"minecraft:{wood}_leaves[persistent=true]"
    # the trunk: straight for the clear height, then a step to the right into the crown, and limbs up inside it
    fork = int(y0)
    trunk = [(0, y, 0) for y in range(fork)] + [(-1, fork, 0), (-1, fork + 1, 0), (-2, fork + 1, 0), (0, fork + 1, 0),
                                               (-1, fork + 2, 0)]
    for c in trunk:
        out[c] = f"minecraft:{wood}_log[axis=y]"
    return out


def blocks(out: tuple[int, int], wood: str = "oak") -> dict:
    """{(dx, dy, dz): block} about the trunk's base column, for a site whose ramp runs out along `out` (a unit
    (x, z) step: W (-1, 0), N (0, -1), E (1, 0), S (0, 1))."""
    ox, oz = out
    lx_v = (oz, -ox)                            # +x of the site frame: left of someone looking out
    return {(lz * ox + lx * lx_v[0], y, lz * oz + lx * lx_v[1]): st
            for (lx, y, lz), st in site_blocks(wood).items()}


def place(ring: tuple[float, float], out: tuple[int, int]) -> tuple[int, int]:
    """World column of the trunk's base for a ring (portal centre) and its ramp's outward step."""
    lx, lz = HERO_TREE
    ox, oz = out
    return (int(math.floor(ring[0] + lz * ox + lx * oz)), int(math.floor(ring[1] + lz * oz - lx * ox)))


if __name__ == "__main__":
    b = site_blocks()
    logs = sum(1 for v in b.values() if "_log" in v)
    print(f"{len(b)} blocks ({logs} logs); the crown seen from the ramp's mouth looking out (right of the view on "
          "the right):")
    for y in range(max(c[1] for c in b), -1, -1):
        row = "".join("L" if "_log" in b.get((x, y, 0), "") else
                      "#" if any(c[0] == x and c[1] == y for c in b) else " " for x in range(4, -7, -1))
        print(f"  y{y} |{row}|")
