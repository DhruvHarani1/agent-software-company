# Published activity discovery

`radar.py` is a read-only diagnostic, not a team registry, lock service, or authorization mechanism. See [interop](interop-protocol.md) and the canonical [safety policy](safety-protocol.md).

```text
python <SKILL_DIR>/scripts/radar.py --repo owner/name --org org-a --paths "src/**,docs/**" --hello
```

It reads default-branch commits and issue comments in the selected window (`--hours`, default 72), all open PRs and their paginated file lists, and the collaborator list. Signals are `Agent-Org:` trailers, valid `from=<org>/<agent>` message fields, and actual GitHub logins. It does not implement branch-prefix matching or enumerate other branches, local files, unpushed work, or active runtime sessions.

Output states scope, scan time, window, and `coverage=complete|partial`. An unavailable authenticated reader exits nonzero with coverage unavailable. A failed collection is reported; a failed permission lookup gives access `unknown`. PR file coverage is partial when reported changed-file counts differ or the API file cap is reached. A complete scan is still an observation of published activity, not proof that nobody else is editing locally.

A declared org is an unverified hint. Actual GitHub actors are shown separately. `teammate` means observed repository push permission; `guest` means no push permission observed in a complete collaborator lookup. Neither grants authority. Claims require owner-reviewed actor bindings and a separate complete claim scan.

`--hello` prints draft introductions only. It checks outgoing greetings by the authenticated login and exact recipient in the current comment window; an incoming greeting or substring match does not suppress the draft. An older greeting outside that window may be suggested again. Read current context before an authorized post.

If overlapping PR files are observed, coordinate ownership or pick non-overlapping work. If coverage is partial, treat overlap as unresolved; do not infer an all-clear. The helper does not detect all semantic/API conflicts or replace claims and integration tests.

For two accounts owned by one person, use distinct org identifiers and separate workspaces. A common GitHub login can produce different discovery hints but does not authenticate separate agents or independent review. Record actual reviewers and their tested artifacts.

Keep normal commits readable; optional trailers help discovery:

```text
Agent-Org: org-a
Agent: frontend-dev
```

Check at meaningful task boundaries, not in a polling loop. Existing task/standing authorization governs whether introductions, status comments, review offers, or overlap notices may be posted. The local `.agent-company/` company ledger is separate and is not synchronized by radar.
