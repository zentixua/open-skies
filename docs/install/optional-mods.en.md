# Open Skies installation

`Open-Skies.zip` is a Prism Launcher instance that updates the pack before every game launch. In Prism, choose
"Add Instance…" → "Import" → this file. The instance uses the Minecraft and NeoForge versions from the pack and
6144 MB of memory. The first launch downloads the mods and asks which optional mods to install.

`Open-Skies.mrpack` installs one version in Prism Launcher or Modrinth App, without automatic updates.

## Optional mods

| Installer entry | Description |
|---|---|
| Flashback | Recording and replay (Flashback): only needed by players who record footage. |
| Flashback Neoforge Fixed | Recording and replay (Flashback): only needed by players who record footage. |
| Sinytra Connector | Recording and replay (Flashback): only needed by players who record footage. |
| Roxy | Long-distance rendering (Roxy and Voxy must be used together): requires OpenGL 4.6; disable both on macOS. |
| Voxy | Long-distance rendering (Roxy and Voxy must be used together): requires OpenGL 4.6; disable both on macOS. |

Enable all three recording mods together if you need recording. Roxy and Voxy are enabled by default in the
auto-updating instance. Prism's `.mrpack` import offers optional mods disabled: select both Roxy and Voxy except
on macOS.

On later launches, choose "Optional mods..." in packwiz-installer to change these choices. Do not toggle the pack's
mods on Prism's Mods page: packwiz-installer restores them.

The installer displays the pack's Russian descriptions. It reads one `option.description` string per mod;
there is no per-language description field in the [packwiz format](https://packwiz.infra.link/reference/pack-format/mod-toml/#option).
The [installer's options window](https://github.com/packwiz/packwiz-installer/blob/main/src/main/kotlin/link/infra/packwiz/installer/ui/gui/OptionsSelectWindow.kt)
displays that string directly. This page supplies the English descriptions; it does not switch the installer's language.
