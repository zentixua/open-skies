"""Drop entities the 1:1 build made wrong, in a stopped world's entities/ regions (field bbox):
inside any silo cylinder (r <= 64, any y: everything there is ours), hostiles and dropped items, and mobs that stood
on the golden's ground or swam in its lakes (y >= golden ground - 4) and are now under new solid ground.
uv run --with numpy --with nbtlib clean_ents.py <world> <layout.json> <field_*.npz> <surf.npz> [--dry]"""
import os, sys, math, collections
sys.path.insert(0, os.path.expanduser('~/claude/silo-1to1/tools/silo'))
import json, numpy as np, regions
from nbtlib import List, Compound
w, lay, fz, sz = sys.argv[1:5]; dry = '--dry' in sys.argv
silos = [(s['x'], s['z']) for s in json.load(open(lay))['silos']]
F = np.load(fz); gx0, gz0 = map(int, os.path.basename(fz)[6:-4].split('_')[:2]); G = F['ground']
S = np.load(sz); sx0, sz0 = int(S['x0']), int(S['z0']); SURF, WET = S['surf'], S['water'] > -9999
HOST = {'zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch', 'drowned', 'husk', 'stray', 'slime', 'phantom',
        'cave_spider', 'zombie_villager', 'pillager', 'vindicator', 'evoker', 'ravager', 'vex', 'silverfish', 'guardian'}
def at(A, x0, z0, x, z):
    i, k = int(math.floor(x)) - x0, int(math.floor(z)) - z0
    return A[i, k] if 0 <= i < A.shape[0] and 0 <= k < A.shape[1] else None
SOLID = ('dirt', 'grass_block', 'stone', 'moss_block', 'podzol', 'sand', 'gravel', 'deepslate', 'mud', 'clay', 'concrete',
         'terracotta', 'andesite', 'diorite', 'granite', 'tuff', 'calcite', 'mycelium', 'sandstone', 'dirt_path')
_chunks = {}
def block(x, y, z):
    cx, cz = int(math.floor(x)) >> 4, int(math.floor(z)) >> 4
    if (cx, cz) not in _chunks:
        reg = regions.read_region(os.path.join(w, 'region', f'r.{cx >> 5}.{cz >> 5}.mca'))
        it = reg.get((cx & 31) + (cz & 31) * 32)
        sec = {}
        if it:
            t = regions.decode_chunk(it[1]); root = t if 'sections' in t else t['']
            sec = {int(q['Y']): q for q in root['sections'] if 'block_states' in q}
        if len(_chunks) > 400: _chunks.clear()
        _chunks[(cx, cz)] = sec
    st = regions.state_at(_chunks[(cx, cz)], int(math.floor(x)), int(math.floor(y)), int(math.floor(z))) or 'air'
    return st.split('[')[0].replace('minecraft:', '')
def solid(x, y, z):
    b = block(x, y, z)
    return b.endswith(SOLID) and not b.endswith(('_slab', '_stairs', '_wall'))
X0, Z0, X1, Z1 = gx0, gz0, gx0 + G.shape[0], gz0 + G.shape[1]
why = collections.Counter(); kinds = collections.Counter()
for path in sorted(os.listdir(os.path.join(w, 'entities'))):
    _, rx, rz, _ = path.split('.'); rx, rz = int(rx), int(rz)
    if rx * 512 + 511 < X0 or rx * 512 > X1 or rz * 512 + 511 < Z0 or rz * 512 > Z1: continue
    full = os.path.join(w, 'entities', path); reg = regions.read_region(full); changed = False
    for i, (ts, payload) in list(reg.items()):
        t = regions.decode_chunk(payload); root = t if 'Entities' in t else t['']
        keep = []
        for e in root.get('Entities', []):
            eid = str(e['id']).replace('minecraft:', ''); x, y, z = (float(v) for v in e['Pos'])
            r = min(math.hypot(x - a, z - b) for a, b in silos)
            g, s, wet = at(G, gx0, gz0, x, z), at(SURF, sx0, sz0, x, z), at(WET, sx0, sz0, x, z)
            reason = None
            if r <= 64: reason = 'in a shaft'
            elif X0 <= x < X1 and Z0 <= z < Z1 and (eid in HOST or eid in ('item', 'experience_orb')): reason = eid if eid in ('item',) else 'hostile'
            elif g is not None and g > -9999 and s is not None and not wet and s - 1 > g and y >= g - 4 and y + 0.5 < s and solid(x, y + 0.2, z): reason = 'buried'   # only where the build raised the ground
            if reason:
                why[reason] += 1; kinds[eid] += 1; changed = True
                if eid in ('villager', 'cat', 'iron_golem') or (eid == 'sheep' and why['buried'] % 200 == 1 and reason == 'buried'): print(eid, reason, round(x), round(y), round(z), 'golden', g, 'new', s - 1)
            else:
                keep.append(e)
        if len(keep) != len(root.get('Entities', [])):
            root['Entities'] = List[Compound](keep); reg[i] = (ts, regions.encode_chunk(t))
    if changed and not dry: regions.write_region(full, reg)
print('removed' if not dry else 'would remove', dict(why), dict(kinds.most_common(20)))
