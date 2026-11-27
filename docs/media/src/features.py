"""'What's inside' strip (1920×532): in-game crops with labels in Incoming's tagline style (Barlow Condensed, cream on
navy); the first tile (Incoming) is twice as wide.

python3 features.py out.jpg 'frame|cx|cy|TITLE|subtitle[|weight[|zoom]]' ...   (cx, cy: crop centre in frame pixels)"""
import sys
from PIL import Image, ImageDraw
from compose import CREAM, crop, spaced, font, save

W, TH, LH = 1920, 400, 132
BAR, MUTED, RULE = (20, 34, 58), (176, 170, 190), (60, 62, 92)

def strip(tiles):
    tiles = [t.split('|') for t in tiles]
    weights = [float(t[5]) if len(t) > 5 else 1.0 for t in tiles]
    im = Image.new('RGB', (W, TH + LH), BAR)
    d = ImageDraw.Draw(im)
    x = 0
    for i, t in enumerate(tiles):
        w = round(W * weights[i] / sum(weights)) if i < len(tiles) - 1 else W - x
        zoom = float(t[6]) if len(t) > 6 else 1.0
        im.paste(crop(t[0], w, TH, float(t[1]), float(t[2]), zoom), (x, 0))
        spaced(d, (x, TH + 22), t[3], font(46), 9, CREAM, w)
        spaced(d, (x, TH + 80), t[4], font(28), 2, MUTED, w)
        if i:
            d.line([(x, TH + 24), (x, TH + LH - 24)], fill=RULE, width=2)
        x += w
    return im

if __name__ == '__main__':
    save(strip(sys.argv[2:]), sys.argv[1])
