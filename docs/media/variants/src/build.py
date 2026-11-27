"""Build every variant's set from the in-game frames and the pixel icons.

python3 build.py FRAMES_DIR OUT_DIR    (BRAND_FONTS: folder with BarlowCondensed-SemiBold.ttf and -Bold.ttf)

Per variant: banner.jpg (GitHub header, 1920×640), store-banner.jpg and store-icon.png (in-game frame only, no
drawing or text), strip.jpg (feature strip, 1920×532). Frames (1920×1080, in-game, HUD hidden unless the HUD is the
subject): see FRAMES below and ../README.md."""
import os, sys
from PIL import Image, ImageDraw
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

def banner_a(frame, cx, cy, zoom=1.0):
    im = shade(crop(F(frame), 1920, 640, cx, cy, zoom), strength=0.6, reach=0.55, side='right')
    wm = render("OPEN SKIES", 11)
    x = 1920 - 120 - wm.width
    im = with_shadow(im, wm, (x, 200))
    im, _ = tagline(im, (x + 8, 200 + 99 + 30), "AN INCOMING MODPACK", spacing=19)
    return im

def banner_b(frame, cx, cy, zoom=1.0):
    im = shade(crop(F(frame), 1920, 640, cx, cy, zoom), strength=0.93, reach=0.68)
    badge = mini_icon(4)                                   # 128 px, Incoming's own icon
    y = 150
    im = with_shadow(im, badge, (120, y + 2), blur=10)
    wm = render("INCOMING", 10)                            # 600×90, Incoming's wordmark
    im = with_shadow(im, wm, (280, y))
    sub = render("OPEN SKIES", 7, SKY + (255,))            # 539×63: the pack's name in the same letters, sky blue
    im = with_shadow(im, sub, (282, y + 90 + 16), blur=4, off=(3, 4), alpha=200)
    im, _ = tagline(im, (126, y + 90 + 16 + 63 + 34), "THE OFFICIAL MODPACK", size=44, spacing=17)
    return im

TRAIL = ['TTTT', 'UUU', 'VV', 'X']

def contrail(im, x0, y0, x1, cell, head=True):
    """A pixel contrail from x1 (old, faint, wide) to x0+... drawn left to right, ending in a missile head at x1."""
    d = ImageDraw.Draw(im)
    n = (x1 - x0) // cell
    for i in range(n):
        f = i / max(1, n - 1)
        c = rgb('X') if f < .3 else rgb('V') if f < .55 else rgb('U') if f < .8 else rgb('T')
        w = 3 if f < .3 else 2 if f < .7 else 1
        for k in range(w):
            y = y0 - k * cell + (cell if w == 3 else 0)
            d.rectangle([x0 + i * cell, y, x0 + (i + 1) * cell - 1, y + cell - 1], fill=c)
    if head:
        hx = x0 + n * cell
        spr = pixels(["xy...", "xyYYY", ".YYYD"], cell, {k: rgb(k) for k in 'xyYD'})
        im.alpha_composite(spr, (hx - cell, y0 - cell))
    return im

MISSILE = ["XXVVUUTTyx.....", ".XXVVUUTTxyYYYD", "XXVVUUTTyx....."]   # a cruise missile and its trail, 15×3

def banner_c(frame, cx, cy, zoom=1.0):
    im = shade(crop(F(frame), 1920, 640, cx, cy, zoom), strength=0.62, reach=0.55, side='right')
    wm = render("OPEN SKIES", 11)
    x = 1920 - 120 - wm.width
    im = with_shadow(im, wm, (x, 150))
    glyph = pixels(MISSILE, 8, {k: rgb(k) for k in 'XVUTyxYD'})
    im = with_shadow(im, glyph, (x + 6, 150 + 99 + 40), blur=3, off=(2, 3))
    im, _ = tagline(im, (x + 6 + glyph.width + 22, 150 + 99 + 30), "INCOMING · CREATE · AIRCRAFT", size=40, spacing=9)
    return im

def brackets(im, box, cell, colour, arm=4):
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        for i in range(arm):
            for (px, py) in ((x + sx * i * cell, y), (x, y + sy * i * cell)):
                a, b = (px, py) if sx > 0 else (px - cell, py), None
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
    im, _ = tagline(im, (x + 8, y + wm.height + 72), "STRIKE FAR WITH INCOMING", size=44, spacing=15,
                    fill=(200, 255, 200))
    return im

# ---------------------------------------------------------------- feature strips

