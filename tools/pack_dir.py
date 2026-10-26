#!/usr/bin/env python3
"""Game directory from pack/ (packwiz), without Prism or packwiz: for Incoming's prod_client.py client checks.

  tools/pack_dir.py ../airstrike/mod/run/pack-b [--optional]
  (in zentixua/incoming) tools/prod_client.py <scenario> --no-copy --dir mod/run/pack-b
                                                            (prod_client.py installs the mod build with scenarios)

The same files Prism installs from the pack's .mrpack: mods and shaderpacks from `*.pw.toml` (each download is
checked against its hash), other files from index.toml (`config/…`) copied as is. Client only: `side = "server"`
is not installed. Optional mods (`[option] optional = true`) follow their default checkbox (`default`, as in
packwiz-installer): disabled ones become `<file>.disabled`, as Prism installs them when unchecked; --optional
enables all of them. The index must be fresh (metafile hashes are checked, as in CI: `packwiz refresh`).
Downloads are cached by hash (default: run/pack-cache) and are not downloaded again. The directory must be new
or have no mods/: do not mix with an earlier set of mods.
"""
import argparse
import hashlib
import http.client
import os
import shutil
import sys
import time
import tomllib
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack")
USER_AGENT = "zentixua/open-skies tools/pack_dir.py"


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(root, rel):
    """Paths from pack files must stay inside the directory (as required by the .mrpack format)."""
    path = os.path.normpath(os.path.join(root, rel))
    if os.path.isabs(rel) or not path.startswith(root + os.sep):
        sys.exit(f"path {rel!r} escapes {root}")
    return path


def fetch(name, download, cache):
    algo, want = download["hash-format"], download["hash"].lower()
    cached = os.path.join(cache, f"{algo}-{want}")
    if os.path.isfile(cached):
        return cached
    tmp = cached + ".part"
    error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(download["url"], headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as out:
                shutil.copyfileobj(r, out)
            break
        except (OSError, http.client.HTTPException) as e:  # Interrupted mid-file: IncompleteRead.
            error = e
            if attempt < 3:
                time.sleep(2 << attempt)
    else:
        sys.exit(f"{name}: cannot download {download['url']}: {error}")
    got = digest(tmp, algo)
    if got != want:
        os.remove(tmp)
        sys.exit(f"{name}: downloaded {algo} {got} ≠ {want} ({download['url']})")
    os.replace(tmp, cached)
    return cached


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("dir", help="game directory (new)")
    ap.add_argument("--optional", action="store_true", help="enable all optional mods")
    ap.add_argument("--cache", default=os.path.join(ROOT, "run", "pack-cache"))
    a = ap.parse_args()
    dest = os.path.abspath(a.dir)
    if os.path.isdir(os.path.join(dest, "mods")):
        sys.exit(f"{dest} already contains mods/ — a new directory is required")

    with open(os.path.join(PACK, "pack.toml"), "rb") as f:
        pack = tomllib.load(f)
    index_file = os.path.join(PACK, pack["index"]["file"])
    if digest(index_file, pack["index"]["hash-format"]) != pack["index"]["hash"]:
        sys.exit("index.toml does not match pack.toml: packwiz refresh")
    with open(index_file, "rb") as f:
        index = tomllib.load(f)
    print(f"{pack['name']} {pack['version']}: " + ", ".join(f"{k} {v}" for k, v in pack["versions"].items()))

    os.makedirs(a.cache, exist_ok=True)
    on, off, files = [], [], 0
    for entry in index["files"]:
        src = inside(PACK, entry["file"])
        if digest(src, entry.get("hash-format", index["hash-format"])) != entry["hash"]:
            sys.exit(f"{entry['file']}: hash does not match index.toml: packwiz refresh")
        if not entry.get("metafile"):
            out = inside(dest, entry["file"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(src, out)
            files += 1
            continue
        with open(src, "rb") as f:
            meta = tomllib.load(f)
        if meta.get("side", "both") == "server":
            continue
        rel = os.path.join(os.path.dirname(entry["file"]), meta["filename"])
        option = meta.get("option", {})
        enabled = a.optional or not option.get("optional", False) or option.get("default", False)
        out = inside(dest, rel if enabled else rel + ".disabled")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(fetch(meta["name"], meta["download"], a.cache), out)
        (on if enabled else off).append(meta["filename"])
    print(f"enabled {len(on)}, disabled {len(off)}{': ' + ', '.join(off) if off else ''}; files copied as is {files} → {dest}")


if __name__ == "__main__":
    main()
