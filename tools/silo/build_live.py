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
import math
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


LOADED = "return server.overworld().getChunkSource().getLoadedChunksCount()"


def settle(bridge: "Bridge", limit: int = 1100, log=print) -> None:
    """Wait until the overworld holds at most `limit` loaded chunks. A deep world (1088 tall, 68 sections) keeps
    ~3.4x the memory per chunk (~2.9 MB live each on 25567: idle 841 loaded, one 128 m lease adds ~1000 through ticket
    propagation); released leases unload only as fast as the game saves them, and a pass of 50 site builds plus
    256 m path tiles filled a 6 GB heap (12.11 01:06). 1100 leaves room for one lease."""
    t0 = time.time()
    while True:
        n = bridge.call("script", {"code": LOADED})["value"]
        if n <= limit or time.time() - t0 > 300:
            if n > limit:
                log(f"still {n} chunks loaded after 5 min; going on")
            return
        time.sleep(3)


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
            settle(bridge, log=log)
        st["done_rows"] = H - y
        if not dry:                     # a dry run must not mark anything done
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
    ap.add_argument("what", choices=["plain", "gaps", "silo", "site", "all"])
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
    from silo1 import Silo1
    from surface import Site
    log = lambda m: print(time.strftime("%H:%M:%S "), m, flush=True)
    field = Field(a.layout, a.world, a.state)
    bridge = None if a.dry else Bridge()
    go = lambda v, name: build(v, name, a.state, bridge, a.max_positions, a.dry, log)
    if a.what in ("plain", "all"):
        for name, v in field.tiles():
            go(v, name)
    if a.what == "gaps":
        for name, v in field.tiles(gaps=Site.radius):
            go(v, name)
    if a.what in ("plain", "gaps"):
        return
    from tunnels import TURNS
    from turn import turn_grid, turn_points, turn_volume
    for s in field.silos:
        if a.number and s["number"] not in a.number:
            continue
        g = grade_of(field, s["x"], s["z"])
        k = TURNS[s.get("dir", "W")]            # the tunnel's bearing: everything is built due west, then turned
        silo = (Silo1 if s["number"] == 1 else Silo)(Spec(number=s["number"]), s["x"], g, s["z"])
        log(f"silo {s['number']} at {s['x']} {g} {s['z']}, tunnel {s.get('dir', 'W')}")
        if a.what in ("silo", "all"):
            go(turn_volume(silo.build(), k, s["x"], s["z"]), f"silo{s['number']}")
            # the digger's bore out of the void (machines.py) reaches 111 m from the axis at the bottom; where that
            # would cut into the next shaft (a neighbour lies on its bearing), the bore is left out for that silo
            import machines
            b = machines.bearing(machines.TUN_PHI) + k * math.pi / 2
            r0, r1 = silo.s.void_radius - 2, silo.s.void_radius - 2 + machines.TUN_LEN + 1
            ax_, az_ = s["x"] + r0 * math.cos(b), s["z"] + r0 * math.sin(b)
            dx_, dz_ = (r1 - r0) * math.cos(b), (r1 - r0) * math.sin(b)
            def clear(o):
                t = max(0.0, min(1.0, ((o["x"] - ax_) * dx_ + (o["z"] - az_) * dz_) / (dx_ * dx_ + dz_ * dz_)))
                return math.hypot(o["x"] - ax_ - t * dx_, o["z"] - az_ - t * dz_) - silo.s.r_outer
            gap = min(clear(o) for o in field.silos if o is not s)
            if gap >= 5:
                go(turn_volume(silo.tunnel_volume(), k, s["x"], s["z"]), f"bore{s['number']}")
            else:
                log(f"silo {s['number']}: no bore, it would pass {gap:.0f} m from the next shaft")
        if a.what in ("site", "all"):
            old = 213 if s["number"] in (a.repair_213 or []) else None    # the first draft's open cut (Silo 1)
            others = []
            for o in field.silos:
                if o is not s:
                    (ox, oz), = turn_points([(o["x"], o["z"])], -k, s["x"], s["z"])
                    others.append((ox, oz, (TURNS[o.get("dir", "W")] - k) % 4))
            grids = [turn_grid(a_, -k) for a_ in field.slice(s["x"], s["z"], Site.radius)]
            site = Site(silo, *grids, old_cut_deg=old, neighbours=others)
            log(f"site {s['number']}: grade {g}, crater floor {site.p_portal - site.floor_drop:.0f}, ramp rise {site.rise}")
            go(turn_volume(site.build(), k, s["x"], s["z"]), f"site{s['number']}")

if __name__ == "__main__":
    main()
