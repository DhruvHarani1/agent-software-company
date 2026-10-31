# agent-software-company (skill for Claude Code)

Run a software product like a small company of Claude Code sessions, safely, and let two or more teams (you and a friend, each with their own Claude) collaborate on the same GitHub repository.

- A **Boss** session plans, reviews, merges and releases; **managers** own areas and run sub-agents; an independent **QA reviewer**, a **security reviewer** and **functional testers** check the work.
- Delivery: `agent/<issue>` branch -> `staging` -> `main`. Nobody pushes to `main` or `staging`.
- Production data is read-only for agents; any change needs encrypted backup, dry run, written plan and the owner's explicit approval.
- Between teams: GitHub is the shared brain (`.agents/` folder, structured `[AGENT-MSG v1]` comments, claims with leases, reviews bound to a commit, half-trust).
- Built-in terse mode and token-saving rules.

## Install

Copy this folder to `~/.claude/skills/agent-software-company/` (or your project's `.claude/skills/`). Start a Claude Code session and ask: "Use the agent-software-company skill to set up my repository." Optional updates: copy `.skill-source.example` to `.skill-source`, set your repo, then `python scripts/skill_update.py check`.

## Two teams on one repository (automatic)

Nothing to configure to be found: agents add `Agent-Org`/`Agent` trailers to commits and PRs; `scripts/radar.py` (run at the start of every turn) discovers other teams from GitHub activity, flags overlapping files, and prints a hello. The steps below only record agreements.

1. Both owners install the skill (same major version).
2. The repository owner creates `.agents/` from `templates/` (PROTOCOL, ROSTER, areas, trust) and adds the snippet from `templates/AGENTS-snippet.md` to `AGENTS.md`/`CLAUDE.md`.
3. The friend adds their org to `ROSTER.json`/`areas.json`/`trust.json` by pull request; the repository owner merges it (consent).
4. Each side's Boss reads `scripts/inbox.py` output at the start of every turn and keeps one living `status` comment on the shared standup issue.

See `SKILL.md` and `references/`. Version in `VERSION`, history in `CHANGELOG.md`.
