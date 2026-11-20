# Agent environment (team reference; rules in .claude/rules/team.md)

- The laptop auto-mode filter accepts agent launches and server actions only after Artem's own line in that thread;
  ask for it up front, for the whole scope. A quiet laptop session is checked by its processes and service state, not
  its last report.
- Project threads run in auto mode (bypass/dontAsk ignored); auto mode drops broad allow rules and every Agent/Monitor
  allow rule. Agent writes to `.claude/settings.json` are blocked as self-modification even after Artem's «да»: send
  him the exact text and the GitHub edit link. A "safety check separate from auto mode" block is an API filter on that
  conversation: continue in a fresh thread.
- Cloud threads cannot delete GitHub branches (proxy 403, no MCP tool); a netcup session with `gh` can
  (`gh api -X DELETE repos/zentixua/<repo>/git/refs/heads/<branch>`) after Artem's line. Merged heads auto-delete.
- Through the cloud proxy, wait for a release jar with a GET (`curl -fsSL -o …`) or the run status, never `curl -I`
  (HEAD loops on the redirect). The GitHub MCP has no create-release tool; cloud sessions get 403 editing releases
  and repo settings.
- Keep the `incoming` plugin (marketplace `zentixua-incoming`) enabled on Artem's claude.ai account: a repo marketplace
  alone does not deliver its skills to project threads.
- «Сделай перезагрузку» / «генеральная уборка» (Artem, 01.10): every working thread stops (WIP pushed to its own
  branch, handoff ≤ 60 lines in the project files' `handoff/<task>.md`); one cleanup thread sorts the project files
  (move to `archive/`, never delete; README index) and closes superseded PRs with a reason; laptop cleanup never
  touches the keep-list or his game, worlds, settings; the lead rewrites project memory; open tasks restart from the
  handoffs.
