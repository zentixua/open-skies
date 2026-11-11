"""Write generated volumes into a stopped world's region files (Anvil, Minecraft 1.21.1).

Only chunks that already exist are edited, section by section: volume ids of 0 keep the world's block, everything else
replaces it. Edited chunks lose their heightmaps and light (isLightOn = 0), so the game recomputes both when it loads
them, and their block entities inside the volume are replaced by the volume's. Sections below the old world bottom
(a deeper dimension_type) are created with the biome of the lowest existing section.
"""
from __future__ import annotations

import copy
import io
import math
import os
import struct
import zlib
from collections import defaultdict

import nbtlib
import numpy as np
from nbtlib import Byte, Compound, Int, List, LongArray, String

from volume import KEEP, Volume


# region file IO ------------------------------------------------------------------------------------------------------

def read_region(path: str) -> dict[int, tuple[int, bytes]]:
    """Index -> (timestamp, raw compressed payload incl. compression byte)."""
    out = {}
    if not os.path.exists(path):
        return out
    b = open(path, "rb").read()
    if len(b) < 8192:
        return out
    for i in range(1024):
        off = int.from_bytes(b[i * 4:i * 4 + 3], "big")
        if off == 0:
            continue
        ts = int.from_bytes(b[4096 + i * 4:4096 + i * 4 + 4], "big")
        o = off * 4096
        ln = int.from_bytes(b[o:o + 4], "big")
        out[i] = (ts, b[o + 4:o + 4 + ln])
    return out


def write_region(path: str, chunks: dict[int, tuple[int, bytes]]) -> None:
    header = bytearray(8192)
    body = bytearray()
    sector = 2
    for i in sorted(chunks):
        ts, payload = chunks[i]
        data = len(payload).to_bytes(4, "big") + payload
        pad = (-len(data)) % 4096
        n = (len(data) + pad) // 4096
        if n > 255:
            raise ValueError(f"chunk {i} too large for region format: {n} sectors")
        header[i * 4:i * 4 + 3] = sector.to_bytes(3, "big")
        header[i * 4 + 3] = n
        header[4096 + i * 4:4096 + i * 4 + 4] = ts.to_bytes(4, "big")
        body += data + bytes(pad)
        sector += n
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(header)
        f.write(body)
    os.replace(tmp, path)


def decode_chunk(payload: bytes) -> nbtlib.Compound:
    comp = payload[0]
    raw = payload[1:]
    if comp == 2:
        raw = zlib.decompress(raw)
    elif comp == 1:
        import gzip
        raw = gzip.decompress(raw)
    elif comp != 3:
        raise ValueError(f"compression {comp}")
    return nbtlib.File.parse(io.BytesIO(raw))


def encode_chunk(tag: nbtlib.Compound) -> bytes:
    buf = io.BytesIO()
    nbtlib.File(tag).write(buf)
    return bytes([2]) + zlib.compress(buf.getvalue(), 6)


# block states ------------------------------------------------------------------------------------------------------------

def parse_state(state: str) -> Compound:
    name, _, props = state.partition("[")
    c = Compound({"Name": String(name)})
    if props:
        kv = props.rstrip("]").split(",")
        c["Properties"] = Compound({k.strip(): String(v.strip()) for k, v in (p.split("=", 1) for p in kv if p)})
    return c


def state_key(entry) -> str:
    name = str(entry["Name"])
    props = entry.get("Properties")
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]"


def canonical(state: str) -> str:
    return state_key(parse_state(state))


def unpack(data, n: int) -> np.ndarray:
    bits = max(4, math.ceil(math.log2(n)))
    per = 64 // bits
    longs = np.array([int(x) & 0xFFFFFFFFFFFFFFFF for x in data], dtype=np.uint64)
    shifts = (np.arange(per, dtype=np.uint64) * np.uint64(bits))
    vals = (longs[:, None] >> shifts[None, :]) & np.uint64((1 << bits) - 1)
    return vals.reshape(-1)[:4096].astype(np.int64)


