# Public modpack built around Incoming: proposal (draft)

Status: draft for Artem's decision (mission `public-pack`, 24.11.2026). Research only: nothing here is published,
created or changed in `pack/`. Facts were checked on 24.11.2026 against the sources linked in each section.

## Summary

1. **The idea is good, if kept narrow.** Incoming has no pack of its own. Popular Create Aeronautics packs on
   Modrinth (75k–103k downloads) are about engineering. BlockFront (491k) is about guns. We found no pack where war
   sits on top of survival. That is the gap.
2. **Recommended:** variant B, "Open Skies". It is a sandbox with no quests and no recipe gating, and about 110 mods:
   today's tested core (Create, Aeronautics, aircraft, Incoming, Big Cannons, guns) plus a light survival and
   exploration layer (structures, food, backpacks, per-player loot, claims). There are no teleports, so flying is
   how you travel.
3. **Format:** packwiz in a public GitHub repository is the single source. A `.mrpack` goes on Modrinth and on GitHub
   releases. There is no CurseForge version for now: Incoming and Voxy are not on CurseForge.
4. **Voxy through Roxy does not block a Modrinth listing.** Voxy's page allows modpacks that link back to it and use a
   version from its page. We use the official `voxy-0.2.16-beta+1.21.11` file from the Modrinth CDN. The spirit of the
   "no unofficial backports" sentence is a grey area. It ships as an optional mod, off by default in `.mrpack`
   launchers, and is credited on the pack page.
5. **What blocks a clean public listing:** Incoming is not on Modrinth, and that needs Artem's word. Some mods leave
   the public pack: BSL and Solas (no modpack permission), Flashback (ARR, "do not redistribute"), Essential (an
   account service with revocable terms), and our personal mods. The pack stays non-monetised because of several
   non-commercial licenses.
6. **Repositories:** the public pack gets a new repository, created from this one's history. `zentixua/open-skies`
   stays the friends' pack: it merges upstream `main` and adds only its own files. Mod updates run upstream only. Note: this repository is already public today.
7. **Name:** "Open Skies" is free on Modrinth and GitHub. On CurseForge the address `open-skies` belongs to a dead
   2017 pack.
8. **Main costs:** the pinned Create 6.0.10, Sable and Aeronautics stack; Roxy supports exactly one Voxy file; mod
   update churn; public support. Mitigations: monthly versioned releases through the existing boot check, and a hard
   cap on scope.

## 1. How the best pack makers work

