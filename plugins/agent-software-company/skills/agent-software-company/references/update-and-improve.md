# Updating the skill and improving its workflows

## Source configuration

An installed copy can contain a local `.skill-source` file:

```json
{ "repo": "owner/agent-software-company", "path": ".", "branch": "main" }
```

`repo` is an `owner/name` repository on GitHub. `branch` is a branch or tag, and `path` is a relative skill subdirectory without `..`, an absolute path, or links. The updater uses Git to fetch; it does not execute downloaded Python, install dependencies, or run hooks from the candidate.

Use this updater for a standalone installed skill directory. A Git checkout must use its normal Git diff/review workflow; the updater refuses to replace `.git` directories or files.

## Review and apply

The paths below assume the installed skill folder for reading/fetching. Before `apply` or `rollback`, switch the shell to a directory outside the installation and invoke the updater by its full path, especially on Windows where a shell's working directory may prevent a rename. The installation still defaults to the script's skill folder. For a different installation, put `--root <installed-folder>` before the command. `check`, `fetch`, and its `pull` alias can access the network. `diff`, `apply`, and `rollback` do not fetch anything.

```text
python scripts/skill_update.py check
python scripts/skill_update.py fetch
python scripts/skill_update.py diff <candidate-folder>
python scripts/skill_update.py apply <candidate-folder> --reviewed <review-digest>
python scripts/skill_update.py rollback <backup-folder>
```

1. `check` reads and validates the remote skill and prints local/remote versions and the immutable source commit. A different version is reported as different, including a lower version; the updater does not silently assume a downgrade is safe.
2. `fetch` creates a unique candidate under a sibling `<skill-name>.updates` directory. `fetch --dest <store-folder>` chooses another store outside the installation. It records the source commit, candidate file hashes, and the current local baseline. Existing candidates are never erased.
3. Inspect the candidate's `payload/`, then run `diff`. The output lists added, modified, and deleted managed files, flags code/policy changes, and prints a review digest. Use an ordinary text diff tool to inspect file contents; the summary alone is not a content review. Have the relevant human owner review changes to authority, trust, or production rules.
4. `apply` requires that digest. It verifies that the candidate and metadata still match the reviewed digest, checks that local managed files still match the recorded baseline, validates Python syntax/frontmatter/version, and stages the exact candidate. It never clones again. A real application still requires the user's authorized update scope; the digest is an integrity check, not an authorization grant.
5. The old installation is renamed into a unique sibling `<skill-name>.backup-<id>/installation`, and the staged installation takes its place. The old copy and candidate remain available. If the second rename fails, the original is restored automatically where possible, with an explicit recovery path if restoration fails too.

Local edits that already existed at fetch appear in the reviewed comparison. Edits made after fetch stop apply rather than being overwritten. Preserve such work and fetch/review again. Applying a candidate removes managed files listed as deleted; this is why deletion review matters.

The updater preserves current `.skill-source`, `.agents-state/`, `.agent-company/`, `.env`, and `.env.*` data. Candidates may not ship these local files. It refuses active or stale state writer locks. Stop active agents before updating: a directory swap cannot reliably coordinate with arbitrary concurrent processes. The updater also uses an exclusive sibling update lock to prevent two updaters from swapping the installation at once.

Candidate/backup paths must stay outside the installation. Symlinks, Windows junctions/reparse points, path traversal, and special files are rejected. Installation swap staging and backups stay beside the installation so renames use the same filesystem. Filesystem permission failures are reported; do not route around a sandbox denial.

`pull` is only an alias for `fetch`. The former `pull --apply` interface is deliberately rejected: applying must name the candidate already reviewed. Unknown arguments are errors.

## Rollback and interrupted updates

`rollback <backup-folder>` validates that the backup belongs to the installation and has not changed. It refuses to overwrite new managed-file edits made after the update. It stages the older code, preserves **current** local configuration and runtime state, and keeps another backup of the replaced version. A code rollback does not undo external data writes, sent messages, or deployments.

A process kill between the two installation renames may leave the installation path missing. The original copy remains in the unique sibling backup folder, with `backup.json` recording the target and expected hashes. To recover:

1. Verify that no updater or company-state writer is active. If a stale `<skill-name>.update.lock` exists, remove only that verified stale lock.
2. Run a trusted retained updater copy, such as the original script under `<backup-folder>/installation/scripts/skill_update.py`, with `--root <missing-installed-folder> rollback <backup-folder>`. This validates and copies the backup back to the missing path without deleting the backup.
3. Inspect state and artifacts before resuming work. A retained `.stage-<id>` folder is diagnostic/recovery material; never delete it or an old backup automatically.

Windows may prevent renaming a directory containing open files. Close the affected process or file only when authorized, then retry the same reviewed candidate. Fault-injection tests exercise failed second rename, recovery of a missing installation, local drift, and rollback preservation. Tests do not perform live network requests or update this working skill.

## Improvement loop

After real delivery work, record a product-independent lesson only when supported by observed behavior. Propose the smallest change that addresses the failure; avoid converting every incident into a universal rule. Keep detailed department and workflow instructions in relevant references rather than expanding the entrypoint indefinitely.

For a behavior change, add a meaningful isolated regression fixture, run the helper tests, review the resulting workflow, and update `VERSION` and `CHANGELOG.md` for a release. Keep skill-version changes separate from AAP wire-protocol compatibility: breaking message semantics require an explicit compatibility plan; adding an optional skill capability need not change the header version.

Prefer independently evaluated realistic tasks when delegation is available and authorized. Do not require live production access, a paid service, or external messages to run the default evaluation. Dashboards, recurring work, signed approvals, and additional integrations should follow demonstrated needs and the company blueprint rather than become prerequisites for ordinary work.
