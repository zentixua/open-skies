# Silo complex at 1:1 (Artem's decision, 12.11.2026)

Artem, 12.11 19:49: "full 1:1 scale, no exceptions"; 20:18 approved this proposal: "start, I'm waiting for full readiness".
Every size below names its source. Measurements and frame lists: `canon/official-layout.md` (production material) and
the project's scale review. Where no source exists, it says so. Frame and video ids: BFDG = "Designing the Silo"
featurette, ew = "Extending worlds" (S2 sets), t = seconds into the video.

## 1. Surface (each of the 50 rings)
| Item | 1:1 | Was | Source |
|---|---|---|---|
| Bowl floor | Ø110 | Ø60 | S3E09 frame 05: people at the far berm 1.7 m = 27 px, frame width there ≈120 m, floor runs past both edges (±25 %) |
| Berm crest | Ø≈155 | Ø84 | floor/crest 0.71 (our profile), crest/path 0.70 (S3E09 aerials 01, 03) |
| Berm height over the floor | ≈4 | 4 | S3E09 frame 10: person on the crest 24 px, slope ≈70 px (±30 %); unchanged |
| Outer path | Ø≈220, 3 wide | Ø128 | crest/path 0.70; width: two people walk side by side, frame 05 |
| Ring spacing | ≈270 | 156 | path/spacing 0.82 (canon fit), agrees with the fan plan's 265 |
| Exit and camera block | inside the bowl, 0–½ radius from the centre, each ring its own side; block ≈4.4×2.4 m | at the crater edge, 115 from the shaft | S3E09 aerials ×4 and the outside shots (`frames/entrance-check/`), frames 05–07 |
| Berm gaps | on some rings, where the path comes in | none | aerials ×4 |

Cross-check with frame 10 (stair to crest): ≈35–57 m depending on the lens. With the exit at 0–½ radius that is a
crest Ø≈100–160: consistent with frame 05, not more precise.

## 2. Shaft
| Item | 1:1 | Was | Source |
|---|---|---|---|
| Shaft axis | at the ring centre | 115 from the ring centre | construction S3E07 #2, S3E08 #8: the bore in the middle of a round pit |
| Outer wall | Ø≈120 (110–140) | Ø92 | no number anywhere; the shaft lies under the whole bowl floor (from the construction frames) |
| Open atrium | Ø≈40 (35–48) | Ø34 | BFDG set plan t2014s: gallery ≈1/6 radius, gallery 3–4 m by a person |
| Stair core | Ø≈8, stair round a solid core, flight 2 wide | stair in the atrium | plan t2014s: core ≈1/5 of the atrium; flight 1.8–2 m by a person |
| Gallery street | 4 wide, columns along the edge, parapet 1.1 | ring corridor | t2163s (set), person 1.7 m |
| Bridges | two radial, ≈135° apart | one | plan t2014s |
| Top | dome with oval coffers over the atrium | slab | BFDG t2240s "dome at top of SHAFT" |
| Behind the gallery | two-storey facades, alleys 3–5 wide, flat modules to the wall (≈36 blocks deep) | room maze 26 blocks | BFDG t1923s, t3452s, S2 ew t0600–t0676 |

## 3. Levels and depth
- **6 blocks per level**: gallery floor 1, lower facade storey 3 (door 2), upper storey 2. Source: the shaft set stood in a
  12.2 m stage and held two levels (BFDG 28:10, Gold Derby 3:21).
- One conflict: the same people say "a mile deep" (≈11 per level). Everything on screen is built to 6. We take 6: 1:1
  to what is on screen.
- 144 levels: level 1 ≈ y 50, level 144 ≈ −808, bottom (machine hall, slab, digger cave) ≈ −885.
- Datapack: `min_y −896`, `height 1216` (was −768/1088, +12 %). Vanilla limit −2032/4064.
- Level assignment (IT 19, medical 50 and 62, farms 80 and 122 etc.) stays from the wiki, as in the current build.

