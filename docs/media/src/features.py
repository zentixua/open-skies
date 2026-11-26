"""'What's inside' strip: four in-game crops with labels in Incoming's tagline style (Barlow Condensed, cream on navy).

python3 features.py out.jpg font_dir 'tile1.png|cx|cy|TITLE|subtitle' ... (crop centre cx, cy in the 1920x1080 frame)"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
CREAM, MUTED, NAVY = (238, 229, 214), (176, 170, 190), (24, 28, 48)
def spaced(d, xy, text, font, spacing, fill, center_w=None):
    w = sum(d.textlength(c, font=font) + spacing for c in text) - spacing
    x, y = xy
    if center_w: x += (center_w - w) / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font) + spacing
out, fonts, tiles = sys.argv[1], sys.argv[2], sys.argv[3:]
TW, TH, LH, GAP = 480, 400, 132, 0
strip = Image.new('RGB', (TW * len(tiles) + GAP * (len(tiles) - 1), TH + LH), NAVY)
d = ImageDraw.Draw(strip)
ft = ImageFont.truetype(os.path.join(fonts, 'BarlowCondensed-SemiBold.ttf'), 46)
fs = ImageFont.truetype(os.path.join(fonts, 'BarlowCondensed-Medium.ttf'), 28)
for i, t in enumerate(tiles):
    src, cx, cy, title, sub = t.split('|')
    im = Image.open(src).convert('RGB')
    scale = 0.75   # 1080p → crop of 640x533 scaled to 480x400
    cw, ch = int(TW / scale), int(TH / scale)
    cx, cy = int(cx), int(cy)
    box = (max(0, min(im.width - cw, cx - cw // 2)), max(0, min(im.height - ch, cy - ch // 2)))
    tile = im.crop((box[0], box[1], box[0] + cw, box[1] + ch)).resize((TW, TH), Image.LANCZOS)
    x = i * (TW + GAP)
    strip.paste(tile, (x, 0))
    spaced(d, (x, TH + 22), title, ft, 9, CREAM, TW)
    spaced(d, (x, TH + 80), sub, fs, 2, MUTED, TW)
    if i: d.line([(x, TH + 24), (x, TH + LH - 24)], fill=(60, 62, 92), width=2)
strip.save(out, quality=90, subsampling=0)
