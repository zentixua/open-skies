#!/usr/bin/env python3
"""Every mod in the pack accepts its NeoForge version from pack.toml.

Downloads the jar for each mods/*.pw.toml (checking its hash), reads META-INF/neoforge.mods.toml, including in
nested jars (listed in META-INF/jarjar/metadata.json, loaded by NeoForge as separate mods), and checks the neoforge
dependency's versionRange against the pack's version. Otherwise, the game stops at "Error loading mods":
Forgified Fabric API 2.3.6 in pack 0.1.27 required NeoForge 21.1.262 while the pack used 21.1.259. Minecraft is not
checked: the pack does not change it, and some mods for 1.21.1 use ranges such as "[1.21,1.21.1)" (Iris, JEI),
yet the game still loads them.

Usage: python3 tools/check_loader.py [pack directory, default: pack]
"""
import concurrent.futures
import hashlib
import http.client
import io
import json
import re
import sys
import tomllib
import urllib.request
import zipfile
from pathlib import Path

CHECKED = ("neoforge",)


def version_key(v):
    """Maven version order for our cases: compare numbers, then put a qualifier (-beta) before no qualifier."""
    v = v.strip()
    main, _, qualifier = v.partition("-")
    nums = [int(n) if n.isdigit() else 0 for n in re.split(r"[.+]", main) if n != ""]
    while nums and nums[-1] == 0:
        nums.pop()
    return nums, 0 if qualifier else 1


def cmp(a, b):
    na, qa = version_key(a)
    nb, qb = version_key(b)
    width = max(len(na), len(nb))
    na, nb = na + [0] * (width - len(na)), nb + [0] * (width - len(nb))
    return (na > nb) - (na < nb) or (qa > qb) - (qa < qb)


def in_range(version, spec):
    """Maven versionRange: "[a,b)", "(,b]", "[a]", or comma-separated ranges; a bare version or "*" is unrestricted."""
    spec = spec.replace(" ", "")
    if spec in ("", "*") or spec[0] not in "[(":
        return True
    for token in re.findall(r"[\[(][^\])]*[\])]", spec):
        lo_br, body, hi_br = token[0], token[1:-1], token[-1]
        if "," not in body:  # [a]: exactly this version
            if cmp(version, body) == 0:
                return True
            continue
        lo, hi = body.split(",", 1)
        ok_lo = not lo or (cmp(version, lo) >= 0 if lo_br == "[" else cmp(version, lo) > 0)
        ok_hi = not hi or (cmp(version, hi) <= 0 if hi_br == "]" else cmp(version, hi) < 0)
        if ok_lo and ok_hi:
            return True
    return False


def dependencies(toml_text):
    """(mod, dependency modId, versionRange, type) from neoforge.mods.toml; None if the file is not TOML."""
    try:
        data = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError:
        return None
    for owner, deps in (data.get("dependencies") or {}).items():
        for dep in deps if isinstance(deps, list) else []:
            kind = str(dep.get("type", "required" if dep.get("mandatory", True) else "optional")).lower()
            yield owner, dep.get("modId"), dep.get("versionRange", ""), kind


def scan(jar_bytes, label, versions, problems):
    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as z:
        names = z.namelist()
        if "META-INF/neoforge.mods.toml" in names:
            deps = dependencies(z.read("META-INF/neoforge.mods.toml").decode("utf-8", "replace"))
            if deps is None:
                problems.append(f"{label}: neoforge.mods.toml cannot be parsed as TOML")
            else:
                for owner, mod, spec, kind in deps:
                    if mod in CHECKED and kind not in ("incompatible", "discouraged") \
                            and not in_range(versions[mod], spec):
                        problems.append(f"{label}: mod {owner} requires {mod} {spec}, the pack has {versions[mod]}")
        if "META-INF/jarjar/metadata.json" in names:
            nested = [j["path"] for j in json.loads(z.read("META-INF/jarjar/metadata.json")).get("jars", [])]
        else:
            nested = [n for n in names if n.endswith(".jar")]
        for name in nested:
            if name in names:
                scan(z.read(name), f"{label} → {name.rsplit('/', 1)[-1]}", versions, problems)


def fetch(meta_path):
    meta = tomllib.loads(meta_path.read_text(encoding="utf-8"))
    if not meta.get("filename", "").endswith(".jar"):
        return meta_path.name, None, None
    download = meta["download"]
    for attempt in range(3):  # An interrupted download is not a pack error.
        try:
            with urllib.request.urlopen(download["url"], timeout=120) as r:
                body = r.read()
            break
        except (OSError, http.client.HTTPException):
            if attempt == 2:
                raise
    digest = hashlib.new(download["hash-format"], body).hexdigest()
    if digest != download["hash"]:
        return meta["filename"], None, f"{meta['filename']}: {download['hash-format']} hash does not match .pw.toml"
    return meta["filename"], body, None


def main():
    pack = Path(sys.argv[1] if len(sys.argv) > 1 else "pack")
    pack_toml = tomllib.loads((pack / "pack.toml").read_text(encoding="utf-8"))
    versions = {k: pack_toml["versions"][k] for k in CHECKED}
    problems = []
    metas = sorted((pack / "mods").glob("*.pw.toml"))
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        for name, body, error in pool.map(fetch, metas):
            if error:
                problems.append(error)
            elif body is not None:
                scan(body, name, versions, problems)
    print(f"NeoForge {versions['neoforge']}: checked {len(metas)} mods")
    for p in problems:
        print("  " + p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
