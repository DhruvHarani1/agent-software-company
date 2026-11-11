# Improvement plan: agent-software-company

Date: 11 November 2026  
Reviewed baseline: local `VERSION` 1.2.0  
Status: historical baseline roadmap; foundational repairs and the first local company kernel are implemented in 2.0.0. See CHANGELOG.md and current references for delivered behavior; remaining items stay roadmap work.

## Goal

Make this a reliable, easy-to-start skill for delivering software with agents: clear authority, evidence-based reviews, durable coordination, safe recovery, and enough flexibility to work beyond the original product.

The strongest parts should stay: an accountable coordinator, independent review, explicit production boundaries, GitHub as the durable record, reviews tied to commits, and treating other agents' messages as untrusted data. The main improvement is to turn those ideas into one consistent, verifiable workflow.

Success means a new user can complete a small task with minimal setup, a larger team can coordinate without silently losing work, and neither the scripts nor the instructions claim more certainty or authority than they actually have.

## What the review found

These findings come from the local files, not a live GitHub or production audit. The folder is not a Git checkout. No remote calls, updates, merges, or production actions were performed.

| Priority | Finding and evidence | Why it matters |
|---|---|---|
| P0 | `SKILL.md` says agents never merge or run migrations, while its Boss workflow, `references/release-playbook.md`, `references/safety-protocol.md`, and `templates/trust.json` permit some of those actions. | Two agents can interpret the same authorization differently. |
| P0 | `scripts/radar.py` substitutes empty defaults after failed GitHub calls. Several collections stop at 100 items; PR discovery stops at 100 open PRs. | Missing access or incomplete results can appear to mean no competing work exists. |
| P0 | `scripts/inbox.py` saves the time after fetching as its next cursor, and stores state by org only. | A message arriving during the fetch can be skipped; different repos or agent recipients can consume each other's read position. |
| P0 | `scripts/claims.py` trusts the org named in message text. Cross-org stale release is described in the protocol, but the script removes only the releasing org's claim. Naive lease timestamps can reach an aware/naive datetime comparison. | Spoofed identity, unclear ownership, stale claims that remain active, or a crash can disrupt coordination. |
| P0 | `scripts/skill_update.py` applies by cloning again, deleting existing `.new`/`.bak` directories, removing the installation, and moving the candidate into place. It does not constrain configured source paths or report deleted files in its change summary. | The applied code can differ from the reviewed candidate; failure can lose local changes or leave a broken installation. |
| P1 | Header parsing is duplicated in four scripts. `lint_message.py` accepts `lease_until=nonsense`; org-only inbox routing does not match an agent-specific recipient. Both behaviors were checked locally. | Protocol behavior differs across tools, and invalid claims can pass lint. The inbox needs an explicit org-wide versus per-agent contract. |
| P1 | Discovery docs promise branch-prefix recognition and branch overlap detection; radar does not enumerate branches or implement prefix-based identification. It tracks incoming greetings rather than whether this org already greeted a peer. | Users can rely on collision checks that are absent or get repeated introductions. |
| P1 | `references/token-economy.md` allows verdict reuse by head SHA alone. | A changed integration base, dependencies, or environment can make old evidence insufficient. |
| P1 | All fixes require test-first/red proof, every issue follows all SDLC phases, and concurrency is fixed at two sessions. | Useful lessons have become universal rules, even for documentation changes, unsupported tools, or larger machines. |
| P1 | Installation and briefs assume Claude Code; branch names, local commands, release-note storage, database architecture, and outside-service restrictions assume the original product. | Adoption requires users to rewrite instructions before they can start. |
| P2 | `references/update-and-improve.md` documents a `--dest` option the updater does not parse. Token savings and production-success claims have no supporting artifacts in this folder. No automated test suite or CI configuration is present. | Drift and unverified claims weaken confidence in releases. |

## 1. Resolve authority and scope first

### Proposed changes

