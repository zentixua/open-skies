# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Find where the 50-silo complex fits a world best (run against a stopped copy or a golden; reads region files only).

Pass 1 (cached in <out>/terrain3.npz): for every chunk, surface and ocean-floor heights on a 4-block grid, block entity
count, and the biome around y 64. Pass 2: a hexagonal layout of 50 silos (Silo 1 in the centre, rings outward) is
tried at many centres and rotations. The plain (field.py) fills water and evens the ground, so water and relief
only cost; surface builds near a silo and buried structures under a shaft rule a placement out.

  uv run tools/silo/site_fit.py <world dir> <out dir> [--spacing 180] [--min-y -64]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import struct
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np

STEP = 4  # grid step in blocks
BE_WEIGHT = {"bee_nest": 0, "beehive": 1, "sculk_sensor": 0, "calibrated_sculk_sensor": 0, "sculk_catalyst": 0,
             "sculk_shrieker": 0, "brushable_block": 0, "trial_spawner": 5, "vault": 5, "command_block": 5,
             "structure_block": 5, "jigsaw": 5}


# --- minimal NBT reader (only what we need) --------------------------------------------------------------------------

def _read(f, t):
    if t == 1: return f.read(1)[0]
    if t == 2: return struct.unpack(">h", f.read(2))[0]
    if t == 3: return struct.unpack(">i", f.read(4))[0]
    if t == 4: return struct.unpack(">q", f.read(8))[0]
    if t == 5: return struct.unpack(">f", f.read(4))[0]
    if t == 6: return struct.unpack(">d", f.read(8))[0]
    if t == 7: n = struct.unpack(">i", f.read(4))[0]; return f.read(n)
    if t == 8: n = struct.unpack(">H", f.read(2))[0]; return f.read(n).decode("utf-8", "replace")
    if t == 9:
        et = f.read(1)[0]; n = struct.unpack(">i", f.read(4))[0]
        return [_read(f, et) for _ in range(n)]
    if t == 10:
        d = {}
        while True:
            tt = f.read(1)[0]
            if tt == 0: return d
            n = struct.unpack(">H", f.read(2))[0]; k = f.read(n).decode("utf-8", "replace"); d[k] = _read(f, tt)
    if t == 11: n = struct.unpack(">i", f.read(4))[0]; return np.frombuffer(f.read(4 * n), ">i4")
    if t == 12: n = struct.unpack(">i", f.read(4))[0]; return np.frombuffer(f.read(8 * n), ">i8")
    raise ValueError(t)


def nbt(b: bytes):
    f = io.BytesIO(b); t = f.read(1)[0]; n = struct.unpack(">H", f.read(2))[0]; f.read(n)
    return _read(f, t)


def heightmap(longs, height: int) -> np.ndarray:
    bits = max(1, math.ceil(math.log2(height + 1)))
    per = 64 // bits
    v = longs.astype(np.uint64)
    shifts = np.arange(per, dtype=np.uint64) * np.uint64(bits)
    vals = (v[:, None] >> shifts[None, :]) & np.uint64((1 << bits) - 1)
    return vals.reshape(-1)[:256].astype(np.int32).reshape(16, 16)  # [z][x]


def scan_region(args):
    path, min_y, height = args
    rx, rz = map(int, os.path.basename(path).split(".")[1:3])
    out = []
    b = open(path, "rb").read()
    if len(b) < 8192:
        return out
    for i in range(1024):
        off = int.from_bytes(b[i * 4:i * 4 + 3], "big")
        if not off:
            continue
        o = off * 4096; ln = int.from_bytes(b[o:o + 4], "big")
        if b[o + 4] != 2:
            continue
        try:
            c = nbt(zlib.decompress(b[o + 5:o + 4 + ln]))
        except Exception:
            continue
        if not str(c.get("Status", "")).endswith("full"):
            continue
        hm = c.get("Heightmaps", {})
        if "WORLD_SURFACE" not in hm or "OCEAN_FLOOR" not in hm:
            continue
        ws = heightmap(hm["WORLD_SURFACE"], height) + min_y - 1
        of = heightmap(hm["OCEAN_FLOOR"], height) + min_y - 1
        biome = ""
        for s in c.get("sections", []):
            if s.get("Y") == 4 and "biomes" in s:
                biome = s["biomes"]["palette"][0]
        cx, cz = rx * 32 + (i & 31), rz * 32 + (i >> 5)
        # block entities of builds on the surface (towns) and of buried structures (trial chambers, ancient cities,
        # dungeons, the map's own command machinery), weighted; natural ones (bee nests, deep dark sculk, suspicious
        # sand and gravel) are neither
        ground = int(of.min())
        top = top_under = 0
        for be in c.get("block_entities", []):
            w = BE_WEIGHT.get(str(be.get("id", "")).removeprefix("minecraft:"), 1)
            if not w:
                continue
            if be.get("y", -9999) >= ground - 6:
                top += w
            else:
                top_under += w
        out.append((cx, cz, ws[::STEP, ::STEP].copy(), of[::STEP, ::STEP].copy(), (top, top_under), biome))
    return out