def pack(idx: np.ndarray, n: int) -> LongArray:
    bits = max(4, math.ceil(math.log2(n)))
    per = 64 // bits
    count = math.ceil(4096 / per)
    padded = np.zeros(count * per, dtype=np.uint64)
    padded[:4096] = idx.astype(np.uint64)
    shifts = (np.arange(per, dtype=np.uint64) * np.uint64(bits))
    longs = np.bitwise_or.reduce(padded.reshape(count, per) << shifts[None, :], axis=1)
    return LongArray([int(np.int64(x)) for x in longs.view(np.int64)])


# writing --------------------------------------------------------------------------------------------------------------

BE_IDS = {
    "bed": "minecraft:bed", "chest": "minecraft:chest", "barrel": "minecraft:barrel", "sign": "minecraft:sign",
    "wall_sign": "minecraft:sign", "hanging_sign": "minecraft:hanging_sign", "wall_hanging_sign": "minecraft:hanging_sign",
    "lectern": "minecraft:lectern", "campfire": "minecraft:campfire", "banner": "minecraft:banner",
    "wall_banner": "minecraft:banner", "furnace": "minecraft:furnace", "smoker": "minecraft:smoker",
    "blast_furnace": "minecraft:blast_furnace", "command_block": "minecraft:command_block",
    "chain_command_block": "minecraft:command_block", "repeating_command_block": "minecraft:command_block",
    "chiseled_bookshelf": "minecraft:chiseled_bookshelf", "decorated_pot": "minecraft:decorated_pot",
    "flower_pot": None, "brewing_stand": "minecraft:brewing_stand", "jukebox": "minecraft:jukebox",
    "dispenser": "minecraft:dispenser", "dropper": "minecraft:dropper", "hopper": "minecraft:hopper",
    "skull": "minecraft:skull", "player_head": "minecraft:skull", "bell": "minecraft:bell",
    "daylight_detector": "minecraft:daylight_detector", "comparator": "minecraft:comparator",
    "end_portal": None, "beacon": "minecraft:beacon", "crafter": "minecraft:crafter",
}


def be_id(state: str) -> str | None:
    name = state.split("[", 1)[0].split(":", 1)[1]
    if name in BE_IDS:
        return BE_IDS[name]
    for suffix in ("_bed", "_sign", "_wall_sign", "_hanging_sign", "_wall_hanging_sign", "_banner", "_wall_banner",
                   "shulker_box", "_skull", "_head", "_wall_skull", "_wall_head"):
        if name.endswith(suffix):
            if "hanging_sign" in suffix:
                return "minecraft:hanging_sign"
            return {"_bed": "minecraft:bed", "_sign": "minecraft:sign", "_wall_sign": "minecraft:sign",
                    "_banner": "minecraft:banner", "_wall_banner": "minecraft:banner",
                    "shulker_box": "minecraft:shulker_box"}.get(suffix, "minecraft:skull")
    return None


def to_tag(value):
    """Plain python -> nbtlib, ints as Int, floats as Double, str as String."""
    if isinstance(value, nbtlib.tag.Base):
        return value
    if isinstance(value, bool):
        return Byte(int(value))
    if isinstance(value, int):
        return Int(value)
    if isinstance(value, float):
        return nbtlib.Double(value)
    if isinstance(value, str):
        return String(value)
    if isinstance(value, dict):
        return Compound({k: to_tag(v) for k, v in value.items()})
    if isinstance(value, list):
        return List([to_tag(v) for v in value])
    raise TypeError(type(value))


