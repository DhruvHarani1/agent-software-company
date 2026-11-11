# Delivery lifecycle and planning

Use the smallest process that preserves scope, ownership, evidence and recovery. A sprint is optional; a documentation edit need not pass through every department or a release ceremony. Follow the [operating model](company-operating-model.md), [commands](company-workflows.md) and canonical [safety policy](safety-protocol.md).

## Gates by outcome

| Stage | Accountable function | Useful artifact / gate |
|---|---|---|
| Understand | Product/research or coordinator | Problem, affected users, constraints, acceptance, uncertainty. |
| Design | Relevant engineering/design lead | Contracts and decisions sufficient for independent tasks; avoid speculative design. |
| Build | Actual assigned worker | Scoped artifact, appropriate checks, revision/digest and limitations. |
| Evaluate | Independent reviewer/QA; security when relevant | Requirements and behavior evaluated on exact submitted revision/context. |
| Integrate | Delivery/platform owner | Authorized integration, current base/merge checks and conflict resolution. |
| Release | Authorized release owner | Concrete release evidence, target, recovery and post-release checks. |
| Learn | Accountable project owner | Outcome, defects, decisions and one supported process improvement. |

Behavioral bug fixes generally need a meaningful regression demonstration. UI, access, data, performance and deployment changes need checks tied to their effects. Documentation, formatting and suitable refactors use proportionate validation. Do not create tests that merely mirror wording or manufacture red proof where it adds no confidence.

A review covers the head and tested base/environment/dependencies, not an eternal PASS on the head alone. Reassess affected evidence when context changes. Isolate baseline experiments from dirty worktrees. Use actual exit status and diagnostics rather than treating any output as failure.

## Plan and dispatch

Record projects with a goal and accountable owner; add tasks with role, acceptance, dependencies, literal owned paths and effort estimate. Agree shared contracts before parallel frontend/backend/design changes. Break a task down when it improves ownership or dependency clarity, not to maximize the number of roles.

`task queue` explains readiness, dependency, capacity and budget blockers. `task start` records an actual host assignment and reserves effort/capacity; it does not dispatch a worker. Default capacity is a preset choice, with actual host limits taking precedence. Managers coordinate non-conflicting work and preserve evaluator independence.

A generic dependency is satisfied at verified-or-later state. If a downstream task requires a deployed service or data operation, explicitly plan that requirement and record real delivery evidence; generic verification alone does not prove deployment. Path ownership checks apply to declared active build paths and are not atomic filesystem locks.

## Blockers and interruptions

A checkpoint preserves phase, actor, latest submission, paths and next action. Marking a blocker does not stop the real worker or release active resources. After confirming the worker stopped, park it and account incurred effort. Resume/handoff only after reconciling files, identities, evidence, budget and capacity; never reset contributor history to make review easier.

Keep ownership disputes visible. Continue unrelated permitted work while a decision is pending. Escalate with the two views, the consequence and a recommendation rather than sending every routine implementation choice to the owner.

## Optional sprint rhythm

For a coherent batch, state a short goal, committed work, dependencies, checkpoint and cut-off. Update status when facts change. Demonstrate outcomes with evidence; unfinished work moves out of the batch rather than being relabeled done. Retrospectives should propose a narrow correction based on an observed failure, not accumulate universal rules.

Useful priorities: P0 immediate incident/data exposure, P1 major wrong behavior or daily-job blockage, P2 workaround exists, P3 polish. Use the project's existing severity scheme if it is already established. Dates and costs are forecasts unless the owner explicitly makes a commitment.

## Definition of completion

Acceptance is met, appropriate independent evidence is recorded, actual integration/release is documented where required, limitations are visible, and ownership/next action is clear. Close a non-release artifact after verification; do not claim it shipped to production. Cleanup must preserve user changes and useful recovery artifacts.

Report useful outcomes: confirmed defects, escaped/reopened issues, lead time, blocked time, evidence failures, duplicate work, resource variance and recovery incidents. The ledger currently stores some of this as operator evidence; it does not collect full telemetry automatically. PR counts, roles activated and tests added are not quality goals by themselves.
