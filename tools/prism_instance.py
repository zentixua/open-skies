#!/usr/bin/env python3
"""Prism Launcher instance with the pack/ modpack, updated automatically before every game launch.

  tools/prism_instance.py [dist/Open-Skies.zip]

The archive contains an empty instance (Minecraft and NeoForge from pack.toml, memory as in the instructions for
friends) and packwiz-installer-bootstrap in the game directory. The instance's pre-launch command runs
packwiz-installer with the pack from this repository's main branch
(https://packwiz.infra.link/tutorials/installing/packwiz-installer/). In Prism: "Add Instance" → "Import" → this
file. On the first launch, packwiz-installer downloads the mods and asks about optional ones; on every later
launch, it applies changes to pack/ on main. The archive does not depend on the pack version: packwiz-installer
updates the instance's Minecraft and NeoForge versions to match pack.toml (after asking the player).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tomllib
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_URL = "https://raw.githubusercontent.com/zentixua/open-skies/main/pack/pack.toml"
BOOTSTRAP = "packwiz-installer-bootstrap.jar"
BOOTSTRAP_URL = f"https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/{BOOTSTRAP}"
BOOTSTRAP_SHA256 = "a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"
# With headroom: measured on the laptop, the game with shaders needs 1.5–2.5 GB of live memory.
MAX_MEMORY_MB = 6144
# Prism components (mmc-pack.json) by [versions] keys in pack.toml, also checked by packwiz-installer.
COMPONENTS = {"minecraft": "net.minecraft", "neoforge": "net.neoforged"}
USER_AGENT = "zentixua/open-skies tools/prism_instance.py"


def ini_value(s):
    """An instance.cfg value as written by Prism (QSettings, INI format): backslash-escape \\ and "."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("out", nargs="?", default=os.path.join(ROOT, "dist", "Open-Skies.zip"))
    a = ap.parse_args()

    with open(os.path.join(ROOT, "pack", "pack.toml"), "rb") as f:
        pack = tomllib.load(f)
    versions = pack["versions"]
    unknown = versions.keys() - COMPONENTS.keys()
    if unknown:
        sys.exit(f"pack.toml: no Prism component for {', '.join(sorted(unknown))}")

    req = urllib.request.Request(BOOTSTRAP_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        bootstrap = r.read()
    got = hashlib.sha256(bootstrap).hexdigest()
    if got != BOOTSTRAP_SHA256:
        sys.exit(f"{BOOTSTRAP}: sha256 {got} ≠ {BOOTSTRAP_SHA256}")

    # Command from the packwiz instructions; Prism runs the pre-launch command in the instance's game directory.
    command = f'"$INST_JAVA" -jar {BOOTSTRAP} {PACK_URL}'
    instance_cfg = "".join(f"{k}={v}\n" for k, v in [
        ("ConfigVersion", "1.3"),
        ("InstanceType", "OneSix"),
        ("name", ini_value(pack["name"])),
        ("notes", ini_value(
            '<a href="https://github.com/zentixua/open-skies/blob/main/docs/install/optional-mods.en.md">'
            'Installation and optional mods (EN)</a><br>'
            '<a href="https://github.com/zentixua/open-skies/blob/main/docs/install/optional-mods.ru.md">RU</a>'
        )),
        ("OverrideCommands", "true"),
        ("PreLaunchCommand", ini_value(command)),
        ("OverrideMemory", "true"),
        ("MaxMemAlloc", str(MAX_MEMORY_MB)),
    ])
    components = [{"uid": COMPONENTS[k], "version": versions[k]} for k in ("minecraft", "neoforge") if k in versions]
    components[0]["important"] = True  # Minecraft: Prism does not allow removing it from the instance.
    mmc_pack = json.dumps({"components": components, "formatVersion": 1}, indent=4) + "\n"

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in [("instance.cfg", "[General]\n" + instance_cfg), ("mmc-pack.json", mmc_pack),
                           (f"minecraft/{BOOTSTRAP}", bootstrap),
                           *[(f"docs/optional-mods.{lang}.md",
                              (Path(ROOT) / "docs" / "install" / f"optional-mods.{lang}.md").read_bytes())
                             for lang in ("en", "ru")]]:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = (stat.S_IFREG | 0o644) << 16  # Regular file, rw-r--r--: without permissions, extraction sets zero.
            z.writestr(info, data, zipfile.ZIP_DEFLATED)
    print(f"{pack['name']}: " + ", ".join(f"{k} {v}" for k, v in versions.items()) + f"; pack {PACK_URL} → {out}")


if __name__ == "__main__":
    main()
