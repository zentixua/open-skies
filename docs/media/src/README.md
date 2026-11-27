# How the images were made

No image generator was used: every picture is an in-game frame, or pixel art placed cell by cell in code written with
AI assistance (Claude). Store pages use only the in-game frames (`icon-ingame.png`, `banner-store.jpg`, the gallery):
docs/store/README.md.

The look puts Incoming at the centre: the pack exists for it. The pixel icon is Incoming's own icon under an open day
sky, and the banner presents the pack as the official Incoming modpack in Incoming's letters (the way Cobblemon's
official modpack carries the mod's mark).

- **Icon** ([icon.py](icon.py)): Incoming's 32×32 icon (its `docs/media/icon.png`, decoded cell by cell), its night sky
  repainted as a day sky with two clouds and a small airship; scaled with nearest neighbour to 512 and 400.
  `python3 icon.py ../icon.png`.
- **Wordmark** ([wordmark.py](wordmark.py)): Incoming's pixel letterforms (9 rows, strokes 2 cells, gaps 2 cells); C, M
  and G decoded from Incoming's INCOMING wordmark, so both names use the same letters.
- **Banner** ([banner.py](banner.py)): Incoming's icon and INCOMING in its ember over OPEN SKIES, tagline "THE OFFICIAL
  INCOMING MODPACK" in Barlow Condensed SemiBold (SIL OFL 1.1), on a navy shade over an in-game frame of an Incoming
  cruise missile strike under a day sky: `still-2.jpg` from Incoming's own media
  ([zentixua/incoming docs/media](https://github.com/zentixua/incoming/tree/main/docs/media)), taken in Incoming's test
  world. `python3 banner.py still-2.jpg 860 250 1.12 ../banner.jpg`.
- **Strip** ([features.py](features.py)): Incoming first and twice as wide (the same `still-2.jpg`), then three gallery
  frames: `python3 features.py ../features.jpg 'still-2.jpg|1150|400|INCOMING|Air strikes and nukes|2|1.3'
  '../gallery/airship.jpg|960|540|FLY|Create airships and aircraft'
  '../gallery/jungle-village.jpg|900|560|EXPLORE|Towns, dungeons and temples'
  '../gallery/airship-valley.jpg|1574|480|SEE FAR|Voxy distance and shaders|1|1.5'`.
- **Store images** ([store.py](store.py), in-game frames only, docs/store/README.md): `icon-ingame.png` (512, and
  `-400`) and `banner-store.jpg` (1920×640) are plain crops of the pack's own `../gallery/strike.jpg`, an Incoming salvo
  hitting a village at dusk: the store shows the pack itself. `python3 store.py ../gallery/strike.jpg ..`.
- Fonts: `BRAND_FONTS=<folder with BarlowCondensed-SemiBold.ttf and -Bold.ttf>` (default `./fonts`), from
  [google/fonts](https://github.com/google/fonts/tree/main/ofl/barlowcondensed).
- **Frames** (`../gallery`): the pack itself (1.0.0) installed with `tools/boot_check.py` on a
  machine without a GPU, Mesa llvmpipe (`MESA_GL_VERSION_OVERRIDE=4.6` for Voxy), 1920×1080, Complementary Unbound
  with Euphoria Patches, HUD hidden (F1), F2 screenshots. A fresh world (seed `open-skies`), pre-generated with
  Chunky and imported into Voxy (`/voxy import world`). Scenes were set with commands: time 12300, the airship
  from [airship.py](airship.py) (Create Aeronautics blocks with levitite, assembled by `/sable assemble area`, turned
  with `/sable teleport`, held with `/tick freeze`), a biplane `/summon immersive_aircraft:biplane … {NoGravity:1b}`,
  and the strike `/incoming salvo missile 3 10 at 192 -752` at `/tick rate 5` so the frames catch the fireball.
