#!/usr/bin/env python3
"""CI gate for .claude/rules/team.md, the team and operations rules every agent loads at start.

Project threads load it because it has no `paths:` frontmatter; laptop sessions get it through the laptop-agents
plugin; Codex reads it as ~/.codex/AGENTS.md beside incoming's AGENTS.md (<= 24 KiB), and Codex stops reading
AGENTS.md files at 32 KiB in total, so this file stays <= 8 KiB. It must never hold secrets.
Run: python3 tools/check_team_rules.py [repo root]
"""
import re
import sys
from pathlib import Path

MAX = 8 * 1024
SECRET = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|"
                    r"(?i:password|passwd|token|api[_-]?key)\s*[:=]\s*\S{6,})")


def check(root: Path) -> list[str]:
    f = root / ".claude/rules/team.md"
    if not f.is_file():
        return [f"{f} is missing"]
    text = f.read_text(encoding="utf-8")
    problems = []
    if text.startswith("---") and re.search(r"^paths:", text.split("---", 2)[1], re.M):
        problems.append("team.md has `paths:`: project threads would never load it")
    if len(text.encode()) > MAX:
        problems.append(f"team.md is {len(text.encode())} B > {MAX} B (Codex AGENTS.md budget)")
    for n, line in enumerate(text.splitlines(), 1):
        if SECRET.search(line):
            problems.append(f"team.md:{n}: looks like a secret")
    return problems


if __name__ == "__main__":
    p = check(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    print("\n".join(p) or "team rules OK")
    sys.exit(1 if p else 0)