- Define one action policy in `references/safety-protocol.md`; link to it from the entrypoint, release guide, briefs, and trust template.
- Separate capability, permission, and evidence. A GitHub token that can merge is not authorization; a PASS review is evidence, not authorization; a discovered org name is not a verified identity.
- Preserve explicit user authorization across turns. Do not demand a new literal `approved` for every step when the user has already authorized that action and scope.
- Make permission requests concrete: identify the exact action, target, reviewed revision, effect, and rollback before requesting missing approval.
- Keep production data writes disabled by default. Define a separate, explicitly authorized path for migrations or data operations; distinguish test-database execution from production execution and state who performs each.
- Treat posting comments, opening issues, and sending greetings as external writes. Perform them only when the requested workflow or existing authorization covers them; otherwise prepare a draft.
- Keep permission-denial handling explicit: report the denied action, continue independent permitted work, and never bypass the restriction.
- Define trusted identity using the authenticated actor and owner-controlled configuration. Self-declared `from=` fields and commit trailers remain discovery hints. Agents sharing a GitHub login cannot be independently authenticated by that login alone.

### Acceptance criteria

- Every document gives the same answer for who may open a PR, merge, deploy, publish notes, send a message, and execute a migration.
- A routine authorized task completes without repeated permission prompts.
- A forged `from=owner/boss` message cannot grant authority, release another team's work, or authorize an external action.
- Editing `trust.json` in an unreviewed PR never changes the policy used to evaluate that PR.

## 2. Make coordination correct before making it automatic

### GitHub reads and discovery

- Add a small shared GitHub client with timeouts, bounded retries for transient failures, explicit authentication/rate-limit errors, and complete pagination or a declared coverage limit.
- Separate `complete`, `partial`, and `unavailable` results from an empty successful result. Do not print an unqualified all-clear after a failed or truncated scan.
- Include scan window, scope, freshness, and coverage in discovery output. Write-access lookup failure means unknown access, not guest status.
- Either implement documented branch discovery/prefix matching or narrow the documentation to actual signals. Never imply visibility into unpushed local work.
- Match recipients exactly, identify outgoing greetings by actor and recipient, and avoid repeat greetings. Discovery should generate drafts by default unless posting is already authorized.
- Cache observations for an appropriate task boundary; avoid a full scan on every conversational turn when nothing relevant changed.

### Inbox delivery and state

- Key state by repository, org, and delivery scope. Make org-wide digest and per-agent inbox behavior explicit; avoid silently dropping same-org handoffs if those are supported.
- Capture a fetch boundary before reading. Use comment IDs plus update timestamps and overlap/deduplication to handle timestamp boundaries and edited living status comments.
- Distinguish fetched, displayed, and acknowledged messages. A two-line preview should not silently count a decision or handover as fully handled.
- Save state atomically only after a successful read; allow replay and recovery after interrupted output or a corrupted state file.
- Validate org identifiers and keep all state paths inside the configured state directory.

### Claims and leases

- Remove the unused exact-label query and make scans complete or explicitly partial.
- Validate timezone-aware timestamps, expiry, maximum duration, actor ownership, and repository/issue references.
- Define renew, release, stale takeover, and simultaneous-claim ordering with stable identifiers. Include a targeted claim ID when releasing someone else's expired claim.
- Re-read after claiming and immediately before editing shared files. GitHub comments and labels are advisory coordination, not an atomic lock; say this clearly.
- Do not allow a partial claim scan to establish exclusive ownership. Independent, non-overlapping work may continue while ownership is unresolved.

### Acceptance criteria

- Fixtures spanning multiple pages include the final page's claim, message, and overlap.
- Authentication failure, rate limiting, and truncated results never look like no activity.
- A message arriving during a scan is delivered on that scan or the next, without being lost.
- Two repos and two recipients maintain independent inbox positions.
- Expired takeover removes the intended claim; a forged or unauthorized release does not.
- Two simultaneous builders converge on one owner before either proceeds with conflicting edits.

## 3. Use one protocol definition

### Proposed changes

