# 1:1 Silo complex on Zearth: site search

Read-only search on the cached Project Zearth terrain (`site5/terrain3.npz`, pre-build golden; regions not re-read).
Layout: the show's canon layout (`tools/silo/canon_layout.json`, branch `claude/project-thread-y7hwdt` @ 3054f2c)
with `edge_m` 270 instead of 156, which puts 50 silos about 2.3-3.1 km apart end to end.

Run: `site_fit.py <golden Project Zearth/world> <out> --canon canon270.json --spacing 270 --rots 0,350 --min-y -768 --height 1088`
with the default `--berm 70 --clear 200 --max-builds 12 --shaft 64`. The crater and plain around each silo stay 1:1,
so only the spacing changes. With the radii scaled ×1.73 (`--berm 121 --clear 346 --max-builds 21`) every placement gets
more conflicts (best: 5), so those numbers are not used.

`site_fit.py` reported at least 4 conflicts for every placement. Its centre grid also stops 1 km short of the map edge.
`score.py` re-ranks every centre (32 m grid, 4° rotations) by conflict count, then cost (10 × water + relief).
It keeps only placements where every silo ±(200 m plain + 100 m blend) lies inside the generated area
x -2816..4799, z -4608..3071. The top 3 are at least 1.5 km apart.
No placement anywhere on the map is conflict-free: the minimum is 3 silos.

| # | Silo 1 shaft (x, z) | rot | water (berm discs) | relief sd | silos on water | extent x × z | margin to edge | conflicts (unfixable by ≤56 m shift) |
|---|---|---|---|---|---|---|---|---|
| 1 | 1488, -3056 | 152° | 63 % | 5.1 m | 32/50 | 2775 × 2227 m | 65 m | 4: Silo 27 by a town (1011 builds), 44 buried structure, 45 (24 builds); 50 (16 builds) moves 8,8. Unfixable: 27, 44, 45 |
| 2 | 3248, -2800 | 128° | 39 % | 7.4 m | 17/50 | 2255 × 2632 m | 213 m | 4: 13 (25 builds), 20 buried, 29 (30 builds), 44 buried; 20 and 29 move ≤34 m. Unfixable: 13, 44 |
| 3 | 1872, 1712 | 180° | 90 % | 1.1 m | 46/50 | 3117 × 2114 m | 18 m | 7: 2 (55 builds), 3/14/46 buried, 4/6/17 small builds; all but Silo 2 move ≤51 m. Unfixable: 2 |

Ruled out: the whole central island (x -2000..3500, z -1500..1000) is the city (thousands of builds),
so every field there conflicts. With the plain and blend added, a 2.2-3.1 km field fits only near the edges;
anything closer than about 300 m to the edge fails the bounds check. The other placements with 3-4 conflicts are
neighbours of pick 1 or 2. Pick 3 is almost all sea (the plain would fill ~90 % of the berm discs), next to the current site.

Fit to bounds: all three fields, plain and blend included, stay inside the generated area (margins above).
Pick 1 and pick 3 are tight (65 m and 18 m).

Current site (edge 156, site5): Silo 1 at 3832, 1848, rot 0, water 49 %, relief sd 5.2, extent 1898 × 1248 m.

`zearth-sites.png`: picks 1-3 (yellow, orange, purple) and the current site C (white); red dots = conflicting silos,
outline = silos + 200 m plain, square = Silo 1. `placements.json`: every silo of each pick, its conflict and a shift if
one exists. Tunnel bearings per silo come from `tunnels.assign`; worst tunnel clearance 106-110 m.
