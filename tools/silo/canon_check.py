"""Check a built or planned 1:1 complex against the show: each silo's ring centre, taken back into canon units
(Silo 1 at 0,0, gate-north, flower edge 1) by the layout's own Silo 1, rotation and edge, must lie within TOL metres
of canon/fit.json's ground point, the one whose homographies Hp (founders' plaque) and Hf (2052 frame) match both
images. Also projects the positions into both images for overlays.

  uv run --with numpy canon_check.py LAYOUT.json [--positions world.json] [--tol 10]

--positions: {"n": [x, z], ...} read from the world (bowl centres), checked instead of the layout's own rings;
Silo 1, rotation and edge still come from the layout (the frame the complex was meant to be built in).
Exit status 1 when any silo is off by more than --tol.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIT = json.load(open(os.path.join(HERE, "canon", "fit.json")))
GROUND = {int(k): tuple(v) for k, v in FIT["ground"].items() if k.isdigit()}
HP, HF = np.array(FIT["Hp"]), np.array(FIT["Hf"])


def to_canon(x: float, z: float, one: tuple[float, float], rot_deg: float, edge: float) -> tuple[float, float]:
    """World x, z -> canon units (inverse of Silo 1 + R(rot) * edge * u)."""
    dx, dz = (x - one[0]) / edge, (z - one[1]) / edge
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    return dx * c + dz * s, -dx * s + dz * c


def to_world(u: tuple[float, float], one: tuple[float, float], rot_deg: float, edge: float) -> tuple[float, float]:
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    return one[0] + edge * (u[0] * c - u[1] * s), one[1] + edge * (u[0] * s + u[1] * c)


def proj(H: np.ndarray, u: tuple[float, float]) -> tuple[float, float]:
    q = H @ np.array([u[0], u[1], 1.0])
    return float(q[0] / q[2]), float(q[1] / q[2])


def check(layout: dict, positions: dict[int, tuple[float, float]] | None = None, tol: float = 10.0):
    """[(number, error_m, canon_u, built_u)], worst first; positions default to the layout's rings."""
    one_s = next(s for s in layout["silos"] if s["number"] == 1)
    one = tuple(one_s.get("ring") or (one_s["x"], one_s["z"]))
    rot, edge = layout["rotation_deg"], layout["spacing"]
    if positions is None:
        positions = {s["number"]: tuple(s["ring"]) for s in layout["silos"]}
    out = []
    for n, g in GROUND.items():
        if n not in positions:
            out.append((n, math.inf, g, None))
            continue
        u = to_canon(*positions[n], one, rot, edge)
        out.append((n, edge * math.hypot(u[0] - g[0], u[1] - g[1]), g, u))
    out.sort(key=lambda r: -r[1])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("layout")
    ap.add_argument("--positions")
    ap.add_argument("--tol", type=float, default=10.0)
    a = ap.parse_args()
    L = json.load(open(a.layout))
    pos = None
    if a.positions:
        pos = {int(k): tuple(v) for k, v in json.load(open(a.positions)).items()}
    res = check(L, pos, a.tol)
    bad = [r for r in res if r[1] > a.tol]
    for n, e, g, u in res[:8]:
        print(f"silo {n:2d}: {e:6.1f} m off canon")
    print(f"{len(res) - len(bad)}/{len(res)} silos within {a.tol} m; worst {res[0][1]:.1f} m (silo {res[0][0]})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
