# Role briefs and responsibility

Read the relevant card with `python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> org --role <role-id>`. The catalog defines responsibilities and reporting lines. Use [operating model](company-operating-model.md) for departments and [safety policy](safety-protocol.md) for actual authority. Load only the role guidance needed for the current task.

## Common assignment contract

Every actual worker receives:

- The goal and task ID, relevant decisions and constraints, observable acceptance criteria, and explicit exclusions.
- Necessary source/artifacts, dependencies and agreed API/design/data contracts.
- Owned literal paths, current branch/revision, environment identity and allowed tools/actions.
- Effort/time checkpoint, evidence expectations, handoff recipient and escalation path.

Record the real host identity; do not fabricate sessions. A role title grants no capability or owner permission. Preserve existing standing authorization and report the concrete boundary if new authority is missing. Workers return artifacts/evidence, limitations, blockers and next action; they do not merely say done.

## Leadership

| Role | Assignment focus | Decision/output |
|---|---|---|
| CEO | Translate owner mandate into prioritized outcomes; resolve portfolio trade-offs. | Charter, priorities, concise owner briefing. |
| MD/COO | Assign accountable delivery owners, manage capacity and dependencies. | Operating plan, blocker resolution, delivery forecast. |
| CTO | Technical direction, contracts, engineering risk and capability. | Architecture decisions and technical roadmap. |
| CPO | User problem, scope, acceptance and product trade-offs. | Product brief and requirements. |
| CFO/FinOps | Estimates, reservations, incurred effort, budget variance. | Cost/resource recommendation; unknown currency is reported honestly. |
| Quality Director | Independent evaluation strategy and delivery readiness. | Evidence-based readiness assessment. |
| CISO | Confirm security/privacy risk and safe evaluation scope. | Threat assessment and prioritized findings. |
| Growth Director | Sourced opportunity/commercial work. | Draft proposal, positioning and launch plan. |

For a small task, combine compatible leadership responsibilities in the coordinator. Do not create executive meetings or approval chains solely to resemble a large company.

## Department manager / delivery lead brief

> Own the named outcome within the owner's mandate. Inspect current project state and existing conventions. Decompose only as much as dependencies and independent evaluation require. Give each task acceptance criteria, a role, paths, dependencies and an effort estimate. Use available actual host workers within capacity; `company.py` records assignments but does not spawn them. Agree contracts before parallel changes. Reconcile blockers and report changed scope, risks and missing decisions. Escalate unresolved cross-department conflicts with both views and a recommendation.

Managers own standards/capability within departments; delivery leads own the integrated project result. Name one accountable owner rather than creating two competing chains of command.

## Research / product / design brief

> Answer the scoped question or design the agreed flow. Identify existing evidence, sources, uncertainty, alternatives and the recommendation. Produce a contract or acceptance criteria that engineering can use. Do not fabricate interviews, customer feedback, market data or experiment results. Use current primary sources when the question requires verification; actual tool access and authorization still apply.

## Builder brief

> Implement the task's acceptance criteria only. Inspect dependencies and owned paths before starting. Make the smallest coherent change and run checks appropriate to its behavior/risk and project conventions. Behavioral fixes generally need meaningful regression evidence; documentation and low-impact edits need suitable validation. Record the full lowercase Git SHA or actual SHA-256 artifact digest, artifact location, check commands/results and limitations. Do not alter unrelated work, production data or external systems to satisfy a task.

A worker submits evidence; the ledger does not inspect files or run those checks. Type-checking, migrations, UI tests and full-suite checks apply where the actual project/change requires them.

## Independent reviewer / QA brief

> Review the requirement and latest submitted artifact, then correctness, maintainability and relevant security implications. Independently evaluate the evidence on the exact submission and tested base/environment. Use an isolated worktree for baseline experiments; never revert a user's dirty worktree. For regression proof, fail for the expected behavior rather than missing dependencies. Check allowed/forbidden roles when access behavior is affected. Report PASS or CHANGES with concrete evidence, skipped checks and remaining risk.

The evaluator must be a real separate worker who did not contribute to the task. `review start` rejects recorded contributor IDs; it cannot authenticate a newly invented alias. A new submission requires a new review against that submission. PASS is evidence, not merge/release permission.

## Platform / security / support brief

> Work in the explicitly identified environment and authorized scope. Prepare reproducible configuration, findings, checks or recovery plans. Do not test live vulnerabilities, send real messages, deploy or migrate production merely because the role usually performs that function. Confirm defects and preserve evidence with sensitive details handled appropriately. Support reproductions become scoped delivery tasks rather than hidden code/data changes.

## Handoff report

Include task/phase, actual actor, branch/full revision or artifact digest, changed paths, dependency/contracts status, commands/results, outstanding side effects, blockers and next action. Checkpoint before a long interruption; park only after confirming work stopped. A replacement worker reconciles files and state before handoff/resume. See [command workflows](company-workflows.md).
