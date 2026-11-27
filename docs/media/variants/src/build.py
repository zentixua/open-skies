"""Build every variant's set from the in-game frames and the pixel icons.

python3 build.py FRAMES_DIR OUT_DIR    (BRAND_FONTS: folder with BarlowCondensed-SemiBold.ttf and -Bold.ttf)

Per variant: banner.jpg (GitHub header, 1920×640), store-banner.jpg and store-icon.png (in-game frame only, no
drawing or text), strip.jpg (feature strip, 1920×532). Frames: in-game screenshots of any size (crop() scales them), see
FRAMES below and ../README.md."""
import os, sys
from PIL import Image, ImageDraw, ImageEnhance
from compose import CREAM, NAVY, crop, shade, with_shadow, tagline, pixels, spaced, font, save
from wordmark import render
from pix import PAL, INC, image as pix_image

FR = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = sys.argv[2] if len(sys.argv) > 2 else '..'
F = lambda n: os.path.join(FR, n)

def rgb(k):
    return tuple(int(PAL[k][i:i + 2], 16) for i in (1, 3, 5)) + (255,)

SKY = (138, 190, 230)      # open-sky blue of variant B
GREEN = (140, 255, 140)    # the Strike Designator's screen cross
EMBER = (255, 166, 64)

def mini_icon(cell):
    """Incoming's own 32×32 icon at cell size (the endorsement badge)."""
    return pix_image([list(r) for r in INC]).resize((32 * cell, 32 * cell), Image.NEAREST).convert('RGBA')

# ---------------------------------------------------------------- banners (GitHub; pixel art and text allowed)

def lift(im, k=1.25):
    """Tone only (brightness and contrast of the in-game frame), no drawing: the store may use it."""
    return ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(k)).enhance(1.08)

def banner_a(frame, cx, cy, zoom=1.0):
    im = shade(lift(crop(F(frame), 1920, 640, cx, cy, zoom)), strength=0.6, reach=0.55, side='right')
    wm = render("OPEN SKIES", 11)
    x = 1920 - 120 - wm.width
    im = with_shadow(im, wm, (x, 200))
    im, _ = tagline(im, (x + 8, 200 + 99 + 30), "AN INCOMING MODPACK", spacing=19)
    return im

def banner_b(frame, cx, cy, zoom=1.0):
    im = shade(crop(F(frame), 1920, 640, cx, cy, zoom), strength=0.95, reach=0.7)
    y = 150
    badge = mini_icon(3)                                   # 96 px, Incoming's own icon
    im = with_shadow(im, badge, (120, y), blur=8)
    top = render("INCOMING", 6, EMBER + (255,))            # 360×54, Incoming's wordmark in its ember
    im = with_shadow(im, top, (240, y + 21), blur=3, off=(2, 3), alpha=200)
    wm = render("OPEN SKIES", 11)                          # the pack's name: the main line
    im = with_shadow(im, wm, (120, y + 96 + 22))
    im, _ = tagline(im, (128, y + 96 + 22 + 99 + 28), "THE OFFICIAL INCOMING MODPACK", size=40, spacing=14)
    return im


def brackets(im, box, cell, colour, arm=4):
    """Pixel corner brackets (the Strike Designator's target marks) around box, arm cells long."""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        for i in range(arm):
            for (px, py) in ((x + sx * i * cell, y), (x, y + sy * i * cell)):
                rx = px if sx > 0 else px - cell
                ry = py if sy > 0 else py - cell
                d.rectangle([rx, ry, rx + cell - 1, ry + cell - 1], fill=colour)
    return im

def banner_d(frame, cx, cy, zoom=1.0, target=None):
    im = shade(crop(F(frame), 1920, 640, cx, cy, zoom), colour=(14, 18, 14), strength=0.7, reach=0.6)
    if target:   # reticle brackets on the strike, as the Strike Designator marks a target
        brackets(im, tuple(target), 8, GREEN + (235,), arm=6)
    wm = render("OPEN SKIES", 11)
    x, y = 150, 175
    im = with_shadow(im, wm, (x, y))
    im = brackets(im, (x - 44, y - 40, x + wm.width + 44, y + wm.height + 40), 8, GREEN + (255,), arm=5)
    im, _ = tagline(im, (x + 8, y + wm.height + 72), "STRIKE FAR WITH INCOMING", size=44, spacing=15)
    return im

# ---------------------------------------------------------------- feature strips

