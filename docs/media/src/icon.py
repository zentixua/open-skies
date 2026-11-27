"""Open Skies pixel icon: Incoming's own icon, cell for cell, under an open day sky, with a small airship.

Incoming's 32×32 icon (zentixua/incoming docs/media/icon.png, 16 px cells) is decoded below letter by letter; the pack's
icon keeps its mushroom cloud and ground and repaints the night sky as a day sky with two clouds and an airship. Cells
placed in code written with AI assistance; no image generator.

python3 icon.py ../icon.png  → icon.png (512), icon-400.png (CurseForge avatar)"""
import sys
from PIL import Image

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
PAL = dict(INC_PAL)
PAL.update({
 # the airship (cream envelope, orange band), clouds and the day sky
 'W': '#f6efe2', 'E': '#e6dac6', 'F': '#c8b79e', 'G': '#97836b', 'K': '#221a1e', 'O': '#ee6a1c', 'R': '#b83c14',
 'C': '#f4f1ea', 'D': '#d9dfe6',
 '1': '#2e5f9e', '2': '#3a71b2', '3': '#4a84c2', '4': '#5e97cf', '5': '#78abd9', '6': '#93bfe2', '7': '#b2d2ea',
})
DAY = '1112222333344445555666677777777'   # sky colour per row, top to bottom
SHIP = [   # small airship with an outline, bow left
    "..KKKKK..",
    ".KFEEWWK.",
    "KRROOOOOK",
    ".KGGFFFK.",
    "...KKK...",
]

def stamp(g, sprite, x0, y0):
    """Paint the sprite over sky cells only: Incoming's cloud and ground stay intact."""
    for y, row in enumerate(sprite):
        for x, c in enumerate(row):
            if c != '.' and g[y0 + y][x0 + x] in SKY_CELLS | set(DAY):
                g[y0 + y][x0 + x] = c

def image(g):
    img = Image.new('RGB', (32, 32))
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            img.putpixel((x, y), tuple(int(PAL[c][i:i + 2], 16) for i in (1, 3, 5)))
    return img

def incoming_icon():
    """Incoming's own icon, 32×32 (the badge on the banner)."""
    return image([list(r) for r in INC])

def pack_icon():
    g = [list(r) for r in INC]
    for y in range(32):
        for x in range(32):
            if g[y][x] in SKY_CELLS:
                g[y][x] = DAY[y] if y < len(DAY) else '7'
    stamp(g, ["..CC....", ".CCCCC..", "CCCCCCCD", ".DDDDDD."], 23, 15)
    stamp(g, [".CC..", "CCCCD", ".DDD."], 1, 18)
    stamp(g, SHIP, 0, 1)
    return image(g)

if __name__ == '__main__':
    out = sys.argv[1]
    img = pack_icon()
    img.resize((512, 512), Image.NEAREST).save(out)
    img.resize((400, 400), Image.NEAREST).save(out.replace('.png', '-400.png'))
