# agent-software-company

A skill for running software work as an IT company: CEO, MD/COO, CTO, CPO, CFO, quality/security leadership, department managers and specialist teams. The included catalog has **80 roles in 18 departments**, activated as needed rather than all spawned together.

## Native subagent edition

The separate [agent-software-company-subagents edition](https://github.com/DhruvHarani1/agent-software-company-subagents) runs from one parent conversation using real native delegation. Its CEO understands the product, chooses roles and worker counts, evolves profiles, and coordinates independent review. The user provides the desired outcome; staffing is handled internally.

That edition ships its own scripts, role catalog, lifecycle journal, safety guidance and tests. It does not depend on this parent folder after packaging. The original general edition below remains available. A native host with the documented collaboration tools is required for actual subagents; the Python journal records execution rather than launching it.

Version **2.0.0** introduces a local company ledger plus repaired GitHub coordination and a reviewed-candidate updater. The ledger records projects, tasks, dependencies, literal owned paths, actual host assignments, revision-bound review, decisions, checkpoints, handoffs and effort budgets. It does not create workers or execute their work.

## Start

Install the complete folder using your host's skill mechanism; keep `SKILL.md`, `scripts/`, `references/` and `templates/` together. For Codex, a conventional user location is `~/.codex/skills/agent-software-company/`; for Claude Code it is `~/.claude/skills/agent-software-company/`. Host installation/discovery behavior is not implemented by this repository. No external Python packages are needed; helpers require Python 3.10+.

From any directory, substitute the actual skill and existing project paths:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> init --name "My IT Company" --preset startup
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> init --name "My IT Company" --preset startup --apply
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> org
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> report
```

Initialization previews by default. `--apply` writes only the project's `.agent-company/state.json`; a second initialization preserves it. Presets set default active capacity to founder=1, startup=2, full-company=4. Default budget is 100 **abstract effort units**, configurable at initialization. These are not tokens, currency or automatic spend measurements.

Use [SKILL.md](SKILL.md), the [operating model](references/company-operating-model.md), and the [command workflows](references/company-workflows.md). The [blueprint](IT_COMPANY_BLUEPRINT.md) describes the broader roadmap; advanced automation there is not yet implemented.

## What actually runs

The host starts real workers, runs commands and performs authorized actions. `company.py` only validates and records workflow consistency. Task submission requires a full lowercase Git SHA or a SHA-256 artifact digest. Review requires a separately assigned non-contributor and covers the exact latest submission. Actor IDs and evidence are operator attestations; the ledger does not authenticate identities, inspect artifacts or prove checks ran.

The canonical [safety policy](references/safety-protocol.md) governs authorization. Executive titles, config flags, GitHub tokens and PASS reviews grant no authority. Scoped standing authorization persists. Production writes are disabled by default, with a separate procedure when explicitly authorized.

State is local, written with an exclusive writer lock and atomic replacement. Preserve a corrupted state/lock for inspection; do not reset it or remove a lock until the actual writer is confirmed stopped. Park/resume and handoff support reconciled recovery, not automatic worker control.

## Optional GitHub coordination

Requires `gh` and authorized repository reads. See [interop](references/interop-protocol.md) and [discovery](references/auto-discovery.md).

- Radar paginates published activity and PR-file scans, flags partial coverage, and prints hello drafts. It does not post or see unpushed work.
- Claims checks actual GitHub actors against an owner-reviewed local roster. Unknown identities remain UNVERIFIED; incomplete reads never establish exclusive ownership.
- Inbox defaults to full-body peek. `--ack` records displayed message versions; `--since` replays without saving. State is independent per repository/org/recipient.
- `.agents/` agreements and GitHub comments are separate from `.agent-company/`; no automatic synchronization exists.

Skill updates use `fetch` → content review/`diff` → `apply <candidate> --reviewed <digest>`; apply never fetches again. Legacy `pull --apply` is rejected. See [update/recovery guidance](references/update-and-improve.md).

## Validation

Run from the skill directory:

```text
python -B -m unittest discover -s tests -v
```

The default suite is offline: mocked GitHub reads and temporary company/update fixtures, without production credentials, live PRs or paid services. Tests were executed on Windows in this workspace. Linux/macOS execution and live provider behavior have not been verified here. A real symlink test may skip when Windows privilege is unavailable; a mocked reparse-point test covers that rejection path separately.

Dashboards, background schedulers, automatic measured telemetry and client-portfolio automation remain future work. The native edition supports the documented collaboration-tool bridge; additional native providers are future work. Change history is in [CHANGELOG.md](CHANGELOG.md).
