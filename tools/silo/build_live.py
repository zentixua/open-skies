# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "httpx>=0.27"]
# ///
"""Build generated volumes into a running server through the Almighty bridge (build method, "layers" ops).

Each volume is sent as horizontal slabs, bottom to top, one build job per slab; the next slab is sent when the
previous job has finished. Progress is kept in a state file, so an interrupted run continues where it stopped.

  ALMIGHTY_URL=http://10.0.6.2:25653 ALMIGHTY_TOKEN_FILE=.../config/almighty/token \\
      uv run tools/silo/build_live.py silo --number 18 --x 3000 --z -2900 --surface 63 --state ~/silo-work/state
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


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("silo")
    s.add_argument("--number", type=int, required=True)
    s.add_argument("--x", type=int, required=True); s.add_argument("--z", type=int, required=True)
    s.add_argument("--surface", type=int, required=True)
    s.add_argument("--state", required=True)
    s.add_argument("--dry", action="store_true")
    s.add_argument("--max-positions", type=int, default=1_500_000)
    a = ap.parse_args()
    from silo import Silo, Spec
    silo = Silo(Spec(number=a.number), a.x, a.surface, a.z)
    v = silo.build()
    print(f"silo {a.number}: origin {v.origin} size {v.size} states {len(v.palette)}", flush=True)
    build(v, f"silo{a.number}", a.state, None if a.dry else Bridge(), a.max_positions, a.dry,
          log=lambda m: print(m, flush=True))


if __name__ == "__main__":
    main()
