"""The four variants' pixel icons, 32×32 cells placed in code (AI-assisted), scaled with nearest neighbour.

python3 icons.py OUTDIR  → OUTDIR/<variant>/icon.png (512), icon-400.png, icon-64.png, icon-32.png"""
import math, os, sys
from pix import INC, SKY_CELLS, grid, stamp, save_icon

# the pack's airship as a silhouette, bow to the left, fins at the stern (right)
SIL = [
    ".....ccccccc.....c.",
    "...ccccccccccc..cc.",
    "..cccccccccccccccc.",
    ".cccccccccccccccccc",
    "..cccccccccccccccc.",
    "...ccccccccccc..cc.",
    ".....ccccccc.....c.",
    "......c...c........",
    "......ccccc........",
]

def rim(g, sprite, x0, y0, light, hot, hot_from):
    """Blast light on the silhouette: top and right edges facing the fireball."""
    for y, row in enumerate(sprite):
        for x, ch in enumerate(row):
            if ch == '.': continue
            up = y == 0 or sprite[y - 1][x] == '.'
            right = x == len(row) - 1 or row[x + 1] == '.'
            if up or right:
                g[y0 + y][x0 + x] = hot if x0 + x >= hot_from else light

# the pack's airship, bow to the left, lit from the right by the blast (cream envelope, orange band, gondola)
LIT_SHIP = [   # 12×9, bow left, lit from the right by the blast; gondola with lit windows
    "..KKKKKKK.K.",
    ".KGFEEEEyKKK",
    "KGFEEEEEEyyK",
    "KRRROOOOOOxK",
    ".KHGGFFFEyKK",
    "..KKKKKKK.K.",
    "....K..K....",
    "...KnynyK...",
    "....KKKK....",
]

def variant_a():
    """Strike Sky: Incoming's mushroom cloud, the pack's airship in front of it, lit by the blast."""
    g = grid(INC)
    stamp(g, LIT_SHIP, 0, 14)   # clear of the cap and the stem, against the sky
    return g

TINY_SHIP = [   # small cream airship, bow left
    "..FEEWWE..",
    ".GFEEEEWWE",
    "GORRROOOOE",
    ".HGGFFFFF.",
    "....KK....",
]

def variant_b():
    """Open Sky: Incoming's icon unchanged, under a clear day sky; a small airship passes."""
    g = grid(INC)
    day = '1112222333344445555666677777777'
    for y in range(32):
        for x in range(32):
            if g[y][x] in SKY_CELLS:
                g[y][x] = day[y] if y < len(day) else '7'
    stamp(g, ["..CC....", ".CCCCC..", "CCCCCCCD", ".DDDDDD."], 23, 15)
    stamp(g, [".CC..", "CCCCD", ".DDD."], 1, 18)
    stamp(g, TINY_SHIP, 1, 1)
    return g


def variant_d():
    """Designator: Incoming's mushroom seen through the Strike Designator's lens, its green reticle on target."""
    g = grid(INC)
    cx, cy, r = 15.5, 15.5, 14.2
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - cx, y - cy)
            if d > r + 1.3:
                g[y][x] = 'Z'
            elif d > r:
                g[y][x] = 'M' if (x + y) % 7 else 'L'
    # reticle ticks from the lens edge inward, and corner brackets on the target (ground zero)
    for i in range(3, 8):     # side ticks only: a top tick would cut through the fireball
        g[15][i] = 'Q'; g[15][31 - i] = 'Q'
        g[16][i] = 'P'; g[16][31 - i] = 'P'
    for (x, y) in [(10, 20), (11, 20), (10, 21), (21, 20), (20, 20), (21, 21),
                   (10, 27), (11, 27), (10, 26), (21, 27), (20, 27), (21, 26)]:
        g[y][x] = 'Q'
    return g

VARIANTS = {'a-strike-sky': variant_a, 'b-open-sky': variant_b, 'd-designator': variant_d}

if __name__ == '__main__':
    out = sys.argv[1]
    for name, fn in VARIANTS.items():
        os.makedirs(os.path.join(out, name), exist_ok=True)
        save_icon(fn(), os.path.join(out, name, 'icon.png'))
