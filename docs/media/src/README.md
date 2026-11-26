# How the images were made

No image generator was used: every picture is an in-game frame, or pixel art placed cell by cell in code written with
AI assistance (Claude). Store pages use only the in-game frames (`icon-ingame.png`, `banner-store.jpg`, the gallery):
docs/store/README.md.

- **Icon** ([icon.py](icon.py)): a 32×32 grid of palette letters, Incoming's icon palette (night sky, dark ground,
  embers), an airship and a small mushroom cloud on the horizon; scaled with nearest neighbour to 512 and 400.
  `python3 icon.py ../icon.png`.
- **Wordmark** ([wordmark.py](wordmark.py)): OPEN SKIES in Incoming's pixel letterforms (9 rows, strokes 2 cells,
  gaps 2 cells; O, N, I, E as in INCOMING).
- **Banner** ([banner.py](banner.py)): Incoming's banner layout (wordmark at x 120, letter-spaced tagline in Barlow
  Condensed SemiBold, SIL OFL 1.1) over a 3:1 crop of an in-game frame, with a navy shade on the left.
- **Strip** ([features.py](features.py)): four crops of gallery frames with labels.
- **Store images** (in-game frames only, docs/store/README.md): `icon-ingame.png` is a 860×860 crop of the airship
  frame scaled to 512 and 400; `banner-store.jpg` is the banner's frame cropped to 1920×640 (rows 250–890) with no
  wordmark, tagline or shade.
- **Frames** (`../gallery`, the banner, the strip): the pack itself (1.0.0) installed with `tools/boot_check.py` on a
  machine without a GPU, Mesa llvmpipe (`MESA_GL_VERSION_OVERRIDE=4.6` for Voxy), 1920×1080, Complementary Unbound
  with Euphoria Patches, HUD hidden (F1), F2 screenshots. A fresh world (seed `open-skies`), pre-generated with
  Chunky and imported into Voxy (`/voxy import world`). Scenes were set with commands: time 12300, the airship
  from [airship.py](airship.py) (Create Aeronautics blocks with levitite, assembled by `/sable assemble area`, turned
  with `/sable teleport`, held with `/tick freeze`), a biplane `/summon immersive_aircraft:biplane … {NoGravity:1b}`,
  and the strike `/incoming salvo missile 3 10 at 192 -752` at `/tick rate 5` so the frames catch the fireball.