def strip(tiles, out, style):
    """tiles: (frame, cx, cy, TITLE, subtitle, weight). Widths by weight over 1920; label bar by style."""
    W, TH, LH = 1920, 400, 132
    total = sum(t[5] for t in tiles)
    bar = {'a': NAVY, 'b': (20, 34, 58), 'c': NAVY, 'd': (16, 20, 16)}[style]
    im = Image.new('RGBA', (W, TH + LH), bar + (255,))
    d = ImageDraw.Draw(im)
    x = 0
    for i, t in enumerate(tiles):
        fr, cx, cy, title, sub, wgt = t[:6]
        w = round(W * wgt / total) if i < len(tiles) - 1 else W - x
        im.paste(crop(F(fr), w, TH, cx, cy, zoom=t[6] if len(t) > 6 else 1.0), (x, 0))
        tc = (200, 255, 200) if style == 'd' else CREAM
        if style == 'b' and i == 0:
            im.alpha_composite(mini_icon(2), (x + 18, TH - 64 - 18))
        if style == 'd':
            brackets(im, (x + 24, 24, x + w - 24, TH - 24), 4, GREEN + (230,), arm=6)
        spaced(d, (x, TH + 22), title, font(46), 9, tc, w)
        spaced(d, (x, TH + 80), sub, font(28), 2, (176, 170, 190), w)
        if i:
            d.line([(x, TH + 24), (x, TH + LH - 24)], fill=(60, 62, 92), width=2)
        x += w
    if style == 'c':
        im.alpha_composite(pixels(MISSILE, 4, {k: rgb(k) for k in 'XVUTyxYD'}), (24, TH + 36))
    save(im, out)

# ---------------------------------------------------------------- per variant

def store(frame_banner, bc, frame_icon, ic, zoom, outdir, bzoom=1.0):
    save(crop(F(frame_banner), 1920, 640, *bc, zoom=bzoom), os.path.join(outdir, 'store-banner.jpg'))
    icon = crop(F(frame_icon), 512, 512, *ic, zoom=zoom)
    save(icon, os.path.join(outdir, 'store-icon.png'))

VARIANTS = {}

def variant(fn):
    VARIANTS[fn.__name__] = fn
    return fn

# Frames: hero = airship at dusk with an Incoming nuke behind it; trails = a cruise-missile salvo's trails over the
# valley; designator = the view through the Strike Designator; plus the 1.0.0 gallery frames.
FRAMES = dict(hero='inc-blast-wave-dusk-hq.jpg', trails='inc-still-4.jpg', designator='strike.jpg', day='inc-still-2.jpg', aim='inc-still-3.jpg',
              ship='airship.jpg', jungle='jungle-village.jpg', valley='valley-dusk.jpg')
POS = {}   # frame → (cx, cy) for the banner crop, (cx, cy, zoom) for the store icon; set in frames.py

def tiles_default(first):
    return [first,
            (FRAMES['ship'], 960, 540, "FLY", "Create airships and aircraft", 1),
            (FRAMES['jungle'], 900, 560, "EXPLORE", "Towns, dungeons and temples", 1),
            (FRAMES['valley'], 1450, 320, "SEE FAR", "Voxy distance and shaders", 1)]

@variant
def a_strike_sky(o):
    p = POS['hero']
    save(banner_a(FRAMES['hero'], *p['banner'], p.get('zoom', 1.0)), os.path.join(o, 'banner.jpg'))
    store(FRAMES['hero'], p['banner'], FRAMES['hero'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['hero'], *p['strip'], "STRIKE", "Incoming: drones to nukes", 2, 1.5)), os.path.join(o, 'strip.jpg'), 'a')

@variant
def b_open_sky(o):
    p = POS['day']
    save(banner_b(FRAMES['day'], *p['banner'], p.get('zoom', 1.0)), os.path.join(o, 'banner.jpg'))
    store(FRAMES['day'], p['banner'], FRAMES['day'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['day'], *p['strip'], "INCOMING", "Air strikes and nukes", 2)), os.path.join(o, 'strip.jpg'), 'b')

@variant
def c_contrail(o):
    p = POS['trails']
    save(banner_c(FRAMES['trails'], *p['banner'], p.get('zoom', 1.0)), os.path.join(o, 'banner.jpg'))
    store(FRAMES['trails'], p['banner'], FRAMES['trails'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['trails'], *p['strip'], "STRIKE", "Incoming: drones to ICBMs", 2)), os.path.join(o, 'strip.jpg'), 'c')

@variant
def d_designator(o):
    p = POS['designator']
    save(banner_d(FRAMES['designator'], *p['banner'], p.get('zoom', 1.0), p.get('target')), os.path.join(o, 'banner.jpg'))
    store(FRAMES['designator'], p['banner'], FRAMES['designator'], p['icon'][:2], p['icon'][2], o, p.get('zoom', 1.0))
    strip(tiles_default((FRAMES['aim'], *POS['aim']['strip'], "AIM AND STRIKE", "Incoming's Strike Designator", 2)),
          os.path.join(o, 'strip.jpg'), 'd')

if __name__ == '__main__':
    import json
    POS.update(json.load(open(os.path.join(FR, 'positions.json'))))
    names = {'a_strike_sky': 'a-strike-sky', 'b_open_sky': 'b-open-sky', 'c_contrail': 'c-contrail',
             'd_designator': 'd-designator'}
    only = sys.argv[3:]
    for k, fn in VARIANTS.items():
        if not only or k in only:
            fn(os.path.join(OUT, names[k]))
