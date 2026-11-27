"""Top-down shaded relief of the 1:1 complex from los.py's surf.npz. uv run --with numpy --with pillow topdown.py out.png [scale]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
d = np.load('surf.npz'); S = d['surf'].astype(float); W = d['water'] > -9999
S[S < -9000] = np.nan; S = np.nan_to_num(S, nan=np.nanmedian(S))
gx, gz = np.gradient(S)
shade = np.clip(0.75 + 0.35 * (-gx - gz) / np.sqrt(1 + gx ** 2 + gz ** 2), 0, 1.3)
h = np.clip((S - 60) / 30, 0, 1)
rgb = np.stack([90 + 60 * h, 140 + 50 * h, 70 + 30 * h], -1) * shade[..., None]
rgb[W] = [60, 90, 170]
img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2))   # [x,z] -> rows = z
lay = json.load(open('/home/ubuntu/claude/silo-work/1to1/layout.json'))
dr = ImageDraw.Draw(img)
for s in lay['silos']:
    x, z = s['x'] - int(d['x0']), s['z'] - int(d['z0'])
    dr.text((x - 6, z - 6), str(s['number']), fill=(255, 255, 255))
sc = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
img = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
img.save(sys.argv[1]); print(img.size)
