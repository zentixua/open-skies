# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "httpx>=0.27"]
# ///
"""Build generated volumes into a running server through the Almighty bridge (build method, "layers" ops).

Each volume is sent as horizontal slabs, bottom to top, one build job per slab; the next slab is sent when the
previous job has finished. Progress is kept in a state file, so an interrupted run continues where it stopped.

  ALMIGHTY_URL=http://10.0.6.2:25653 ALMIGHTY_TOKEN_FILE=.../config/almighty/token \\
      uv run tools/silo/build_live.py all --layout site/layout.json --world <golden world> --state ~/silo-work/state

"plain" shapes the field (tiles nearest Silo 1 first), "silo" digs the shafts, "site" shapes the ground above each;
"all" does the plain, then each silo with its site. Grade = mean plain height within 34 blocks of the axis.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import httpx
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volume import KEEP, Volume  # noqa: E402

CHARS = [c for c in (chr(i) for i in range(33, 127)) if c not in ".\\\""] + [chr(i) for i in range(0x100, 0x2000)]


class Bridge:
    def __init__(self):
        url = os.environ.get("ALMIGHTY_URL", "http://127.0.0.1:25650").rstrip("/") + "/rpc"
        token = os.environ.get("ALMIGHTY_TOKEN") or open(os.environ["ALMIGHTY_TOKEN_FILE"]).read().strip()
        self.url = url
        self.c = httpx.Client(timeout=120, trust_env=False, headers={"Authorization": "Bearer " + token})

    def call(self, method, params):
        r = self.c.post(self.url, json={"method": method, "params": params})
        d = r.json()
        if not d.get("ok"):
            raise RuntimeError(f"{method}: {d.get('error')}")
        return d["result"]


def slab_ops(v: Volume, y0: int, y1: int, max_ops: int = 10_000) -> tuple[list[dict], int]:
    """Layers ops for local rows y0..y1-1, cropped to the bounding box of non-keep blocks."""
    sub = v.ids[:, y0:y1, :]
    nz = np.argwhere(sub != KEEP)
    if len(nz) == 0:
        return [], 0
    xa, ya, za = nz.min(axis=0)
    xb, yb, zb = nz.max(axis=0)
    sub = sub[xa:xb + 1, ya:yb + 1, za:zb + 1]
    used = [int(i) for i in np.unique(sub) if i != KEEP]
    if len(used) > len(CHARS):
        raise ValueError("too many block states in one slab")
    lut = np.full(len(v.palette), ord("."), dtype=np.uint32)
    palette = {}
    for n, i in enumerate(used):
        lut[i] = ord(CHARS[n])
        palette[CHARS[n]] = v.palette[i]
    chars = lut[sub]                                      # [x, y, z]
    layers = []
    for y in range(chars.shape[1]):
        rows = []
        for z in range(chars.shape[2]):
            rows.append("".join(map(chr, chars[:, y, z])))
        layers.append(rows)
    ox, oy, oz = v.origin
    op = {"op": "layers", "origin": [ox + int(xa), oy + y0 + int(ya), oz + int(za)], "palette": palette, "layers": layers}
    return [op], int(sub.size)


def build(v: Volume, name: str, state_dir: str, bridge: Bridge, max_positions: int = 1_500_000, dry=False, log=print):
    """Top to bottom: players watching see the shaft sink from the surface."""
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, name + ".json")
    st = json.load(open(path)) if os.path.exists(path) else {"done_rows": 0, "jobs": []}
    area = v.size[0] * v.size[2]
    rows = max(1, max_positions // area)
    H = v.size[1]
    t0 = time.time(); sent = 0
    while st["done_rows"] < H:
        y1 = H - st["done_rows"]
        y = max(0, y1 - rows)
        ops, n = slab_ops(v, y, y1)
        sent += len(json.dumps(ops)) if ops else 0
        if ops and not dry:
            res = bridge.call("build", {"ops": ops, "wait": 50})
            jid = res["id"]
            while res.get("state") not in ("done", "failed", "cancelled"):
                res = bridge.call("job", {"id": jid, "wait": 50})
            if res["state"] != "done":
                raise RuntimeError(f"slab {y}..{y1} job {jid}: {res}")
            st["jobs"].append(jid)
        st["done_rows"] = H - y
        json.dump(st, open(path, "w"))
        log(f"{name}: down to y {v.origin[1] + y} ({100 * st['done_rows'] / H:.0f}%), {n} positions, "
            f"{sent / 1e6:.1f} MB sent, {time.time() - t0:.0f}s")
    return st


def grade_of(field, x: int, z: int) -> int:
    h, *_ = field.slice(x, z, 34)
    r = np.hypot(*np.meshgrid(np.arange(69) - 34, np.arange(69) - 34, indexing="ij"))
    vals = h[(r <= 34) & (h > -9999)]
    return int(round(float(vals.mean()))) if len(vals) else 64


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["plain", "silo", "site", "all"])
    ap.add_argument("--layout", required=True, help="site_fit layout.json")
    ap.add_argument("--world", required=True, help="golden copy of the world (region files are only read)")
    ap.add_argument("--state", required=True)
    ap.add_argument("--number", type=int, nargs="*", help="silos to build (default: all, Silo 1 first)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--max-positions", type=int, default=1_500_000)
    ap.add_argument("--repair-213", type=int, nargs="*", help="silos whose first-draft open cut at 213 degrees is filled")
    a = ap.parse_args()
    from field import Field
    from silo import Silo, Spec
    from surface import Site
    log = lambda m: print(time.strftime("%H:%M:%S "), m, flush=True)
    field = Field(a.layout, a.world, a.state)
    bridge = None if a.dry else Bridge()
    go = lambda v, name: build(v, name, a.state, bridge, a.max_positions, a.dry, log)
    if a.what in ("plain", "all"):
        for name, v in field.tiles():
            go(v, name)
    if a.what == "plain":
        return
    for s in field.silos:
        if a.number and s["number"] not in a.number:
            continue
        g = grade_of(field, s["x"], s["z"])
        silo = Silo(Spec(number=s["number"]), s["x"], g, s["z"])
        log(f"silo {s['number']} at {s['x']} {g} {s['z']}")
        if a.what in ("silo", "all"):
            go(silo.build(), f"silo{s['number']}")
        if a.what in ("site", "all"):
            old = 213 if s["number"] in (a.repair_213 or []) else None    # the first draft's open cut (Silo 1)
            go(Site(silo, *field.slice(s["x"], s["z"], Site.radius), old_cut_deg=old).build(), f"site{s['number']}")


if __name__ == "__main__":
    main()
