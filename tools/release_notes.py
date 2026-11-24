#!/usr/bin/env python3
"""Release notes for the pack version in pack/pack.toml, from its section in CHANGELOG.md.

Every new version needs a `## <version>` section in CHANGELOG.md; CI runs this on every PR, so a version without one
cannot reach main or be released.

Usage: python3 tools/release_notes.py OUT
"""
import argparse
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/zentixua/open-skies"


def render(root=ROOT):
    pack = tomllib.loads((root / "pack/pack.toml").read_text(encoding="utf-8"))
    version = pack["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid pack version: {version!r}")
    sections = re.split(r"^## ", (root / "CHANGELOG.md").read_text(encoding="utf-8"), flags=re.M)[1:]
    found = [s.split("\n", 1) for s in sections if s.split("\n", 1)[0].split()[:1] == [version]]
    if len(found) != 1 or not found[0][1].strip():
        raise ValueError(f"CHANGELOG.md: expected one non-empty '## {version}' section, got {len(found)}")
    incoming = tomllib.loads((root / "pack/mods/incoming.pw.toml").read_text(encoding="utf-8"))["filename"]
    incoming = incoming.removeprefix("incoming-").removesuffix(".jar")
    versions = pack["versions"]
    changes = found[0][1].strip().replace("](#", f"]({REPO}#")
    return (f"Minecraft {versions['minecraft']}, NeoForge {versions['neoforge']}, Incoming {incoming}.\n\n"
            f"{changes}\n\n"
            "### Installation\n\n"
            "- `Open-Skies.mrpack`: import it in Modrinth App, Prism Launcher or ATLauncher. Stays on this version.\n"
            "- `Open-Skies.zip`: a Prism Launcher instance that updates itself to the latest release before every "
            "launch (\"Add Instance\" → \"Import\").\n\n"
            f"Requirements, servers and optional parts: [README]({REPO}#install).\n")


def main():
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.write_text(render(), encoding="utf-8")
    print(f"Release notes → {args.out}")


if __name__ == "__main__":
    main()
