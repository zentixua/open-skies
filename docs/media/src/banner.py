"""Open Skies banner (GitHub header, 1920×640): Incoming's icon and INCOMING in its ember over OPEN SKIES, tagline
"THE OFFICIAL INCOMING MODPACK", on a navy shade over an in-game frame of an Incoming strike under a day sky.

python3 banner.py FRAME CX CY ZOOM out.jpg
docs/media/banner.jpg: Incoming's still-2.jpg (zentixua/incoming docs/media, a cruise missile strike on a power
plant), CX 860, CY 250, ZOOM 1.12."""
import sys
from PIL import Image
from compose import crop, shade, with_shadow, tagline, save
from wordmark import render
from icon import incoming_icon

EMBER = (255, 166, 64)

def banner(frame, cx, cy, zoom):
    im = shade(crop(frame, 1920, 640, cx, cy, zoom), strength=0.95, reach=0.7)
    y = 150
    badge = incoming_icon().resize((96, 96), Image.NEAREST).convert('RGBA')
    im = with_shadow(im, badge, (120, y), blur=8)
    top = render("INCOMING", 6, EMBER + (255,))            # 360×54: Incoming's wordmark in its ember
    im = with_shadow(im, top, (240, y + 21), blur=3, off=(2, 3), alpha=200)
    wm = render("OPEN SKIES", 11)                          # the pack's name: the main line
    im = with_shadow(im, wm, (120, y + 96 + 22))
    im, _ = tagline(im, (128, y + 96 + 22 + 99 + 28), "THE OFFICIAL INCOMING MODPACK", size=40, spacing=14)
    return im

if __name__ == '__main__':
    f, cx, cy, zoom, out = sys.argv[1:6]
    save(banner(f, float(cx), float(cy), float(zoom)), out)
