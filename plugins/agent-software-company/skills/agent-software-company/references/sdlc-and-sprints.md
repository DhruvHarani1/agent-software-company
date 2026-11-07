# SDLC, sprints and turn-taking

## Phases (every issue passes all of them)

| # | Phase | Owner | Output | Gate |
|---|---|---|---|---|
| 1 | Requirements | Owner / Boss | Issue: why, who is affected, acceptance criteria in plain words | Ready: one problem, testable, decisions answered |
| 2 | Design | Manager | Short plan in the issue: screens, rules, data, risk level | High risk: Boss approves; business rules: owner |
| 3 | Build | Fixer | Branch, failing test first, then the fix | Red on old code, green on the fix, type-check clean |
| 4 | Code review | QA + Boss | Verdict comment + risk review | PASS, role matrix checked, release note right |
| 5 | Integration | Boss | Merge into the integration branch one at a time | Compiles; full suite green after a batch |
| 6 | Functional test | Role testers | Walk changed flows as each role | No open defect |
| 7 | Release | Boss | Release pull request, backup, draft notes | Owner's go for risky items; rollback note |
| 8 | Operate | Boss / security | Post-release check, watch reports | No incident in the first day |

**Definition of Done:** merged, tested, release note (if visible), area note updated, issue closed with the link, no temporary folders left.

## Sprint (about a week; agents work on request, so dates are the contract)

- **Planning:** pick issues by value and risk, check dependencies, set the turn order, write "Sprint N plan" (goal in one sentence, committed list, stretch list, waits) with a milestone and due date.
- **Daily standup:** each manager edits one comment on the standup issue at the start of their turn: Doing, Done, Blocked, Needs, Next. The Boss reads it before giving the next turn.
- **Mid-sprint check:** re-order or drop.
- **Review:** the release pull request is the demo (what shipped, what did not, proof).
- **Retro:** a file `retro-sprint-N.md`: what went well, what hurt, one change; fold rule changes back into the docs.
- **Cut-off is fixed.** Work not Done moves to the next sprint; never merge half-finished work to hit a date.

## Turn-taking and work-in-progress limits

1. At most 2 sessions work at once: one builder + the QA reviewer. Testers and the security reviewer get their own turn.
2. Dependencies decide the order. If A needs B's output, A pauses with label `blocked` and a standup note; B goes next; A resumes after B is merged.
3. Shared files belong to whoever's turn it is.
4. One batch in flight: finish and merge (or park) before starting a new one.
5. Max 5 pull requests per manager per turn. Quality over count.
6. If the machine is slow (merges taking minutes), reduce concurrency.

## Priorities

P0 security hole / data loss / site down: hotfix the same day, straight to a release. P1 wrong money, wrong permission, blocks a daily job: this sprint. P2 wrong with a workaround: next planning. P3 polish.

## Metrics (report each sprint)

Issues found vs confirmed; pull requests merged; first-pass approval rate; reopened bugs; lead time issue to release; abandoned pull requests; incidents caused by changes; tests added.

## Rollout order for a new setup

Step 0 safety foundation (test database, protected branches, backups rehearsed). Step 1 one manager only. Step 2 QA reviewer + release path rehearsed. Step 3 add managers one at a time. Step 4 security reviewer, functional testers. Step 5 data-quality and architecture teams. Step 6 scheduled runs only after a clean fortnight, starting read-only.

## Test routine (v1.3)
Per pull request: type-check plus the tests related to the change (`vitest run --changed origin/staging`, or your runner's equivalent) and the whole test file of every touched file. Full suite once on the integration branch before each release, and nightly. Pin the clock in any test that touches a date rule.