def strip(tiles, out, style):
    """tiles: (frame, cx, cy, TITLE, subtitle, weight). Widths by weight over 1920; label bar by style."""
    W, TH, LH = 1920, 400, 132
    total = sum(t[5] for t in tiles)
    bar = {'a': NAVY, 'b': (20, 34, 58), 'd': (16, 20, 16)}[style]
    im = Image.new('RGBA', (W, TH + LH), bar + (255,))
    d = ImageDraw.Draw(im)
    x = 0
    for i, t in enumerate(tiles):
        fr, cx, cy, title, sub, wgt = t[:6]
        w = round(W * wgt / total) if i < len(tiles) - 1 else W - x
        im.paste(crop(F(fr), w, TH, cx, cy, zoom=t[6] if len(t) > 6 else 1.0), (x, 0))
        tc = CREAM
        if style == 'd' and i == 0:
            brackets(im, (x + 24, 24, x + w - 24, TH - 24), 4, GREEN + (230,), arm=6)
        spaced(d, (x, TH + 22), title, font(46), 9, tc, w)
        spaced(d, (x, TH + 80), sub, font(28), 2, (176, 170, 190), w)
        if i:
            d.line([(x, TH + 24), (x, TH + LH - 24)], fill=(60, 62, 92), width=2)
        x += w
    save(im, out)

# ---------------------------------------------------------------- per variant

def store(frame_banner, bc, frame_icon, ic, zoom, outdir, bzoom=1.0, tone=lambda im: im):
    save(tone(crop(F(frame_banner), 1920, 640, *bc, zoom=bzoom)), os.path.join(outdir, 'store-banner.jpg'))
    icon = tone(crop(F(frame_icon), 512, 512, *ic, zoom=zoom))
    save(icon, os.path.join(outdir, 'store-icon.png'))

VARIANTS = {}

def variant(fn):
    VARIANTS[fn.__name__] = fn
    return fn

# Frames (in-game): hero = Incoming's nuke at dusk; day = an Incoming strike under a day sky; designator / salvo =
# the pack's cruise-missile salvo; blast = its blast wave; ship, jungle, valley = the pack's 1.0.0 gallery.
FRAMES = dict(hero='inc-blast-wave-dusk-hq.jpg', designator='strike.jpg', day='inc-still-2.jpg', salvo='strike.jpg', blast='blast-wave.jpg',
              ship='airship.jpg', jungle='jungle-village.jpg', valley='valley-dusk.jpg')
POS = {}   # per frame: banner (cx, cy) and zoom, icon (cx, cy, zoom), strip (cx, cy); from <frames>/positions.json

def tiles_default(first):
    return [first,
            (FRAMES['ship'], 960, 540, "FLY", "Create airships and aircraft", 1),
            (FRAMES['jungle'], 900, 560, "EXPLORE", "Towns, dungeons and temples", 1),
            (FRAMES['valley'], 1450, 320, "SEE FAR", "Voxy distance and shaders", 1)]

@variant
def a_strike_sky(o):
    p = POS['hero']
    save(banner_a(FRAMES['hero'], *p['banner'], p.get('zoom', 1.0)), os.path.join(o, 'banner.jpg'))
    store(FRAMES['hero'], p['banner'], FRAMES['hero'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0), lift)
    strip(tiles_default((FRAMES['salvo'], *POS['salvo']['strip'], "STRIKE", "Incoming: drones to nukes", 2)), os.path.join(o, 'strip.jpg'), 'a')

@variant
def b_open_sky(o):
    p = POS['day']
    save(banner_b(FRAMES['day'], *p['banner'], p.get('zoom', 1.0)), os.path.join(o, 'banner.jpg'))
    store(FRAMES['day'], p['banner'], FRAMES['day'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['day'], *p['strip'], "INCOMING", "Air strikes and nukes", 2)), os.path.join(o, 'strip.jpg'), 'b')


@variant
def d_designator(o):
    p = POS['designator']
    save(banner_d(FRAMES['designator'], *p['banner'], p.get('zoom', 1.0), p.get('target')), os.path.join(o, 'banner.jpg'))
    store(FRAMES['designator'], p['banner'], FRAMES['designator'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['blast'], *POS['blast']['strip'], "AIM AND STRIKE", "Incoming's Strike Designator", 2)),
          os.path.join(o, 'strip.jpg'), 'd')

if __name__ == '__main__':
    import json
    POS.update(json.load(open(os.path.join(FR, 'positions.json'))))
    names = {'a_strike_sky': 'a-strike-sky', 'b_open_sky': 'b-open-sky', 'd_designator': 'd-designator'}
    only = sys.argv[3:]
    for k, fn in VARIANTS.items():
        if not only or k in only:
            fn(os.path.join(OUT, names[k]))
