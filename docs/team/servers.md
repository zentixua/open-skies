# Servers and hosts (team reference; rules in .claude/rules/team.md)

Procedures: the `game-servers` skill. Live state (ports in use, settings, golden maps): the lead's project files.

## netcup
- 12 vCPU EPYC, 31 GiB, Ubuntu 24.04, no GPU, no sudo; Artem's Docker services are not ours; keep ≥ 4 GB free.
- The host reboots itself for kernel updates and Crafty servers do not autostart afterwards.
- CPU-rendered incoming clients (vanilla frames, incoming `client-scenario.md` "CPU rendering"): clone in
  `~/incoming-soft`, Java 21 in `~/jdk-21*`; environment `JAVA_HOME=~/jdk-21* ORG_GRADLE_PROJECT_noRecompile=1
  ORG_GRADLE_PROJECT_mcModsDir=run/ci-mods GRADLE_OPTS="-Dorg.gradle.daemon=false -Xmx1200m" INCOMING_SOFT_HEAP=1536m`,
  then `tools/sandbox.sh start` / `shot` as on the laptop; one client at a time; copy frames back with `scp`.
- The laptop reaches it with `ssh vps` (Tailscale, user ubuntu). Slow Tailscale upload: check the laptop's wlan IPv6
  MTU first (a mobile router announces 1280; `nmcli` ipv6.mtu 1480 on that connection fixes it).
- A netcup Remote Control session starts only on Artem's message in that thread, hears only his messages and returns
  text only; stop it once its task is done (it answers every message and burns quota); a replacement first checks for
  the old process and its jobs.

## Crafty play servers
- online-mode=false + TrueUUID (licensed players verified via Mojang, unknown names offline only), whitelist, op only
  ZentixUA; plain offline mode on a public IP is unsafe. A new player gets the right UUID in
  `config/trueuuid-registry.json` (Artem's brother plays with an offline UUID registered there). The Crafty panel is tailnet-only; its admin
  password file is never copied.
- Stops, restarts, world resets or deletions of any server, and starting a public one, need Artem's own line in the
  working thread.
- Golden worlds ship pre-generated chunks plus a prebuilt LSS store (`<world>/lss-lod/`, SQLite, copied with the
  world): Chunky on a prep server, then `/lsslod store backfill start` (never while Chunky runs). The store drops
  itself on registry drift: re-run backfill. A golden reset bumps .mca header stamps of changed chunks (reset.sh /
  mark_stale.py), or clients keep blasted LODs.
- packwiz installs only mods on a server, not the loader: when `pack.toml` changes `[versions] neoforge`, install that
  NeoForge on each server with the official installer (Artem's line).
- A pre-release test jar on a server or in Artem's Prism needs packwiz disabled (server `start.sh`, Prism
  PreLaunchCommand) with backups; restore both right after the release, or neither gets pack updates again. Play
  servers run without `MaxTenuringThreshold=1`/`SurvivorRatio=32` (early promotion doubled heap peaks).
- `airstrike-world reset tiktok` deletes the played world; never say it is kept.
- Almighty full-map war for TikTok: driver `~/airstrike-server/gm-agent/war/war.py` (`tiktok prep` → `run --minutes N
  --follow ZentixUA [--mspt 30]` → `stop` → `teardown`); one spectator bot per side owns its SAMs (console strikes are
  hostile to every SAM); launch only on Artem's «го», stop on «стоп».

## Laptop
- TikTok recording: `mc-vertical` (~/.local/bin) toggles a borderless 9:16 Minecraft window; the «OBS TikTok»
  desktop shortcut records, F9 starts.
- Friends' PCs are 1.5–2× weaker than Artem's laptop: frame-cost limits must hold there (Artem, 02.10).
