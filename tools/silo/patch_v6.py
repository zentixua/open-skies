"""v6 patch (15.11): the way out as one straight tunnel facing the path, level 1 re-planned round it, written into
an existing complex's region files without rebuilding it: per silo, level 1 and the earth over it (whole shaft
disc, rows from level 1's floor to under the lawn) from a fresh Silo build, and the bowl-floor columns of the old and
new trench, camera shelter and the stub path from a fresh Site build. Server stopped.

The patched chunks are left unlit (isLightOn = 0, see regions.py): start the server and run check/relight.py on it
before LSS/MapSyncer serve them or the world is saved as a golden, or far LODs draw every patched bowl black.

  uv run --with numpy --with scipy --with nbtlib patch_v6.py --layout L --golden G --world W --state S [--number N ..]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_offline as bo  # noqa: E402
from volume import Volume  # noqa: E402

OLD = [(-41, -34, -2, 2), (-32, -27, -3, 3)]          # v5's trench with its curb, v5's shelter with its plinth


def crop(v: Volume, y0: int, y1: int, keep=None) -> Volume:
    """Rows y0..y1 (indices) of v as a new volume; with keep (a 2D [x, z] mask), only those columns."""
    out = Volume((v.origin[0], v.origin[1] + y0, v.origin[2]), (v.size[0], y1 - y0 + 1, v.size[2]))
    out.palette, out.index = v.palette, v.index
    out.ids = v.ids[:, y0:y1 + 1, :].copy()
    if keep is not None:
        out.ids[~np.broadcast_to(keep[:, None, :], out.ids.shape)] = 0
    out.block_entities = {(x, y - y0, z): n for (x, y, z), n in v.block_entities.items() if y0 <= y <= y1
                          and (keep is None or keep[x, z])}
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("layout", "golden", "world", "state"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--number", type=int, nargs="*")
    a = ap.parse_args()
    a.what, a.terrain_for_towns, a.canon_ground = [], None, None
    from silo import CAMERA, EXIT_X, PORTAL_X, TUN_Z, Silo, Spec
    from silo1 import Silo1
    from surface import Site
    from tunnels import TURNS
    from turn import turn_grid, turn_points, turn_volume
    b = bo.Builder(a)
    new = [(PORTAL_X - 1, EXIT_X, TUN_Z[0] - 1, TUN_Z[1] + 1), (CAMERA[0], CAMERA[1] + 1, CAMERA[2] - 1, CAMERA[3] + 1)]
    for s in b.layout["silos"]:
        n, x, z = s["number"], s["x"], s["z"]
        if a.number and n not in a.number:
            continue
        t0 = time.time()
        k = TURNS[s["dir"]]
        grade = b.done[f"silo{n}"]["grade"]
        silo = (Silo1 if n == 1 else Silo)(Spec(number=n), x, grade, z)
        vol = silo.build()
        R = silo.R
        X, Z = silo.X, silo.Z
        m = np.zeros_like(X, bool)
        for x0, x1, z0, z1 in OLD + new:
            m |= (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
        g = silo.yi(0)
        y_lo = silo.level_y(1) - 3
        parts = [crop(vol, y_lo, g - 1, silo.r < R), crop(vol, g, g, m)]
        # the site: the same columns plus the stub over the bowl floor
        RS = Site.radius
        grids = [turn_grid(gg, -k) for gg in b.field.slice(x, z, RS)]
        paths_g = turn_grid(b.grid(b.path_cells, x, z, RS), -k)
        road_g = turn_grid(b.grid(b.road_cells, x, z, RS), -k)
        others = [turn_points([(o["x"], o["z"])], -k, x, z)[0] for o in b.layout["silos"] if o is not s]
        site = Site(silo, *grids, neighbours=others, paths=paths_g, road=road_g, gap_bearing=bo.cut_bearing(s, k),
                    wobble=n != 1)
        sv = site.build()
        SX, SZ = np.meshgrid(np.arange(2 * RS + 1) - RS, np.arange(2 * RS + 1) - RS, indexing="ij")
        sm = np.zeros_like(SX, bool)
        for x0, x1, z0, z1 in OLD + new:
            sm |= (SX >= x0) & (SX <= x1) & (SZ >= z0) & (SZ <= z1)
        sm |= paths_g & (np.hypot(SX, SZ) < Site.floor_r - 1)
        parts.append(crop(sv, 0, sv.size[1] - 1, sm))
        vols = [turn_volume(p, k, x, z) for p in parts]
        b.apply(vols, f"silo {n} v6 ({s['dir']}, built {time.time() - t0:.0f}s)")
        bo.log(f"silo {n}: done")
    bo.log("patched chunks are unlit: start the server and run check/relight.py before LSS/MapSyncer or a golden save")


if __name__ == "__main__":
    main()
