"""Open Skies pixel icon: 32x32 hand-placed pixels (palette from Incoming's icon), nearest-neighbour scaled.

python3 icon.py out.png  → out.png (512), out-400.png (CurseForge avatar), out-32.png (the 32×32 source)"""
import sys
from PIL import Image
P = {
 'a':'#1a2240','o':'#1c2443','p':'#1f2645','q':'#252846','r':'#2f2b4a','u':'#43304e','v':'#100e12','z':'#08080b',
 'W':'#f6efe2','E':'#e6dac6','F':'#c8b79e','G':'#97836b','H':'#6a5a4a','K':'#221a1e',
 'h':'#ee6a1c','g':'#b83c14','f':'#7a2310','j':'#ffa640','i':'#ffe2a0','y':'#ffd27a','w':'#ff8a26','x':'#c8461a',
 'n':'#5a3426','t':'#3a2622','m':'#2c1f1d','c':'#261e21','d':'#1b161a','b':'#3b3442','e':'#4a160f',
}
SKY = ['a']*15 + ['o']*3 + ['p']*3 + ['q']*2 + ['r']*2 + ['u']*2 + ['v'] + ['z']*4
SHIP = {  # '.' = sky
 2: ".KK..........KKKKKKKK...........",
 3: ".KEK......KKKEEEWWWWWKKKK.......",
 4: ".KFEK..KKKEEEEEEWWWWWWWWWKK.....",
 5: "..KFEKKFFEEEEEEEEEEWWWWWWWWK....",
 6: "..KGFFFFFFFEEEEEEEEEEEEEWWWWWK..",
 7: "...KGFFFFFFFFEEEEEEEEEEEEEEWWEK.",
 8: "...KGGFFFFFFFFFFFFEEEEEEEEEEEEK.",
 9: "...KfggggggggghhhhhhhhhhhhhhhhK.",
10: "...KHGGGGGGFFFFFFFFFFFFFFFFFFFK.",
11: "...KHHGGGGGGGGGGGGFFFFFFFFFFFK..",
12: "..KHHKHHHGGGGGGGGGGGGGGGGGGGK...",
13: ".KHHK.KKKHHHHHHHHHHHHHHHHKKK....",
14: ".KHK.....KKKKKKKKKKKKKKKKK......",
15: ".KK.........d.....d.............",
}
g = [[SKY[y]]*32 for y in range(32)]
for y, row in SHIP.items():
    assert len(row) == 32, (y, len(row))
    for x, c in enumerate(row):
        if c != '.': g[y][x] = c
# panel seams, one shade darker
DARK = {'W':'E','E':'F','F':'G','G':'H','H':'H','h':'g','g':'f','f':'f'}
for y in range(3, 14):
    for x in (11, 21):
        if g[y][x] in DARK: g[y][x] = DARK[g[y][x]]
# gondola, windows lit
for x in range(11, 22): g[16][x] = 'c' if x in (11, 21) else 'n'
for x in (13, 15, 17, 19): g[16][x] = 'y'
for x in range(12, 21): g[17][x] = 't'
for x in range(14, 19): g[18][x] = 'm'
for (x, y, c) in [(9, 15, 'b'), (9, 16, 'd'), (10, 16, 'c'), (9, 17, 'b')]: g[y][x] = c
# a distant strike on the horizon (Incoming): small smoke-capped mushroom cloud
for (x,y,c) in [(26,18,'b'),(27,18,'c'),(28,18,'b'),(25,19,'c'),(26,19,'f'),(27,19,'g'),(28,19,'f'),(29,19,'c'),
                (25,20,'g'),(26,20,'j'),(27,20,'i'),(28,20,'j'),(29,20,'g'),(25,21,'e'),(26,21,'h'),(27,21,'j'),
                (28,21,'h'),(29,21,'e'),(26,22,'e'),(27,22,'g'),(28,22,'e'),(27,23,'n'),(27,24,'n'),
                (25,25,'x'),(26,25,'h'),(27,25,'j'),(28,25,'h'),(29,25,'x')]: g[y][x] = c
# ground: dark, the strike's glow and embers (as in Incoming's icon)
for x in range(23, 31): g[26][x] = 'f'
for x in (24, 27, 30): g[26][x] = 'w'
g[27][25] = 'x'; g[27][29] = 'x'
img = Image.new('RGB', (32, 32))
for y in range(32):
    for x in range(32):
        img.putpixel((x, y), tuple(int(P[g[y][x]][i:i+2], 16) for i in (1, 3, 5)))
out = sys.argv[1]
img.save(out.replace('.png', '-32.png'))
img.resize((512, 512), Image.NEAREST).save(out)
img.resize((400, 400), Image.NEAREST).save(out.replace('.png', '-400.png'))
