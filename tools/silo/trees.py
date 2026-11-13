"""Trees as blocks, for the offline build (build_offline.py): the live build planted them with /place feature.

Shapes follow vanilla's own: the oak and birch (straight trunk 4-7, two wide leaf layers with ragged corners and two
narrow ones on top) and the fancy oak (a taller trunk under a round crown with a few branch logs). Leaves are
persistent, so the trees keep however the trunk is cut later.
"""
from __future__ import annotations

import random


def _leaves(wood: str) -> str:
    return f"minecraft:{wood}_leaves[distance=1,persistent=true,waterlogged=false]"


def tree_blocks(kind: str, seed: int) -> dict:
    """{(dx, dy, dz): state} about the trunk's foot; dy 0 is the first block above the ground."""
    rnd = random.Random(seed)
    if "dark_oak" in kind:
        return _dark_oak(rnd)
    if "spruce" in kind:
        return _spruce(rnd)
    wood = "birch" if "birch" in kind else "oak"
    log = f"minecraft:{wood}_log[axis=y]"
    leaves = _leaves(wood)
    out: dict = {}
    if "fancy" in kind:
        h = rnd.randint(7, 9)
        cy, r = h - 2, 3.2
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                for dy in range(cy - 3, cy + 3):
                    d = (dx * dx + dz * dz) ** 0.5 + abs(dy - cy) * 0.9
                    if d <= r + rnd.random() * 0.6:
                        out[(dx, dy, dz)] = leaves
        for k in range(rnd.randint(2, 3)):               # branches
            dx, dz = rnd.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            y = h - 4 + k
            out[(dx, y, dz)] = f"minecraft:oak_log[axis={'x' if dx else 'z'}]"
            out[(2 * dx, y + 1, 2 * dz)] = f"minecraft:oak_log[axis={'x' if dx else 'z'}]"
    else:
        h = rnd.randint(5, 7) if wood == "birch" else rnd.randint(4, 6)
        for dy in range(h - 3, h + 1):
            r = 2 if dy < h - 1 else 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    corner = abs(dx) == r and abs(dz) == r
                    if corner and (dy == h or rnd.random() < 0.5):
                        continue
                    out[(dx, dy, dz)] = leaves
    for dy in range(h):
        out[(0, dy, 0)] = log
    return out


def _dark_oak(rnd) -> dict:
    """Vanilla's dark oak: a 2 x 2 trunk 6-8 tall under a broad, flat, dark crown (radius 3-4) - the closed dark
    canopy of the show's groves."""
    leaves = _leaves("dark_oak")
    log = "minecraft:dark_oak_log[axis=y]"
    out: dict = {}
    h = rnd.randint(6, 8)
    for dy in range(h - 3, h + 2):
        r = 4.2 if dy in (h - 1, h) else (3.2 if dy == h - 2 or dy == h - 3 else 2.2)
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = ((dx - 0.5) ** 2 + (dz - 0.5) ** 2) ** 0.5
                if d <= r - rnd.random() * 0.8:
                    out[(dx, dy, dz)] = leaves
    for dy in range(h):
        for dx in (0, 1):
            for dz in (0, 1):
                out[(dx, dy, dz)] = log
    return out


def _spruce(rnd) -> dict:
    """Vanilla's spruce: a tall trunk under a cone of leaf rings, for the outer forest's darker edge."""
    leaves = _leaves("spruce")
    log = "minecraft:spruce_log[axis=y]"
    out: dict = {}
    h = rnd.randint(8, 12)
    for dy in range(2, h + 1):
        k = (h - dy)
        r = 0 if dy == h else (1 if k % 2 else min(3, 1 + k // 3))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r and abs(dz) == r and r > 1:
                    continue
                if dx * dx + dz * dz <= r * r + 1:
                    out[(dx, dy, dz)] = leaves
    out[(0, h + 1, 0)] = leaves
    for dy in range(h):
        out[(0, dy, 0)] = log
    return out
