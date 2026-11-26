# For pack makers

How Open Skies is built and checked, the settings it ships, and how to use it as a template. Players need none of
this: see the [README](../README.md). Contributor rules: [AGENTS.md](../AGENTS.md).

## How it is built

```text
pack/                    ← the pack: pack.toml (game and NeoForge versions, pack version), index.toml (hashes),
                           mods/*.pw.toml and shaderpacks/*.pw.toml (download source and hash), config/ (copied
                           into the game as is)
CHANGELOG.md             ← one "## <version>" section per release; the GitHub release notes come from it
tools/                   ← checks and launcher files (below)
.github/workflows/build.yml ← CI on every PR and main push; a new version on main becomes release v<version>
docs/                    ← this page, the key list, the store kit and the images
```

The pack is a [packwiz](https://packwiz.infra.link/) pack in `pack/`, not the repository root, so repository files stay
out of the index and the game. Every mod is linked from its official source (the Modrinth CDN, or an allowed source
with its license), never bundled. CI checks every PR:
- the index is fresh, every file comes from an allowed source with valid sides (`tools/check_sources.py`), and every
  mod (including nested jars) accepts the NeoForge version in `pack.toml` (`tools/check_loader.py`);
- a server reaches "Done" and a client enters a world and joins the server, both installed from scratch
  (`tools/boot_check.py`, which also runs locally; CI has no GPU, so Voxy's and shaders' rendering is not part of it);
- the launcher files build: `Open-Skies.mrpack` and the auto-updating Prism instance `Open-Skies.zip`
  (`tools/prism_instance.py`).

A new `version` in `pack.toml` on `main`, with its `CHANGELOG.md` section, becomes GitHub release `v<version>` with
both files under fixed names (`releases/latest/download/<name>` always points to the latest pack).

## Releases and updates

Numbered releases with a [changelog](../CHANGELOG.md), about once a month, plus fixes for crashes. Each release is a PR
that updates mods (`packwiz update --all`; pinned mods by hand), bumps `version` in `pack.toml` and adds its
`CHANGELOG.md` section; CI boots it from scratch before it can be merged and released. Create, Sable, Create
Aeronautics and Immersive Aircraft are pinned to what Incoming is tested against; Voxy is pinned to the one file Roxy
loads.

## Settings the pack ships

Every other mod keeps its defaults. Each file in [pack/config](../pack/config) is there for a reason:
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
- `defaultoptions/keybindings.txt`: the pack's key layout ([Keys](keys.md)).

## Use it as a template

Fork the repository (or copy it) and you have a working pack with its checks:
1. `pack/`: change `name`, `author` and `version` in `pack.toml`; add or remove mods with packwiz
   (`packwiz modrinth add <slug>`, `packwiz remove <name>`), then `packwiz refresh`.
2. `tools/prism_instance.py`: set `PACK_URL` to your repository's `pack/pack.toml`, and `REPO` in
   `tools/release_notes.py` to your repository.
3. `tools/check_sources.py`: your own non-Modrinth files go to `ALLOWED` with their license; `EXCLUDED` keeps out
   what you must not link.
4. CI (`.github/workflows/build.yml`) then checks every PR as above, and a new `version` on `main` with its
   `CHANGELOG.md` section becomes a GitHub release with the `.mrpack` and the Prism zip.
5. `docs/media` and `docs/store` are Open Skies' own images and store texts: replace them with yours.