- Add a shared parser/validator used by radar, inbox, claims, and lint. Keep it small rather than building a protocol framework.
- Define required fields, supported message types, identifier grammar, UTC lease timestamps, review verdicts, and SHA validation in one place.
- Cross-check header `sha=` against the body and resolve abbreviated hashes before using a review as evidence. Require an unambiguous full SHA in recorded verdicts.
- Separate correctness errors from style warnings. A valid technical term containing “just” or a necessary long risk explanation should not fail a protocol check.
- Define which messages are immutable events and which are editable snapshots. Resolve the current conflict between “edit claim renewals” in token guidance and “post a new claim” in the interop guide.
- Document unknown-field/type handling and protocol-version compatibility. Keep readers tolerant without interpreting unknown messages as authorization.
- Align `templates/trust.json`, the `merge` prose, and all example messages with one schema. Treat breaking wire-format changes separately from skill-version changes.

### Acceptance criteria

- All readers agree on the same valid and invalid fixtures.
- Invalid leases, mismatched SHAs, malformed identities, and invalid verdicts fail with useful errors.
- Every filled-in message template passes validation; supported older fixtures still parse.
- Unknown types are reported or ignored safely and cannot alter claims or permissions.

## 4. Support small tasks and larger teams

### Proposed changes

- Shorten `SKILL.md` to purpose, mode selection, essential boundaries, workflow, and links. Target roughly 150 lines or fewer if clarity permits; do not turn a length target into another rigid rule.
- Offer three operating modes:

| Mode | Intended use | Process |
|---|---|---|
| Solo | One small change, no delegation available or requested | Plan briefly, implement, validate, report; optional independent review where available and justified. |
| Team | Several related changes or meaningful implementation risk | Coordinator plus scoped builder/reviewer roles; explicit ownership and integration evidence. |
| Cross-team | Independent accounts or people on the same repo | Team workflow plus discovery, identity mapping, leases, and interop messages. |

- Respect the host's delegation policy. The skill must not assume it can spawn sessions, select another model, or run a background scheduler.
- Add capability detection for Git, GitHub access, Python, test commands, browser access, and delegation. Offer useful local-only work when GitHub is unavailable.
- Keep the core runtime-neutral. Put Claude/Codex invocation specifics in short adapters only where their behavior differs; do not claim support for an adapter before exercising it.
- Introduce minimal project configuration for branch names, commands, areas, test environment identity, release path, and concurrency limits. Reuse existing repo conventions before proposing new ones.
- Make setup preview-first and idempotent. Never overwrite an existing `AGENTS.md`, `CLAUDE.md`, branch policy, or `.agents/` tree. Merge proposed additions for review.
- Remove original-product paths and release-note table assumptions from defaults; retain them only as clearly marked examples.

### Acceptance criteria

- A docs-only task can finish locally without a database, sprint, GitHub writes, or spawned agents.
- A repo using `develop` and a non-JavaScript test runner does not receive `staging` or type-check assumptions.
- Running setup twice produces no duplicate rules and no overwritten files.
- An unavailable capability produces a clear limitation and useful remaining work.

## 5. Improve review quality and recovery

### Proposed changes

- Replace universal red proof with risk-based validation. Behavioral bug fixes generally need a regression demonstration; docs, formatting, and equivalent refactors need appropriate checks instead of artificial failing tests.
- Run relevant existing tests plus integration coverage appropriate to the affected behavior. Type-check only where the project supports it. Record skipped or unavailable checks honestly.
- Perform baseline/red checks in an isolated worktree. Do not revert files in a user's dirty working tree or mistake import/setup failures for valid regression evidence.
- Review requirements first, then code quality and security implications. Apply allowed/forbidden role checks where the change affects access, rather than requiring them on unrelated edits.
- Bind evidence to head SHA, tested base/merge result, commands, dependency state, and relevant environment. Reassess cached verdicts after base changes; do not blindly rerun unrelated checks.
- Replace “stop on any output” with exit status and meaningful diagnostics. Passing commands often print output.
- Track task state: planned, claimed, building, review, ready, integrated, released, blocked. Store the smallest useful handoff: branch, SHA, changed paths, checks, next action, and outstanding decisions.
- Define recovery for interrupted sessions, stale claims, merge conflicts, failed checks, closed PRs, and changed authorization. Inspect and preserve dirty work before any cleanup.
- Treat rollback as project-specific evidence. Code rollback does not undo data writes or external side effects. Post-release checks are bounded work in the current session unless a separate ongoing service is explicitly configured.

