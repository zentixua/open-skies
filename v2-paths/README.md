# Ground path lines on the live 25567 complex (v2 field, read-only check, 13 Nov 2026)

Read-only scan of the live "Zearth Silo" world (server 2a8f50af, port 25567), checking whether the show's
ground marking lines from `tools/silo/paths.py` survived the v2 field rebuild (5c2ae87). Paths are smooth
sandstone flush with the lawn. The scan reads the saved region files (top ground block per column) and compares
each planned feature's centreline against sandstone on the ground.

## What exists

- **Ring paths round all 50 rings — complete.** 50/50 features, 35000/35000 centreline columns are sandstone.
- **Stubs into each bowl — complete.** 49/49 (Silo 1 has no stub by design, its set runs the path south).
- **Links between neighbouring rings — mostly there, broken where a filled lake crosses.** 29/42 at ≥95%;
  overall 80% of centreline. The short links are the most affected because they are short.
- **Rosettes (seven) — 4 of 7 intact, 3 sit on filled lakes and are largely gone.**
  Intact near Silos 32, 14, and two others; the rosette over (49,48,43), over (31,30,29) and over (12,7,11)
  land on filled water and read 0%, 36%, 46%.
- **Axis road (gate→Silo 1→Silo 2) — laid but with long gaps** (65% N, 64% S).
- **Founders' lines from Silo 1 (W→42, E→25, SW→30, SE→10, N cross) — laid but gappy** (56% overall;
  the N cross paths worst at 31–34%).
- **Silo 1 opening-day south path + apron — present** (apron 88%, path 91%).

## The cause of every gap

One cause: `field.py`'s plain tiler lays a path block only `if ... not filled[a, b]` — it refuses to put
sandstone on a column where the plain filled in a lake (`tools/silo/field.py`, `tile()`). Water inside the
complex hull is filled to grass, but the path never gets written over that fill. Of the planned path columns
that are missing sandstone, **13434 are on filled-lake columns and 0 are on dry land** — every gap lines up
exactly with a former lake crossed by the hull-wide plain. Rings and stubs are near the shafts (dry, raised
bowls) so they are untouched; the long straight founders'/axis/rosette lines cross the old lakes and break there.

## Files

- `complex-overview.png` — colour top-down of the whole complex, ~2 blocks/px, vanilla-style palette, Silo 1 ringed.
- `silo1-closeup.png` — 700×700, 1 block/px around Silo 1 (ring, apron, founders' lines, axis).
- `feature-counts.json` — per-feature hit/total, worst gaps, block under each miss.