## 4. Halls
| Hall | 1:1 | Source |
|---|---|---|
| Level 1 cafeteria | its own round hall Ø≈28 behind the gallery, ceiling 5, no columns; the "flower" with a lamp over the middle; curved screen on the far wall opposite the oval portal; steps down; serving counter between two entrances | BFDG t2338s, t2375s, 39:19, 40:34; RU wiki |
| Sheriff's office | round office, cells on the same floor, entered through the cafeteria | BFDG 44:08; EN wiki |
| Holding cell 3 → airlock → ramp | airlock door ≈2.4; ramp with a ribbed floor up to a slot with steps | BFDG 46:23; S1E02 #25, #27; S3E09 #77 |
| Lower cafeterias | with columns | BFDG 43:55 |
| IT (level 19) | curved blue corridors with wooden doors; Bernard's office rectangular, 2 columns | S2 ew t986s–t1072s; Valette qek8GD |
| Server room | round, stepped racks along the wall, ring light, a dais | S2 ew t1126s |
| Vault | round door from the fan room, tall library with spiral stairs | S2 ew t1080s–t1230s |
| Farms | one tall storey (≈7–8) the full width, behind a ring of columns | Valette 1x3gyL; Gold Derby 8:25 |
| Generator room | round hall, generator in the middle, catwalks over pits, control desk behind glass | Valette QXD6Yr; LRM 9:16 |

Artem, 12.11 20:16: the "Algorithm" Bernard talks to through the server-room console is the voice of Silo 1's staff.
So the Silo 18 server-room console and Silo 1's operator side belong together (S2/S3): Silo 1 has the operator room
on the other end of that line.

## 5. The way in
The airlock is at the edge of level 1 (behind the holding cell, in the rooms behind the gallery, r≈50–55). Level 1's
floor is ≈13–17 below the bowl floor. The ramp climbs towards the centre over the outer rooms, past the dome, and comes
out as a slot with steps at 0–½ radius. Length ≈30–50. This is our inference: no frame or plan shows the whole tunnel.

## 6. Place on Zearth
At spacing 270 the 50 shafts span 2.3–3.1 km, plus 0.6 km of plain and blend. The old site (3832, 1848) is too small.
Search: `site_fit.py` at edge 270 plus `score.py` (orphan branch `silo-site-1to1`, f203ab4).
**Chosen: pick 2**, Silo 1 at (3248, −2800), rotation 128°: water 39 %, relief sd 7.4 m, extent 2255×2632, 213 m to
the map edge. Conflicts: silo 13 on 25 Zearth build blocks, silo 44 over a buried structure (both cleared by the shaft
and plain); silos 20 and 29 shift ≤34 m. The city is now south of the field, so Atlanta in S3E09 frame 16 lies the
other way. The relief is rougher than the old site: more fill.

## 7. Cost
- Blocks per silo ≈×2–2.4 (area ×1.7–2, depth ×1.19). Build time grows the same.
- Reworked surface ≈×3. Memory per loaded chunk +12 % (world height).
- Silo 1 (the high-tech staff silo) is rebuilt to the same sizes.

## 8. Not in any source
- Shaft diameter in metres (120 from the bowl size, range 110–140).
- Tunnel length and direction, depth of level 1 under the bowl.
- Number and depth of alleys per level; whether every level has them.
- IT hall of 40 desks and the "Algorithm" computer (not shown); the server room's level.
- Relative position of the cafeteria and the sheriff's office on level 1.

## 9. Steps
1. `tools/silo` code: new sizes in `Spec` and `Site`, axis at the ring centre, gallery, two bridges, core, dome, facades,
   cafeteria, the way in.
2. Build on a copy of the Zearth golden at the new site, datapack −896/1216.
3. Check with frames from the show's own viewpoints (bowl, crest, gallery, down the atrium, cafeteria, server room)
   beside the show's frames.
4. New golden. 25567 restarts only on Artem's own line; the old world stays beside it.
