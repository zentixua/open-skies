#!/usr/bin/env python3
"""Every file in the pack comes from a source we may link in a public pack.

A Modrinth pack links files, it never re-uploads them. Modrinth's rule: a file is fine if it is hosted on Modrinth,
or its license or author allows redistribution. This pack is one step stricter (README, "Licenses and credits"):
- a file on the Modrinth CDN passes, unless its project is on EXCLUDED (the author forbids redistribution or can
  revoke the permission);
- any other download URL must match an ALLOWED entry, which records the license and why the file is linked from
  there. A `.mrpack` accepts only a few download hosts (MRPACK_HOSTS), so an allowed URL must also be on one of them.
Also checked: every file has a valid `side`, and shaderpacks are client-only (packwiz writes "both" for Modrinth
shaderpacks, whose environment is unspecified).

Usage: python3 tools/check_sources.py [pack directory, default: pack]
"""
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse

MODRINTH_CDN = "cdn.modrinth.com"
# Download hosts a .mrpack may use (Modrinth modpack format).
MRPACK_HOSTS = {"cdn.modrinth.com", "github.com", "raw.githubusercontent.com", "gitlab.com"}
# (URL pattern, license, reason): files linked from outside Modrinth.
ALLOWED = [
    (r"https://github\.com/zentixua/incoming/releases/download/v[^/]+/incoming-[^/]+\.jar", "GPL-3.0-only",
     "Incoming, this pack's own mod: the official GitHub release jar (not on Modrinth yet; a .mrpack may link github.com)"),
]
# Modrinth project id: (name, reason it stays out).
EXCLUDED = {
    "Q1vvjJYV": ("BSL Shaders", "ARR, redistribution without the author's permission is forbidden"),
    "EpQFjzrQ": ("Solas Shader", "ARR without a modpack statement; Photon, Complementary and MakeUp cover its role"),
    "4das1Fjq": ("Flashback", "ARR, 'Do not redistribute'"),
    "QaOcZcLU": ("Flashback NeoForge Fixed", "needs Flashback"),
    "k2ZPuTBm": ("Essential", "the permission to include it can be revoked at any time; pushes an account service"),
}
SIDES = {"client", "server", "both"}


def problems(pack: Path):
    for f in sorted(pack.rglob("*.pw.toml")):
        rel = f.relative_to(pack)
        meta = tomllib.loads(f.read_text(encoding="utf-8"))
        side = meta.get("side")
        if side not in SIDES:
            yield f"{rel}: side {side!r}, expected one of {sorted(SIDES)}"
        if rel.parts[0] == "shaderpacks" and side != "client":
            yield f"{rel}: shaderpacks are client-only (side = \"client\")"
        url = meta.get("download", {}).get("url", "")
        host = urlparse(url).hostname or ""
        if host == MODRINTH_CDN:
            pid = meta.get("update", {}).get("modrinth", {}).get("mod-id") or url.split("/")[4]
            if pid in EXCLUDED:
                name, why = EXCLUDED[pid]
                yield f"{rel}: {name} stays out of this pack: {why}"
            continue
        if host not in MRPACK_HOSTS:
            yield f"{rel}: {url or 'no download URL'}: a .mrpack cannot link {host or 'it'}"
            continue
        if not any(re.fullmatch(pattern, url) for pattern, _, _ in ALLOWED):
            yield (f"{rel}: {url} is not on the Modrinth CDN; add it to ALLOWED in tools/check_sources.py with its "
                   "license and the reason it may be linked")


def main():
    pack = Path(sys.argv[1] if len(sys.argv) > 1 else "pack")
    found = list(problems(pack))
    for p in found:
        print(p)
    count = len(list(pack.rglob("*.pw.toml")))
    if found:
        sys.exit(f"{len(found)} problem(s) in {count} files")
    print(f"{count} files: Modrinth CDN or allowed sources, sides valid")


if __name__ == "__main__":
    main()
