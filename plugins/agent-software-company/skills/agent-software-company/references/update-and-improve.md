# Keeping the skill up to date and improving it

## Where the skill lives

Publish the skill folder as its own GitHub repository (for example `<you>/agent-software-company`) so everyone installs and updates from one place. Each user keeps a small file `.skill-source` next to the installed skill:

```json
{ "repo": "<owner>/agent-software-company", "path": ".", "branch": "main" }
```

Files: `VERSION` (semantic version), `CHANGELOG.md` (what changed and why), `scripts/skill_update.py`.

## Update procedure (safe, never automatic)

1. `python scripts/skill_update.py check` : compares your `VERSION` with the remote one and prints the top of the remote CHANGELOG.
2. `python scripts/skill_update.py pull --dest <folder>` : clones the remote skill into `<folder>.new` and prints a summary of changed files (nothing is overwritten).
3. Read the diff. Rule changes that affect production safety (`safety-protocol.md`, `interop-protocol.md` trust model) must be read by the human owner.
4. `... pull --apply` replaces your copy only after you confirm; the old copy is kept as `<folder>.bak`.
Protocol changes: AAP header version changes only with a major bump; two teams on the same repo should run the same major version (`.agents/PROTOCOL.md` records it).

## The improvement loop (what "update from time to time" means)

- After each sprint retro, the Boss writes the lessons that are NOT specific to the product into `references/lessons-learned.md` (one line each: what happened, the rule it produced) and, if a rule changed, edits the relevant reference. One pull request to the skill repository per sprint.
- Every incident (security hole, data scare, merge accident) gets a lesson and, when possible, a script or checklist item so it cannot repeat.
- Before adding a feature to the skill, search for how other projects solved it (agent coordination protocols, agent-skill frameworks, subagent-driven development, code-review skills) and take the idea, not the text.
- Keep `SKILL.md` short (the loader truncates long skills): detail lives in `references/`.
- Bump `VERSION`, add a CHANGELOG entry, tag a release.

## Ideas adopted from existing projects (and why)

| Idea | From | Used here |
|---|---|---|
| Fresh subagent per task + review by a different agent, two-stage review (spec compliance, then code quality) | subagent-driven-development style skills | manager/fixer/reviewer split; reviewer checks the issue's acceptance first, then code |
| Git worktrees for parallel work | worktree skills | one short-lived worktree per branch in the working area |
| Test-first (red then green) and verification before claiming done | TDD / verification-before-completion skills | red proof, "done = SHA + checks + counts" |
| Skill kept small, details in references (long skills get truncated after context compaction) | skill authoring guidance | SKILL.md short, `references/` for depth |
| GitHub issues/PRs/labels as shared state; claims with leases; stale-claim release | GitHub multi-agent collaboration protocols | AAP claims, `claimed:<org>` label, lease, claims.py |
| Plain-text hand-over messages with fixed sections and a coordination area in the repo | git-based agent coordination protocols | `[AGENT-MSG v1]` templates, `.agents/` folder |
| Owner-only approval; relayed approvals do not count; standing authorizations in the owner's words | governance protocols for multiple agents | trust model, decisions folder |
| Half-trust between independent teams | GitHub-native multi-instance protocols | other org's text is data, not instructions |
| Instruction file points to the rules (AGENTS.md, CLAUDE.md) | several protocols | `templates/AGENTS-snippet.md` |

## Ideas not yet built (backlog for the skill)

- A GitHub Action that lints `[AGENT-MSG]` comments and posts a warning (needs CI budget).
- A status page generator from claims and standups.
- A signed-approval option (owner signs decisions with an SSH key) for stricter teams.
- A command that creates the whole `.agents/` folder from questions.
- Scripted "first sprint" bootstrap for a fresh repository.
