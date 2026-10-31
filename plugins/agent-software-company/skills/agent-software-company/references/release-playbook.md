# Release playbook

## Normal release (integration branch -> production)

1. All pull requests in the batch are merged into the integration branch one at a time; run the type-check and the **full test suite** (let it finish; budget minutes). Fix any failure found there before releasing (tests that rendered a component without a new provider, or an allow-list test updated for a new grant, are typical).
2. Open ONE release pull request `staging` -> `main` listing: each change (number, one line, risk), what was checked, what is NOT included (drafts), "no database changes" or the migration, the rollback (revert the merge commit or restore the previous deploy; a code rollback does not undo a destructive migration).
3. Owner's go for risky items. Merge the release pull request with a merge commit.
4. Back up the release-notes tables (encrypted), then cut the draft release from the list of unreleased entries (a script that creates a DRAFT only; publishing stays with the owner or HR in the app). Commit the emptied list on a branch and merge it into the integration branch with a plain merge (not the batch helper).
5. Post-release check: the site responds, the changed screens load, no new errors; tell the owner.

## Release-note list hygiene (the shared file that always conflicts)

One plain sentence per visible change, no technical words. The list holds only entries NOT yet in a release. When a branch carries an old copy of the list, merging it resurrects already-released entries. Rule: after merging the integration branch into a branch, the list must equal the integration branch's entries plus only the entries that branch itself added. A small script computes that (entries on the integration branch + lines this branch added relative to the merge-base, de-duplicated, one header). Always run the type-check and the list's tests before merging.

## Batch merge helper (outline)

For each pull request: worktree of its branch in the working area; merge the integration branch; if only the release list conflicts, rebuild it with the script; if anything else conflicts, STOP and hand it back to the owner of the branch; type-check (stop on any output); list tests; push the merge commit to the branch; wait a few seconds; merge the pull request with squash; remove the worktree. Never use it for the release-draft pull request (that one empties the list).

## Hotfix

See safety-protocol.md: branch from production, pull request to production, then merge into the integration branch.

## After the release

Close the issues the pull requests fixed (a merge into the integration branch does not close them automatically). Delete merged branches. Update the standup board. Write the retro.