def build_terrain(world: str, out: str, min_y: int, height: int):
    cache = os.path.join(out, "terrain3.npz")      # 3: surface and buried block entities, weighted
    if os.path.exists(cache):
        d = np.load(cache, allow_pickle=True)
        return {k: d[k] for k in d.files}
    reg = os.path.join(world, "region")
    files = [os.path.join(reg, f) for f in os.listdir(reg) if f.endswith(".mca")]
    rows = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        for res in ex.map(scan_region, [(f, min_y, height) for f in files], chunksize=2):
            rows.extend(res)
    cxs = np.array([r[0] for r in rows]); czs = np.array([r[1] for r in rows])
    x0, z0 = cxs.min() * 16, czs.min() * 16
    nx, nz = (cxs.max() - cxs.min() + 1) * 16 // STEP, (czs.max() - czs.min() + 1) * 16 // STEP
    surf = np.full((nx, nz), -9999, np.int32); floor = np.full((nx, nz), -9999, np.int32)
    bes = np.zeros((nx // 4, nz // 4), np.int32); under = np.zeros((nx // 4, nz // 4), np.int32)
    biomes = np.empty((nx // 4, nz // 4), dtype=object); biomes[:] = ""
    for cx, cz, ws, of, nbe, biome in rows:
        gx, gz = (cx * 16 - x0) // STEP, (cz * 16 - z0) // STEP
        surf[gx:gx + 4, gz:gz + 4] = ws.T
        floor[gx:gx + 4, gz:gz + 4] = of.T
        bes[gx // 4, gz // 4], under[gx // 4, gz // 4] = nbe
        biomes[gx // 4, gz // 4] = biome
    d = {"x0": np.array(x0), "z0": np.array(z0), "surf": surf, "floor": floor, "bes": bes, "bes_under": under, "biomes": biomes}
    np.savez_compressed(cache, **d)
    return d


def hex_layout(n: int, spacing: float, rot: float) -> list[tuple[float, float]]:
    pts = []
    for q in range(-8, 9):
        for r in range(-8, 9):
            x = spacing * (q + r / 2); z = spacing * (r * math.sqrt(3) / 2)
            pts.append((x, z))
    pts.sort(key=lambda p: (round(math.hypot(*p), 3), math.atan2(p[1], p[0])))
    pts = pts[:n]
    c, s = math.cos(rot), math.sin(rot)
    return [(x * c - z * s, x * s + z * c) for x, z in pts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world"); ap.add_argument("out")
    ap.add_argument("--spacing", type=float, default=200,
                    help="silo spacing; the explorethesilo model's neighbouring craters lie 153-226 m from their nearest")
    ap.add_argument("--centre", help="x,z: keep Silo 1 here (already built) and search rotations only")
    ap.add_argument("--rots", default="0,58", help="rotation range in degrees; every portal must stay clear of the other "
                    "shafts and tunnels, which at spacing 200 holds best near 30 (112 m and more)")
    ap.add_argument("--min-y", type=int, default=-64); ap.add_argument("--height", type=int, default=384)
    ap.add_argument("--berm", type=float, default=70, help="radius that must be dry and gentle")
    ap.add_argument("--clear", type=float, default=200, help="radius free of surface builds (the plain reaches this far)")
    ap.add_argument("--max-builds", type=int, default=12, help="weighted surface block entities allowed in that radius")
    ap.add_argument("--shaft", type=float, default=64, help="radius free of buried structures (trial chambers, cities)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t = build_terrain(a.world, a.out, a.min_y, a.height)
    x0, z0, surf, floor, bes = int(t["x0"]), int(t["z0"]), t["surf"], t["floor"], t["bes"]
    buried = (t["bes_under"] >= 5).astype(float)
    known = surf > -9999
    water = (surf > floor) | ~known
    print(f"terrain grid {surf.shape} origin {x0},{z0}", file=sys.stderr)
    # disc offsets
    def disc(radius, step):
        rr = int(radius // step)
        return [(i * step, j * step) for i in range(-rr, rr + 1) for j in range(-rr, rr + 1) if (i * i + j * j) * step * step <= radius * radius]
    berm = disc(a.berm, STEP * 2)
    clear = disc(a.clear, 16)
    # Per-cell disc statistics, so each silo is a lookup (the same sums as sampling the discs silo by silo).
    W, H = surf.shape
    bk = 2 * int(a.berm // (STEP * 2))  # berm disc offsets in 4-block cells (every second cell)
    kb = np.zeros((2 * bk + 1, 2 * bk + 1))
    for dx, dz in berm:
        kb[dx // STEP + bk, dz // STEP + bk] = 1
    ck = int(a.clear // 16)
    kc = np.zeros((2 * ck + 1, 2 * ck + 1))
    for dx, dz in clear:
        kc[dx // 16 + ck, dz // 16 + ck] = 1

    def conv(img, k):  # sum of img over kernel k centred on every cell (zero outside), via FFT
        r = k.shape[0] // 2
        sh = (img.shape[0] + k.shape[0], img.shape[1] + k.shape[1])
        f = np.fft.irfft2(np.fft.rfft2(img, sh) * np.fft.rfft2(k[::-1, ::-1], sh), sh)
        return f[r:r + img.shape[0], r:r + img.shape[1]]

    n = kb.sum()
    hf = surf.astype(float)
    wmap = conv(water.astype(float), kb) / n
    m1 = conv(hf, kb) / n
    sdmap = np.sqrt(np.maximum(conv(hf * hf, kb) / n - m1 * m1, 0))
    bep = np.pad(bes.astype(float), ck, mode="edge")  # edge cells repeat, like the old clip
    bemap = np.rint(conv(bep, kc)[ck:-ck, ck:-ck]).astype(np.int64)
    sk = int(math.ceil(a.shaft / 16))
    ax_ = np.arange(-sk, sk + 1)
    ks = ((ax_[:, None] ** 2 + ax_[None, :] ** 2) * 256 <= (a.shaft + 8) ** 2).astype(float)
    bup = np.pad(buried, sk, mode="constant")
    burmap = conv(bup, ks)[sk:-sk, sk:-sk] > 0.5
    results = []
    r0, r1 = (int(v) for v in a.rots.split(","))
    for rot_deg in range(r0, r1 + 1, 2 if a.centre else 10):
        layout = np.array(hex_layout(50, a.spacing, math.radians(rot_deg)))
        if a.centre:
            cxs, czs = (np.array([int(v)]) for v in a.centre.split(","))
        else:
            cxs = np.arange(x0 + 1000, x0 + W * STEP - 1000, 64)
            czs = np.arange(z0 + 1000, z0 + H * STEP - 1000, 64)
        CX, CZ = np.meshgrid(cxs, czs, indexing="ij")
        pen = np.zeros(CX.shape); wet = np.zeros(CX.shape); sdt = np.zeros(CX.shape)
        bet = np.zeros(CX.shape, np.int64); ok = np.ones(CX.shape, bool)
        for px, pz in layout:
            sx, sz = CX + px, CZ + pz
            gx = np.floor((sx - x0) / STEP).astype(np.int64); gz = np.floor((sz - z0) / STEP).astype(np.int64)
            ok &= (gx - bk >= 0) & (gz - bk >= 0) & (gx + bk < W) & (gz + bk < H)
            gxc = np.clip(gx, 0, W - 1); gzc = np.clip(gz, 0, H - 1)
            bx = np.clip(np.floor((sx - x0) / 16).astype(np.int64), 0, bes.shape[0] - 1)
            bz = np.clip(np.floor((sz - z0) / 16).astype(np.int64), 0, bes.shape[1] - 1)
            w = wmap[gxc, gzc]; sd = sdmap[gxc, gzc]; nb = bemap[bx, bz]
            wet += w; sdt += sd; bet += nb
            # the plain fills water and evens the ground, so both only cost blocks; builds and buried
            # structures must not be touched at all
            ok &= (nb <= a.max_builds) & ~burmap[bx, bz]
            pen += 10 * w + sd
        for i, j in zip(*np.nonzero(ok)):
            results.append((float(pen[i, j]), int(CX[i, j]), int(CZ[i, j]), rot_deg, float(wet[i, j] / 50),
                            float(sdt[i, j] / 50), int(bet[i, j])))
    results.sort()
    if not results:
        raise SystemExit("no placement fits; relax --max-builds or --shaft")
    best = results[:15]
    for r in best:
        print("pen %.1f centre %d,%d rot %d  water/silo %.3f  relief sd %.1f  block entities %d" % r)
    pen, cx, cz, rot_deg, *_ = best[0]
    layout = hex_layout(50, a.spacing, math.radians(rot_deg))
    silos = []
    for i, (px, pz) in enumerate(layout):
        sx, sz = int(round(cx + px)), int(round(cz + pz))
        gx, gz = (sx - x0) // STEP, (sz - z0) // STEP
        silos.append({"number": i + 1, "x": sx, "z": sz, "surface": int(surf[gx, gz]), "water_here": bool(water[gx, gz])})
    # surface builds (towns, villages) near the field: the plain fades out before them (field.py)
    xs_, zs_ = [s_["x"] for s_ in silos], [s_["z"] for s_ in silos]
    towns = []
    for i, k in zip(*np.nonzero(bes >= 6)):
        tx, tz = x0 + i * 16 + 8, z0 + k * 16 + 8
        if min(xs_) - 500 <= tx <= max(xs_) + 500 and min(zs_) - 500 <= tz <= max(zs_) + 500:
            towns.append([int(tx), int(tz)])
    json.dump({"spacing": a.spacing, "centre": [cx, cz], "rotation_deg": rot_deg, "candidates": best, "silos": silos,
               "towns": towns},
              open(os.path.join(a.out, "layout.json"), "w"), indent=1)
    print(os.path.join(a.out, "layout.json"))


if __name__ == "__main__":
    main()
