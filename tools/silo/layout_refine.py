# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Place the 50 silos on their own dry, gentle ground, away from towns, as one compact field.

The show's complex is a field of silos, not a drawn grid. Every 4-block cell of the world is rated once: the berm
disc (--berm) must be dry, its relief gentle, and the cell outside any town (chunks with many block entities, plus
a margin). Then, for many candidate centres, silos are packed greedily: the best-rated cells nearest the centre
first, each at least --min-gap from the others; Silo 1 takes the cell nearest the centre. The centre whose 50
silos are flattest and closest together wins. The grade (bowl floor) is the mean surface of the berm disc.

  uv run tools/silo/layout_refine.py <site_fit out dir (terrain2.npz)> [--berm 64] [--min-gap 140]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

STEP = 4
DEPTH = 812          # grade to the bottom of the silo volume (silo.py with cover 4); the world bottom is -768


def disc_kernel(radius_cells: float) -> np.ndarray:
    r = int(math.ceil(radius_cells))
    ax = np.arange(-r, r + 1)
    X, Z = np.meshgrid(ax, ax, indexing="ij")
    return (X * X + Z * Z <= radius_cells * radius_cells).astype(float)


def conv(a: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Same-size 2D convolution with zero padding (FFT)."""
    kr = k.shape[0] // 2
    sh = (a.shape[0] + k.shape[0], a.shape[1] + k.shape[1])
    out = np.fft.irfft2(np.fft.rfft2(a, sh) * np.fft.rfft2(k, sh), sh)
    return out[kr:kr + a.shape[0], kr:kr + a.shape[1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--count", type=int, default=50)
    ap.add_argument("--berm", type=float, default=64, help="radius of bowl and berm that must be dry")
    ap.add_argument("--min-gap", type=float, default=140)
    ap.add_argument("--max-sd", type=float, default=8, help="largest relief (standard deviation) over the berm disc")
    ap.add_argument("--max-water", type=float, default=0.03)
    ap.add_argument("--town-be", type=int, default=6, help="block entities per chunk that mark a town chunk")
    ap.add_argument("--town-margin", type=float, default=110)
    ap.add_argument("--shaft", type=float, default=70, help="radius kept clear of buried structures (silo 52 + chunk)")
    ap.add_argument("--per-sd", type=float, default=60, help="metres of distance from the centre worth one unit of relief sd")
    ap.add_argument("--centre-step", type=int, default=128)
    a = ap.parse_args()
    t = np.load(os.path.join(a.dir, "terrain2.npz"), allow_pickle=True)
    x0, z0, surf, floor, bes = int(t["x0"]), int(t["z0"]), t["surf"], t["floor"], t["bes"]
    known = surf > -9999
    water = ((surf > floor) | ~known).astype(float)
    h = np.where(known, surf, 0).astype(float)
    k = disc_kernel(a.berm / STEP)
    n = k.sum()
    wet = conv(water, k) / n
    mean = conv(h, k) / n
    sd = np.sqrt(np.maximum(conv(h * h, k) / n - mean * mean, 0))
    town_chunks = (bes >= a.town_be).astype(float)
    town = np.repeat(np.repeat(town_chunks, 4, 0), 4, 1)[:surf.shape[0], :surf.shape[1]]
    town = conv(town, disc_kernel(a.town_margin / STEP)) > 0.5
    # buried structures (trial chambers, dungeons, strongholds) stay whole: no shaft through them
    buried = (t["bes_under"] >= 3).astype(float)
    buried = np.repeat(np.repeat(buried, 4, 0), 4, 1)[:surf.shape[0], :surf.shape[1]]
    town |= conv(buried, disc_kernel(a.shaft / STEP)) > 0.5
    W, H = surf.shape
    edge = int(a.berm // STEP) + 2
    ok = (wet <= a.max_water) & (water == 0) & ~town & (sd <= a.max_sd) & (mean - DEPTH >= -766)
    ok[:edge] = ok[-edge:] = False
    ok[:, :edge] = ok[:, -edge:] = False
    # candidate cells on an 8-block grid
    gx, gz = np.nonzero(ok[::2, ::2])
    gx, gz = gx * 2, gz * 2
    wx = x0 + gx * STEP + 2
    wz = z0 + gz * STEP + 2
    rating = sd[gx, gz] + 40 * wet[gx, gz]
    print(f"{len(gx)} good cells (of {W * H // 4}); towns cover {town.mean():.0%} of the map")
    gap2 = a.min_gap ** 2

    def pack(cx, cz):
        d = np.hypot(wx - cx, wz - cz)
        idx = np.nonzero(d < 1400)[0]
        if len(idx) < a.count:
            return None
        order = idx[np.argsort(rating[idx] + d[idx] / a.per_sd)]
        px, pz, chosen = np.empty(a.count), np.empty(a.count), []
        for i in order:
            x, z = wx[i], wz[i]
            m = len(chosen)
            if m and np.min((px[:m] - x) ** 2 + (pz[:m] - z) ** 2) < gap2:
                continue
            px[m], pz[m] = x, z
            chosen.append(i)
            if len(chosen) == a.count:
                chosen = np.array(chosen)
                return float((rating[chosen] + d[chosen] / a.per_sd).sum()), cx, cz, chosen
        return None

    def search(xs, zs, best):
        for cx in xs:
            for cz in zs:
                r = pack(cx, cz)
                if r and (best is None or r[0] < best[0]):
                    best = r
        return best

    coarse = a.centre_step * 2
    best = search(range(x0 + 600, x0 + W * STEP - 600, coarse), range(z0 + 600, z0 + H * STEP - 600, coarse), None)
    if best is not None:
        _, bx, bz, _ = best
        fine = a.centre_step // 2
        best = search(range(bx - coarse, bx + coarse + 1, fine), range(bz - coarse, bz + coarse + 1, fine), best)
    if best is None:
        raise SystemExit("no centre fits the field; relax --max-sd, --max-water or --min-gap")
    cost, cx, cz, chosen = best
    d = np.hypot(wx[chosen] - cx, wz[chosen] - cz)
    chosen = chosen[np.argsort(d)]          # Silo 1 nearest the centre, numbers grow outward
    silos = []
    for num, i in enumerate(chosen, 1):
        silos.append({"number": num, "x": int(wx[i]), "z": int(wz[i]), "grade": int(round(mean[gx[i], gz[i]])),
                      "relief_sd": round(float(sd[gx[i], gz[i]]), 1), "water": round(float(wet[gx[i], gz[i]]), 3),
                      "from_centre": round(float(np.hypot(wx[i] - cx, wz[i] - cz)))})
    out = {"centre": [cx, cz], "berm": a.berm, "min_gap": a.min_gap, "cost": round(cost, 1), "silos": silos}
    json.dump(out, open(os.path.join(a.dir, "layout_final.json"), "w"), indent=1)
    for s in silos:
        print(f"silo {s['number']:2d}: {s['x']},{s['z']} grade {s['grade']} sd {s['relief_sd']} water {s['water']} "
              f"from centre {s['from_centre']}")
    g = [s["grade"] for s in silos]
    print(f"centre {cx},{cz}, field radius {max(s['from_centre'] for s in silos)} m, grade {min(g)}..{max(g)}, "
          f"mean sd {np.mean([s['relief_sd'] for s in silos]):.1f}")


if __name__ == "__main__":
    main()
