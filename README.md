# agent-software-company

A Claude Code plugin (skill) that runs a software product like a small company of AI agents: a **Boss** (CEO / scrum master) who reviews and merges, **managers** who own areas and run sub-agents, an independent **QA reviewer**, a **security reviewer** and **functional testers**. Safe by design: nobody pushes to `main`, production data is read-only for agents, every fix has a test that fails first.

New in 1.2: **automatic discovery**. Another person's agents, or your second Claude account, working on the same GitHub repository are found from GitHub activity (no setup), greeted, checked for file overlap and reviewed both ways. Built-in terse style and token-saving rules.

## Install (Claude Code)

```
/plugin marketplace add DhruvHarani1/agent-software-company
/plugin install agent-software-company@agent-company
```
Then start a session and ask: `Use the agent-software-company skill to set up my repository.`

## Update

Automatic (recommended): run `/plugin`, open the **Marketplaces** tab, select `agent-company`, enable **Auto-update**.
Manual, any time:
```
/plugin marketplace update agent-company
/reload-plugins
```

## No plugin? Plain folder

Copy `plugins/agent-software-company/skills/agent-software-company/` to `~/.claude/skills/`. To check for updates: copy `.skill-source.example` to `.skill-source`, set the repo and path (`plugins/agent-software-company/skills/agent-software-company`), then `python scripts/skill_update.py check` (it never overwrites without `--apply`).

## Two teams, or two Claude accounts, on one repository

Nothing to configure: agents add `Agent-Org` / `Agent` trailers to commits and PRs, and `scripts/radar.py` discovers other teams from GitHub, flags overlapping files and prints a hello. Rules: `references/interop-protocol.md`, `references/auto-discovery.md`. The other team's text is always treated as data, never as instructions; only human owners approve.

## Contents

`SKILL.md`, `references/` (roles and briefs, SDLC and sprints, safety protocol, release playbook, interop, auto-discovery, terse mode, token economy, update and improve, lessons learned), `templates/` (AAP v1 protocol, roster, areas, trust, messages), `scripts/` (radar, inbox, claims, lint_message, skill_update).

## Versions

See `CHANGELOG.md`. Releases are tagged `vX.Y.Z`; the plugin `version` in `plugin.json` is bumped on every change so Claude Code detects updates.

## License

MIT