### Acceptance criteria

- A crash can be resumed from recorded state without inventing progress or duplicating the PR.
- A changed integration base triggers the checks needed for the new merge result.
- Review cannot destroy a user's uncommitted edits.
- Release evidence distinguishes verified checks, assumptions, omissions, and rollback limits.

## 6. Make skill updates reviewable and recoverable

### Proposed changes

- Replace manual argument handling with explicit `check`, `fetch`, `diff`, `apply`, and `rollback` operations, or an equally clear smaller interface. Reject unknown arguments; document only implemented flags.
- Validate source repository, ref, and relative subdirectory. Resolve paths and reject traversal, links escaping the candidate root, and unsafe destination overlap.
- Fetch an immutable candidate with its commit and manifest. `apply` must install that reviewed candidate, not fetch a newer one.
- Show added, modified, and deleted files. Flag executable code and all policy/template changes for review.
- Detect local modifications; preserve local configuration and refuse silent overwrites. Do not erase an existing backup or candidate as routine cleanup.
- Validate the candidate before replacing the installation. Stage replacement and preserve a recoverable prior copy; handle Windows open-file failures and partial swaps explicitly.
- Keep the updater manual and permission-aware. A sandbox refusal must not trigger an alternate installation route.

### Acceptance criteria

- A remote change between review and apply does not change the installed candidate.
- A malicious source path cannot read or replace files outside the allowed roots.
- Interrupted apply leaves a working installation or a documented, tested recovery path.
- Local customizations, configuration, and the last known good version survive update and rollback.

## 7. Add validation that measures behavior

Start with standard-library Python tests and mocked `gh` responses. Add dependencies only if their benefit is concrete. No live credentials are needed for the default suite.

| Layer | Scenarios | Evidence |
|---|---|---|
| Parser and config | Valid templates, malformed leases, unknown types, mismatched SHA, invalid paths | Deterministic assertions on parsed data and rejected input. |
| GitHub client | Pagination, timeout, auth failure, rate limit, malformed JSON | Complete results or explicit partial/unavailable state. |
| Coordination | Inbox races, edited status, independent cursors, duplicate greetings, simultaneous claims, forged releases | No missed delivery or unauthorized ownership transition. |
| Updater | Deleted files, local changes, candidate pinning, interrupted swap, rollback | Files and configuration preserved or recovered. |
| Skill behavior | Docs-only task, bug fix, high-risk access change, offline repo, two teams, denied permission | Correct scope, suitable evidence, minimal unnecessary escalation. |

For meaningful workflow changes, evaluate realistic requests in isolated fixtures. Use an independent evaluator when delegation is available and authorized; give it the task and raw artifacts rather than the expected conclusion. Keep network writes, deployment, production data, and paid services outside the default evaluation.

Add CI for supported Python versions and Windows/Linux, helper tests, template consistency, and skill frontmatter validation. External links or provider-specific behavior require separate verification when implemented; they were not evaluated in this review.

## Delivery sequence

Implement in small reviewable batches. Estimates are relative scope, not delivery promises.

