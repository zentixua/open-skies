# Open Skies: contributor rules

These rules apply to every contributor, human or agent. Read this file in full before changing the pack. Players'
documentation is README.md; release history is CHANGELOG.md. Everything in this repository is in English.

Open Skies is a public NeoForge 1.21.1 modpack built around [Incoming](https://github.com/zentixua/incoming): Create,
Create Aeronautics and aircraft, a light survival and exploration layer, Voxy long-distance rendering through Roxy.
It is also meant as a template other pack makers can fork.

## Layout

```text
pack/                    ← the pack: pack.toml (game and NeoForge versions, pack version), index.toml (hashes),
                           mods/*.pw.toml and shaderpacks/*.pw.toml (download source and hash), config/ (copied
                           into the game as is)
CHANGELOG.md             ← one "## <version>" section per release; the GitHub release notes come from it
tools/check_sources.py   ← every file is on the Modrinth CDN or an allowed source with its license; excluded projects
                           stay out; valid sides
tools/check_loader.py    ← every mod (including nested jars) accepts the NeoForge version in pack.toml
tools/boot_check.py      ← the pack boots from scratch: server to "Done", client into a world and onto the server
tools/prism_instance.py  ← Prism instance that installs pack/ from main before every launch (Open-Skies.zip)
tools/release_notes.py   ← release notes for the current version from CHANGELOG.md
.github/workflows/build.yml ← CI on every PR and main push; a new version on main becomes release v<version>
```

The pack lives in `pack/`, not the root, so repository files stay out of the index and the game. `main` is always the
latest release: packwiz-installer instances and servers read `pack/` from `main`.

## Rules

- **Scope.** A sandbox: no quests, no recipe changes, no teleports, no terrain overhaul, one mod per role. A new mod
  needs a role in README's "What's inside" and must not duplicate one.
- **Sources.** Link files, never bundle them: Modrinth CDN, or an `ALLOWED` entry in `tools/check_sources.py` with
  the license and the reason. A mod whose author forbids redistribution or can revoke it goes to `EXCLUDED`. Jars in
  `config/` or other overrides are forbidden.
- **Configs.** Other mods keep their defaults. Every file in `pack/config` has its reason in README's "Settings the
  pack ships", in the same PR.
- **Sides.** `side` must be right: servers install with `-s server` and skip `client` mods. A client mod that
  registers anything the server may send to players (sounds, particles, entities, items) must also be on the server
  (`side = "both"`) if the mod supports it: in multiplayer the client gets registry ids from the server, and
  client-only entries have none. Worldgen mods (structures) are `both`, or singleplayer worlds would lack them.
  packwiz writes `side = "both"` for Modrinth shaderpacks; set `"client"`.
- **Versions.** Every change to `pack/` bumps `version` in `pack.toml` (semver: patch for fixes and updates, minor for
  added or removed mods) and adds its `CHANGELOG.md` section in the same PR. Merging it releases `v<version>`.
- **Pins.** Create, Sable, Create Aeronautics and Immersive Aircraft are pinned to the versions Incoming is tested
  against; change them together with Incoming. Voxy is pinned (`packwiz pin voxy`): Roxy loads only
  `voxy-0.2.16-beta+1.21.11` (Modrinth version `H3w2nVdU`); update it only when Roxy announces another version.
- **Keys.** `pack/config/defaultoptions/keybindings.txt` lists every key of every mod except JEI. A new mod's default
  key that is taken moves to Alt + the same key, or is unbound when its action has a menu; README's key table changes
  with it.
- **Stores.** The pack is published on GitHub only. Uploading it to Modrinth or CurseForge needs the owner's word and
  a license pass first: Photon's license forbids redistribution on platforms that pay creators, and several mods allow
  only non-commercial use (README, "Licenses and credits").
- **Merging.** A PR merges after green CI and one review by someone (or a model) who did not write it. Only serious
  errors (wrong behaviour, a crash) block.

## Workflow

```sh
go install github.com/packwiz/packwiz@v0.0.0-20260906154125-ef87d964f8cb
cd pack && packwiz update --all           # monthly release; pinned mods stay
cd pack && packwiz modrinth add <slug>    # a new mod (then check its side and README)
cd pack && packwiz refresh                # the index with hashes, in the same commit (CI checks it)
python3 tools/check_sources.py && python3 tools/check_loader.py pack
python3 tools/boot_check.py server run/boot/server   # and `client` (see the script header)
```

## Pitfalls

- `config/fml.toml` keeps `maxThreads = 1`: Create 6.0.10 registers items through tables that are not thread-safe,
  and parallel mod construction occasionally fails with `Trying to access unbound value … create:…` (README,
  "Settings the pack ships"). Remove it only once Create fixes it.
- Voxy and Roxy are required: `.mrpack` launchers show optional files unticked, which would leave every player
  without long-distance rendering. macOS and GPUs without OpenGL 4.6 remove both by hand (README).
- `packwiz modrinth add` rewrites the `.pw.toml` of every dependency it resolves, even one already in the pack, and
  drops its `pin = true` (adding Create: Central Kitchen unpinned Create). After adding a mod, `git diff` the existing
  files and restore the pins.
- GitHub caches raw files for up to 5 minutes: right after a merge, `pack.toml` and `index.toml` may come from
  different commits, and packwiz-installer reports an incorrect index hash ("Quit", launch again later).
- packwiz-installer removes only what it installed: an instance installed from `.mrpack` that switches to the
  auto-updating zip must move its `mods` folder aside first, or old jars with other names stay next to the new ones.
- Index paths cannot leave `pack/`, and `pack.toml` carries the index hash: file contents cannot redirect the pack to
  another address. A fork sets its own address in `tools/prism_instance.py`.
