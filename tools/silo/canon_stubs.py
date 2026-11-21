"""Each ring's stub bearing as the show's 2052 frame shows it: the only straight path between the berm and the outer
ring path is the stub that runs through the berm's cut into the bowl (S3E09 aerials, the 2052 frame). For every
ring, sample the frame (through canon/fit.json Hf) along each bearing over r 0.30-0.39 of the flower edge (berm
crest to ring path at 1:1: 82-106 m of 270) and take the brightest bearing; it counts only where it stands clear of
the ring's other bearings. Bearings are canon frame (gate north, x east, z south), degrees clockwise from east
(atan2(dz, dx)).

  uv run --with numpy --with pillow canon_stubs.py FRAME.jpg OUT.json
"""
import json
import math
import sys

import numpy as np
from PIL import Image

import canon_check

R0, R1 = (float(v) for v in (sys.argv[3:5] if len(sys.argv) > 4 else (0.08, 0.27)))
img = np.asarray(Image.open(sys.argv[1]).convert("L"), float)
H, W = img.shape
out = {}
for n, (gx, gz) in canon_check.GROUND.items():
    prof = []
    for a in range(0, 360, 2):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        vals = []
        for r in np.linspace(R0, R1, 14):
            u, v = canon_check.proj(canon_check.HF, (gx + r * c, gz + r * s))
            if 0 <= u < W - 1 and 0 <= v < H - 1:
                vals.append(img[int(v), int(u)])
        prof.append(np.mean(vals) if len(vals) >= 10 else np.nan)
    prof = np.array(prof)
    if np.isnan(prof).sum() > 20:
        continue
    # smooth over the fit's error (~11 px rms in this frame, a few degrees at this range)
    p = np.nan_to_num(prof, nan=np.nanmedian(prof))
    k = np.convolve(np.r_[p[-2:], p, p[:2]], np.ones(5) / 5, mode="valid")
    i = int(np.argmax(k))
    contrast = (k[i] - np.median(k)) / (np.std(k) + 1e-6)
    out[n] = {"bearing": 2 * i, "contrast": round(float(contrast), 2)}
json.dump(out, open(sys.argv[2], "w"), indent=0)
for n in sorted(out):
    print(n, out[n])