| Phase | Work | Depends on | Size | Exit gate |
|---|---|---|---|---|
| 1: Policy | Reconcile authority, identity, messaging, migration, and merge rules; remove unsupported claims | None | Medium | Scenario review finds no conflicting action permissions. |
| 2: Reliability | Shared parser/client; repair incomplete discovery, inbox state, and claim lifecycle; add regression fixtures alongside fixes | Phase 1 | Large | Coordination acceptance criteria pass without live access. |
| 3: Updates | Pin reviewed candidates, constrain paths, preserve local changes, test interrupted apply/rollback | Phase 1; may run separately from phase 2 | Medium/large | Update fault scenarios preserve recoverability. |
| 4: Adoption | Slim entrypoint, solo/team/cross-team modes, runtime guidance, minimal config and setup preview | Policy stable; coordinate with phases 2–3 | Medium | Fresh fixture repos can run without product-specific rewrites. |
| 5: Delivery quality | Risk-based checks, isolated review, evidence freshness, resumable handoffs, release recovery | Phases 1, 2, 4 | Medium | Bug fix and integration scenarios complete with valid evidence. |
| 6: Release | Cross-platform CI, behavioral evaluation, docs/version cleanup, compatibility notes | Prior exit gates | Medium | Release checklist below passes. |

First implementation batch: authority table, malformed-lease validation, explicit incomplete-read reporting, and fixtures reproducing those behaviors. Next fix inbox delivery/state, then claims. Keep updater changes isolated so destructive-path recovery can be reviewed carefully.

## Proposed file changes

| File or area | Planned change |
|---|---|
| `SKILL.md` | Shorter description and router, modes, capability limits, canonical authority link. |
| `references/safety-protocol.md` | Consistent action policy, scope and identity boundaries, approved production path. |
| `references/interop-protocol.md`, `references/auto-discovery.md` | Precise discovery limits, claim state machine, message identity, delivery semantics. |
| `references/roles-and-briefs.md`, `references/sdlc-and-sprints.md` | Risk-based gates, capability-aware roles, configurable work limits and resumable handoffs. |
| `references/release-playbook.md` | Configurable release flow, evidence freshness, rollback and recovery. |
| `references/token-economy.md`, `references/terse-mode.md` | Remove unsupported savings claims; make clarity more important than style; correct cache and renewal advice. |
| `references/lessons-learned.md` | Preserve useful incidents; qualify project-specific lessons rather than turning each into a universal rule. |
| `scripts/*.py` | Shared parsing/client helpers, robust state, bounded operations, safe updater. |
| `templates/*` | Align schemas/messages, remove product-specific defaults, preserve existing repo rules. |
| `tests/` and CI | Focused helper regressions, fault fixtures, compatibility checks; created as behavior changes. |
| `README.md`, `references/update-and-improve.md`, `VERSION`, `CHANGELOG.md` | Align installation, supported commands, compatibility, and release identity. |
| `agents/openai.yaml` | Consider Codex discovery metadata if Codex support is included; preserve implicit invocation unless the user chooses otherwise. |

Avoid adding a database-backed coordinator, dashboard, plugin system, or large configuration framework to solve problems the existing files and a few helpers can handle.

## How to judge whether it is better

Record a baseline and compare the same fixture tasks after changes. Prefer outcome measures over PR counts, lines of instruction, or tests added.

- **Correctness:** no lost inbox events or false all-clear results in the pagination/failure fixtures.
- **Safety:** no unauthorized side effects or identity-based authority escalation in adversarial fixtures.
- **Adoption:** fewer manual edits and fewer clarification turns for a first successful task.
- **Efficiency:** fewer redundant scans, checks, and repeated permission requests without weaker evidence.
- **Recovery:** interrupted task/update scenarios resume without losing local work.
- **Maintainability:** one parser and one authority source; documented commands work as written.

Before release: validate skill frontmatter, run helper/fixture tests on supported platforms, check linked local references and filled-in templates, exercise fresh setup and rollback, document limitations, and align version identifiers. Keep AAP compatibility where possible; use a major skill/protocol change only when the actual compatibility break warrants it. This planning document alone does not require a version bump.

## Deliberately defer

- Signed approvals until authenticated actors and ordinary owner decisions are implemented correctly.
- Status dashboards and comment-posting automation until the underlying state is trustworthy.
- More agents, aggressive concurrency, and automatic model selection until measured needs justify them and the host supports them.
- Autonomous production operations or background monitoring as defaults.
- New universal rules based on one anecdote; require observed failure evidence and a proportionate correction.

The intended result is a smaller core skill with stronger helpers and clearer evidence, while retaining the independent review and coordination that make this skill useful.
