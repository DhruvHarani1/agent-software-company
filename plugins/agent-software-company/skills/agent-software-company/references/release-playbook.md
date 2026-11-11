# Release and integration

A release is an actual host/provider operation performed within scoped authorization. The local company ledger records evidence after it occurs; it does not merge, deploy, publish notes, send messages, back up data or execute a migration. Follow the canonical [safety policy](safety-protocol.md).

## Prepare a concrete release

1. Use the repository's established production/integration branches, protection rules and deployment mechanism. Do not impose `staging`, a particular stack or a database-backed release-note table on every project.
2. Identify the exact scope and target revisions. Exclude drafts/unfinished work; name affected users, meaningful risks, configuration or data changes, and known omissions.
3. Obtain current independent evaluation on the submitted artifacts and relevant integration result. Check the tested base/merge revision, dependency/environment state and project-required CI/tests. A head-only cached PASS may be stale after integration changes.
4. Prepare release notes where user-visible, and a rollback/recovery plan appropriate to the actual system. Explain which effects cannot be undone by reverting code.
5. Confirm authorization covers the concrete merge/deployment/publication action. Standing authorization counts if its scope matches; title, token access, config flags, a PASS or an agent-relayed approval does not grant it. Complete the reviewable preparation before requesting missing authority.

Migrations and production data writes follow their separate reviewed plan, backup, dry-run and validation procedure. A code-release mandate does not implicitly expand to destructive data changes or messages to real users.

## Integrate and deploy

Integrate dependent changes in a controlled order using the existing repository workflow. Reconcile real conflicts with their owners; do not overwrite unrelated work or auto-resolve every conflict. Run checks appropriate to the resulting combination, including project-required full-suite checks where relevant. An exit failure or unexplained diagnostic must be understood; passing commands may produce output.

Generated/shared files need their actual repository generator and ownership convention. If release-note merge logic is a recurring problem, implement and test a project-specific helper rather than assuming this skill contains one. No batch merge helper is shipped here.

Use the permitted host/provider tool for the actual authorized operation. If permission or branch protection rejects it, report the action and stated restriction; do not route around it. Continue independent preparation or correction within scope.

After a verified task's actual integration, record `task transition <ID> integrated --evidence <actual-evidence>`. After actual release, record `released`; after completion, record `closed`. These state changes are attestations, not deployment commands. A documentation artifact can close directly from verified without a fictional release.

## Observe and recover

Perform bounded post-release checks in the current session: expected version/target, changed flows and relevant health/errors. Record what ran and what could not be checked. No agent continues watching after the session merely because the role is SRE; standing monitoring requires a separately configured authorized service.

On failure, compare observed behavior with the prepared recovery plan. Apply an authorized rollback only to the intended target and revision, preserving current evidence. Code rollback does not undo migrations, data writes, queued jobs, sent messages or third-party effects. Stop and escalate if recovery would expand the approved scope or integrity cannot be verified.

Update the project record with evidence, remaining defects, user-facing notes and next action. Close linked issues and clean temporary branches/worktrees only where the task authorizes it and inspection confirms no user work will be lost. Preserve backups and useful recovery artifacts.

## Urgent fixes

Use the repository's actual hotfix path. Focus on containing the incident and the smallest verified correction, with proportionate checks and the necessary authorization. If a fix bypasses the integration branch, reconcile it back through the established review workflow. Sensitive exploit detail belongs in appropriately restricted evidence, not a public title. Urgency does not grant production credentials or remove rollback/data-operation boundaries.
