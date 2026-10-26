#!/usr/bin/env python3
"""Generate English-first and Russian release notes for the current pack version.

For each new version, add docs/releases/<version>.en.md with the English translation
of its README.md version-table row. CI requires both before a release can be built.
"""
import argparse
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parent.parent


def render(root=ROOT):
    pack = tomllib.loads((root / "pack/pack.toml").read_text(encoding="utf-8"))
    version = pack["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"Invalid pack version: {version!r}")
    rows = []
    for line in (root / "README.md").read_text(encoding="utf-8").splitlines():
        cells = line.split(" | ", 2)
        if len(cells) == 3 and cells[0] == f"| {version}":
            rows.append((cells[1], cells[2].removesuffix(" |")))
    if len(rows) != 1:
        raise ValueError(f"README.md: expected one version-table row for {version}, got {len(rows)}")
    mod, russian = rows[0]
    english = (root / f"docs/releases/{version}.en.md").read_text(encoding="utf-8").strip()
    if not english:
        raise ValueError(f"Empty English release notes for {version}")
    sections = []
    for language, changes in (("en", english), ("ru", russian)):
        changes = changes.replace("](#", "](https://github.com/zentixua/open-skies#")
        template = (root / f"docs/releases/template.{language}.md").read_text(encoding="utf-8")
        sections.append(template.format(**pack["versions"], mod=mod, changes=changes).strip())
    return "\n\n---\n\n".join(sections) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.write_text(render(), encoding="utf-8")
    print(f"English and Russian release notes → {args.out}")


if __name__ == "__main__":
    main()
