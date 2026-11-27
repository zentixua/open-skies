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
LIT_SHIP = [
    "....KKKKKKKK....",
    "..KKGFFEEEEyyK.K",
    ".KHGFFEEEEEEyyKK",
    "KHGGFFFEEEEEEyyK",
    "KRRRRROOOOOOOOxK",
    "KHHGGGFFFFEEEyyK",
    ".KHHGGGFFFFEEyKK",
    "..KKHHGGGFFEKK.K",
    "....KKKKKKKK....",
    ".....K....K.....",
    ".....KnynynK....",
    "......KKKKK.....",
]

def variant_a():
    """Strike Sky: Incoming's mushroom cloud, the pack's airship in front of it, lit by the blast."""
    g = grid(INC)
    stamp(g, LIT_SHIP, 0, 13)
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

def variant_c():
    """Contrail: an Incoming cruise missile dives out of the dusk sky, its trail drawn across the icon."""
    g = grid(INC)
    # remove the mushroom: every cell above the ground takes its row's sky colour
    sky = {y: 'e' for y in range(15)}
    sky.update({15: 'g', 16: 'g', 17: 'g', 18: 'h', 19: 'h', 20: 'h', 21: 'i', 22: 'i', 23: 'm', 24: 'm'})
    for y in range(25):
        g[y] = [sky[y]] * 32
    g[25] = list('pppppppppppppppppppppppppppppppp')
    g[26] = list('ppoppppppppppppppppppppppppopppp')
    for y in range(27, 32):
        g[y] = ['a'] * 32
    # a village on the horizon (dark roofs, lit windows) where the missile is heading
    stamp(g, ["..cc....cc...", ".cccc..cccc..", "ccccccccccccc", "cyccccycccycc"], 17, 24)
    # trail: quadratic Bézier from off the top left to the head; older = wider and fainter
    P0, P1, P2 = (-2, 3), (13, 1), (20, 18)
    pts = []
    for i in range(400):
        t = i / 399
        x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0]
        y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]
        pts.append((t, x, y))
    for t, x, y in pts:
        w = 1.9 - 1.1 * t
        c = 'X' if t < 0.25 else 'V' if t < 0.5 else 'U' if t < 0.78 else 'T'
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= w * w:
                    xi, yi = round(x + dx), round(y + dy)
                    if 0 <= xi < 32 and 0 <= yi < 32 and g[yi][xi] not in 'TU' or (c == 'T' and 0 <= yi < 32 and 0 <= xi < 32):
                        g[yi][xi] = c
    # missile head and exhaust (Incoming's cruise missile colours: grey body, orange flame)
    stamp(g, ["yx...", "xyx..", ".xUY.", "..YYY", "...YY"], 18, 16)
    # small airship watching from the right
    stamp(g, TINY_SHIP, 21, 4)
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
    for i in range(3, 8):
        g[15][i] = 'Q'; g[15][31 - i] = 'Q'; g[i][15] = 'Q'
        g[16][i] = 'P'; g[16][31 - i] = 'P'; g[i][16] = 'P'
    for (x, y) in [(10, 20), (11, 20), (10, 21), (21, 20), (20, 20), (21, 21),
                   (10, 27), (11, 27), (10, 26), (21, 27), (20, 27), (21, 26)]:
        g[y][x] = 'Q'
    # the red button of the designator, lower right corner
    stamp(g, ["SS", "SS"], 28, 28)
    return g

VARIANTS = {'a-strike-sky': variant_a, 'b-open-sky': variant_b, 'c-contrail': variant_c, 'd-designator': variant_d}

if __name__ == '__main__':
    out = sys.argv[1]
    for name, fn in VARIANTS.items():
        os.makedirs(os.path.join(out, name), exist_ok=True)
        save_icon(fn(), os.path.join(out, name, 'icon.png'))
