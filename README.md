# Open Skies

A NeoForge 1.21.1 modpack about a world worth defending. Explore and settle, build machines with Create, fly
everywhere, and fight when you choose: [Incoming](https://github.com/zentixua/incoming) adds remote-guided strikes,
from a Shahed drone to cruise missiles and a nuclear ICBM, aimed with binoculars at anything you can see.

- **Sandbox, no quests.** Vanilla progression and recipes; advancements and this page are the guide. Survival and
  creative, singleplayer, LAN and dedicated servers.
- **Flight is the travel.** Create Aeronautics airships, Immersive Aircraft and Man of Many Planes. No teleports.
- **A light survival layer.** Better dungeons, temples and towns to raid from the air, Farmer's Delight cooking,
  backpacks, per-player loot, claims for servers.
- **Horizon-wide view.** Voxy long-distance rendering, on by default.
- About 100 mods, every one with a single job ([What's inside](#whats-inside)); built in the open with
  [packwiz](https://packwiz.infra.link/) and checked by CI on every change (a server and a client boot from scratch).

## Install

Download from the [latest release](https://github.com/zentixua/open-skies/releases/latest) (no GitHub account needed):
- [Open-Skies.mrpack](https://github.com/zentixua/open-skies/releases/latest/download/Open-Skies.mrpack): import it
  in [Modrinth App](https://modrinth.com/app), [Prism Launcher](https://prismlauncher.org/download/) ("Add
  Instance" → "Import") or ATLauncher. The instance stays on that version; install a newer release over it when you
  want to update.
- [Open-Skies.zip](https://github.com/zentixua/open-skies/releases/latest/download/Open-Skies.zip), advanced: a Prism
  Launcher instance that updates itself to the latest release before every launch
  ([packwiz-installer](https://packwiz.infra.link/tutorials/installing/packwiz-installer/) in its pre-launch command).
  Worlds and your own settings stay; files of the pack are replaced when a release changes them.

Optional files: Prism and Modrinth App show them **unticked**. Tick Simple Voice Chat if your server runs it.

**Requirements.** Java 21 (launchers install it), 6 GB of memory for the game (the Prism zip sets 6144 MB; set the
same in Modrinth App) and 16 GB of system RAM, a GPU with OpenGL 4.6 (GTX 1660 / RX 580 class or better without
shaders). Shaders, Voxy at long distances and big Create builds want more.

**macOS and older GPUs.** Voxy needs OpenGL 4.6; macOS has OpenGL 4.1, so Voxy runs there only through Roxy's extra
libraries ([Roxy's macOS guide](https://github.com/RasaNovum/Roxy/blob/main/Roxy-macOS-compat/setup-guide.md)).
Without them, or on a GPU without OpenGL 4.6, remove both `roxy-*.jar` and `voxy-*.jar` from the instance's `mods`
folder (Roxy does nothing without Voxy). In the auto-updating Prism instance, packwiz-installer would bring them back:
use the `.mrpack` there.

**Lite setup** for weaker PCs: no shaderpack (the default), Voxy and Roxy removed as above, Simple Voice Chat unticked;
about 4–5 GB of memory is then enough.

## Servers

Install the server side of the pack with NeoForge (version in [pack.toml](pack/pack.toml)) and then either:
- packwiz-installer, in the server directory:
  `java -jar packwiz-installer-bootstrap.jar -g -s server https://raw.githubusercontent.com/zentixua/open-skies/main/pack/pack.toml`
  ([bootstrap jar](https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest); `main` is always the latest
  release), or
- the `.mrpack` with a server tool that reads it, for example the
  [itzg/minecraft-server](https://docker-minecraft-server.readthedocs.io/en/latest/types-and-platforms/mod-platforms/modrinth-modpacks/)
  Docker image (`MODRINTH_MODPACK`).

Client-only mods are skipped on the server; every mod that registers something the server sends to players is
installed on both sides. Notes for server owners:
- **Claims and parties:** [Open Parties and Claims](https://modrinth.com/mod/open-parties-and-claims) protects
  builds from other players (`/openpac-claims`, `/openpac-parties`, or the `'` key in game). Whether claims also stop Incoming's strikes is not
  verified yet: test it on your server before relying on it. Incoming's own world rules switch block damage and fire
  on or off, cap active strikes per player, and keep nuclear weapons operator-only by default
  ([Incoming's guide](https://github.com/zentixua/incoming/tree/main/docs/guide)).
- **Voice chat:** [Simple Voice Chat](https://modrinth.com/plugin/simple-voice-chat) needs UDP port 24454 open
  (configurable in `config/voicechat/voicechat-server.properties`).
- **Pre-generation:** [Chunky](https://modrinth.com/plugin/chunky) (`/chunky radius 3000`, `/chunky start`) saves
  lag on first exploration; [LOD Server Support](https://modrinth.com/mod/lod-server-support) sends distant terrain
  to players' Voxy and Xaero's map.
- **Performance:** [spark](https://spark.lucko.me/) (`/spark tps`, `/spark profiler`).

## What's inside

| role | mods |
|---|---|
| core | [Create](https://modrinth.com/mod/create) 6.0.10, [Sable](https://modrinth.com/mod/sable) and [Create Aeronautics](https://modrinth.com/mod/create-aeronautics) (pinned: Incoming is tested against them), [Incoming](https://github.com/zentixua/incoming) (GitHub release jar) |
| Create | Propulsion: Simulated, Aeroworks, Tweaked Controllers, Create Big Cannons (+ Ritchie's Projectile Library), Create: Connected, Create Deco, Diesel Generators, Aeronautics Hot Air Fix |
| aircraft and weapons | Immersive Aircraft, Man of Many Planes, Vic's Point Blank (+ GeckoLib), Point Blank Aeronautics compat, Do a Barrel Roll (banking elytra flight, + Forgified Fabric API) |
| exploration | YUNG's Better Dungeons, Mineshafts, Strongholds, Desert Temples, Jungle Temples, Ocean Monuments, Witch Huts, Nether Fortresses and End Island, YUNG's Bridges and Extras (+ YUNG's API); Towns and Towers (+ Cristel Lib). Vanilla terrain: worlds stay cheap to generate and Voxy shows them right |
| survival | Farmer's Delight and Create: Central Kitchen (+ Create: Dragons Plus), Sophisticated Backpacks and Storage (+ Sophisticated Core), Lootr (per-player chests), Comforts (sleeping bags and hammocks for long flights), AppleSkin, GraveStone (+ its Sable patch) |
| multiplayer | Open Parties and Claims, Simple Voice Chat (optional), No Chat Reports, Chunky, spark |
| long-distance rendering | [Voxy](https://modrinth.com/mod/voxy) through [Roxy](https://modrinth.com/mod/roxy), LOD Server Support |
| performance | Sodium, Sodium Extra, Reese's Sodium Options, Lithium, FerriteCore, ModernFix, ImmediatelyFast, Entity Culling, More Culling (+ Cloth Config), Dynamic FPS, Clumps |
| look and sound | Iris (+ Colorwheel) and three shaderpacks (below), Euphoria Patches, Subtle Effects (+ Fzzy Config, Kotlin for Forge), Particle Rain, AmbientSounds (+ CreativeCore), Sound Physics Remastered, LambDynamicLights, Contraption Lights, Burnt (fire burns structures down), 3D Skin Layers, Not Enough Animations, Aeronautics Camera Sync |
| interface | JEI (+ MezzConfig), Jade and Jade Sable Compat, Xaero's Minimap and World Map, Create – Xaero's map, Better Advancements, Controlling (+ Searchables), Mouse Tweaks, Ok Zoomer, Default Options (+ Balm) |

**Shaders** run through Iris: K toggles them, O picks one. None is selected by default; the pack ships three, all
with Voxy support: [Photon](https://modrinth.com/shader/photon-shader) (the most beautiful and the heaviest),
[Complementary Unbound](https://modrinth.com/shader/complementary-unbound) (middle, with low-end presets; Euphoria
Patches adds its own copy, "ComplementaryUnbound + EuphoriaPatches", on first launch) and
[MakeUp Ultra Fast](https://modrinth.com/shader/makeup-ultra-fast-shaders) (for weak PCs). If Voxy cannot start its
renderer with a shaderpack, Voxy turns shaders off and Iris remembers it: press K to turn them on again.

**Not in the pack, on purpose:** quests and recipe changes (a sandbox), teleports and waystones (flight is the travel),
terrain overhauls (cost and Voxy), a second mod for a role already filled.

## Settings the pack ships

Every other mod keeps its defaults. Each file in [pack/config](pack/config) is there for a reason:
- `fml.toml`: NeoForge's defaults except `maxThreads = 1`, so mods are constructed one at a time. Create 6.0.10
  registers its blocks and items through shared tables that are not thread-safe ("some of these registrations are not
  thread-safe" in its `Create.java`), and Create addons touch Create classes from their constructors; with parallel
  construction a registration is occasionally lost and startup fails with `Trying to access unbound value:
  ResourceKey[minecraft:item / create:…]` (Create issue #10534). Cost: about 1–2 s of startup. Remove when Create
  fixes it.
- `voxy-config.json`: `sectionRenderDistance = 12` instead of Voxy's 16. Voxy sizes its LOD geometry buffer from free
  video memory when you join (about 1.8–2.1 GB on an 8 GB card); at 16 it fills on such cards and the game crashes
  with `IllegalStateException: Geometry OOM`. 12 covers a little over half the area. With more video memory, raise it
  in Video Settings → Voxy.
- `entityculling.json`: Entity Culling's defaults plus Incoming's entities in `entityWhitelist`. Their trails, launch
  clouds and burning debris smoke are spawned in the entity's client tick; culling would cut the trail of a missile
  behind a hill or behind the player.
- `aero_cam_sync-client.toml`: Aeronautics Camera Sync's defaults with `configSchemaVersion = 5`. Version 1.4.0 writes
  a new file with schema 0 and then, on the next launch, opens a "Config Reset" question instead of the main menu.
- `moreculling.toml`: `useBlockStateCulling = false`. More Culling's block face culling overrides Create Aeronautics'
  rule that draws faces next to levitite; everything else is More Culling's default.
- `subtle_effects/general.toml`: Subtle Effects' defaults except `particleRenderDistance = 32` (its default is 5
  chunks). Its particle culling would otherwise hide Incoming's debris, splashes and fragments beyond 80 blocks.
- `sound_physics_remastered/sound_rates.properties`: `0` for every `incoming:` sound. Incoming models distance, air,
  terrain and echo for its own sounds; Sound Physics keeps everything else at its defaults.
- `defaultoptions/keybindings.txt`: the pack's key layout ([Keys](#keys)).

## Keys

Default Options makes the pack's layout the default: a new instance gets it on first launch, and "Reset Keys" in
Controls returns to it. NeoForge triggers every action bound to a pressed key, so mods' defaults that collide are
moved. Rules: Minecraft's keys stay where they are; one key, one action where both could fire; a mod's key that is
taken moves to Alt + the same key.

| key | action |
|---|---|
| Left mouse | attack; in Incoming's binoculars: launch; on a Big Cannons mount: fire |
| R | reload (Point Blank); Tweaked Controllers: center the mouse |
| B, V, Y | fire mode, sight, attachments (Point Blank); Alt+Y: its settings |
| G | use or place a block while holding a weapon, whose right click aims (Point Blank) |
| C (hold) | zoom; mouse wheel changes it (Ok Zoomer) |
| X | leave an aircraft (Immersive Aircraft) or a Tweaked Controller |
| Ctrl | sprint; in an aircraft: boost |
| H (hold) | Tweaked Controllers: mouse as joystick; in an aircraft: free look |
| \` | Big Cannons mount: aim or move; in an aircraft: mouse steering on/off |
| Left Alt | Create's schematic menu and toolbox |
| M, ], [ | world map, its settings, minimap settings (Xaero) |
| U, J, Z, Num + | waypoints, new waypoint, larger minimap, instant waypoint (Xaero) |
| N, ",", "." | projectile camera, targeting map, second key (Incoming) |
| I | camera tilts with the craft (Aeronautics Camera Sync) |
| A, D | on elytra: yaw (Do a Barrel Roll); roll and pitch with the mouse |
| K, O | shaders on/off, shaderpack selection (Iris) |
| Shift, Num 0, Num 1 | details, settings and overlay of Jade |
| Alt+B, Alt+C, Alt+Z, Alt+X | open backpack, its inventory upgrades, toggle upgrades 1 and 2 (Sophisticated Backpacks) |
| Caps Lock, Alt+V, Alt+M | push to talk, voice chat menu (mute, groups, settings inside), mute (Simple Voice Chat) |
| ' | Open Parties and Claims menu |

## Licenses and credits

This repository's own files (tools, CI, configs, docs) are under the [MIT license](LICENSE). The pack links every mod
from its official source and bundles none: each file keeps its author's license. The pack is not monetised, because
several mods it uses (Big Cannons assets, Jade, Man of Many Planes, Towns and Towers, Cristel Lib, Entity Culling and
3D Skin Layers) allow only non-commercial use.
- **Voxy** is by MCRcortex: [modrinth.com/mod/voxy](https://modrinth.com/mod/voxy). The pack uses the official file
  `voxy-0.2.16-beta+1.21.11` from that page, unmodified. **Roxy** ([modrinth.com/mod/roxy](https://modrinth.com/mod/roxy))
  runs it on NeoForge 1.21.1: report problems with Voxy in this pack to Roxy or to us, never to Voxy.
- **Complementary Shaders** by EminGT: [complementary.dev](https://www.complementary.dev/).
- **Subtle Effects** ([modrinth.com/mod/subtle-effects](https://modrinth.com/mod/subtle-effects)) is credited here as
  its author asks; Default Options and Balm (BlayTheNinth) ask that their names stay out of a pack's title.
- Left out on purpose: shaderpacks and mods whose authors forbid redistribution or can revoke it (BSL, Flashback,
  Essential). `tools/check_sources.py` enforces this in CI.

## Use it as a template

Fork the repository (or copy it) and you have a working pack with its checks:
1. `pack/`: change `name`, `author` and `version` in `pack.toml`; add or remove mods with packwiz
   (`packwiz modrinth add <slug>`, `packwiz remove <name>`), then `packwiz refresh`.
2. `tools/prism_instance.py`: set `PACK_URL` to your repository's `pack/pack.toml`, and `REPO` in
   `tools/release_notes.py` to your repository.
3. `tools/check_sources.py`: your own non-Modrinth files go to `ALLOWED` with their license; `EXCLUDED` keeps out
   what you must not link.
4. CI (`.github/workflows/build.yml`) then checks every PR: fresh index, sources, NeoForge ranges
   (`tools/check_loader.py`), and a server and a client booting from scratch (`tools/boot_check.py`, which also runs
   locally). A new `version` on `main` with its `CHANGELOG.md` section becomes a GitHub release with the `.mrpack` and
   the Prism zip.

## Releases and updates

Numbered releases with a [changelog](CHANGELOG.md), about once a month, plus fixes for crashes. Each release is a PR
that updates mods (`packwiz update --all`; pinned mods by hand), bumps `version` in `pack.toml` and adds its
`CHANGELOG.md` section; CI boots it from scratch before it can be merged and released. Create, Sable, Create
Aeronautics and Immersive Aircraft are pinned to what Incoming is tested against; Voxy is pinned to the one file Roxy
loads.

## Problems

Open an [issue](https://github.com/zentixua/open-skies/issues) with the pack version, your launcher, OS and GPU, and
the log: `logs/latest.log` from the instance folder (and `crash-reports/` if the game crashed). Try the lite setup
first if the game crashes on a weaker PC.
