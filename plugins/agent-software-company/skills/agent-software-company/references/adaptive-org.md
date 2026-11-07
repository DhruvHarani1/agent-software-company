# Adaptive organisation: the Boss designs the company for THIS project (v1.4)

The skill is not tied to one product. A pure internal script, a public SaaS, an open-source library, a mobile app and a regulated payments system need different companies. The Boss (CEO) profiles the project, composes the org from a role catalog, writes the decision down, and re-checks it on a schedule. The owner may veto; the Boss does not wait to be asked.

## 1. Profile the project (do this first, 10 minutes, write `docs/team/PROFILE.md`)
Run `python scripts/org_profile.py <repo>` for a first guess (languages, frameworks, deploy files, tests, CI, database, payments/auth/PII hints, size), then fix it by hand. Answer these:
| Question | Why it matters |
|---|---|
| Who uses it: only staff (internal), customers (external), the public, developers (library/API)? | decides support, comms, marketing, docs weight |
| Money, personal data, health, regulated? | decides security/compliance depth, who must approve |
| Size: files, modules, test count, team of agents you can afford | decides squads versus one generalist |
| Release shape: web deploy, app store, package registry, on-prem | decides release/DevOps role |
| Uptime promise? Data you cannot lose? | decides reliability/incident role, backup rigor |
| Does a human owner decide business rules? How available? | decides how many decisions you queue vs take |
| Existing process (CI, reviews, branches)? | adapt, do not replace |

## 2. Presets (start from the nearest, then adjust)
| Preset | Core roles | Add when |
|---|---|---|
| **Solo internal tool** (script, dashboard, one user group) | Boss + 1 builder + 1 reviewer | security reviewer once it touches secrets or people's data |
| **Internal business app** (staff portal, money/HR flows) | Boss, 1 manager per area, QA reviewer, security, data-quality | comms/support when users complain; CFO-lite for usage cost |
| **Public SaaS / customer product** | Boss, CPO, CTO, squads, QA, security, DevOps/SRE, support, comms/marketing, data/analytics | compliance, finance when billing exists |
| **Open-source library / API** | Boss, maintainers (core, docs), QA, security, release manager, community manager | marketing/devrel when adoption is the goal |
| **Mobile or desktop app** | Boss, squads per platform, QA with device matrix, release (store review), support, comms | marketing at launch |
| **Data / ML product** | Boss, data engineering, ML/eval, QA with eval sets, security, MLOps | ethics/compliance review for sensitive data |
| **Regulated or money-critical** | any of the above plus compliance officer, strict change control, owner approval on every release | audit trail officer |
Roles are hats first (see `org-structure.md`). A session is started only when the role has queue.

## 3. Role catalog and the trigger that justifies each
| Role | Start when |
|---|---|
| CTO (architecture, platform, dependencies, test speed) | more than ~3 squads, upgrade debt, slow tests, or shared code duplicated |
| COO / PMO (flow, backlog hygiene, cleanup, cadence) | more than ~15 open issues or 2+ concurrent builders |
| CPO / Product & Research | users exist and the backlog needs ranking; requirements unclear |
| CISO / Security | any secrets, auth, personal or financial data; always before first release |
| CDO / Data quality | imported or synced data, spreadsheets, reconciliation, analytics |
| CCO / Comms & support | non-technical users, release notes, feedback channel |
| CMO / Growth & marketing | **external or public product** with adoption goals; skip for internal tools |
| Developer relations / docs | library, API or SDK |
| SRE / Reliability | uptime promise, on-call, incidents more than monthly |
| Compliance / legal liaison | regulated data, contracts, licences |
| CFO-lite (cost and usage) | agent usage limits bite, hosting or build cost matters |
| Localisation, accessibility, design systems | users in many languages, public sector, big UI |
Never hire for the title. Hire when: the queue holds about a week of work for that role, or one incident exposed the gap.

## 4. Decision rights: how smart the Boss is allowed to be
| Level | Meaning | Examples |
|---|---|---|
| **Decide** | Boss acts, records it in the decision log | priority order, WIP limits, starting/ending sessions, role hats, process and tooling, cleanup, test routine, doc structure |
| **Decide and inform** | Boss acts, tells the owner in the next report | org changes, new departments, releases of verified low-risk work, dependency patch updates |
| **Ask first** | owner's explicit word | business rules, who sees what, money, dates, production data, publishing/sending to real people, costs above the agreed budget, anything irreversible |
The owner can move any item between levels; record it in `.agents/decisions.md`. If unsure which level, treat as one higher.

## 5. Self-adjusting loop (monthly, or after any incident)
1. Count per role: queue length, work done, idle weeks, defects it caused or caught.
2. Retire or merge roles with no queue for a month (back to a hat). Split a role whose queue exceeds two weeks.
3. Compare preset to reality: did the project change type (internal became public)? Re-profile.
4. Fix repeat failures: each incident becomes a rule in the docs and a lesson in the skill.
5. Write the changes into `ORG.md`, `PROFILE.md` and the decision log; tell the owner.

## 6. Decision log entry (one line each, `docs/team/DECISIONS.md`)
`date | decision | level (decide / inform / ask) | why | who can reverse`

## 7. Weekly owner report (same for every project)
Decisions needed (reason, cause, suggestion, approach) first; released; in review; blocked; numbers; risks; org changes made and why; next week; usage/cost.
