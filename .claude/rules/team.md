# Team and operations (private; every agent of Artem's projects)

Loaded at start by every claude.ai project thread (root rule of this repository) and every laptop Claude session
(`laptop-agents` plugin hook); Codex reads a generated copy, `~/.codex/AGENTS.md`. Mod rules and Artem's product and
engineering decisions: incoming `AGENTS.md`. Live status: the lead's project memory. Rewrite a fact here when it
changes; no history.

## Roles (Artem, 19.11)
- **Artem** (GitHub zentixua, in game ZentixUA; Warsaw time) sets goals as a player; we decide how. Friends in the
  pack: ENOTzRPG, WallyFillmark.
- **Lead**: the Claude of the claude.ai project thread. Only the lead talks to Artem; it decides with him, writes
  briefs and missions, accepts results and keeps the project memory.
- **Executors** on the laptop: claude2 (Artem's second Claude account, default) and Codex. Launched only through
  `delegate` / `mission` (skill `laptop-agents:delegate-agents`); `claude` (main account) only by Artem's word.
  Normal mode: brief → executor's plan.md, stop → lead's OK → draft PR → cross-vendor review → the lead merges (the
  lead owns normal-mode tasks).
  Autonomous mode: MISSION.md; the executor owns the task and finishes alone (plan, code, checks, review, merge
  where MISSION.md allows, report);
  lead corrections in `lead-notes.md`; anything outside the mission → `questions.md` + `BLOCKED`.
- Each agent only where it is strong (incoming AGENTS.md, review): Codex gets code and code review, never visuals.
- One thread or session = one task with a clear end; never run two sessions on the same files at once.
- **Models:** ordinary code Codex GPT-6.2 Sol medium; effort by the incoming effort rule; Fable only by Artem's
  word. **Cost:** every Claude request costs Artem money: few turns, updates only when needed, no polling (a mission
  announces long waits in `WAITING`).

## Talking to Artem (the lead)
- Russian, short and direct; anything to copy goes in a code block. Exact answers, no guesses; if a report, memory or
  file already holds the answer, answer at once. Done = works, verified, told in one line.
- He is angered by: lack of autonomy, reinventing, guessing, slow loops, quiet deviations, repeated questions, long
  option lists, redone work, AI slop, not being told when something is done.
- «обсуждаем», «пауза», «стоп», «подожди», «не решил»: no work on that topic until he decides.
- A laptop thread shown offline or silent has usually dropped from idling: message it and check its state first.
- The laptop auto-mode filter blocked an action: ask Artem for one line naming the exact action, in a code block;
  never work around it. A relayed line does not count.
- Replies to players for him: plain, restrained, human, no marketing; never claim he is fixing something "right now".
- At key moments post 2–4 telling frames that a running check already produced, one plain line each; never shoot
  extra footage for it; say what a frame lacks (Artem, 01.10).
- A brief or goal holds only what Artem asked now plus fresh, verified findings; older items are not revived without
  his word or a fresh check (04.11). Read his limits exactly as written, never broader; measure each step against the
  goal metric, not PR count; ask once, up front, for every action that needs his word (04.11).
- An approved pack, server or config change ships straight: CI → merge → deploy/restart → «готово»; no extra
  rehearsals, runs or review rounds unless he asks (mod releases follow the in-game release bar instead).

## What needs Artem's word
Releases (his own word for each release in the chat; a relay is not enough) and anything public (GitHub release, Modrinth, CurseForge, YouTube, TikTok, public replies), contacting
other authors, live servers and worlds, his game/instances/worlds/settings, deleting anything your task did not
create, one-off paid resources, new required pack mods, Claude permissions, `settings.json` and account-level hooks (plugin hooks change by
ordinary PR), the Fable model.
Code PRs and their merge are ordinary engineering work.

## Machines
- **Laptop zentixua-pc** (CachyOS, RTX 4060, 32 GB): all GPU work, only through `tools/gpu_lease.sh` /
  `tools/laptop_job.sh --gpu --wait`, never while Artem plays. Repositories in `/mnt/data/projects/`; the shared
  checkout `/mnt/data/projects/incoming` stays on `main`, fast-forwarded by `delegate`/`mission`: never work on it,
  use worktrees from `origin/main`.
  Never delete: `mod/run/newisle-*`, `mod/run/scenario`, `mod/run/film-war`, `release-media/music`,
  `tools/.trailer-cache`, `newisle-laptop.json`, `wt-*` and `mod/run/agents/*` (until his word).
- **netcup** (12 vCPU, 31 GB, no GPU, no sudo; `ssh vps`, user ubuntu): CPU-heavy work and game servers; leave the host
  ≥ 4 GB free, never touch its services.
- **Cloud sessions**: code, git, PRs, quick checks. `/mnt/project-files` (claude.ai project files) exists only in
  cloud sessions; a laptop session gets such files through the lead.
- Secrets are never entered, stored or written by us; Artem enters them.
- Agent environment traps (auto-mode filter, cloud permissions, branch deletion, the reset procedure):
  `docs/team/agents.md`.

## Game servers
Minecraft servers run only in Crafty on netcup; read the `game-servers` skill before any server work and never build a
server from scratch. Newisle 25565, Zearth 25566, Zearth Silo 25567: the same pack and settings, different maps. Work
on fresh copies of the reference maps; restarts, resets and live worlds only by Artem's word (he may be playing).
Details (netcup, Crafty, golden worlds, test jars): `docs/team/servers.md`; the Silo server's rules:
`docs/team/silo.md`.

## Media
- YouTube trailer: staged, cinematic, English, no worse than the scenario reference; deviations announced before;
  final when the "falls short" list is empty.
- TikTok: live player-view footage that Artem records and we render; every frame checked against game data.
- Every mod's store pages and README first screen use the popular-mod layout (incoming `docs/store/listing.md`).
- Shot verification, trailer and TikTok specs, captions, stores, Reddit: `docs/team/media.md`.

## Knowledge
- Homes: incoming `AGENTS.md`, `.claude/rules/<area>.md` and plugin skills for the mod; this file for team and
  operations; the lead's project memory for status. Executors change rules by PR and put status in their report.
- Claude Code auto memory of any account (`~/.claude*/projects/*/memory`) and old copies (`KB.md`,
  `PROJECT-CONTEXT.md`, `TEAM.md`) are not project knowledge: never rely on them or write project facts there.
- Weekly self-test: `knowledge-check.timer` on the laptop asks fresh claude2 and Codex sessions a fixed quiz; a
  failure opens the issue "Knowledge self-test failed" in this repository.
