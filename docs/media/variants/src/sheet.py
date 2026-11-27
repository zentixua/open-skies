"""Comparison sheet: the current set and every variant side by side at real sizes.

python3 sheet.py VARIANTS_DIR CURRENT_MEDIA_DIR out.png
Per row: name and idea; launcher tile (the 64 px pixel icon as Prism shows it); store search card (96 px in-game
store icon, as Modrinth lists packs); GitHub README header (banner at 880 px, the README column) and the feature
strip under it. UI fonts: Noto Sans (store card mock), Barlow Condensed (labels)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
from compose import font

VD, CUR, OUT = sys.argv[1:4]
NOTO = '/usr/share/fonts/noto/NotoSans-%s.ttf'
ui = lambda s, b=False: ImageFont.truetype(NOTO % ('Bold' if b else 'Regular'), s)

ROWS = [
    ('now', 'Current set (1.0.0)', 'Airship icon, a biplane over a smoke column; Incoming is one strip tile.',
     dict(icon=os.path.join(CUR, 'icon.png'), store=os.path.join(CUR, 'icon-ingame.png'),
          banner=os.path.join(CUR, 'banner.jpg'), strip=os.path.join(CUR, 'features.jpg'))),
    ('a-strike-sky', 'A · Strike Sky', "Incoming's mushroom cloud is the mark; the pack's airship flies in front of it. "
     'Banner: a real Incoming nuke at dusk. "An Incoming modpack".', None),
    ('b-open-sky', 'B · Official Pack', "Incoming's own icon under an open day sky; INCOMING + OPEN SKIES lockup with "
     'the mod\'s badge. "The official Incoming modpack" (Cobblemon model).', None),
    ('c-contrail', 'C · Contrail', 'An Incoming cruise missile dives out of the dusk sky; its contrail is the brand '
     'line. Banner: a real launch, wordmark on the open sky.', None),
    ('d-designator', 'D · Designator', "The view through Incoming's Strike Designator: the mushroom in the lens, green "
     'reticle. Banner: the pack\'s real strike framed as a target.', None),
]

BG, CARD, TEXT, MUTED = (22, 24, 28), (38, 41, 48), (236, 236, 240), (160, 164, 176)
W, ROW_H, PAD = 1880, 600, 28
BW = 880
sheet = Image.new('RGB', (W, 90 + ROW_H * len(ROWS)), BG)
d = ImageDraw.Draw(sheet)
d.text((PAD, 24), 'Open Skies brand variants — real sizes: 64 px launcher icon, 96 px store card icon, 880 px GitHub '
       'README header + feature strip', font=ui(22, True), fill=TEXT)

def rounded(img, r):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], r, fill=255)
    out = Image.new('RGBA', img.size)
    out.paste(img.convert('RGBA'), (0, 0), m)
    return out

for i, (key, name, idea, files) in enumerate(ROWS):
    y = 90 + i * ROW_H
    if files is None:
        v = os.path.join(VD, key)
        files = dict(icon=os.path.join(v, 'icon.png'), store=os.path.join(v, 'store-icon.png'),
                     banner=os.path.join(v, 'banner.jpg'), strip=os.path.join(v, 'strip.jpg'))
    if i:
        d.line([(PAD, y - 14), (W - PAD, y - 14)], fill=(48, 52, 60), width=2)
    # name and idea
    d.text((PAD, y + 4), name, font=font(40, True), fill=TEXT)
    words, line, ly = idea.split(), '', y + 60
    for wd in words:
        if d.textlength(line + ' ' + wd, font=ui(17)) > 380:
            d.text((PAD, ly), line.strip(), font=ui(17), fill=MUTED); ly += 25; line = ''
        line += ' ' + wd
    d.text((PAD, ly), line.strip(), font=ui(17), fill=MUTED)
    # launcher tile: Prism-like instance tile, 64 px icon
    tx, ty = PAD, y + 230
    d.rounded_rectangle([tx, ty, tx + 120, ty + 112], 8, fill=(44, 47, 56))
    ic = Image.open(files['icon']).convert('RGB').resize((64, 64), Image.NEAREST)
    sheet.paste(ic, (tx + 28, ty + 12))
    d.text((tx + 60, ty + 84), 'Open Skies', font=ui(14), fill=TEXT, anchor='mt')
    d.text((tx + 140, ty + 40), 'launcher\n64 px', font=ui(14), fill=MUTED)
    # store card: Modrinth-like search result
    cx, cy = PAD, y + 370
    d.rounded_rectangle([cx, cy, cx + 420, cy + 130], 14, fill=CARD)
    st = rounded(Image.open(files['store']).convert('RGB').resize((96, 96), Image.LANCZOS), 14)
    sheet.paste(st, (cx + 16, cy + 17), st)
    d.text((cx + 128, cy + 16), 'Open Skies', font=ui(20, True), fill=TEXT)
    d.text((cx + 128 + d.textlength('Open Skies ', font=ui(20, True)), cy + 21), 'by zentixua', font=ui(14), fill=MUTED)
    summ = 'Build airships, explore and defend your world from the air: a Create pack built around Incoming.'
    words, line, ly = summ.split(), '', cy + 50
    for wd in words:
        if d.textlength(line + ' ' + wd, font=ui(14)) > 270:
            d.text((cx + 128, ly), line.strip(), font=ui(14), fill=MUTED); ly += 20; line = ''
        line += ' ' + wd
    d.text((cx + 128, ly), line.strip(), font=ui(14), fill=MUTED)
    d.text((cx + 16, cy + 136), 'store card (in-game icon only), 96 px', font=ui(14), fill=MUTED)
    # GitHub header + strip
    bx = W - PAD - BW
    b = Image.open(files['banner']).convert('RGB').resize((BW, round(BW / 3)), Image.LANCZOS)
    sheet.paste(b, (bx, y))
    s = Image.open(files['strip']).convert('RGB')
    s = s.resize((BW, round(BW * s.height / s.width)), Image.LANCZOS)
    sheet.paste(s, (bx, y + b.height + 8))
    d.text((bx - 16, y + 4), 'GitHub\nheader\n880 px', font=ui(14), fill=MUTED, anchor='ra', align='right')
    # 1:1 icon preview at 192 px between the columns
    big = Image.open(files['icon']).convert('RGB').resize((192, 192), Image.NEAREST)
    sheet.paste(big, (470, y + 20))
    d.text((470 + 96, y + 222), 'pixel icon (GitHub, launcher)', font=ui(13), fill=MUTED, anchor='mt')
    sb = Image.open(files['store']).convert('RGB').resize((192, 192), Image.LANCZOS)
    sheet.paste(sb, (470 + 212, y + 20))
    d.text((470 + 212 + 96, y + 222), 'store icon (in-game frame)', font=ui(13), fill=MUTED, anchor='mt')
sheet.save(OUT)
