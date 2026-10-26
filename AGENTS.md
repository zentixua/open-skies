# Open Skies — Artem and friends' NeoForge 1.21.1 modpack

These project rules apply to every contributor, human or agent. Read this file in full before starting.

Our own "Open Skies" modpack in [packwiz](https://packwiz.infra.link/): Create, Create Aeronautics, Incoming,
Voxy long-distance rendering (through Roxy), shaders, replay recording, and Almighty on the server. See README.md
for the contents and installation. The mod is at https://github.com/zentixua/incoming;
the Almighty host bridge (server only) is at https://github.com/zentixua/almighty.

## People and rules

- Author/host: **Artem** (GitHub zentixua, in-game ZentixUA). Friends: **ENOTzRPG**, **WallyFillmark**.
  Chat in Russian, briefly and to the point.
- **`pack/` on `main` is the live modpack**: players' auto-updating instances (Prism, packwiz-installer before every
  launch) and the dedicated server install it from `main` on their next launch. Only CI-verified changes and jars
  from published releases go into `main` (modpack PRs follow the mod release).
- Keep the modpack clean and reliable: standard mechanisms, no workarounds; other mods' settings stay at their
  defaults, and every file in `config/` needs a reason in README.md. Add a required mod only on Artem's instruction.
- Bump `version` in `pack.toml` for every change to the modpack's composition, and add a row to README.md's version
  table: all players must have the same set. Each new pack version also needs
  `docs/releases/<version>.en.md` with the English translation of that row; CI requires both.
- GitHub releases are automatic: a new `version` on `main` becomes release `v<version>` (downloads without signing in
  at `releases/latest/download/Open-Skies.zip` and `…/Open-Skies.mrpack`).
  Other public steps (Modrinth, etc.) require Artem's explicit instruction.
- Merge a ready PR yourself after green CI and one review round by a model that did not write it. Review the diff
  and surrounding code, not the PR description. Only serious errors (wrong behaviour, a crash) block;
  everything else is optional.
- A commit ends with the `Co-Authored-By:` line of your own agent.
- **Languages (Artem, 26.10).** Everything in the repository is in English: code, comments, log messages, CLAUDE.md,
  `.claude/rules`, AGENTS.md, internal docs, `tools/`, CI, commits and PRs. English plus Russian only for what players
  need: the public docs (README, `docs/guide`, release notes, store pages) and the mod's interface (`en_us`/`ru_ru`).
  No mixing inside one file. Chat with Artem stays in Russian.

## Layout

```text
pack/                    ← the modpack: pack.toml (game and NeoForge versions), index.toml, mods/*.pw.toml and
                           shaderpacks/*.pw.toml (download sources and hashes), config/ (copied into the game as is)
tools/prism_instance.py  ← Prism instance that installs pack/ from main before every launch (Open-Skies.zip)
tools/pack_dir.py        ← game directory from pack/ without Prism (mods checked by hash), for Incoming client checks
tools/check_loader.py    ← every mod (including nested jars) accepts the NeoForge version in pack.toml; a CI step
tools/boot_check.py      ← the modpack boots from scratch: server reaches "Done", client enters a world, client on
                           this server records a Flashback replay; CI job "Запуск с нуля" (client: Xvfb and Mesa);
                           manually: client in Incoming's nested KWin (see the script header)
.github/workflows/build.yml  ← CI "Сборка модов": fresh index, .mrpack and Prism instance (artifact open-skies);
                               and "Запуск с нуля" (boot_check.py); a new version on main becomes release v<version>
                               with these files only if both pass (notes: README's version table row and
                               docs/releases/<version>.en.md)
```

Modpack address for packwiz-installer: `https://raw.githubusercontent.com/zentixua/open-skies/main/pack/pack.toml`;
instances installed under the previous modpack name (Airstrike Pack) use the old address
`zentixua/airstrike-pack/…`. GitHub serves it while zentixua has no repository with that name (keep the name unused).
The modpack lives in `pack/`, not the root: repository files (README, CI, tools) stay out of the index and the game.

## Workflow

```sh
go install github.com/packwiz/packwiz@v0.0.0-20260906154125-ef87d964f8cb
cd pack && packwiz update <name>          # mod from Modrinth; exact version: packwiz modrinth add --project-id … --version-id …
cd pack && packwiz refresh                # hash index in the same commit (CI checks it)
cd pack && packwiz mr export              # .mrpack: one-time installation without auto-updates
python3 tools/prism_instance.py           # dist/Open-Skies.zip: new auto-updating instance
```

New Incoming release: `packwiz url add Incoming https://github.com/zentixua/incoming/releases/download/v<version>/incoming-<version>.jar --meta-name incoming`;
Almighty works the same way: `almighty-<version>.jar` from https://github.com/zentixua/almighty, `side = "server"`.

## Pitfalls

- The modpack's `config/fml.toml` keeps `maxThreads = 1`: NeoForge constructs mods in parallel, but Create 6.0.10
  registers items through tables that are not thread-safe. Occasionally startup crashes with
  `Trying to access unbound value … create:…` (README's contents section). Remove this only once Create fixes it.
- Roxy loads only `voxy-0.2.16-beta+1.21.11` (Modrinth `H3w2nVdU`): do not update Voxy until Roxy announces support
  for another version. Roxy and Voxy are optional, selected by default, and must be enabled or disabled together.
  Voxy is pinned (`packwiz pin voxy`): `packwiz update --all` leaves it alone.
- GitHub caches raw files for up to 5 minutes: immediately after a merge, `pack.toml` and `index.toml` may come from
  different commits. packwiz-installer reports an incorrect index hash ("Quit", launch again later).
  Restart the server ~5 minutes after a merge.
- The modpack does not select a shaderpack (`config/iris.properties` is absent: the player chooses;
  Artem's decision, 23.10).
- For Modrinth shaderpacks, packwiz writes `side = "both"` (their environment is unspecified); set it to `"client"`.
- Mods must have the correct `side`: the server installs the modpack with `-s server`, skipping `client` mods;
  server-only mods (Almighty) use `side = "server"`, so players do not download them.
- A client mod with its own entries in registries that the server sends to players (sounds, particles, entities,
  items) must also be installed on the server (`side = "both"`) if the mod supports it. After joining a server,
  client-only entries have no id, so packets containing them cannot be encoded. Flashback records sounds that the
  client plays itself, and recording crashed on Subtle Effects snoring (README's contents section).
  CI checks this: a client on the modpack server records a replay next to a sleeping villager.
- packwiz-installer removes only what it installed: when converting an instance from `.mrpack` to auto-updates,
  move `mods` aside (README.md), or an old jar with a different name would remain alongside the new one.
- Index paths cannot leave `pack/` (packwiz-installer discards extra `..`), and `pack.toml` contains the index hash:
  file contents cannot redirect the modpack to another address. Enter the new address in the instance's
  "Pre-launch command". Renaming the GitHub repository does not break the address: raw.githubusercontent.com
  also serves files under the old name.
- An instance with a different address in its "Pre-launch command" does not get the modpack from `main`;
  reinstall it from `Open-Skies.zip`.
