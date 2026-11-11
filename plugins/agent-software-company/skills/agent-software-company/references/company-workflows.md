# Company command workflows

Run commands against an existing workspace. `--workspace` is a global option before the subcommand. The examples use `<SKILL_DIR>`, `<PROJECT_DIR>` and values returned by previous commands; replace them before use. IDs such as `<TASK_ID>` are ledger IDs. `<ACTUAL_HOST_ID>` comes from a real host assignment, never an invented persona. Commands mutate only the local ledger unless explicitly described as separate host work.

## Initialize and inspect

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> init --name "Acme IT" --mission "Deliver the agreed portal" --preset startup --max-active 2 --budget 100
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> init --name "Acme IT" --mission "Deliver the agreed portal" --preset startup --max-active 2 --budget 100 --apply
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> org --role frontend-engineer
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> status
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> budget
```

The first command previews without writing. Repeated `init --apply` returns the existing company without resetting it or changing limits. Presets provide default capacities founder=1, startup=2, full-company=4; the whole catalog remains available in every preset. Budget units are abstract effort, not a promise about token/currency costs. `org` can inspect the bundled catalog before initialization.

## Plan a scoped outcome

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> project plan "Customer portal" --goal "Customers can inspect their own requests" --owner md
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task add "Specify request API" --project <PROJECT_ID> --role api-architect --acceptance "Ownership, fields and error behavior are explicit" --path docs/contracts --estimate 2
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task add "Implement request screen" --project <PROJECT_ID> --role frontend-engineer --acceptance "Only the customer's own requests appear" --depends <CONTRACT_TASK_ID> --path src/client --estimate 5
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task queue
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task show <TASK_ID>
```

Use returned IDs in later commands. Repeat `--acceptance`, `--depends` or `--path` for multiple values. Paths are relative literal files/directories; globs, traversal, drive paths and absolute paths are rejected. Do not infer ownership of undeclared files. Dependencies permit dispatch after the predecessor is verified or later; if deployment is required, incorporate that prerequisite into scope and actual orchestration.

A documentation-only project can use `technical-writer` and a docs path. It needs no database, GitHub, deployment or running web app merely to use the ledger. Choose appropriate artifact checks and independent review.

## Assign actual work, then submit evidence

First obtain the actual builder identity from the host. Confirm the task queue, mandate, environment and paths. Then record the assignment:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task start <TASK_ID> --actor <ACTUAL_BUILDER_HOST_ID>
```

This reserves capacity and estimated effort. It does not start an agent, edit code, create a branch or run a check. The real worker does those things with the permitted host tools. The ledger prevents recorded dependency/capacity/budget/active path conflicts; these checks are not filesystem isolation or proof another process stopped.

After actual work and checks, calculate the real revision or artifact digest and record the evidence:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task submit <TASK_ID> --revision <FULL_LOWERCASE_GIT_SHA> --artifact <ACTUAL_ARTIFACT_LOCATION> --evidence <ACTUAL_CHECK_REPORT_LOCATION>
```

For a non-Git artifact use `--revision sha256:<64-lowercase-hex-digest>` calculated from the actual reviewed file. Evidence should include acceptance results, commands/outcomes, tested base/merge revision where relevant, environment/dependencies, and omissions. The CLI accepts an evidence string and does not inspect the file, validate truth or run checks.

Submission accounts the reserved remaining estimate by default. Supply `--actual <MEASURED_UNITS>` only when those units were actually measured. If earlier effort was accounted while parking, report only the completion segment here rather than double-counting it. Estimated and measured entries remain distinct; actual usage may exceed a forecast and show a deficit.

## Independent review and revision

Obtain a real separate evaluator's host identity. It must not be any recorded contributor to this task. A new alias for the same builder is not an independent review.

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> review start <TASK_ID> --reviewer <ACTUAL_REVIEWER_HOST_ID> --estimate 2
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> review finish <TASK_ID> --reviewer <ACTUAL_REVIEWER_HOST_ID> --verdict PASS --revision <EXACT_LATEST_SUBMISSION_REVISION> --evidence <ACTUAL_REVIEW_REPORT_LOCATION>
```

Review assignment reserves capacity/effort. The evaluator performs relevant checks outside the ledger; finish records the result and accounts its remaining estimate, or measured `--actual` if supplied. The named revision must exactly match the latest submission. PASS marks verified. CHANGES returns to ready: start an actual builder assignment, fix, submit a new revision, and perform a new review. Prior evidence does not automatically cover a new submission or changed integration context.

If no independent evaluator exists, report the limitation and leave the review gate unmet. Do not manufacture an identity or evidence string to advance state.

## Checkpoint, park, resume and handoff

A checkpoint records recovery information without freeing capacity or stopping a worker:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task checkpoint <TASK_ID> --next "Inspect the failing integration case before continuing" --blocked
```

For an interruption, first confirm the real builder/reviewer has stopped and reconcile files and external effects. Then park the active assignment:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task park <TASK_ID> --next "Worker stopped; reconcile the recorded revision before continuing" --spent 1 --basis estimate
```

Use actual newly incurred effort since the last accounting boundary; `--basis measured` is appropriate only for a measured value. Parking preserves delivery phase, contributor history, submission and assignment while recording spent effort and releasing active capacity/remaining reservation. It does not stop a process. Repeated parking without a resumed assignment is rejected.

After inspecting actual work and confirming the original worker is available:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> resume <TASK_ID>
```

Resuming a parked assignment rechecks budget, capacity, actor availability and applicable active build paths before restoring its reservation. It preserves the delivery stage rather than starting a fresh build or resetting reviews. For a blocked checkpoint without parking, resume clears the reconciled blocker; it does not duplicate the active reservation. No worker is spawned.

If a different worker must take over, obtain its actual host identity and record reconciliation evidence:

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task handoff <TASK_ID> --actor <ACTUAL_REPLACEMENT_HOST_ID> --evidence <ACTUAL_RECONCILIATION_REPORT>
```

This transfers an active or parked assignment without erasing authorship. A contributor cannot take over its independent review. For parked work, hand off before resume if the old worker cannot continue; then reconcile the replacement and resume. Always confirm the original actor has stopped before transferring actual ownership.

## Decisions and verified delivery events

```text
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> decision "Which error behavior is in scope?" --outcome "Return the agreed temporary error" --source <AUTHENTIC_OWNER_DECISION_REFERENCE> --owner cpo
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task transition <TASK_ID> integrated --evidence <ACTUAL_INTEGRATION_EVIDENCE>
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task transition <TASK_ID> released --evidence <ACTUAL_RELEASE_EVIDENCE>
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> task transition <TASK_ID> closed --evidence <ACTUAL_COMPLETION_EVIDENCE>
python <SKILL_DIR>/scripts/company.py --workspace <PROJECT_DIR> report
```

A decision entry records a source, not authorization. Integration/release transitions record completed, independently authorized host actions; they never merge/deploy/publish. Follow [release guidance](release-playbook.md). A verified documentation artifact may close without claiming integration or release. `report` prints Markdown; redirect it to an owner-chosen file if needed.

## Recovery boundaries

Inspect state and real artifacts first after a crash. Writer locks are exclusive; confirm a writer is stopped before removing a stale lock. Corrupt or unknown schema state fails closed and is not reset by `init`. Preserve the state and restore a known snapshot through an authorized recovery procedure. The ledger cannot discover missed side effects, repair damaged product files or reconcile unauthenticated worker claims automatically.

For GitHub communication use [interop](interop-protocol.md), not a fictional company CLI command. For skill installation recovery use [update guidance](update-and-improve.md). All actions remain governed by the [safety policy](safety-protocol.md).
