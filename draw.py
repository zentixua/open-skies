import sys, json, math, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/ubuntu/claude/silo-recon')
picks = json.load(open(sys.argv[1]))[:3]; site5 = json.load(open('/home/ubuntu/claude/silo-work/site5/layout.json'))
# shift feasibility: a conflicting silo may move up to 56 m (site_fit --shift) to a non-conflict spot
t = np.load(sys.argv[3], allow_pickle=True); x0, z0, bes, bu = int(t['x0']), int(t['z0']), t['bes'], t['bes_under'] >= 5
def bad(x, z, clear=200, maxb=12, shaft=64):
    bx, bz = (x-x0)//16, (z-z0)//16; r = clear//16; s = math.ceil(shaft/16)
    nb = sum(int(bes[i, k]) for i in range(bx-r, bx+r+1) for k in range(bz-r, bz+r+1) if (i-bx)**2+(k-bz)**2 <= r*r)
    bur = any(bu[i, k] for i in range(bx-s, bx+s+1) for k in range(bz-s, bz+s+1) if ((i-bx)**2+(k-bz)**2)*256 <= (shaft+8)**2)
    return nb > maxb or bur
for p in picks:
    for s in p['silos']:
        if s['conflict']:
            s['shift'] = next(([dx, dz] for r in range(8, 57, 8) for dx in range(-r, r+1, 8) for dz in range(-r, r+1, 8)
                               if math.hypot(dx, dz) <= 56 and not bad(s['x']+dx, s['z']+dz)), None)
json.dump(picks, open(sys.argv[1].replace('.json', '_shift.json'), 'w'), indent=1)
d = np.load('/home/ubuntu/claude/silo-recon/grid.npz'); G = d['G']; WAT = d['WAT']
X0, Z0 = -2816, -4608
g = np.nan_to_num(G, nan=0); dx = np.gradient(g, axis=1); shade = np.clip(0.75+dx*0.04, 0.3, 1.2); tt = np.clip((g-62)/80, 0, 1)
rgb = np.stack([90+120*tt, 150+60*tt-40*tt*tt, 70+90*tt], -1)*shade[..., None]
w = WAT > 0.5; rgb[w] = np.stack([30+0*g, 70+np.clip(g, 0, 62)*1.5, 170+0*g], -1)[w]
rgb = rgb*0.75+40  # fade the base so the fields read
im = Image.fromarray(np.clip(rgb, 0, 255).astype('uint8')).resize((G.shape[1]*2, G.shape[0]*2), Image.NEAREST)
dr = ImageDraw.Draw(im)
P = lambda x, z: ((x-X0)/8, (z-Z0)/8)
for gx in range(-2000, 4801, 1000): dr.line([P(gx, Z0), P(gx, 3071)], fill=(255, 255, 255)); dr.text((P(gx, 0)[0]+2, 2), f"x{gx}", fill=(0, 0, 0))
for gz in range(-4000, 3072, 1000): dr.line([P(X0, gz), P(4799, gz)], fill=(255, 255, 255)); dr.text((2, P(0, gz)[1]+2), f"z{gz}", fill=(0, 0, 0))
def hull(pts):
    pts = sorted(set(pts)); 
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def field(sil, col, label, r=200):
    ring = [(s['x']+r*math.cos(a/12*math.pi), s['z']+r*math.sin(a/12*math.pi)) for s in sil for a in range(24)]
    h = [P(*q) for q in hull(ring)]; dr.line(h+[h[0]], fill=col, width=3)
    for s in sil:
        x, z = P(s['x'], s['z']); c = (255, 40, 40) if s.get('conflict') else col
        dr.ellipse([x-3, z-3, x+3, z+3], fill=c, outline=(0, 0, 0))
    x, z = P(sil[0]['x'], sil[0]['z']); dr.rectangle([x-9, z-9, x+9, z+9], outline=(0, 0, 0), fill=col); dr.text((x-4, z-6), label, fill=(0, 0, 0))
field(site5['silos'], (255, 255, 255), 'C', r=200)
for k, (p, col) in enumerate(zip(picks, [(255, 230, 0), (255, 120, 0), (200, 0, 255)])): field(p['silos'], col, str(k+1))
dr.rectangle([0, im.height-58, 520, im.height], fill=(255, 255, 255))
dr.text((6, im.height-54), "Zearth: 1:1 Silo fields, canon layout, edge 270 m (1-3); C = current site, edge 156 m", fill=(0, 0, 0))
dr.text((6, im.height-38), "dot = silo shaft, red dot = conflict (buried structure or builds); outline = silos + 200 m plain", fill=(0, 0, 0))
dr.text((6, im.height-22), "square = Silo 1. Map = generated area x -2816..4799, z -4608..3071", fill=(0, 0, 0))
im.save(sys.argv[2]); print(im.size)
for p in picks: print(p['centre'], p['rot'], [(s['n'], s['conflict'], s['shift']) for s in p['silos'] if s['conflict']])