Sources: Fabulously Optimized principles (https://wiki.download.fo/principles), SynfulChaot's "Building a modpack"
(https://SynfulChaot.github.io/posts/building-a-modpack-pt.1), the ATM10 FAQ
(https://allthemods.github.io/alltheguides/atm10/faq), the Prominence II page
(https://www.curseforge.com/minecraft/modpacks/prominence-2-rpg), the Create: Astral repository
(https://github.com/Laskyyy/Create-Astral), and the Create: Above and Beyond page
(https://www.curseforge.com/minecraft/modpacks/create-above-and-beyond).

- **Pick the pack type first.** SynfulChaot lists the types: challenge, progression, skyblock, survival, vanilla+ and
  kitchen sink. A kitchen sink like ATM10 (about 500 mods, "doesn't commit to a single theme") lives on volume and a
  big team. Themed packs win on coherence. For a small team the choice is a themed pack.
- **Mod selection rule (ATM10):** no mod that is buggy, ruins performance or progression, or is not updated to the
  pack's version. Add mods in waves of two or three and launch between waves (SynfulChaot).
- **Remove duplicates.** One ore, one food system, one backpack, one map. Two mods doing the same job confuse players
  (SynfulChaot).
- **Balance through optional paths.** Prominence II keeps its tech mods optional: "the campaign can be finished without
  touching them". For us that means war is a path layered on survival, not a requirement, and survival works without
  war.
- **Progression vs sandbox.** Quest-gated packs such as Create: Above and Beyond and Create: Astral use KubeJS recipe
  rewrites plus FTB Quests. They are the most expensive kind to build and maintain. They also fit single-player best,
  because in multiplayer a friend can hand you the items you were meant to earn. A "fun for everyone" multiplayer pack
  is a sandbox. Guidance comes from advancements and short docs. If quests are added, they should be "minimal and
  purposeful", explaining rather than gating.
- **Performance baseline.** Fabulously Optimized is the reference: sustainable, "100% server-compatible", no
  opinionated extras. The NeoForge 1.21.1 standard stack is Sodium, Lithium, FerriteCore, ModernFix,
  ImmediatelyFast and Entity Culling; Open Skies already has it. Heavy visuals are opt-in. ATM10 asks for 8–12 GB.
  A pack of about 110 mods centred on Create should state 6 GB allocated and 16 GB system RAM.
- **Config defaults.** Other mods keep their defaults. Server-facing tweaks are documented (ATM10 explains claims,
  homes and `/rtp` limits). This matches our rule that every `config/` file has a written reason.
- **Client and server sides.** Every mod gets a correct side, with a server pack or server-side install path (FO,
  ATM). Open Skies already does this and checks it in CI (server to "Done", client into a world).
- **Updates and versioning.** Public packs ship numbered versions with changelogs. ATM10's changelogs openly list
  reverts ("reverted ... to fix heavy lag"). Bugs go to GitHub issues and support to a channel with a "how to send
  logs" answer. Silent continuous updates, like our 3-hourly friends' flow, are wrong for public players: a player
  must be able to stay on a version. A development `main` may still update continuously, as long as players install
  release tags (section 6).

## 2. Format and distribution

Sources: the Modrinth `.mrpack` format (https://support.modrinth.com/en/articles/8802351-modrinth-modpack-format-mrpack),
modpack permissions (https://support.modrinth.com/en/articles/8797527-obtaining-modpack-permissions), the Modrinth June
2026 permissions process (https://modrinth.com/news/article/modpack-permissions), CurseForge third-party mods
(https://support.curseforge.com/support/solutions/articles/9000197908), the CurseForge distribution toggle
(https://support.curseforge.com/support/solutions/articles/9000207877), and packwiz-installer
(https://packwiz.infra.link/tutorials/installing/packwiz-installer/).

| | packwiz (source) | Modrinth `.mrpack` | CurseForge zip |
|---|---|---|---|
| what it is | TOML per mod, hashes, hosted over HTTP; a pre-launch updater | a zip with `modrinth.index.json` (URLs, hashes, `env`) and `overrides/` | `manifest.json` (CurseForge project and file ids) and `overrides/` |
| which mods | any URL | download hosts limited to `cdn.modrinth.com`, `github.com`, `raw.githubusercontent.com`, `gitlab.com`; external files need proof of permission (from June 2026, before a version is published) | CurseForge projects only; anything else must be on CurseForge's approved non-CurseForge list (MIT/GPL, official jar), "personal permissions will not be accepted" |
| client/server | `side` per mod; server via `packwiz-installer -s server` | `env.client` / `env.server`: `required` / `optional` / `unsupported` | no side split |
| optional mods | yes, with default on/off | yes, but launchers show them unchecked (no default) | no |
| launchers | Prism, MultiMC and ATLauncher via the pre-launch command; itzg Docker (`PACKWIZ_URL`) | Modrinth App, Prism, ATLauncher; itzg Docker | CurseForge app, Prism, Modrinth App (imports CurseForge zips) |

We checked that `packwiz mr export` (our CI) already writes the Incoming and Almighty GitHub release URLs straight
into `files[]` (release 0.1.64: 82 files, 2 from github.com). A Modrinth listing would still prefer Incoming as a
Modrinth project: that is the "uploaded to Modrinth" case, and it is also needed for discovery.

**Recommendation.** packwiz stays the source of truth in the public repository. Every release produces:
- a `.mrpack`, published to Modrinth (once Artem says yes) and attached to the GitHub release;
- a server pack zip, built from the server side of the `.mrpack` or with `packwiz-installer -s server`;
- an optional Prism zip with auto-update, documented as "advanced, always latest".

CurseForge is skipped until Incoming has a CurseForge project. Even then, a CurseForge build would have to drop
Voxy and Roxy.

**Template-friendliness.** This follows Fabulously Optimized and Create: Astral, whose packs are built in public
repositories.
- The repository is public and forkable, with a "Use this as a template" section.
- A mod list table with each mod's role and its reason for being in the pack.
- Every config file is listed with its reason, as in our README today.
- Heavy or taste-dependent parts are optional mods: Voxy and Roxy, shaderpacks, Sound Physics, and Simple Voice Chat.
- `tools/` and CI are reusable: `check_loader.py` and `boot_check.py` work for any packwiz pack.

## 3. Licenses and redistribution

A Modrinth pack links files; it does not re-upload them. Modrinth's rule is that a file is fine if it is uploaded to
Modrinth, or its license allows redistribution, or its description grants permission, or the author agrees in
writing. "The author's wishes and any licensing agreements always take priority."

| mod | public Modrinth pack | condition / note | source |
|---|---|---|---|
| Voxy (ARR) | **yes, with conditions** | "Feel free to include the mod in modpacks ... as long as you link the mod back to this page and the version used is available on this modrinth mod page (i.e. please do not use or include unofficial backports or versions)". Our file is the official `H3w2nVdU`. Grey area: running it on NeoForge 1.21.1 through Roxy is what the author never released. | https://modrinth.com/mod/voxy |
| Roxy (MIT) | yes | "as long as it's downloaded from our official sources"; it does not redistribute Voxy | https://modrinth.com/mod/roxy |
| Create, Create Aeronautics | yes | code MIT, assets ARR: link only, never bundle | https://github.com/Creators-of-Create/Create/blob/HEAD/LICENSE.md · https://github.com/Creators-of-Aeronautics/Simulated-Project/blob/main/LICENSE.md |
| Sable, Sodium (PolyForm Shield) | yes | the restriction is only on competing products | https://github.com/ryanhcode/sable/blob/main/LICENSE.md |
| Immersive Aircraft (GPL-3.0) | yes | none | https://modrinth.com/mod/immersive-aircraft |
| Man of Many Planes, Jade (CC-BY-NC-SA), Big Cannons (assets CC-BY-NC-SA), 3D Skin Layers, Entity Culling (tr7zw: no "monetary compensation") | yes, **if the pack is not monetised** | credit; turn off payouts for the pack | https://github.com/Cannoneers-of-Create/CreateBigCannons/blob/0b3e234/LICENSE.md · https://github.com/tr7zw/NotEnoughAnimations/blob/main/LICENSE |
| Propulsion: Simulated | yes | free download, no sale of the pack | https://github.com/Propulsion-Team/create-propulsion-simulated/blob/main/LICENSE |
| Aeroworks | yes | official artifacts only, never in overrides | https://github.com/aeroworks-hangar/aeroworks-license/blob/main/LICENSE.md |
| Complementary Unbound | yes | visible credit on the pack page; problems are the pack author's responsibility | https://github.com/ComplementaryDevelopment/ComplementaryShadersV4/blob/main/License.txt |
| Photon | yes | its license explicitly allows "Redistribute Photon Shaders as part of a (commercial) Modpack"; re-uploading it to Modrinth or CurseForge needs permission, linking does not | https://github.com/sixthsurge/photon/blob/main/LICENSE |
| MakeUp Ultra Fast (LGPL), Euphoria Patches (MPL) | yes | — | Modrinth pages |
| **BSL** (ARR) | **no**, leave out | "You're not allowed to ... Redistribute the shaderpack without my permission" | https://modrinth.com/shader/bsl-shaders |
| **Solas** (ARR) | leave out | no modpack statement; its role is covered by the three shaderpacks we keep | https://modrinth.com/shader/solas-shader |
| **Flashback** (ARR) | leave out | "Do not redistribute. All rights reserved."; Fabric-only, runs through Connector; recording is our personal need | https://github.com/Moulberry/Flashback/blob/master/LICENSE.md |
| **Essential** (ARR, source-available) | leave out | no modpack grant; "reserves the right to revoke this permission at any time"; pushes an account and cosmetics service on players | https://github.com/EssentialGG/Essential/blob/main/LICENSE |
| Xaero's Minimap and World Map | yes | monetisation only through CurseForge or Modrinth; the pack name must not be confusable with Xaero's | https://modrinth.com/mod/xaeros-world-map |
| Subtle Effects, Contraption Lights, Default Options and Balm | yes | credit or link (Subtle Effects); do not use Default Options or Balm in the pack title | https://mods.twelveiterations.com/permissions |
| Fzzy Config (TDL-M) | yes | "Modpacks [may] include this software as long as ... via a manifest which would download this software from its respective CurseForge or Modrinth page" | https://github.com/fzzyhmstrs/fconfig/blob/master/LICENSE |
| Vista, Moonlight (Supplementaries Team License) | yes | "an unmodified copy obtained from Our Sources", not bundled | https://github.com/MehVahdJukaar/Supplementaries-Team-License/blob/main/LICENSE.md |
| LambDynamicLights (Lambda License) | yes, low risk | its binary clause asks for written approval to distribute binaries; a link to the Modrinth file is the "uploaded to Modrinth" case | https://github.com/LambdAurora/LambDynamicLights/blob/1.21.5/LICENSE |
| Vic's Point Blank, its Aeronautics compat, GraveStone, Ok Zoomer (ARR, no statement) | yes on Modrinth (Modrinth-hosted file) | no explicit grant: the weakest link of the war layer; ask the authors when going public | Modrinth pages |
| Incoming (GPL-3.0-only, ours) | yes | best as a Modrinth project (needs Artem's word); a GitHub release URL is allowed by the format, with "Your project" on the permissions page | https://github.com/zentixua/incoming |

**Our inclusion policy.** Modrinth's rule would let us link any Modrinth-hosted file. We go one step stricter: we
leave out a file when the author's own text forbids redistribution (BSL, Flashback) or makes the permission
revocable (Essential). We also leave out a mod that duplicates a role already filled (Solas: Photon, Complementary
and MakeUp cover the shader range). ARR mods with no statement either way (Point Blank, GraveStone, Ok Zoomer) stay
as Modrinth-hosted links, and we ask their authors before listing.

**Voxy and Roxy, plainly.** They do not block a Modrinth listing. By the letter of the page, we use the official
Modrinth file, link back to the page, and never re-upload it. The soft spot is the spirit: the author asks packs not
to ship "unofficial backports". Roxy is not a modified Voxy, but it runs a 1.21.11 Fabric build on NeoForge 1.21.1,
which the author did not release.

What we do about it:
- Voxy and Roxy are optional and off by default. Prism's `.mrpack` dialog shows optional files unchecked;
  in the public packwiz files `voxy.pw.toml` gets `default = false` and an English option text that says to tick
  Roxy and Voxy together (today it is `default = true`, in Russian). Neither format can bind two optional files, so
  the pack page says it too. They have extra limits anyway: OpenGL 4.6, no macOS without Roxy's patch, and "Geometry OOM" on 8 GB cards at section render distance 16.
- The pack page credits and links Voxy, says Roxy issues go to Roxy and never to Voxy (Roxy's own request), and drops
  Voxy at once if its author objects.
- A courtesy note to the Voxy author before listing would remove the doubt, but it needs Artem's word.

If the Voxy author objects, the pack keeps working without LOD: Voxy is optional.

**What would block a CurseForge version:**
- Incoming is not on CurseForge.
- Voxy is not on CurseForge and is ARR, and Roxy is useless without it.
- Flashback, BSL and Solas.
- Possibly LambDynamicLights and the ARR mods without a statement, whose distribution toggle we cannot read without
  an API key.

## 4. Pack variants

The core shared by all variants is today's tested Open Skies base without our personal mods:
- NeoForge 1.21.1;
- Create 6.0.10, Sable 2.0.6, Create Aeronautics 1.3.2 (pinned);
- Incoming;
- Immersive Aircraft and Man of Many Planes;
- Big Cannons and RPL;
- Propulsion and Aeroworks;
- Vic's Point Blank and its Aeronautics compat;
- Tweaked Controllers;
- the performance stack, JEI, Jade, Xaero's maps, GraveStone and Mouse Tweaks.

Our personal mods stay in the friends' fork: Almighty, TrueUUID, LAN Server Properties, Essential, the Flashback trio,
MapSyncer, and the Vista/Silo configs.

### A. "Frontline": aviation warfare and Create (about 75 mods)
- **Concept:** today's pack, cleaned for the public; build machines, fly and fight.
- **Mods by role:** the core; Create Deco, Connected and Diesel Generators; Do a Barrel Roll; the sound and atmosphere
  layer (Subtle Effects, Particle Rain, AmbientSounds, Sound Physics, Burnt); Photon, Complementary and MakeUp
  shaderpacks (optional); Voxy and Roxy plus LOD Server Support (optional); Open Parties and Claims for servers.
- **First hour:** vanilla start, a Strike Designator and a Shahed (vanilla recipes work without Create), a Create
  waterwheel, the first biplane.
- **First week:** an Aeronautics airship, Big Cannons on a fort, SAM air defense, salvos at other players' bases with
  spotting rules; nuclear weapons stay operator-only.
- **PC:** 6 GB allocated, 16 GB system RAM, a GTX 1660 or RX 580 class card without shaders. With Voxy: OpenGL 4.6
  and a card with more than 8 GB, or Voxy's default render distance.
- **Pros:** almost all of it is already tested by `boot_check.py` and by our play. Lowest maintenance.
- **Cons:** a thin survival loop. Once the war is over there is little to do, and the niche is crowded by Create
  Aeronautics packs.
- **Maintenance:** about 2–3 hours a month.

### B. "Open Skies": balanced survival, war and adventure (about 110 mods), **recommended**
- **Concept:** a world worth defending. Explore and settle, build with Create, fly everywhere, fight when you choose.
- **Mods:** A plus about 35. Each one has a single job; versions come from the Modrinth API, 24.11.
  - **Exploration:** YUNG's Better Dungeons, Mineshafts, Strongholds and Temples, with YUNG's API (LGPL);
    Towns and Towers (CC-BY-NC-SA). No terrain overhaul: vanilla terrain keeps worlds cheap to generate and Voxy
    looks right.
  - **Food:** Farmer's Delight (MIT) and Create Central Kitchen (LGPL).
  - **Storage:** Sophisticated Backpacks and Storage (ARR, widely packed).
  - **Loot:** Lootr (per-player chests: fair on servers).
  - **Servers:** Open Parties and Claims (LGPL: claims, parties and PvP rules); Simple Voice Chat (optional).
  - **No teleports and no Waystones**, by design: aircraft and Create trains are the travel, which keeps the theme
    coherent and gives flight a purpose.
  - **No quest book:** advancements (Incoming has its own), and a "first hour" page in the README and the pack
    description.
- **First hour:** survive the first night, loot a YUNG's dungeon or a Towns and Towers village, a Create mill and a
  cooking pot, the first biplane to scout.
- **First week:**
  - a base with SAM cover and sirens;
  - an airship freight route between towns;
  - raids on dungeons from the air;
  - optional PvP between parties under Incoming's spotting rules;
  - claims protect builds from casual griefing.
- **Balance knobs we already have, without code:**
  - Incoming world rules: block damage and fire on or off, a per-player active-strike limit, and nuclear weapons
    operator-only by default;
  - the pack's server config notes;
  - a KubeJS cooldown recipe for strike costs in Incoming's pack-maker guide, as an example for servers rather than a
    default.
- **PC:** as A, with about 1 GB more RAM for structures.
- **Pros:**
  - It answers "fun for everyone": the PvE loop works without war.
  - It shows Incoming in a real world.
  - It is still small enough to test fully in CI.
- **Cons:**
  - About 35 more mods to update.
  - Structure mods need a balance pass so that loot does not outclass Create progression.
  - It must be checked that claims actually stop Incoming's custom destruction (open question: Incoming documents no
    claim integration; it is a candidate Incoming feature).
- **Maintenance:** about 4–6 hours a month at monthly releases.

### C. "Lite" profile (not a separate pack)
B with the heavy parts unticked: no Voxy, no shaderpacks, no Sound Physics, no Simple Voice Chat. That means 4–5 GB
allocated and an integrated or older card. It is shipped as optional mods inside B, not as a second pack: one pack,
one test matrix, one changelog.

### D. Progression campaign (FTB Quests, KubeJS gating): **rejected**
It is the most expensive type to build, it suits single-player best, FTB Quests is not on Modrinth (CurseForge
only), and it contradicts "fun for everyone".

Hour and GPU figures above are estimates from our own pack (6144 MB allocated today, Voxy OOM seen on 8 GB cards),
not measurements of variant B. The candidate mods' compatibility with the pinned Create 6.0.10 was not tested here;
building B means adding them in waves through `check_loader.py` and `boot_check.py`.

**Recommendation: B**, with C as its optional profile.

## 5. Name

Checked 24.11.2026 through the Modrinth API (`/v2/project/<slug>`), cfwidget for CurseForge, and the GitHub API.

| name | Modrinth | CurseForge | GitHub (zentixua) | note |
|---|---|---|---|---|
| **Open Skies** | slug `open-skies` free | slug `open-skies` taken by a dead 2017 pack (last file 2017-09-10, 2,766 downloads); our project would get another slug | `zentixua/open-skies` is the friends' pack, so the public repository needs another repository name | continuity with what friends know; fits a flight pack; also the name of a real-world treaty, harmless |
| Contested Skies | free | free | free | says "war in the air"; less friendly to the survival half |
| Air Superiority | free | free | free | narrow, military |

**Recommended:** "Open Skies", with Modrinth slug `open-skies` and public repository `zentixua/open-skies-modpack`. If
CurseForge ever matters, the title can stay "Open Skies" with a different slug (unverified whether CurseForge allows
a duplicate title). Default Options and Balm forbid their names in a pack title, and Xaero forbids confusable names;
none of the candidates conflict.

## 6. Repository structure: public upstream and the friends' fork

**Facts that shape it:**
- `zentixua/open-skies` is **already public** on GitHub and is not a fork (checked with `gh api`). It carries the team
  and operations docs (`.claude/rules/team.md`, `docs/team/*`: servers, laptop, agent procedures). We found no
  secrets in them, but it is not a private repository.
- It cannot be made private without breaking friends' instances. Prism's pre-launch command reads
  `raw.githubusercontent.com/zentixua/open-skies/main/pack/pack.toml` without a token, and the release downloads
  need no sign-in.
- A GitHub fork of a public repository is always public, and an account cannot fork its own repository
  (https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-permissions-and-visibility-of-forks).
  The "fork" is therefore a git relationship (an `upstream` remote), not GitHub's Fork button.
- `zentixua/open-skies` must keep its name. Friends' instances and the old `zentixua/airstrike-pack` redirect point at
  it. If the public pack took that name after a rename, the redirect would stop and every friend would silently get
  the public pack.

| what | public repository (`zentixua/open-skies-modpack`) | friends' repository (`zentixua/open-skies`) |
|---|---|---|
| `pack/` base: versions, mods, shaderpacks, configs with reasons | owns it | merges it from upstream |
| Almighty, TrueUUID, LAN Server Properties, Essential, Flashback, MapSyncer, Vista/Silo configs, ServerCore settings | no | adds them as its own files |
| auto-update Prism instance | optional, "advanced" | the default install, as today |
| `update.yml` (3-hourly Incoming, weekly Modrinth, each checked by CI) | yes, onto `main` only: `main` is the development line; players get monthly release tags | no own mod bumps: it merges upstream `main` every 3 hours instead (below) |
| `check_loader.py`, `boot_check.py` | yes | yes |
| release: GitHub release with `.mrpack` and server zip; Modrinth upload as a manual job | yes (the upload after Artem's word) | GitHub release only |
| `.claude/rules/team.md`, `docs/team/` | no | better moved to a private ops repository (Artem's word) |
| README | English: players and pack makers, "use as a template" | Russian: friends' install, as today |

**How the fork pulls upstream.** There is one update stream, upstream's, and the fork only adds files:
1. **Updates happen upstream only.** Today's `update.yml` moves to the public repository and keeps committing checked
   Incoming and Modrinth updates to upstream `main`. A public player is not affected: they install release tags, cut
   monthly (plus crash hotfixes), not `main`. The friends' fork drops its own mod bumps; its `update.yml` merges
   `upstream/main` into `pack-update` every 3 hours, so friends keep today's 3-hour delay for new Incoming releases.
   Almighty is the one fork-only mod with its own GitHub bump, and it lives in a file upstream never has.
2. **Shared history.** The public repository is created from this repository's history (a copy of `main`, then one
   commit that removes the personal files and rewrites the README in English), not from an empty tree. The fork
   records that commit once with `git merge -s ours` (taken as merged, nothing deleted), so later merges see only real
   changes. Without this the first merge has no common base (`--allow-unrelated-histories`) and conflicts in every file.
3. **Files that always differ** are resolved by standard git mechanisms, not by hand:
   - `README.md` (English upstream, Russian in the fork) has `merge=ours` in the fork's `.gitattributes`, with the
     `ours` driver enabled in CI;
   - `pack/index.toml` is always regenerated with `packwiz refresh`;
   - `pack/pack.toml` takes upstream's Minecraft and NeoForge versions, and its `version` is the upstream version
     plus a fourth number for the fork's own changes (`1.2.0` becomes `1.2.0.1`; no `+` or `-`, so tags, URLs and
     the existing release flow keep working; untested until built).

   Any other conflict fails the job and opens the existing "Automatic pack update failed" issue.
4. `build.yml` checks `pack-update` as today (index, loader ranges, boot from scratch, Flashback replay) and only then
   moves it to `main`.
5. Rule in both AGENTS.md files: a base change goes upstream first. The fork never edits a base file; its extras live
   only in files upstream never touches.
6. **Composition is Artem's call.** Merging upstream variant B would bring about 35 new mods (structures, claims,
   Lootr, backpacks) into the friends' world and server, and a new required mod needs Artem's word. So the fork
   starts merging upstream only after he says the friends' pack becomes "public base plus our extras". Until then the
   friends' repository runs exactly as today, and the public repository starts from today's base.

**CI:**
- **Public, every PR:** index freshness, `check_loader.py`, `boot_check.py` (server and client), `.mrpack` export, and
  a permission check: every file is a Modrinth CDN file or on an allowlist with its license and reason.
- **Public, version tag:** a GitHub release.
- **Public, Modrinth upload:** a separate manual workflow.
- **Fork:** as today, with the upstream merge instead of its own mod bumps.

## 7. Honest verdict

**Where it is weak or costly:**
- **The pinned stack.** Create 6.0.10, Sable 2.0.6 and Aeronautics 1.3.2 are pinned because Incoming and Almighty
  test against them. Public players expect "latest Create". Addons will move on, and every Create bump becomes a
  coordinated Incoming, Almighty and pack release.
- **Voxy through Roxy.** Roxy supports exactly one Voxy file (`0.2.16-beta+1.21.11`). If Roxy stalls, LOD freezes. If
  the Voxy author objects, LOD goes. Hence optional.
- **Support load.** Unknown PCs, crash logs, and macOS and Intel GPU players. This is the real cost, more than the
  mods. It needs an issue template that asks for logs, a FAQ, and the rule "Lite first".
- **Update churn.** About 110 mods update weekly. Public worlds cannot take silent updates, so the pack needs monthly
  releases with changelogs and hotfixes only for crashes, each through `boot_check.py`.
- **Server griefing.** Public war means griefing. Claims cover normal building; whether they cover Incoming
  destruction is open and must be verified before the pack is advertised for servers.
- **The niche.** Create Aeronautics packs are many. Our edge is Incoming, so the pack only makes sense while Incoming
  is actively developed.

**What would make it fail:**
- Listing without Incoming on Modrinth, so new players get a "download this jar from GitHub" step.
- Heavy defaults (Voxy and shaders on) that crash mid-range PCs in the first session.
- Scope creep towards a kitchen sink.
- No release discipline: silent breaking updates.
- No owner time for issues in the first month after launch.

**Overall:** worth doing as variant B. It is a showcase and a template for Incoming. It reuses our CI and checks,
stays small and Modrinth-only, ships versioned releases, and has a written scope cap.

## Needs Artem's word

1. Creating the public repository (`zentixua/open-skies-modpack`) and the name "Open Skies".
2. Publishing Incoming on Modrinth (and CurseForge later), and then the pack on Modrinth.
3. Contacting authors: a courtesy note to Voxy; asking Vic's Point Blank, Point Blank Aeronautics compat, GraveStone
   and Ok Zoomer for modpack permission.
4. Monetisation: we propose off, because of the non-commercial licenses.
5. Moving `.claude/rules/team.md` and `docs/team/` out of the public `zentixua/open-skies` into a private ops
   repository.
6. Whether the friends' pack becomes "public base plus our extras", which brings variant B's new mods into the
   friends' world and server (section 6, step 6).
