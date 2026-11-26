"""OPEN SKIES pixel wordmark in Incoming's letterforms (9 rows, 2-cell strokes, 2-cell gaps). Cells placed one by one in code, written with AI assistance.

python3 wordmark.py out.png CELL [#rrggbb]"""
import sys
from PIL import Image
G = {
'O': [".#####.","#######","##...##","##...##","##...##","##...##","##...##","#######",".#####."],
'P': ["######.","#######","##...##","##...##","#######","######.","##.....","##.....","##....."],
'E': [".######","#######","##.....","##.....","######.","######.","##.....","#######",".######"],
'N': ["##...##","###..##","###..##","####.##","##.####","##..###","##..###","##...##","##...##"],
'S': [".######","#######","##.....","######.",".######",".....##",".....##","#######","######."],
'K': ["##...##","##..###","##.###.","#####..","####...","#####..","##.###.","##..###","##...##"],
'I': ["##"]*9,
}
def cells(text, gap=2, space=5):
    cols = []
    for i, ch in enumerate(text):
        if ch == ' ':
            cols += [[0]*9] * (space - gap); continue
        g = G[ch]
        for x in range(len(g[0])): cols.append([1 if g[y][x] == '#' else 0 for y in range(9)])
        if i < len(text) - 1 and text[i+1] != ' ': cols += [[0]*9] * gap
        elif i < len(text) - 1: cols += [[0]*9] * gap
    return cols
def render(text, cell, color=(238, 229, 214, 255)):
    cols = cells(text)
    img = Image.new('RGBA', (len(cols) * cell, 9 * cell), (0, 0, 0, 0))
    for x, col in enumerate(cols):
        for y, on in enumerate(col):
            if on: img.paste(color, (x*cell, y*cell, (x+1)*cell, (y+1)*cell))
    return img
if __name__ == '__main__':
    c = tuple(int(sys.argv[3][i:i+2], 16) for i in (1,3,5)) + (255,) if len(sys.argv) > 3 else (238, 229, 214, 255)
    render("OPEN SKIES", int(sys.argv[2]), c).save(sys.argv[1])
