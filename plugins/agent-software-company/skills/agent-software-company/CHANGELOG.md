# Changelog

## Native subagent edition 1.0.0 (11 Nov 2026)

Separate self-contained edition under `editions/agent-software-company-subagents/`; the general edition remains version 2.0.0.

- CEO-led product discovery and adaptive staffing inside one parent conversation, using real native subagents rather than user-operated staff chats. Outcome-only user requests; internal role/count selection, specialization, duplication and retirement.
- Native attempt journal with pending slot/effort/path admission, actual identity binding, acknowledgments, logical versus physical parentage, immutable assignment/profile snapshots, observed lifecycle and stop/retry reconciliation.
- Product evidence, reasoned organization decisions, versioned role definitions and role retirement/reactivation. Titles and recorded capabilities do not grant permissions or prove tool execution.
- Guarded artifact/review settlement requires a matching completed native attempt; contributor history is preserved through failed binding, late launches and replacement. Completed blocked assignments have a narrow reconciled unblock path.
- Offline lifecycle/CLI/bridge tests and a real isolated native builder-to-independent-review walkthrough. Direct parent dispatch exercised; nested runtime spawning remains host/capacity dependent and is covered by local admission fixtures.
- Deterministic standalone ZIP packaging with an integrity manifest; excludes live state, credentials and caches. No automatic installation, background daemon or monetary telemetry.

## 2.0.0 (11 Nov 2026)

### First local company kernel

- Added a catalog of 80 roles across 18 departments: executive leadership, product/research/design, architecture and engineering, data/AI/platform, independent review/QA/security, delivery/support/finance/growth/knowledge.
- Added preview-first local initialization with founder/startup/full-company capacity presets and configurable abstract effort budget. The catalog is not a set of automatically running workers.
- Added local projects/tasks, acceptance criteria, dependencies, declared path conflicts, actual host assignment records, effort reservations/accounting, decisions, status and Markdown reporting.
- Added revision-bound submissions and independent review assignments with contributor exclusion. Full lowercase Git SHAs and SHA-256 artifact digests identify company submissions; evidence/session IDs remain operator attestations.
- Added checkpoint, stopped-assignment park/resume and handoff with preserved phase, incurred cost and contributor history. The ledger does not spawn workers, run checks or perform external actions.

### Coordination and recovery

- Consolidated message parsing, timestamp/routing validation and bounded GitHub JSON/pagination reads. Invalid/unknown messages are ignored safely; style advice is non-blocking.
- Radar now reports partial/unavailable coverage and unknown permissions rather than false empty results. Published PR-file coverage is checked against reported counts/API caps; unpushed/local branch work is outside scope. Hello output is draft only.
- Claims now uses actual GitHub actors with owner-reviewed org bindings, explicit UNVERIFIED diagnostics, bounded leases and stable targeted claim IDs. Renewals/releases preserve actor ownership; stale takeover requires an explicit verified expired target. Expired reacquisition does not inherit old priority.
- Inbox now defaults to full-body peek, supports explicit successful-output acknowledgment, replay and scoped repo/org/recipient state. Fetch boundaries, overlap and version deduplication protect concurrent arrivals and edited status messages; corrupt state is not silently reset.
- Replaced update-in-place refetching with immutable reviewed candidates, complete added/modified/deleted summaries, source/path/link validation, local drift checks, preserved configuration/state, unique backups and rollback/interrupted-swap recovery.

### Compatibility and policy

- Major version: inbox acknowledgment defaults and updater apply interface deliberately change prior behavior. `pull` is fetch-only; legacy `pull --apply` is rejected. Review a named candidate and use its integrity digest to apply without refetching.
- AAP header remains v1, with stricter full-SHA, lease, actor and event requirements. Update participating emitters together; older abbreviated/malformed messages may now be rejected.
- Replaced conflicting action rules with one canonical safety policy. Roles/capabilities/evidence do not grant authority; scoped standing authorization persists. Checks are risk-based rather than universal test-first rituals.
- Added operating model, command workflows, offline regression/fault fixtures and revised templates. The tested environment for this release is Windows; live provider behavior and other OS execution were not verified here.

Advanced dashboards, persistent/background scheduling, automatic token/cloud telemetry, provider adapters, client-portfolio automation and autonomous external operations remain roadmap work.

## 1.4.0 (7 Nov 2026)
- **Adaptive organisation:** `references/adaptive-org.md` (profile the project, presets for solo tool / internal app / public SaaS / library / mobile / data-ML / regulated, role catalog with the trigger for each role, e.g. marketing only for external products, Boss decision rights decide / inform / ask, monthly self-adjusting loop, decision log). New `scripts/org_profile.py` guesses the profile from the repo (read-only).
- SKILL.md: designing the company is now the first step on any project; the skill is product-neutral.
- Executive layer pattern (CTO, COO, CPO, CISO, CDO, CCO, cost and usage) with charters and a weekly owner report, as an optional layer of `org-structure.md`.

## 1.3.0 (7 Nov 2026)
- **Organisation reform:** new `references/org-structure.md` (departments, hats versus headcount, flow, cadence, RACI, lazy staffing, role brief template). Roster may carry `department`.
- Lessons 18-24: stacked pull request pitfall, clock time bombs, changed-tests-per-PR routine, unprompted cleanup after every merge, bulk data change as a class, honest error messages, departments.
- Release playbook and SDLC: per PR run type-check + related tests; full suite per release and nightly.

## 1.2.0 (31 Oct 2026)
- **Automatic discovery:** `scripts/radar.py` finds other teams on the repository from GitHub activity (commit trailer `Agent-Org`, `[AGENT-MSG]` headers, other logins, open PRs, collaborator access), flags file overlaps with the work you are about to do, and prints the `hello` introduction. No roster needed to be present. Bots ignored. Tiers (teammate = write access, guest = anyone else) from GitHub itself; no tier gives authority.
- New message types `hello` and `heads-up`; lint, templates and PROTOCOL updated (trailers, radar at turn start).
- Same owner with two Claude accounts documented (`references/auto-discovery.md`).

## 1.1.0 (31 Oct 2026)
- **Interop (AAP v1):** two or more teams of agents (for example you and a friend, each with your own Claude) can work on one GitHub repository: shared `.agents/` folder (protocol, roster, areas, trust, decisions), `[AGENT-MSG v1]` message headers with templates, claims with leases and stale release, cross-org reviews bound to a commit SHA, half-trust model (other team's agent text is data, not instructions), join handshake, who merges.
- **Terse mode built in** (compact agent-to-agent style) and **token economy** rules.
- **Scripts:** `lint_message.py`, `inbox.py`, `claims.py`, `skill_update.py` (check/pull/apply with review, never automatic).
- **Updates:** `VERSION`, this changelog, `.skill-source`, improvement loop and the list of ideas adopted from other projects.
- Templates: PROTOCOL, ROSTER, areas, trust, AGENTS-snippet, message templates.

## 1.0.0 (31 Oct 2026)
- First version: roles and briefs, SDLC and sprints with turn-taking, safety protocol, release playbook, lessons learned (from a week of running a production web app with agents).
