"""Pixel wordmarks in Incoming's letterforms (9 rows, 2-cell strokes, 2-cell gaps). O, N, I, E as in OPEN SKIES;
C, M, G decoded cell by cell from Incoming's own INCOMING wordmark. Written with AI assistance; no image generator.

render(text, cell, colour) → RGBA image; text uses the letters below and spaces."""
from PIL import Image
G = {
'O': [".#####.","#######","##...##","##...##","##...##","##...##","##...##","#######",".#####."],
'P': ["######.","#######","##...##","##...##","#######","######.","##.....","##.....","##....."],
'E': [".######","#######","##.....","##.....","######.","######.","##.....","#######",".######"],
'N': ["##...##","###..##","###..##","####.##","##.####","##..###","##..###","##...##","##...##"],
'S': [".######","#######","##.....","######.",".######",".....##",".....##","#######","######."],
'K': ["##...##","##..###","##.###.","#####..","####...","#####..","##.###.","##..###","##...##"],
'I': ["##"]*9,
'C': [".######","#######","##.....","##.....","##.....","##.....","##.....","#######",".######"],
'M': ["##...##","###.###","#######","##.#.##","##...##","##...##","##...##","##...##","##...##"],
'G': [".######","#######","##.....","##.....","##..###","##..###","##...##","#######",".######"],
}

def cells(text, gap=2, space=5):
    cols = []
    for i, ch in enumerate(text):
        if ch == ' ':
            cols += [[0] * 9] * (space - gap)
            continue
        g = G[ch]
        for x in range(len(g[0])):
            cols.append([1 if g[y][x] == '#' else 0 for y in range(9)])
        if i < len(text) - 1:
            cols += [[0] * 9] * gap
    return cols

def render(text, cell, color=(238, 229, 214, 255)):
    cols = cells(text)
    img = Image.new('RGBA', (len(cols) * cell, 9 * cell), (0, 0, 0, 0))
    for x, col in enumerate(cols):
        for y, on in enumerate(col):
            if on:
                img.paste(color, (x * cell, y * cell, (x + 1) * cell, (y + 1) * cell))
    return img
