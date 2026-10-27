#!/usr/bin/env python3
"""Automatic pack update for .github/workflows/update.yml.

  releases  Point mods downloaded from GitHub releases (Incoming, Almighty) at their latest published release.
  finish    If any mod or shaderpack file changed against HEAD (after `releases` and `packwiz update --all`), bump the
            pack's patch version, refresh the index, add the README.md version-table row and
            docs/releases/<version>.en.md, and write the commit message. The new version goes to $GITHUB_OUTPUT as `version`.

Only published releases count (GitHub's "latest" skips drafts and pre-releases), so a jar reaches the pack only after
its release. Pinned mods (`pin = true`) stay as they are: packwiz skips them, and so does `releases`.

Usage: python3 tools/update_pack.py releases | finish [--message FILE]
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"
GITHUB_JAR = re.compile(r"https://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/([^/]+\.jar)")
NOTES = "https://github.com/{owner}/{repo}/blob/main/docs/releases/{version}.md"


def get(url, headers=None):
    request = urllib.request.Request(url, headers={"User-Agent": "zentixua/open-skies update_pack.py", **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def github_api(path):
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    return json.loads(get(f"https://api.github.com/{path}", headers))


def metafiles():
    return sorted([*PACK.glob("mods/*.pw.toml"), *PACK.glob("shaderpacks/*.pw.toml")])


def releases():
    for path in metafiles():
        text = path.read_text(encoding="utf-8")
        meta = tomllib.loads(text)
        match = GITHUB_JAR.fullmatch(meta["download"]["url"])
        if not match or meta.get("pin"):
            continue
        owner, repo, tag, filename = match.groups()
        latest = github_api(f"repos/{owner}/{repo}/releases/latest")
        if latest["tag_name"] == tag:
            continue
        jars = [a for a in latest["assets"] if a["name"].endswith(".jar") and not a["name"].endswith("-sources.jar")]
        if len(jars) != 1:
            raise SystemExit(f"{owner}/{repo} {latest['tag_name']}: expected one jar, got {[a['name'] for a in jars]}")
        jar = jars[0]
        url = jar["browser_download_url"]
        sha256 = hashlib.sha256(get(url)).hexdigest()
        # Keep name, side and layout; replace the four fields that name the file.
        for key, old, new in (("filename", filename, jar["name"]), ("url", meta["download"]["url"], url),
                              ("hash-format", meta["download"]["hash-format"], "sha256"),
                              ("hash", meta["download"]["hash"], sha256)):
            text, n = re.subn(rf'^{re.escape(key)} = "{re.escape(old)}"$', f'{key} = "{new}"', text, count=1,
                              flags=re.M)
            if n != 1:
                raise SystemExit(f"{path.name}: cannot replace {key}")
        path.write_text(text, encoding="utf-8")
        print(f"{meta['name']}: {tag} -> {latest['tag_name']}")


def at_head(path):
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return tomllib.loads(result.stdout) if result.returncode == 0 else None


def display_version(meta):
    """Version as the mod's authors name it: the release tag or Modrinth's version number."""
    match = GITHUB_JAR.fullmatch(meta["download"]["url"])
    if match:
        return match.group(3).removeprefix("v")
    modrinth = meta.get("update", {}).get("modrinth")
    if modrinth:
        return json.loads(get(f"https://api.modrinth.com/v2/version/{modrinth['version']}"))["version_number"]
    return meta["filename"]


def changes():
    """[(name, version, notes URL or None)] for every metafile whose file differs from HEAD."""
    changed = []
    for path in metafiles():
        meta = tomllib.loads(path.read_text(encoding="utf-8"))
        old = at_head(path)
        if old is None or old["filename"] == meta["filename"]:
            continue
        match = GITHUB_JAR.fullmatch(meta["download"]["url"])
        notes = None
        if match:
            owner, repo, tag, _ = match.groups()
            notes = NOTES.format(owner=owner, repo=repo, version=tag.removeprefix("v"))
        changed.append((meta["name"], display_version(meta), notes))
    return changed


def describe(changed, notes_word, mods_word):
    linked = [f"{name} {version} ([{notes_word}]({notes}))" for name, version, notes in changed if notes]
    other = [f"{name} {version}" for name, version, notes in changed if not notes]
    parts = []
    if linked:
        parts.append("; ".join(linked) + ".")
    if other:
        parts.append(f"{mods_word}: " + ", ".join(other) + ".")
    return " ".join(parts)


def finish(message_file):
    changed = changes()
    if not changed:
        print("No mod changes", flush=True)
        return
    pack_toml = PACK / "pack.toml"
    text = pack_toml.read_text(encoding="utf-8")
    old = tomllib.loads(text)["version"]
    major, minor, patch = (int(n) for n in old.split("."))
    version = f"{major}.{minor}.{patch + 1}"
    pack_toml.write_text(text.replace(f'version = "{old}"', f'version = "{version}"', 1), encoding="utf-8")
    subprocess.run(["packwiz", "refresh"], cwd=PACK, check=True)

    incoming = tomllib.loads((PACK / "mods/incoming.pw.toml").read_text(encoding="utf-8"))
    mod = display_version(incoming)
    russian = describe(changed, "заметки", "Обновлены моды") + " Обновление автоматическое."
    english = describe(changed, "notes", "Updated mods") + " Automatic update."
    readme = ROOT / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines(keepends=True)
    header = lines.index("## Версии\n")
    separator = next(i for i in range(header, len(lines)) if lines[i].startswith("|---"))
    lines.insert(separator + 1, f"| {version} | {mod} | {russian} |\n")
    readme.write_text("".join(lines), encoding="utf-8")
    (ROOT / f"docs/releases/{version}.en.md").write_text(english + "\n", encoding="utf-8")

    title = f"Open Skies {version}: " + ", ".join(f"{name} {v}" for name, v, _ in changed)
    if len(title) > 72:
        title = f"Open Skies {version}: {len(changed)} mod updates"
    body = "\n".join(f"- {name} {v}" for name, v, _ in changed)
    if message_file:
        message_file.write_text(f"{title}\n\nAutomatic update (update.yml).\n\n{body}\n", encoding="utf-8")
    print(f"Open Skies {version}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"version={version}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["releases", "finish"])
    parser.add_argument("--message", type=Path, help="finish: write the commit message here")
    args = parser.parse_args()
    if args.step == "releases":
        releases()
    else:
        finish(args.message)


if __name__ == "__main__":
    main()