def apply(world_dir: str, vols: list[Volume], dim_min_y: int, log=print) -> dict:
    """Write volumes into <world_dir>/region. Returns stats."""
    by_region: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    chunks_needed = set()
    for v in vols:
        x0, y0, z0 = v.origin
        for cx in range(x0 >> 4, (x0 + v.size[0] - 1 >> 4) + 1):
            for cz in range(z0 >> 4, (z0 + v.size[2] - 1 >> 4) + 1):
                chunks_needed.add((cx, cz))
    for cx, cz in chunks_needed:
        by_region[(cx >> 5, cz >> 5)].append((cx, cz))
    stats = {"chunks": 0, "sections": 0, "missing_chunks": 0, "block_entities": 0}
    reg_dir = os.path.join(world_dir, "region")
    for (rx, rz), clist in sorted(by_region.items()):
        path = os.path.join(reg_dir, f"r.{rx}.{rz}.mca")
        region = read_region(path)
        for cx, cz in clist:
            i = (cx & 31) + (cz & 31) * 32
            if i not in region:
                stats["missing_chunks"] += 1
                continue
            ts, payload = region[i]
            tag = decode_chunk(payload)
            root = tag if "sections" in tag else tag[""]
            changed = edit_chunk(root, cx, cz, vols, dim_min_y, stats)
            if changed:
                region[i] = (ts, encode_chunk(tag))
                stats["chunks"] += 1
        write_region(path, region)
    log(f"regions: {stats}")
    return stats


def edit_chunk(root, cx: int, cz: int, vols: list[Volume], dim_min_y: int, stats: dict) -> bool:
    sections = {int(s["Y"]): s for s in root["sections"]}
    lowest = min(sections)
    base_biomes = sections[lowest].get("biomes")
    changed = False
    bes = [be for be in root.get("block_entities", [])]
    written: dict[int, np.ndarray] = {}
    auto = []
    added = []
    for v in vols:
        x0, y0, z0 = v.origin
        lx0, lz0 = cx * 16 - x0, cz * 16 - z0
        if lx0 + 16 <= 0 or lz0 + 16 <= 0 or lx0 >= v.size[0] or lz0 >= v.size[2]:
            continue
        for sy in range(max(y0, dim_min_y) >> 4, ((y0 + v.size[1] - 1) >> 4) + 1):
            ly0 = sy * 16 - y0
            # local block of this section in volume space, with clipping
            xs = slice(max(lx0, 0), min(lx0 + 16, v.size[0]))
            ys = slice(max(ly0, 0), min(ly0 + 16, v.size[1]))
            zs = slice(max(lz0, 0), min(lz0 + 16, v.size[2]))
            sub = v.ids[xs, ys, zs]
            if not sub.any():
                continue
            sec = sections.get(sy)
            if sec is None:
                sec = Compound({"Y": Byte(sy)})
                if base_biomes is not None:
                    sec["biomes"] = copy.deepcopy(base_biomes)
                sec["block_states"] = Compound({"palette": List[Compound]([parse_state("minecraft:air")])})
                sections[sy] = sec
            pal, idx = section_states(sec)
            grid = idx.reshape(16, 16, 16)          # y, z, x
            keymap = {k: n for n, k in enumerate(pal)}
            dx0, dy0, dz0 = xs.start - lx0, ys.start - ly0, zs.start - lz0
            vids = np.unique(sub)
            lut = np.full(len(v.palette), -1, dtype=np.int64)
            for vid in vids:
                if vid == KEEP:
                    continue
                key = canon_cache(v.palette[int(vid)])
                k = keymap.get(key)
                if k is None:
                    k = len(pal)
                    pal.append(key)
                    keymap[key] = k
                lut[vid] = k
            mapped = lut[sub].transpose(1, 2, 0)    # x,y,z -> y,z,x
            target = grid[dy0:dy0 + mapped.shape[0], dz0:dz0 + mapped.shape[1], dx0:dx0 + mapped.shape[2]]
            write = mapped >= 0
            target[write] = mapped[write]
            wgrid = written.setdefault(sy, np.zeros((16, 16, 16), dtype=bool))
            wgrid[dy0:dy0 + mapped.shape[0], dz0:dz0 + mapped.shape[1], dx0:dx0 + mapped.shape[2]] |= write
            need = needs_be(v)[sub].transpose(1, 2, 0) & write
            for iy, iz, ix in np.argwhere(need):
                st = v.palette[int(sub[ix, iy, iz])]
                auto.append((cx * 16 + dx0 + ix, sy * 16 + dy0 + iy, cz * 16 + dz0 + iz, be_id(canon_cache(st))))
            set_section_states(sec, pal, grid.reshape(-1))
            for lk in ("SkyLight", "BlockLight"):
                if lk in sec:
                    del sec[lk]
            stats["sections"] += 1
            changed = True
        for (bx, by, bz), nbt in v.block_entities.items():
            wx, wy, wz = x0 + bx, y0 + by, z0 + bz
            if wx >> 4 == cx and wz >> 4 == cz and wy >= dim_min_y:
                st = v.get(bx, by, bz)
                if st is not None and be_id(canon_cache(st)) is not None:   # the block may have been overwritten
                    added.append((wx, wy, wz, nbt))
    if not changed:
        return False
    # block entities for blocks that need them but were given none
    def was_written(x, y, z):
        g = written.get(y >> 4)
        return g is not None and bool(g[y & 15, z & 15, x & 15])
    keep = [be for be in bes if not was_written(int(be["x"]), int(be["y"]), int(be["z"]))]
    have = {(w[0], w[1], w[2]) for w in added}
    for wx, wy, wz, bid in auto:
        if (wx, wy, wz) not in have:
            added.append((wx, wy, wz, {"id": bid}))
    for wx, wy, wz, nbt in added:
        c = to_tag(dict(nbt))
        c["x"], c["y"], c["z"] = Int(wx), Int(wy), Int(wz)
        c["keepPacked"] = Byte(0)
        keep.append(c)
    stats["block_entities"] += len(added)
    root["block_entities"] = List[Compound](keep)
    root["sections"] = List[Compound]([sections[k] for k in sorted(sections)])
    if "Heightmaps" in root:
        root["Heightmaps"] = Compound({})
    root["isLightOn"] = Byte(0)
    return True


