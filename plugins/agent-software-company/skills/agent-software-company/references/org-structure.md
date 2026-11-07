# Organisation structure: run the agents like an IT company (v1.3)

A flat "Boss + managers + reviewers" works for a small backlog. When the work grows, organise by **departments** that own outcomes. Same rules apply: GitHub is the record, the owner decides business rules, production data needs the owner's explicit approval.

## Principles
1. **Departments own outcomes, not tasks.** Each has a head, a charter (purpose, inputs, outputs), numbers it is measured on, and a one-page brief a new session can read.
2. **Hats, not headcount.** A session costs usage budget and machine time. A role is a hat with a brief; one session may wear several hats. Start a dedicated session only when that role's queue holds more than about a week of work or an incident shows a gap. Cap: 2 builders plus the reviewers at once.
3. **Separation of duties.** The author never reviews or merges. QA is independent of Engineering; Security is independent of both. The Boss merges and releases; the owner decides business rules.
4. **Everything durable lives on GitHub** (issues, pull requests, standup issue, priority list).

## Departments (copy, delete what you do not need)
| Department | Roles (hats) | Owns | Measured on |
|---|---|---|---|
| PMO / Delivery | delivery manager (Boss), backlog groomer | sprint plan, turn order, priority tiers, cleanup after every merge, weekly numbers | lead time, open PR age, blocked items |
| Product & Research | head of product, UX designer, product analyst, field researcher | requirements with acceptance criteria, open-questions list, usage and feedback themes | work shipped that users asked for, questions answered |
| Engineering | one **squad per product area** (tech lead + fixer sub-agents + in-squad reviewer), Platform & Architecture (shared code, upgrades, debt) | building, area notes, tests first | first-pass QA approval, defects after release |
| Quality Assurance | QA lead, QA reviewers, functional testers (one per user role), test-automation engineer | review with red proof, role walk-throughs, full suite before every release, flaky and clock-dependent tests | escaped defects, false passes |
| Security & Compliance | security lead (read-only), data guardian | route and screen access review, backups and restore rehearsal, secrets, access review | open P0/P1, restore test passed |
| DevOps & Release | release manager, DevOps engineer, incident manager | release PR, backups of release data, environments, monitoring, hotfix handling | rollbacks, time to restore |
| Data & Integrations | data-quality lead, integration engineer, data analyst | dirty data (always under the data protocol), sync health, read-only numbers for the owner | rows cleaned with audit, sync failures |
| Support & Documentation | support desk, technical writer, training lead | feedback to issues, plain-language release notes, area notes, how-to messages | feedback answered in 2 days |

## Flow
feedback -> Support/Research (issue with steps) -> Product (value, acceptance, tier) -> PMO (turn order) -> Engineering squad -> QA -> Security (only who-sees-what changes) -> Boss merges into `staging` + full suite -> Release -> Support/Writer tells users -> Research confirms with users -> PMO closes and cleans up.

## Cadence
Daily: standup board, cleanup, release if verified work is waiting. Weekly: plan, turn order, mid-sprint check, retro. Monthly: access review, backup restore test, flaky test and dependency sweep. Quarterly: architecture and debt review, roadmap with the owner.

## Staffing plan: start lazily
Core from day one: Boss, one tech lead per area, a QA reviewer, a security reviewer. Everything else is a hat the Boss or a lead wears until its queue justifies a session. Write the charter into the repo first (template below), then start the session. Suggested order of the next hires: test-automation engineer, data-quality lead, support desk, platform and architecture, DevOps.

## Role brief template
```
Role: <name> in <department>. Reports to: <lead>.  Purpose: one sentence.
Inputs: issues/labels it reads. Outputs: what it produces and where.
Rules: read-only or write; folders allowed; production forbidden; terse style; commit trailers.
Done means: measurable result. Stop and ask the Boss when: money, permissions, dates, data change, unclear rule.
```

## RACI sketch
Business rule: owner A, product R. Design and build: Boss A, engineering R. Code review: QA R. Who-sees-what or money change: owner A, Boss, engineering, QA and security all R. Release: Boss R, owner A for risky items. Production data change: owner A (written "approved"), data team R. Backups and secrets: security and DevOps R. User message and release notes: writer R, Boss A.

## Roster
Record each agent in `.agents/ROSTER.json` with `role` and `areas` (add `department`). Departments are labels; they do not change who may merge or approve.
