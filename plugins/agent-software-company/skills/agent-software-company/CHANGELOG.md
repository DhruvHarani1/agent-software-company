# Changelog

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
