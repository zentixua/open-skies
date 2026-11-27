# Brand-set variants (draft, not for main)

Mission pack-brand-2: the owner asked for the pack's look to put Incoming at its centre ("the pack was made for this
mod"). Four complete variants sit here side by side; the owner picks or corrects one, then only that one replaces
`docs/media/` and this folder is removed before merge. Study: [concept.md](concept.md). All at real sizes:
[comparison-sheet.png](comparison-sheet.png).

| Variant | Idea |
|---|---|
| [A · Strike Sky](a-strike-sky) | Incoming's mushroom cloud is the mark; the pack's airship flies in front of it, lit by the blast. Banner: a real Incoming nuke at dusk, "AN INCOMING MODPACK". |
| [B · Official Pack](b-open-sky) | Incoming's own icon under an open day sky; INCOMING / OPEN SKIES lockup with the mod's icon as a badge, "THE OFFICIAL MODPACK" (the Cobblemon Official Modpack model). |
| [C · Contrail](c-contrail) | An Incoming cruise missile dives out of the dusk sky toward a village; its contrail is the brand line. Banner: a real launch, the wordmark on the open sky. |
| [D · Designator](d-designator) | The view through Incoming's Strike Designator: the mushroom in the lens with its green reticle. Banner: the pack's real strike framed as a target, "STRIKE FAR WITH INCOMING". |

Each folder: `icon.png` (512, pixel, GitHub and launcher; `icon-400.png` CurseForge avatar, `icon-64.png`, `icon-32.png`
source), `banner.jpg` (GitHub header 1920×640), `strip.jpg` (feature strip 1920×532), and the store pair from in-game
frames only, with no drawing or text: `store-icon.png` (512) and `store-banner.jpg` (1920×640) (Modrinth rule 6.2,
docs/store/README.md).

## Frames
All frames are real in-game screenshots; no image generator was used. The pack's own (1.0.0 gallery, `../gallery`,
`../banner-store.jpg`): D's banner and store images (`strike.jpg`), and the FLY / EXPLORE / SEE FAR tiles. Incoming's
own media (zentixua/incoming `docs/media`, Incoming in its test world): A (`blast-wave-dusk-hq.jpg`), B (`still-2.jpg`),
C (`still-4.jpg`), D's AIM tile (`still-3.jpg`). A fresh shoot in the pack itself (the airship at dusk with an Incoming
nuke behind it) was started and stopped: the full pack on CPU rendering needs more memory than netcup or the laptop
could spare that day. The chosen variant gets its own frame from the pack when it is finished.

## How they are made
`src/` (Python, Pillow; written with AI assistance): `pix.py` (Incoming's icon decoded cell by cell, palette, sprites),
`icons.py` (the four 32×32 icons), `wordmark.py` (Incoming's letterforms; C, M, G decoded from Incoming's wordmark),
`compose.py` and `build.py` (banners, strips, store crops; Barlow Condensed, SIL OFL 1.1), `sheet.py` (the comparison
sheet). `BRAND_FONTS=<dir with BarlowCondensed-SemiBold.ttf, -Bold.ttf> python3 build.py <frames> ..` with the frames
named in `build.py` and their crop centres in `<frames>/positions.json`.
