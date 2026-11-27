"""Banners, feature strips and store images for the brand variants, composed over in-game frames.

Text: pixel wordmarks (wordmark.py) and Barlow Condensed (SIL OFL 1.1, Incoming's tagline typeface). Pixel ornaments
(reticle brackets, contrail, badge icon) are cells placed in code. Store images (store-icon.png, store-banner.jpg)
are in-game frames only: crops, no text or drawing (Modrinth rule 6.2, docs/store/README.md)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from wordmark import render

FONTS = os.environ.get('BRAND_FONTS', os.path.join(os.path.dirname(__file__), 'fonts'))
CREAM = (238, 229, 214)
NAVY = (24, 28, 48)

def font(size, bold=False):
    return ImageFont.truetype(os.path.join(FONTS, 'BarlowCondensed-Bold.ttf' if bold else 'BarlowCondensed-SemiBold.ttf'), size)

def spaced(d, xy, text, f, spacing, fill, center_w=None):
    w = sum(d.textlength(c, font=f) + spacing for c in text) - spacing
    x, y = xy
    if center_w:
        x += (center_w - w) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing
    return x

def crop(frame, W, H, cx=None, cy=None, zoom=1.0):
    """Scale the frame so W×H at the given zoom fits, crop around (cx, cy) in frame pixels."""
    im = Image.open(frame).convert('RGB')
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    cx = im.width / 2 if cx is None else cx * s
    cy = im.height / 2 if cy is None else cy * s
    x = int(max(0, min(im.width - W, cx - W / 2)))
    y = int(max(0, min(im.height - H, cy - H / 2)))
    return im.crop((x, y, x + W, y + H))

def shade(im, colour=(22, 28, 52), strength=0.62, reach=0.58, side='left'):
    W, H = im.size
    g = Image.new('RGBA', (W, H))
    px = g.load()
    for x in range(W):
        f = x / (W * reach) if side == 'left' else (W - x) / (W * reach)
        a = int(255 * max(0.0, 1 - f) ** 1.6 * strength)
        for y in range(H):
            px[x, y] = colour + (a,)
    return Image.alpha_composite(im.convert('RGBA'), g)

def with_shadow(im, layer, xy, blur=7, off=(6, 8), alpha=150):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (xy[0] + off[0], xy[1] + off[1]), layer)
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(blur)))
    im.alpha_composite(layer, xy)
    return im

def tagline(im, xy, text, size=44, spacing=17, fill=CREAM):
    tl = Image.new('RGBA', im.size, (0, 0, 0, 0))
    spaced(ImageDraw.Draw(tl), (xy[0] + 2, xy[1] + 3), text, font(size), spacing, (0, 0, 0, 170))
    im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(3)))
    end = spaced(ImageDraw.Draw(im), xy, text, font(size), spacing, fill + (255,))
    return im, end

def pixels(rows, cell, pal):
    """A small pixel sprite (rows of palette keys, '.' transparent) at cell size."""
    img = Image.new('RGBA', (len(rows[0]) * cell, len(rows) * cell), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != '.':
                img.paste(pal[c], (x * cell, y * cell, (x + 1) * cell, (y + 1) * cell))
    return img

def save(im, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im = im.convert('RGB')
    if out.endswith('.png'):
        im.save(out)
    else:
        im.save(out, quality=92, subsampling=0)
