# Rank canon-layout placements: conflicts, water, relief, bounds of field (+blend).
import sys, math, json, numpy as np
sys.path.insert(0, '/home/ubuntu/claude/silo-work/open-skies/tools/silo')
import site_fit as sf
from tunnels import assign, shafts
canon, cache, berm_r, clear_r, maxb, shaft_r, step = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), 64, 4
BX0, BX1, BZ0, BZ1, BLEND = -2816, 4799, -4608, 3071, 100
t = np.load(cache, allow_pickle=True)
x0, z0, surf, floor, bes = int(t['x0']), int(t['z0']), t['surf'], t['floor'], t['bes']
buried = (t['bes_under'] >= 5).astype(float); known = surf > -9999; water = (surf > floor) | ~known
W, H = surf.shape; STEP = 4
def disc(r, s):
    rr = int(r // s); return [(i*s, j*s) for i in range(-rr, rr+1) for j in range(-rr, rr+1) if (i*i+j*j)*s*s <= r*r]
bk = 2*int(berm_r//8); kb = np.zeros((2*bk+1,)*2)
for dx, dz in disc(berm_r, 8): kb[dx//4+bk, dz//4+bk] = 1
ck = int(clear_r//16); kc = np.zeros((2*ck+1,)*2)
for dx, dz in disc(clear_r, 16): kc[dx//16+ck, dz//16+ck] = 1
def conv(img, k):
    r = k.shape[0]//2; sh = (img.shape[0]+k.shape[0], img.shape[1]+k.shape[1])
    f = np.fft.irfft2(np.fft.rfft2(img, sh)*np.fft.rfft2(k[::-1, ::-1], sh), sh); return f[r:r+img.shape[0], r:r+img.shape[1]]
n = kb.sum(); hf = surf.astype(float)
wmap = conv(water.astype(float), kb)/n; m1 = conv(hf, kb)/n; sdmap = np.sqrt(np.maximum(conv(hf*hf, kb)/n-m1*m1, 0))
bemap = np.rint(conv(np.pad(bes.astype(float), ck, mode='edge'), kc)[ck:-ck, ck:-ck]).astype(np.int64)
sk = math.ceil(shaft_r/16); a_ = np.arange(-sk, sk+1); ks = ((a_[:, None]**2+a_[None, :]**2)*256 <= (shaft_r+8)**2).astype(float)
burmap = conv(np.pad(buried, sk), ks)[sk:-sk, sk:-sk] > 0.5
res = []; lays = {}
for rot in range(0, 360, step):
    rings = sf.canon_layout(canon, math.radians(rot))[0]
    dirs, worst = assign(rings, {0: 'W'}); sh = shafts(rings, dirs)
    lay = np.array([(x-sh[0][0], z-sh[0][1]) for x, z in sh]); lays[rot] = (lay, worst)
    cxs = np.arange(x0, x0+W*STEP, 32); czs = np.arange(z0, z0+H*STEP, 32)
    CX, CZ = np.meshgrid(cxs, czs, indexing='ij')
    # bounds: all silos +- (clear + blend) inside generated area
    m = clear_r + BLEND
    inb = (CX+lay[:, 0].min()-m >= BX0) & (CX+lay[:, 0].max()+m <= BX1) & (CZ+lay[:, 1].min()-m >= BZ0) & (CZ+lay[:, 1].max()+m <= BZ1)
    conf = np.zeros(CX.shape, int); wet = np.zeros(CX.shape); sdt = np.zeros(CX.shape); ok = inb.copy()
    for px, pz in lay:
        sx, sz = CX+px, CZ+pz
        gx = np.floor((sx-x0)/4).astype(int); gz = np.floor((sz-z0)/4).astype(int)
        ok &= (gx-bk >= 0) & (gz-bk >= 0) & (gx+bk < W) & (gz+bk < H)
        gxc = np.clip(gx, 0, W-1); gzc = np.clip(gz, 0, H-1)
        bx = np.clip(np.floor((sx-x0)/16).astype(int), 0, bes.shape[0]-1); bz = np.clip(np.floor((sz-z0)/16).astype(int), 0, bes.shape[1]-1)
        conf += (bemap[bx, bz] > maxb) | burmap[bx, bz]; wet += wmap[gxc, gzc]; sdt += sdmap[gxc, gzc]
    for i, j in zip(*np.nonzero(ok)):
        res.append((int(conf[i, j]), float(10*wet[i, j]+sdt[i, j]), int(CX[i, j]), int(CZ[i, j]), rot, wet[i, j]/50, sdt[i, j]/50))
res.sort()
print('in-bounds candidates', len(res), 'min conflicts', res[0][0] if res else None)
picks = []
for r in res:
    if all(math.hypot(r[2]-p[2], r[3]-p[3]) > 1500 for p in picks): picks.append(r)
    if len(picks) == 6: break
out = []
for c, pen, cx, cz, rot, w, sd in picks:
    lay, worst = lays[rot]; sil = []
    for k, (px, pz) in enumerate(lay):
        sx, sz = int(round(cx+px)), int(round(cz+pz)); bx, bz = (sx-x0)//16, (sz-z0)//16
        why = 'buried structure' if burmap[bx, bz] else (f'{int(bemap[bx, bz])} builds' if bemap[bx, bz] > maxb else '')
        sil.append({'n': k+1, 'x': sx, 'z': sz, 'conflict': why, 'water': bool(water[(sx-x0)//4, (sz-z0)//4])})
    xs = [s['x'] for s in sil]; zs = [s['z'] for s in sil]; m = clear_r+BLEND
    margin = min(min(xs)-m-BX0, BX1-max(xs)-m, min(zs)-m-BZ0, BZ1-max(zs)-m)
    d = dict(conflicts=c, pen=round(pen, 1), centre=[cx, cz], rot=rot, water=round(w, 3), sd=round(sd, 2), worst_tunnel=round(worst, 1),
             extent=[max(xs)-min(xs), max(zs)-min(zs)], margin=int(margin), silos=sil)
    out.append(d); print(c, d['pen'], cx, cz, rot, d['water'], d['sd'], d['extent'], 'margin', d['margin'], [f"{s['n']}:{s['conflict']}" for s in sil if s['conflict']])
json.dump(out, open(sys.argv[6], 'w'), indent=1)
