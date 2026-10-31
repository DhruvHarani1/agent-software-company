# Safety protocol

## Production data (the non-negotiable rule)

Agents read code and the test environment only. Any change to real data follows ALL of:
1. **Encrypted backup first**, every time, even for one row. A script that writes an AES-256-GCM file outside the repository, key derived (scrypt) from a passphrase kept in an environment variable (never beside the file, never in the repo). Verify: decrypt, compare the checksum, compare row counts. Rehearse a restore into the TEST database before trusting a backup type.
2. **Dry run:** the script prints exactly what it would change; no writes.
3. **Written plan for the whole class of the problem** (not one example): which rows, how many, how to undo, who is told.
4. **Execute only after the owner writes "approved"**; the script writes a before/after log.
Never: agents using production keys, sending real messages, publishing release notes, running migrations. A needed migration is described in the issue; the Boss writes it with a rollback, the reviewer checks it on the test database, the owner approves the exact script, the owner (or the Boss on the owner's explicit instruction) runs it, the Boss verifies with counts. Approval never triggers a run by itself.

## Environments

| Environment | Data | Who |
|---|---|---|
| Checkout | none; tests use mocks | everyone |
| Local staging app | test database, all outside connections off (mail, chat webhooks, cloud APIs, cron, error reporting) | testers, managers |
| Deploy previews and the integration branch | test database via per-context hosting variables | review |
| Production | real | only through a release; data only via the protocol |

The local staging launcher refuses to start unless the database is the test one, and blanks the production-only variables (empty, not absent: some frameworks never override a variable that is already set).

## Branch protection

Protect the production branch AND the integration branch: pull request required, no direct push, no force push, applies to admins. No required status check if CI cannot run; then the local runs by the reviewer are the evidence and must be written in the pull request.

## Secrets

- Env files git-ignored (`.env*`). Production values only in the hosting provider's production context.
- A secret pasted into a chat is exposed: reset it when the work is finished (for test-only keys the owner may accept the risk).
- Backups and tokens live outside the repository; tokens given to the Boss are stored in a git-ignored file, never printed.
- CI workflows on agent branches must not receive production secrets (use protected environments with approval).

## Stop conditions (stop and escalate, no workaround)

Failing checks you do not understand; a backup that cannot be verified; the environment differs from expected; an agent discovers it has production access it should not have; a permission denial for an action (do not route around it: report it).

## Hotfix path (P0)

Fix on a branch cut from production, test red/green, pull request straight to production, then merge the same change into the integration branch. Describe the exposure in plain words in the pull request body, not in an issue title, and say whether it was tested live.
