#!/usr/bin/env python3
"""CI gate for .claude/rules/team.md, the team and operations rules every agent loads at start.

Project threads load it because it is a root rule without frontmatter (a `paths:` header, even a malformed one,
would stop that); laptop sessions get it through the laptop-agents plugin (`git show origin/main:<file>`, so it must be
a real file, not a symlink); Codex reads it as ~/.codex/AGENTS.md. It stays a short, non-empty regular file <= 8 KiB
(every byte is loaded by every session) and never holds secrets.
It also keeps Artem's permanent autonomy rule (21.11): agents decide everything inside an approved goal, and a mission
stops only for an item on the "What needs Artem's word" list. A rewrite that drops either anchor fails here.
Run: python3 tools/check_team_rules.py [repo root]
"""
import re
import sys
from pathlib import Path

MAX = 8 * 1024
SECRETS = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:ant-|proj-)?[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}"
    r"|xox[abpr]-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:password|passwd|api[_-]?key|secret)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']",
    re.I)

# (anchor, why): matched after collapsing whitespace, so rewrapping a paragraph keeps passing
ANCHORS = [
    ("## What needs Artem's word", "the list of what waits for Artem"),
    ("Everything else inside a goal or look Artem approved is ours to decide", "the autonomy rule (Artem, 21.11)"),
    ("A mission stops (`BLOCKED`) only on an item from the list above", "the only reason a mission stops"),
]


def check(root: Path) -> list[str]:
    f = root / ".claude/rules/team.md"
    if f.is_symlink() or not f.is_file():
        return [f"{f} must be a regular file (not missing, not a symlink)"]
    raw = f.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return [f"team.md is not valid UTF-8 ({e.reason} at byte {e.start}): its readers would fail"]
    problems = []
    if not text.strip():
        problems.append("team.md is empty")
    if raw.lstrip().startswith(b"---"):
        problems.append("team.md has frontmatter: a root rule must have none, or project threads may not load it")
    if len(raw) > MAX:
        problems.append(f"team.md is {len(raw)} B > {MAX} B")
    flat = " ".join(text.split())
    for anchor, why in ANCHORS:
        if anchor not in flat:
            problems.append(f"team.md lost {why}: expected the text {anchor!r}")
    for n, line in enumerate(text.splitlines(), 1):
        if SECRETS.search(line):
            problems.append(f"team.md:{n}: looks like a secret")
    return problems


if __name__ == "__main__":
    p = check(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    print("\n".join(p) or "team rules OK")
    sys.exit(1 if p else 0)
