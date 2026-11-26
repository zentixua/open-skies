# Store kit: Modrinth and CurseForge

Everything needed to put Open Skies on a store page, ready to paste. Nothing here is published: creating a store
project, uploading and publishing need the owner's word (AGENTS.md, "Stores"). Until then the pack is on GitHub only.

## Verdict per platform (26.11.2026)

| Platform | Verdict | What has to happen first |
|---|---|---|
| GitHub | **live** | Releases with `.mrpack` and the Prism zip; this README and the images. |
| Modrinth | **later, ready to upload** | 1. Incoming public on Modrinth, then `pack/mods/incoming.pw.toml` switched to its Modrinth file (a pack release). Until then the `.mrpack` links Incoming from GitHub, which Modrinth accepts only with a permission declaration ("Your project"). 2. The "Contains AI-generated content" disclosure set (rule 6.1). Store images are in-game frames only (rule 6.2, below). |
| CurseForge | **later** | Not reachable as the pack is today: Voxy (and so Roxy and LOD Server Support) cannot be in a CurseForge pack, Incoming is not on CurseForge, packs must be built with the CurseForge App, and some files are unverified there. |

**Why Modrinth waits.** Modrinth reviews modpacks by hand. Since June 2026 a creator declares a permission for every
file not hosted on Modrinth before submitting, and the version is withheld until that is reviewed
([modpack permissions](https://modrinth.com/news/article/modpack-permissions)). Its content rules
([rules](https://modrinth.com/legal/rules), 6.1–6.2) require the AI disclosure when "a substantial portion of the
project's code is a product of AI output" or "any element of the project's page such as description or publishing
relies on generative AI", and forbid gallery, icon or description images "created or derived from generative AI
output". The pack's own files and these texts were written with Claude's help, so the disclosure applies. The store images are therefore
in-game frames only: [icon-ingame.png](../media/icon-ingame.png) (a crop of the airship frame) as the icon and
[banner-store.jpg](../media/banner-store.jpg) (the banner's frame without the wordmark) at the top of the description.
The pixel icon and wordmark were placed cell by cell in code written with AI assistance ([../media/src](../media/src)),
which a moderator could read as "derived from generative AI output": they stay on GitHub. Weapons content is not a rule issue on either store: Modrinth and CurseForge host similar
mods (HBM's Nuclear Tech, ICBM, Warium, Superb Warfare); the page keeps real-world politics out.

**Why CurseForge waits.** CurseForge packs may contain only CurseForge files, or non-CurseForge mods on its approved
list; mods whose permission adds conditions beyond credit, such as Voxy's "link back", "will not be considered"
([third-party mods](https://support.curseforge.com/support/solutions/articles/9000197908)). Voxy has no CurseForge
page. Packs "must be created with the CurseForge App"
([moderation policies](https://support.curseforge.com/en/support/solutions/articles/9000197279)). A CurseForge
edition would be a different pack (no Voxy, Incoming published there first).

## Fields

| Field | Value |
|---|---|
| Title | Open Skies |
| Slug | `open-skies` |
| Summary (EN) | Build Create airships, fly anywhere and defend your world with air strikes from Incoming. A survival sandbox for friends. |
| Summary (RU, extra field only) | Стройте дирижабли Create, летайте куда угодно и защищайте свой мир авиаударами Incoming. Песочница для игры с друзьями. |
| Description | [description.md](description.md), then a `---` line, then [description.ru.md](description.ru.md) |
| Game, loader | Minecraft 1.21.1, NeoForge (version in `pack/pack.toml`) |
| Environment | Client required, server optional (singleplayer works; servers install the server side) |
| Modrinth categories | Technology, Adventure, Multiplayer; additional: Combat |
| CurseForge categories (later) | Tech (main); Exploration, Multiplayer |
| License | MIT (the repository's own files; each mod keeps its license) |
| Source | https://github.com/zentixua/open-skies |
| Issues | https://github.com/zentixua/open-skies/issues |
| Wiki | https://github.com/zentixua/open-skies#readme |
| Discord, donations | none |
| Icon | [icon-ingame.png](../media/icon-ingame.png) 512×512 (Modrinth); [icon-ingame-400.png](../media/icon-ingame-400.png) 400×400 (CurseForge avatar). Not the pixel icon (rule 6.2, above) |
| Version name, file | `Open Skies <version>`, the release's `Open-Skies.mrpack` (same file as on GitHub) |
| Changelog | the version's section of [CHANGELOG.md](../../CHANGELOG.md) |
| Content disclosure | Contains AI-generated content (the pack's tools and these texts were written with AI assistance; the store images are untouched in-game frames) |

The description repeats no download links: stores install through their own launchers, and CurseForge forbids
external downloads. Images are absolute `raw.githubusercontent.com` links to `main`; they load once this kit is
merged.

## Gallery

Untouched in-game frames, 1920×1080, from this pack with Complementary Unbound + Euphoria Patches. The world is a fresh one; scenes were set up with commands, and the airship is a real Create
Aeronautics contraption assembled from blocks. Featured image: the first.

| File | Title | Description |
|---|---|---|
| [airship-valley.jpg](../media/gallery/airship-valley.jpg) | Airship over the valley (featured) | A Create Aeronautics airship and a biplane over a river valley at sunset. |
| [airship.jpg](../media/gallery/airship.jpg) | Built from blocks | Balloon, burner, gondola and propeller: an airship assembled with Create Aeronautics. |
| [strike.jpg](../media/gallery/strike.jpg) | Incoming: cruise missile strike | A missile salvo hits a village at dusk. |
| [blast-wave.jpg](../media/gallery/blast-wave.jpg) | Blast wave | Dust from the impact rolls over the hillside. |
| [jungle-village.jpg](../media/gallery/jungle-village.jpg) | Towns and Towers | A jungle village among the trees in the morning. |

Also in [../media](../media): [banner-store.jpg](../media/banner-store.jpg) 1920×640 (store page header, a plain
frame); [banner.jpg](../media/banner.jpg) and [features.jpg](../media/features.jpg) (with the wordmark and typeset
labels) are for GitHub only. How each image was made:
[../media/src](../media/src).

## License pass (26.11.2026)

All 98 files (95 mods, 3 shaderpacks) were checked against the Modrinth API and their upstream licenses. A `.mrpack`
links files and bundles none, so Modrinth's question is whether each file may be linked; CurseForge's is whether each
is on CurseForge with distribution allowed.

| File | License | Modrinth | CurseForge | Source |
|---|---|---|---|---|
| Incoming 3.13.0 | GPL-3.0-only (the owner's mod) | after Incoming is on Modrinth, or declared "Your project" | no: not on CurseForge | [releases](https://github.com/zentixua/incoming/releases) |
| Voxy 0.2.16-beta+1.21.11 | All Rights Reserved; modpacks allowed "as long as you link the mod back to this page and the version used is avaible on this modrinth mod page. (i.e. please do not use or include unofficial backports or versions)". The pack links that official file unmodified; Roxy runs it on 1.21.1, which a moderator may ask about | yes (Modrinth CDN, credited) | no: link-back condition, no CurseForge page | [modrinth.com/mod/voxy](https://modrinth.com/mod/voxy) |
| Roxy, LOD Server Support | MIT | yes | no Voxy, no use (LOD Server Support's 1.21.1 file there unverified) | [Roxy](https://modrinth.com/mod/roxy), [LSS](https://modrinth.com/mod/lod-server-support) |
| Create Aeronautics (bundled) 1.3.2 | code MIT, assets All Rights Reserved | yes (Modrinth CDN) | unverified: a CurseForge project exists, this file not confirmed | [source](https://github.com/Creators-of-Aeronautics/Simulated-Project) |
| GraveStone × Sable patch 1.0.0 | MIT | yes | not on CurseForge: needs the approved list | [source](https://github.com/thallada/gravestone-sable-compat) |
| Photon shader v1.4 | Photon License: no redistribution on paying platforms without permission, but "Redistribute Photon Shaders as part of a (commercial) Modpack" is allowed | yes (linked from its own Modrinth page) | yes (same clause) | [LICENSE](https://github.com/sixthsurge/photon/blob/main/LICENSE) |
| Complementary Unbound r5.10 | Complementary agreement: modpacks through the platforms' own systems, unmodified, credited | yes (credited) | yes | [License.txt](https://github.com/ComplementaryDevelopment/ComplementaryReimagined/blob/main/License.txt) |
| MakeUp Ultra Fast | LGPL-3.0-or-later | yes | yes | [source](https://github.com/javiergcim/MakeUpUltraFast) |
| Non-commercial: Jade, Man of Many Planes, Towns and Towers, Cristel Lib, Big Cannons assets, Propulsion, 3D Skin Layers, Entity Culling, Not Enough Animations, Better Advancements | CC-BY-NC(-SA/-ND) or custom non-commercial | yes: hosted on Modrinth, linked only; the pack is never monetised | yes: all on CurseForge | Modrinth API |
| Custom or All Rights Reserved, modpacks allowed: Point Blank, Xaero's maps, Sophisticated ×3, Simple Voice Chat, GraveStone, Lootr, Ok Zoomer, Subtle Effects (credit), Default Options and Balm (names out of the pack title), Contraption Lights, Create, Aeroworks, Sable, Sodium, LambDynamicLights, Fzzy Config, Aeronautics Camera Sync | various | yes (Modrinth CDN) | yes, a few unconfirmed (Sophisticated Core, Simple Voice Chat, Balm) | Modrinth API |
| 57 others | MIT, LGPL, GPL, AGPL, Apache, BSD, MPL, Unlicense, WTFPL | yes | yes; unconfirmed: Iris, FerriteCore, Chunky, YUNG's Better Dungeons, YUNG's Bridges | Modrinth API |

Creator rewards: Modrinth pays uploaders automatically and documents no opt-out
([rewards](https://modrinth.com/legal/cmp-info)); CurseForge rewards are opt-in per account. Because of the
non-commercial mods, the pack's project must never take rewards.
