# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Move each silo of a site_fit layout onto its own dry, gentle ground, away from towns.

The show's complex is a field of silos, not a drawn grid; each silo here may move up to --move blocks from its
hexagonal spot. Silos are placed in order (Silo 1 first); a spot must be dry over the berm disc, outside any town
(chunks with many block entities, plus a margin) and at least --min-gap from silos already placed. Among the spots
that pass, the flattest one closest to the grid wins. The grade (bowl floor) is the mean surface of the berm disc.

  uv run tools/silo/layout_refine.py <site_fit out dir> [--move 72] [--berm 64] [--min-gap 130]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import numpy as np

STEP = 4


def disc_kernel(radius_cells: float) -> np.ndarray:
    r = int(math.ceil(radius_cells))
    ax = np.arange(-r, r + 1)
    X, Z = np.meshgrid(ax, ax, indexing="ij")
    return (X * X + Z * Z <= radius_cells * radius_cells).astype(float)


def conv(a: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Same-size 2D convolution with zero padding (FFT)."""
    kr = k.shape[0] // 2
    sh = (a.shape[0] + k.shape[0], a.shape[1] + k.shape[1])
    f = np.fft.rfft2(a, sh) * np.fft.rfft2(k, sh)
    out = np.fft.irfft2(f, sh)
    return out[kr:kr + a.shape[0], kr:kr + a.shape[1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--move", type=float, default=72)
    ap.add_argument("--berm", type=float, default=64, help="radius of bowl and berm that must be dry")
    ap.add_argument("--min-gap", type=float, default=130)
    ap.add_argument("--town-be", type=int, default=6, help="block entities per chunk that mark a town chunk")
    ap.add_argument("--town-margin", type=float, default=110)
    ap.add_argument("--max-water", type=float, default=0.04)
    a = ap.parse_args()
    t = np.load(os.path.join(a.dir, "terrain.npz"), allow_pickle=True)
    lay = json.load(open(os.path.join(a.dir, "layout.json")))
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
    W, H = surf.shape
    mv = int(a.move // STEP)
    placed = []
    report = []
    for s in lay["silos"]:
        gx0, gz0 = (s["x"] - x0) // STEP, (s["z"] - z0) // STEP
        best = None
        for relax in (1, 2, 4, 8, 1e9):  # last pass: any dry centre; the site generator fills the wet part of the berm
            for dx in range(-mv, mv + 1):
                for dz in range(-mv, mv + 1):
                    if dx * dx + dz * dz > mv * mv:
                        continue
                    gx, gz = gx0 + dx, gz0 + dz
                    if not (0 <= gx < W and 0 <= gz < H) or town[gx, gz] or water[gx, gz]:
                        continue
                    if mean[gx, gz] - 818 < -766:      # the void floor must stay above the deep world's bottom (-768)
                        continue
                    if wet[gx, gz] > a.max_water * relax:
                        continue
                    wx, wz = x0 + gx * STEP + 2, z0 + gz * STEP + 2
                    if any(math.hypot(wx - p["x"], wz - p["z"]) < a.min_gap for p in placed):
                        continue
                    score = sd[gx, gz] + 60 * wet[gx, gz] + 0.03 * STEP * math.hypot(dx, dz)
                    if best is None or score < best[0]:
                        best = (score, gx, gz, wx, wz, relax)
            if best:
                break
        if best is None:
            report.append(f"silo {s['number']}: no spot within {a.move} m")
            placed.append({**s, "grade": None, "ok": False})
            continue
        score, gx, gz, wx, wz, relax = best
        grade = int(round(mean[gx, gz]))
        placed.append({"number": s["number"], "x": wx, "z": wz, "grade": grade, "moved": round(math.hypot(wx - s["x"], wz - s["z"])),
                       "relief_sd": round(float(sd[gx, gz]), 1), "water": round(float(wet[gx, gz]), 3), "ok": True})
        report.append(f"silo {s['number']:2d}: {wx},{wz} grade {grade} moved {placed[-1]['moved']} sd {sd[gx, gz]:.1f} "
                      f"water {wet[gx, gz]:.3f}{' (relaxed)' if relax > 1 else ''}")
    out = {**{k: lay[k] for k in ("spacing", "centre", "rotation_deg")}, "berm": a.berm, "silos": placed}
    json.dump(out, open(os.path.join(a.dir, "layout_final.json"), "w"), indent=1)
    print("\n".join(report))
    grades = [p["grade"] for p in placed if p["ok"]]
    print(f"placed {len(grades)}/50, grade {min(grades)}..{max(grades)}, deepest bottom {min(grades) - 819}")


if __name__ == "__main__":
    main()
