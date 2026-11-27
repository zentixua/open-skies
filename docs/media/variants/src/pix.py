"""Shared 32×32 pixel-art helpers for the brand variants: Incoming's icon (decoded cell by cell from its 512 px icon,
16 px per cell), palette and small sprites. Cells are placed in code written with AI assistance; no image generator."""
from PIL import Image

# Incoming's icon, 32×32, its own palette (zentixua/incoming docs/media/icon.png)
INC_PAL = {
 'a':'#08080b','b':'#0d0a0d','c':'#100e12','d':'#1a1214','e':'#1a2240','f':'#1b161a','g':'#1c2443','h':'#1f2645',
 'i':'#252846','j':'#261e21','k':'#2a120e','l':'#2c1f1d','m':'#2f2b4a','n':'#3a2622','o':'#3b3442','p':'#43304e',
 'q':'#4a160f','r':'#5a3426','s':'#7a2310','t':'#b83c14','u':'#c8461a','v':'#ee6a1c','w':'#ff8a26','x':'#ffa640',
 'y':'#ffd27a','z':'#ffe2a0',
}
INC = """
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
eeeeeeeeeeeeooooooooeeeeeeeeeeee
eeeeeeeeeeoojjjjjjjjoeeeeeeeeeee
eeeeeeeeeejjjjjjjjjjjoeeeeeeeeee
eeeeeeeooojjjjjjjjjjjjoooeeeeeee
eeeeeeojjjjjjjjjjjjjjjjjjeeeeeee
eeeeeefffffffqqqqqqqfffffoeeeeee
eeeeeeffqssssttsssttsqqqffeeeeee
eeeeoofqssttvzxvvvvtssssqfooeeee
eeeoffqstttvxzxxzzzvtttsqfffeeee
eeefffqttvvxzzxxzzzxvvtsqfffeeee
eeefffqsstvzzzxzzxvvvvtsqqffeeee
eeeeffqsseeevvxzzxvteeeqqqfeeeee
eeeeeeeeeeeeeekqqqeeeeeeeeeeeeee
eeeeeeeeeeeeeebllreeeeeeeeeeeeee
ggggggggggggggbllrgggggggggggggg
gggggggggggggbbllrgggggggggggggg
gggggggggggggbbllrgggggggggggggg
hhhhhhhhhhhhhbbllrhhhhhhhhhhhhhh
hhhhhhhhhhhhhbbllrhhhhhhhhhhhhhh
hhhhhhhhhhhhhbbllrhhhhhhhhhhhhhh
iiiiiiiiiiiibblllriiiiiiiiiiiiii
iiiiiiiiiiffbblllrfffiiiiiiiiiii
mmmmmmmfmffbbbbllllrffmfmmmmmmmm
mmmmmfffffddddddnnnnnfffffmmmmmm
pppjjjjjjjjjjjjjjjjjjjjjjjjjpppp
ppppsssssssssssssssssssssssppppp
cccwcuccsywsssssssssswycccucwccc
aaaaaaaaaaaaaauaaauaaaaaaaaaaaaa
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
""".split()
SKY_CELLS = set('eghimp')   # Incoming's sky rows (navy to dusk violet)

# the pack's airship (cream envelope, orange band) and a few extra colours
PAL = dict(INC_PAL)
PAL.update({
 'W':'#f6efe2','E':'#e6dac6','F':'#c8b79e','G':'#97836b','H':'#6a5a4a','K':'#221a1e',
 'O':'#ee6a1c','R':'#b83c14',
 # day sky (variant B)
 '1':'#2e5f9e','2':'#3a71b2','3':'#4a84c2','4':'#5e97cf','5':'#78abd9','6':'#93bfe2','7':'#b2d2ea',
 'C':'#f4f1ea','D':'#d9dfe6',
 # contrail (variant C)
 'T':'#f2ece2','U':'#cfc6ba','V':'#9d958f','X':'#6e6874',
 # designator (variant D): its olive body, screen green and reticle green, red button
 'L':'#404a2c','M':'#56623a','N':'#1e221e','P':'#285a32','Q':'#8cff8c','S':'#dc281e','Z':'#181a16','Y':'#3c3e42',
})

def grid(rows=None, fill='e'):
    return [list(r) for r in rows] if rows else [[fill] * 32 for _ in range(32)]

def stamp(g, sprite, x0, y0, transparent='.'):
    for y, row in enumerate(sprite):
        for x, c in enumerate(row):
            if c != transparent and 0 <= y0 + y < 32 and 0 <= x0 + x < 32:
                g[y0 + y][x0 + x] = c

def image(g, size=None):
    img = Image.new('RGB', (len(g[0]), len(g)))
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            img.putpixel((x, y), tuple(int(PAL[c][i:i + 2], 16) for i in (1, 3, 5)))
    return img.resize((size, size), Image.NEAREST) if size else img

def save_icon(g, out):
    """out.png (512), out-400.png (CurseForge avatar), out-64.png (launcher size), out-32.png (source)"""
    img = image(g)
    img.save(out.replace('.png', '-32.png'))
    for s, suf in ((512, ''), (400, '-400'), (64, '-64')):
        img.resize((s, s), Image.NEAREST).save(out.replace('.png', f'{suf}.png'))