_canon = {}


def canon_cache(state: str) -> str:
    c = _canon.get(state)
    if c is None:
        c = _canon[state] = canonical(state)
    return c


_needs = {}


def needs_be(v) -> np.ndarray:
    """Per volume palette id: does the block need a block entity."""
    key = (id(v), len(v.palette))
    arr = _needs.get(key)
    if arr is None:
        arr = np.array([i != KEEP and be_id(canon_cache(st)) is not None for i, st in enumerate(v.palette)], dtype=bool)
        _needs[key] = arr
    return arr


def section_states(sec) -> tuple[list[str], np.ndarray]:
    bs = sec.get("block_states")
    if bs is None:
        return ["minecraft:air"], np.zeros(4096, dtype=np.int64)
    pal = [state_key(e) for e in bs["palette"]]
    data = bs.get("data")
    if data is None or len(pal) == 1:
        return pal, np.zeros(4096, dtype=np.int64)
    return pal, unpack(data, len(pal))


def set_section_states(sec, pal: list[str], idx: np.ndarray) -> None:
    used = np.unique(idx)
    remap = np.full(len(pal), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    new_pal = [pal[u] for u in used]
    new_idx = remap[idx]
    bs = Compound({"palette": List[Compound]([parse_state(p) for p in new_pal])})
    if len(new_pal) > 1:
        bs["data"] = pack(new_idx, len(new_pal))
    sec["block_states"] = bs


def state_at(sections, wx, wy, wz) -> str | None:
    sec = sections.get(wy >> 4)
    if sec is None:
        return None
    pal, idx = section_states(sec)
    return pal[int(idx[((wy & 15) << 8) | ((wz & 15) << 4) | (wx & 15)])]
