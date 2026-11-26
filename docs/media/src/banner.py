"""Open Skies banner: an in-game frame (3:1 crop), Incoming's banner layout: pixel wordmark + letter-spaced tagline.

python3 banner.py frame.png top out.jpg font.ttf ["TAGLINE"]
The font is Barlow Condensed SemiBold (SIL OFL 1.1, github.com/google/fonts/tree/main/ofl/barlowcondensed), the
typeface of Incoming's banner tagline. docs/media/banner.jpg: frame top 250, cell 11, y0 105,
tagline "CREATE · AIRCRAFT · AIR STRIKES"."""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from wordmark import render
FONT = 'BarlowCondensed-SemiBold.ttf'
CREAM = (238, 229, 214)

def tagline(draw, xy, text, size, spacing, fill):
    f = ImageFont.truetype(FONT, size)
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing
    return x

def banner(frame, top, out, W=1920, H=640, cell=14, x0=122, y0=212, tag="AIRSHIPS & AIR STRIKES", shade=0.62):
    im = Image.open(frame).convert('RGB')
    s = W / im.width
    im = im.resize((W, round(im.height * s)), Image.LANCZOS).crop((0, top, W, top + H)).convert('RGBA')
    # navy shade on the left (Incoming's night palette), fading out before the middle
    g = Image.new('RGBA', (W, H))
    px = g.load()
    for x in range(W):
        a = max(0.0, 1 - x / (W * 0.58)) ** 1.6 * shade
        for y in range(H):
            px[x, y] = (22, 28, 52, int(255 * a))
    im = Image.alpha_composite(im, g)
    wm = render("OPEN SKIES", cell)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 150), (x0 + 6, y0 + 8), wm)
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    im = Image.alpha_composite(im, sh)
    im.alpha_composite(wm, (x0, y0))
    d = ImageDraw.Draw(im)
    ty = y0 + 9 * cell + 30
    # tagline shadow, then text
    tl = Image.new('RGBA', im.size, (0, 0, 0, 0))
    tagline(ImageDraw.Draw(tl), (x0 + 10, ty + 3), tag, 44, 17, (0, 0, 0, 170))
    im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(3)))
    tagline(ImageDraw.Draw(im), (x0 + 8, ty), tag, 44, 17, CREAM + (255,))
    im.convert('RGB').save(out, quality=92, subsampling=0)

if __name__ == '__main__':
    FONT = sys.argv[4]
    banner(sys.argv[1], int(sys.argv[2]), sys.argv[3], cell=11, x0=120, y0=105,
           tag=sys.argv[5] if len(sys.argv) > 5 else "CREATE · AIRCRAFT · AIR STRIKES")
