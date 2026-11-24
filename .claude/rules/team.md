# Team and operations rules: moved

The team and operations rules for every agent of Artem's projects moved on 24.11.2026, with the friends' pack, to
`zentixua/open-skies-friends`: `.claude/rules/team.md` there, references in its `docs/team/`. Read that file in full
before any work and follow it; this pointer holds no rules.
- Laptop: `git -C /mnt/data/projects/open-skies-friends show origin/main:.claude/rules/team.md` (the laptop-agents
  hook injects it at session start).
- Cloud project thread: the project repository `zentixua/open-skies-friends` loads it natively; until it is added,
  `curl -fsSL https://raw.githubusercontent.com/zentixua/open-skies-friends/main/.claude/rules/team.md`.

This repository becomes the public Open Skies pack once Artem confirms every instance and server has moved; this
pointer leaves with that switch.
