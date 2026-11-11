# Agent IT Company: organization and feature blueprint

Date: 11 November 2026  
Status: long-term design roadmap; the first local company kernel is implemented in 2.0.0, with advanced automation still deferred  
Scope: expand `agent-software-company` into a coordinated IT-company operating system for AI agents

## 1. The vision

You act as the human owner of an IT company. You can give it a business goal, a product idea, a client requirement, an existing codebase, or a production problem. Its leadership turns that request into an accountable plan. Department heads assign managers; managers organize specialist teams; those teams research, design, build, review, test, deliver, and improve the result.

The company should handle both **building its own products** and **delivering projects for clients**. It should support multiple projects, existing-product maintenance, research, releases, support, and operational improvement.

The intended experience is: “Here is the goal and the constraints. Organize the right people, coordinate the work, show me the evidence, and bring me the decisions that actually need me.”

This is a long-term blueprint, not a guarantee that every feature is implemented. Version 2.0.0 delivers the first local role/project/task/review/resource kernel and repaired coordination helpers; current operating references and CHANGELOG.md describe supported behavior. Broader automation below remains proposed.

This blueprint extends [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md). That document covers correctness, safety, and maintainability repairs. This one defines the larger company experience. Its broader role catalog supersedes the earlier suggestion to defer additional roles, while retaining the earlier reliability requirements and on-demand execution model.

## 2. What makes it work like a company

The organization needs more than role names and separate prompts. It needs:

- **Leadership:** a mission, business priorities, technical direction, budgets, and accountable decisions.
- **Departments:** stable ownership of expertise, standards, systems, and knowledge.
- **Delivery squads:** temporary teams from several departments that own a specific outcome.
- **Work management:** projects, dependencies, assigned owners, acceptance criteria, schedules, and change control.
- **Coordination:** reliable requests, handoffs, status, escalation, shared contracts, and conflict resolution.
- **Quality:** independent review, appropriate testing, security, release evidence, and user acceptance.
- **Operations:** support, incidents, reliability, maintenance, cost management, and recovery.
- **Learning:** documented decisions, reusable knowledge, retrospectives, and measurable improvements.

Every important work item has one directly responsible owner. Department reporting lines do not create several competing bosses for the same task.

## 3. Organization structure

The following is the full company template. A smaller company can combine executive responsibilities and activate fewer teams.

```text
Human Owner / Board
|
+-- CEO: mission, portfolio, business outcomes
    |
    +-- MD / COO: company execution and delivery operations
    |   +-- PMO / Delivery Director
    |   |   +-- Program Managers
    |   |       +-- Project / Delivery Managers
    |   |           +-- Cross-functional delivery squads
    |   +-- Customer Success & Support Manager
    |   +-- People / Agent Operations & Knowledge Manager
    |       +-- Role operations, technical writing, knowledge curation
    |
    +-- CTO: technology direction and engineering capability
    |   +-- Architecture / Principal Engineering
    |   +-- Engineering Director
    |   |   +-- Frontend Manager -> frontend, UI, accessibility specialists
    |   |   +-- Backend Manager -> API, service, integration specialists
    |   |   +-- Data Manager -> database, pipeline, analytics specialists
    |   |   +-- Mobile / Desktop Manager -> platform specialists
    |   +-- Platform & DevOps Manager -> CI/CD, SRE, release, developer tools
    |   +-- Research & Applied AI Manager -> researchers, prototypes, evaluations
    |
    +-- CPO / Product Director: user problems and product outcomes
    |   +-- Product Managers / Business Analysts
    |   +-- Design Manager -> UX research, UI design, content, design systems
    |
    +-- Quality Director: independent delivery assurance
    |   +-- Code Review Lead -> code quality and architecture reviewers
    |   +-- QA Manager -> functional, automation, integration, performance testers
    |
    +-- CISO / Security Lead: security and risk assurance
    |   +-- Application Security / Dependency / Privacy specialists
    |
    +-- CFO: resource planning, cost visibility, budget controls
    |   +-- FinOps / Cost Analyst
    |   +-- Commercial / Project Estimation Analyst
    |
    +-- Growth / Commercial Lead, when needed
        +-- Market Research, Sales Engineering, Marketing, Launch Content
```

Code review and QA have an independent reporting path so delivery pressure does not let builders certify their own work. Security can escalate directly to the owner. They still collaborate with engineering on implementation and remediation. Documentation and knowledge report through Agent Operations & Knowledge; Growth commissions launch material from that team rather than owning a second documentation function.

### Executive responsibilities and boundaries

| Role | Owns | Main outputs | Decision boundary |
|---|---|---|---|
| Human owner / board | Company purpose, business rules, authorization, risk tolerance, external commitments | Goals, constraints, authorized action scope, major decisions | Retains authority over real spending, contracts, access, and actions outside delegated scope. |
| CEO | Strategy, priorities across projects, value versus effort, executive alignment | Company charter, portfolio priorities, outcome review, owner briefing | Prioritizes within the owner's mandate; does not invent new commitments. |
| MD: Managing Director | Delivery across the company, resolving department conflicts, execution against the plan | Operating plan, delivery forecast, escalation decisions | Owns delivery coordination; does not override technical or assurance evidence. |
| COO | Repeatable processes, resource flow, service operations, capacity | Capacity plan, delivery health, process improvements | Combined with MD by default; split when company scope justifies distinct work. |
| CTO | Architecture, technical strategy, engineering standards, technical trade-offs | Technical roadmap, architecture decisions, engineering risk assessment | Chooses implementation direction within product requirements and authorized constraints. |
| CPO | Customer problems, product definition, roadmap, acceptance and user value | Product brief, requirements, acceptance criteria, prioritized roadmap | Resolves product trade-offs; escalates new business rules to the owner when needed. |
| CFO | Budget allocation proposals, forecasts, measured cost, resource trade-offs | Budget plan, estimate/actual report, cost alerts, commercial estimates | Can enforce configured resource limits; cannot approve its own overspend, purchase, or payment. |
| Quality Director | Review independence, test strategy, release evidence | Quality plan, defect assessment, evidence-based readiness verdict | Can hold readiness when required evidence fails; cannot approve scope changes or deploy by title. |
| CISO / Security Lead | Threat analysis, security findings, privacy and exposure risks | Threat model, security review, remediation priorities | Can hold readiness for a documented security violation and escalate unresolved risk. |

These titles describe responsibilities. Actual tool permissions and standing authorization are separate. A role cannot gain production access, spending power, or publication rights by calling itself an executive.

## 4. Departments, managers, and specialist teams

This is the initial role catalog. Specialist roles are added when they have concrete work and required tools; creating a department does not require starting a separate live session for every title.

| Department | Manager / lead | Specialist teams and roles | Deliverables |
|---|---|---|---|
| Product & Business Analysis | Product lead | Product manager, business analyst, requirements analyst, domain analyst | Problem statement, user stories, acceptance criteria, process maps, roadmap. |
| Research & Innovation | Research manager | Technical researcher, market researcher, feasibility analyst, benchmark engineer, prototyper | Sourced findings, alternatives, experiments, recommendation, confidence and open questions. |
| UX / UI & Design | Design manager | UX researcher, interaction designer, UI designer, accessibility specialist, content designer, design-system maintainer | User flows, wireframes, specifications, component guidance, usability findings. |
| Architecture | Principal architect | System architect, API architect, data architect, solution architect | System boundaries, interface contracts, architecture decisions, migration approaches. |
| Frontend Engineering | Frontend manager | Web engineer, component specialist, state/data integration engineer, accessibility engineer | Screens, components, client integrations, UI tests, performance improvements. |
| Backend Engineering | Backend manager | API engineer, service engineer, integrations engineer, authorization specialist | Services, APIs, business logic, integrations, backend tests. |
| Data & Database | Data manager | Database engineer, migration author, data engineer, data-quality analyst, analytics engineer | Schemas, queries, migration/rollback plans, pipelines, data-quality reports. |
| Mobile / Desktop | Platform manager | Mobile engineer, desktop engineer, platform integration specialist | Platform-specific applications, packaging plans, compatibility evidence. |
| AI / ML, when relevant | Applied AI lead | AI engineer, evaluation engineer, retrieval specialist, ML/data scientist | Model-assisted features, evaluation sets, measured quality, data and cost constraints. |
| Platform / DevOps / SRE | Platform manager | CI/CD engineer, cloud engineer, SRE, release engineer, developer-experience engineer | Build pipelines, environment definitions, deployment plans, runbooks, reliability evidence. |
| Code Review | Review lead | Correctness reviewer, maintainability reviewer, architecture reviewer | Findings against a named revision, requested changes, verified re-review. |
| QA & Testing | QA manager | Test strategist, unit/integration automation engineer, E2E tester, exploratory tester, performance/compatibility tester | Test plan, reproducible defects, test evidence, regression assessment. |
| Security & Privacy | Security lead | AppSec reviewer, threat analyst, dependency/supply-chain analyst, privacy reviewer | Confirmed findings, threat model, dependency checks, access-control assessment. |
| Project / Program Delivery | PMO lead | Program manager, project manager, delivery coordinator, facilitator | Project plan, dependency map, delivery forecast, blocker resolution, change log. |
| Customer Success & Support | Support manager | Support triage analyst, technical support engineer, customer-feedback analyst | Reproduction steps, support knowledge, incident routing, feedback linked to backlog. |
| Finance / FinOps | Finance lead | Token/tool-cost analyst, cloud-cost analyst, estimator, commercial analyst | Budget forecasts, cost variance, project estimates, billing drafts when requested. |
| Growth / Sales / Marketing | Commercial lead | Market analyst, sales engineer, proposal writer, positioning/content specialist | Opportunity briefs, proposals, demos, launch drafts, adoption experiments. |
| Documentation & Knowledge | Knowledge lead | Technical writer, API documentation specialist, knowledge curator | User guides, technical docs, onboarding notes, searchable decisions and runbooks. |
| People / Agent Operations | Agent operations manager | Role curator, onboarding coordinator, capability evaluator, capacity planner | Role profiles, capability inventory, assignment recommendations, reusable training examples. |
| Legal / Compliance support, optional | Compliance coordinator | License reviewer, policy analyst, compliance-evidence curator | License inventory, policy gaps, evidence packets, questions needing qualified human review. |

People operations manages agent roles and capabilities; it does not simulate real employment actions. Finance and legal roles produce analysis and reviewable artifacts. Actual transactions and binding commitments follow the owner's authorization and appropriate human review.

## 5. How managers and subteams work

Each department has a manager with a clear ownership area. For example, the Backend Manager might form an API subteam, a billing-services subteam, and an integrations subteam. Each subteam has a lead and scoped specialists.

For a project such as “build the customer portal,” the delivery manager assembles a squad with product, design, frontend, backend, QA, and platform representatives. Their functional managers supply expertise and standards. The delivery manager owns the dependency plan and outcome. The CTO resolves technical conflicts; the CPO resolves requirement conflicts; the MD resolves capacity conflicts.

Every role profile should define:

| Field | Purpose |
|---|---|
| Mission | What outcome the role exists to produce. |
| Reporting manager | Who handles capability, capacity, and escalation. |
| Project assignment | Which delivery owner sets this assignment's scope and priority. |
| Inputs / outputs | Required information and concrete artifacts to deliver. |
| Allowed actions | Tool capability and authorization references; no authority inferred from a title. |
| Ownership | Repositories, paths, services, contracts, and shared files it may work on. |
| Completion criteria | How its work is accepted and who reviews it. |
| Resource limit | Concurrency, task/time/token/tool limits, and what to do at the limit. |
| Handoff / escalation | Who receives unfinished work or unresolved decisions. |

### Company sizes

| Preset | Organization | Execution approach |
|---|---|---|
| Founder | Combined CEO/MD/product coordinator, engineer, independent reviewer when available | Minimal process for small work; label self-checks honestly if an independent session is unavailable. |
| Startup | Separate product, engineering, QA, and platform responsibilities; finance/security on demand | Small active squad, explicit cross-team contracts and budget. |
| Full company | Executive responsibilities, department managers, several projects and squads | Capacity-aware scheduling, portfolio reporting, independent assurance. |
| Partner companies | Multiple independent orgs using the shared protocol | Existing interop plus scoped identity, ownership, delivery contracts, and cross-org review. |

Presets describe responsibility coverage, not a promised number of simultaneous agents. Available runtime slots, permissions, cost, and project needs determine actual concurrency. Multiple roles can be performed sequentially; an independent review must never be fabricated by renaming the builder.

## 6. Features to add

P0 means foundation needed before depending on company automation. P1 means core company behavior. P2 means an extension after the core works. These are roadmap priorities, not incident severities.

| ID | Feature | What it does | Priority |
|---|---|---|---|
| F01 | Company charter and setup | Records mission, products/services, owner mandate, environments, tools, repo conventions, and company preset; previews additions before writing. | P0 |
| F02 | Organization and role registry | Defines executives, departments, managers, subteams, reporting lines, and capability/permission mappings. | P0 |
| F03 | Project and work registry | Tracks initiatives, epics, tasks, incidents, experiments, owners, dependencies, acceptance criteria, evidence, and state. | P0 |
| F04 | Reliable coordination | Repairs inbox/claim/parser/discovery issues in the earlier plan; adds internal requests, acknowledgment, and deduplication. | P0 |
| F05 | Task dispatcher and capacity planner | Chooses qualified roles, assigns scoped work, queues tasks when slots are full, and avoids cyclic delegation or duplicate ownership. | P0 |
| F06 | Authority and decision registry | Separates recommendations, verdicts, and authorized actions; reuses standing authorization within its scope. | P0 |
| F07 | Budget ledger | Tracks estimated and observed token/tool/compute/time use, budget reservations, limits, and forecast variance. Unknown costs remain unknown. | P0 |
| F08 | Durable checkpoint and resume | Saves branch/revision, artifacts, tests, budget, next action, and pending decisions so work survives interruption. | P0 |
| F09 | Portfolio and roadmap planning | Lets leadership compare opportunities, rank projects, allocate capacity, and review outcomes. | P1 |
| F10 | Research and feasibility pipeline | Turns questions into sourced research, experiments, comparisons, and a proceed/change/stop recommendation. | P1 |
| F11 | Product discovery and requirements | Converts business goals into scoped briefs, user journeys, acceptance criteria, and prioritized work. | P1 |
| F12 | Design and architecture contracts | Produces design specs, API/data contracts, architecture decisions, and compatibility rules before dependent implementation. | P1 |
| F13 | Engineering delivery squads | Coordinates frontend/backend/data/platform work against shared contracts and acceptance criteria. | P1 |
| F14 | Independent code review service | Routes changes to a different reviewer, records evidence against the exact revision, and handles re-review. | P1 |
| F15 | QA and user acceptance service | Selects relevant automated/manual checks, reproduces defects, tests integration, and records acceptance evidence. | P1 |
| F16 | Security and privacy assurance | Adds risk-triggered threat modeling, access-control checks, dependency review, and remediation tracking. | P1 |
| F17 | Release and change management | Builds release candidates, integration evidence, deployment/rollback plans, and authorized release actions. | P1 |
| F18 | Support and incident workflow | Classifies incoming defects/incidents, assigns an incident lead, captures recovery evidence, and feeds prevention work into backlog. | P1 |
| F19 | Knowledge and lessons system | Stores decisions, contracts, runbooks, project summaries, and reusable lessons with owners and freshness. | P1 |
| F20 | Executive reporting | Generates owner briefs with outcomes, risks, budget, blockers, evidence, and the next decision. | P1 |
| F21 | Multi-project staffing | Allocates shared specialists across projects and prevents priority starvation, context leakage, and conflicting file ownership. | P2 |
| F22 | Client-project workflow | Creates a scope brief, estimate, milestones, change requests, demo plan, acceptance pack, and handover. | P2 |
| F23 | Commercial and finance support | Produces proposal, pricing, cost and margin scenarios, and invoice drafts using supplied or connected data. | P2 |
| F24 | Growth and launch workflow | Prepares positioning, documentation, demo and launch assets, experiments, and outcome measurements. | P2 |
| F25 | Agent capability improvement | Evaluates role profiles, identifies recurring mistakes, proposes scoped improvements, and tests them before adoption. | P2 |
| F26 | Optional company dashboard | Displays projects, squads, work queues, risks, budgets, dependencies, decisions, and evidence from existing state. | P2 |
| F27 | Optional scheduled operations | Runs explicitly configured recurring triage, maintenance, or health checks through an available scheduler. | P2 |
| F28 | Partner-company delivery | Extends existing cross-org collaboration with project contracts, compatible protocols, scoped review, and shared milestones. | P2 |

F26 and F27 are separate later deliverables. A Markdown skill alone does not provide a persistent server, live dashboard, background employees, telemetry, or a scheduler.

## 7. Work and coordination model

### Work hierarchy

```text
Company objective
  -> Portfolio initiative
     -> Product or client project
        -> Epic / milestone
           -> Work item with one responsible owner
              -> Scoped specialist assignment
                 -> Artifact + evidence + handoff
```

Use only the levels needed. A bug fix can be a single work item; it need not become an initiative with executive meetings.

### Work item contract

A work item records its ID, goal, request source, project, responsible owner, contributors, reviewer, dependencies, affected contracts/paths, acceptance criteria, risk, budget, delivery state, blocker/pause flags, artifacts, checks, and next action. Optional fields appear only when useful. An acceptance criterion should describe observable behavior, not “the agent says done.”

Suggested delivery states:

```text
intake -> scoped -> ready -> assigned -> in-progress -> review -> verified
       -> integrated -> released -> outcome-checked -> closed
```

`blocked` and `paused` are flags that preserve the underlying delivery state, with a reason, resolution owner, and resume condition. A checkpoint must show whether work was building, reviewing, or integrating when interrupted. `cancelled` is a terminal outcome. Pause and cancellation reflect owner instructions or configured controls; budget exhaustion stops new dispatch under the agreed policy. Research and documentation tasks can close after accepted artifacts; local-only work need not be released. A failed review returns work to its owner. A pushed code change invalidates evidence that no longer applies.

### Coordination rules

1. A manager delegates an outcome, scope, evidence requirement, and resource limit; it does not send an unexplained “do this.”
2. Assignment and handoff use stable IDs and acknowledgments. A sent message is not proof that the recipient started.
3. Frontend and backend agree on an API contract. Data and backend agree on schema/migration assumptions. Platform and QA agree on the test environment. Contract changes notify affected owners and revise dependent work.
4. Shared-file edits and integration merges are serialized or explicitly split. Claims remain advisory; the system rechecks ownership and current revision before conflicting work.
5. Blockers are classified: requirement, technical, dependency, budget, access, or tooling. Send each to the person who can resolve it, with a recommendation.
6. Disputes go first to the relevant manager; technical direction goes to CTO, product scope to CPO, resource conflicts to MD/CFO. Owner decisions are reserved for matters outside their delegated mandate.
7. High-risk unresolved findings prevent readiness. Executives cannot turn a failed check into a PASS; any authorized risk exception is recorded separately with its scope and evidence.
8. Internal coordination uses the host's available delegation tools and durable records. Email, chat apps, GitHub comments, or client messages are sent only within explicit or already-established authorization.
9. Planning stops recursive delegation at a configured depth. Each child assignment consumes the parent project's budget and returns its evidence to an accountable owner.
10. Status and meetings produce decisions or artifacts. Prefer one concise asynchronous update to repeated summaries up the hierarchy.

## 8. Example: delivering a customer portal

Owner request: “Build a customer portal with sign-in, account details, downloadable invoices, and support requests.”

| Stage | Coordinating role | Team contribution | Required result |
|---|---|---|---|
| Intake | CEO / MD | Identify product goal, scope, available repo, constraints, and existing authorization | Project brief and responsible delivery owner. |
| Discovery | CPO | Business analyst and research team inspect current flows and requirements | User journeys, acceptance criteria, unanswered business decisions. |
| Feasibility | CTO | Architecture, backend, security, platform evaluate implementation choices | Recommended design and risks; experiments for uncertain assumptions. |
| Planning | Delivery manager + CFO | Department managers estimate capacity; finance records resource estimate and limits | Milestones, dependency graph, staffed assignments, budget. |
| Contracts | Design and architecture leads | UX/UI, frontend, backend, data agree on screens, API behavior, identity, and ownership | Versioned design/API/data contracts and test strategy. |
| Build | Engineering managers | Frontend and backend implement scoped work; data/platform prepare required test support | Working increments and reproducible checks. |
| Assurance | Review, QA, security leads | Independent review, integration testing, invoice access isolation, invalid-input and failure checks | Evidence tied to tested revisions; confirmed defects returned to owners. |
| Delivery | Release engineer + delivery manager | Prepare candidate, docs, release and rollback plan | Reviewable release pack; execute only authorized actions. |
| Adoption | Support + product | Test changed flows, prepare support guide, collect permitted feedback | Acceptance evidence and prioritized follow-up. |
| Learning | MD | Compare outcomes, defects, delays, and actual/estimated resources | A short retrospective and targeted process improvements. |

The CEO receives summaries and exceptions rather than approving every component. The owner sees completed work, meaningful choices, and the evidence needed to assess them.

### Other company workflows

- **Research request:** research manager assigns questions and evidence standards; specialists investigate; technical/product leads compare options; accepted findings become a proposal or an explicitly closed experiment.
- **Production incident:** support triages; MD appoints one incident lead; SRE and relevant engineers investigate within allowed access; security joins if warranted; recovery actions follow authorization; QA verifies recovery; the company records cause and prevention work.
- **Client scope change:** delivery manager records the request and impact; product/architecture revise scope; CFO estimates cost/capacity effects; an authorized human accepts contractual or commercial changes before they are promised externally.
- **Maintenance:** dependency or reliability findings become ranked work; engineering, security, QA, and platform handle only the relevant parts of the delivery flow.

Research must identify actual sources and experiments. Proposed interviews, user demand, market data, and customer feedback must never be presented as observations unless they were actually obtained.

## 9. Budgets, capacity, and useful autonomy

The CFO and MD should make resource use visible and bounded, rather than merely report it afterward.

- Configure company/project/task limits for active workers, delegation depth, tool calls, elapsed effort, and tokens or currency where measurable.
- Reserve a reasonable allocation before dispatch, reconcile known usage afterward, and release unused reservations. Mark estimates, measured values, and unavailable telemetry separately.
- Hold capacity for review and integration so coding does not create a growing queue of unreviewed work.
- Use dependency and ownership constraints to select parallel work. Queue new assignments when slots are full; do not pretend unavailable workers are active.
- Reuse a role or checkpoint where appropriate; keep sensitive project context separate. Context handoffs should include relevant facts, not the full company history.
- At a configured soft limit, reduce scope or propose an adjustment. At a hard limit, checkpoint and stop new dispatch; preserve enough budget for handoff where possible. In-flight work is cancelled or allowed to finish only according to host support and the agreed policy.
- Use estimates as forecasts, not promises. A role change does not reset a project's budget or retry count.
- Continue routine work within the owner's mandate. Batch unresolved business choices with a recommendation rather than asking the owner to approve every internal step.

## 10. Company memory and reporting

Different records serve different purposes:

| Record | Contents | Accountable owner |
|---|---|---|
| Company charter | Mission, priorities, authorized scope, operating model | CEO / human owner. |
| Organization registry | Roles, departments, reporting, capability and authority references | Agent operations / MD. |
| Portfolio and project records | Objectives, work, dependencies, responsible owners, status | CEO / delivery managers. |
| Product and technical decisions | Requirement decisions, accepted trade-offs, API/data contracts, architecture decisions | Product / architecture owners. |
| Evidence records | Reviews, commands, results, artifacts, revisions, coverage and limitations | Reviewer / QA / relevant specialist. |
| Resource ledger | Estimates, reservations, measured usage, variance, unavailable data | CFO / FinOps. |
| Runbooks and knowledge | Setup, troubleshooting, supported procedures, lessons and freshness | Department owners / knowledge lead. |
| Incident and support history | Reproduction, impact, recovery, follow-ups, linked defects | Support / incident lead. |

GitHub remains the shared record for distributed teams using it. Local-only execution uses validated local records until external synchronization is authorized and available. Each record type has one canonical location; issue comments, Markdown summaries, and dashboards link to it or are generated views. They must not become competing writable versions of the truth.

Operational scratch state and sensitive information stay outside committed documentation. Use atomic writes locally, stable IDs, versioned schemas, and explicit concurrency/reconciliation rules. Do not assume a shared JSON file provides reliable multi-writer locking.

The default owner report answers: what outcome changed, what evidence supports it, what is blocked or risky, how the budget is doing, what decision needs the owner, and what happens next. A dashboard, if later added, reads these same records.

## 11. Proposed implementation structure

Keep the skill entrypoint short and load the relevant department/workflow references on demand. The following is a target layout, to be created incrementally as each feature is implemented, not as empty scaffolding now.

```text
agent-software-company/
  SKILL.md                       company entrypoint and mode routing
  references/
    company-operating-model.md   hierarchy, delivery ownership, escalation
    role-catalog.md              role definitions and assignment briefs
    company-workflows.md         product, research, client, incident flows
    resource-management.md       budget and capacity semantics
    ...existing references...    reconciled safety, interop, review, release
  templates/
    company.json                 charter/configuration starter
    organization.json            departments, roles, reporting, capabilities
    project.json                 minimum useful work/project contract
    ...existing templates...     compatible roster, trust, messages, areas
  scripts/
    company.py                   proposed thin command entrypoint
    ...existing helpers...       repaired and reused rather than duplicated
    lib/                         shared protocol, validation, state, resources
  tests/
    fixtures/                    isolated repositories, messages, state, failures
    ...behavior-focused tests...
```

Preserve the distinction between an installed skill's templates and a company's generated project records. Keep existing `.agents/` protocol consumers compatible where feasible; a proposed company configuration must not silently replace roster/trust files with a second authority model.

### Candidate user commands

These are proposed capabilities and example interfaces, not commands available today:

```text
company init --preset startup       preview a charter and organization
company org                         show roles, managers, teams, capabilities
company project plan <brief>         create a scoped delivery plan
company task assign <id>             dispatch or queue a scoped assignment
company status                      show projects, owners, blockers, evidence
company budget                      show limits, estimates, and known usage
company review <work-id>             request an independent review
company incident open <summary>     prepare incident triage and ownership
company resume <work-id>             inspect a checkpoint and resume safely
company report                      generate an owner briefing
```

The skill should also understand ordinary requests such as “Ask research to compare these options,” “Have frontend and backend build this together,” and “Show me what each department is doing.” Natural-language requests and commands should operate on the same records and authorization model.

## 12. Implementation roadmap

| Phase | Scope | Features | Completion gate |
|---|---|---|---|
| 0. Repair the foundation | Reconcile authority, repair coordination and updater weaknesses, add regression fixtures from the earlier plan | Prerequisite for F04/F06/F08 | No silent incomplete-read success, unsafe claim transitions, or unreviewed update replacement. |
| 1. Model the company | Charter, role profiles, department hierarchy, presets, project/work records, policy references | F01–F03, F06 | A fixture company can answer who owns each decision, work item, and department without contradictory rules. |
| 2. Coordinate real assignments | Dispatcher, dependency-aware queue, capacity limits, internal handoffs, budget ledger, checkpoints | F04–F08 | A small squad finishes a fixture task, survives interruption, and respects resource limits. |
| 3. Deliver as departments | Research, product/design, engineering squads, review, QA, security, integration and release preparation | F10–F17 | A frontend/backend feature passes independent review and integrated acceptance checks. |
| 4. Operate the company | Portfolio priorities, reporting, support, incidents, knowledge and improvement loop | F09, F18–F20 | Leadership can explain delivery health and budget; support can route a reproduced issue into verified remediation. |
| 5. Expand business workflows | Multi-project staffing, client delivery, commercial analysis, launch work, role evaluations, partner workflows | F21–F25, F28 | Competing projects and a client scope change are handled with clear ownership and no unauthorized commitments. |
| 6. Add optional interfaces | Dashboard and authorized scheduled operations where runtime support exists | F26–F27 | Views match canonical state; recurring work has explicit ownership, limits, and a stop mechanism. |

**First usable company release:** combined CEO/MD coordinator, product/BA role, CTO/engineering manager, frontend and backend specialists, independent reviewer, QA, and on-demand platform/security/CFO analysis. It must support one complete project and a clear budget/handoff trail before adding a larger roster.

**Later expansion:** split combined roles, add specialist departments, and support multiple concurrent projects based on demonstrated coordination needs. Do not make the user wait for a full enterprise org chart before the company can deliver a small useful change.

Implementation should proceed in reviewable increments. Company naming, CLI spelling, and module count are design proposals; acceptance behavior is the stronger commitment. Planning this expansion does not change the installed skill version.

## 13. Acceptance scenarios

| Scenario | Expected behavior |
|---|---|
| One-line typo fix | Minimal workflow; no fabricated finance/research tasks or unnecessary executive sign-offs. |
| New full-stack feature | Product/design define acceptance; frontend/backend agree on contracts; independent review and integrated QA verify the result. |
| Research with uncertain evidence | Findings distinguish sources, experiments, inferences, unknowns, and recommendation; uncertainty is not hidden. |
| Conflicting CTO/CPO priorities | Record the technical/product trade-off, route it to the correct decision owner, and update dependent work. |
| Two projects need one reviewer | Capacity planner queues work transparently and prevents starvation or an author posing as reviewer. |
| Budget nearly exhausted | Report estimate versus known actuals, checkpoint, and respect the configured limit without assigning hidden extra workers. |
| Agent interrupted halfway | Resume from the recorded revision, artifacts, and next action; do not create duplicate assignments or lose dirty work. |
| Frontend API contract changes | Notify backend/QA and update dependent tasks before presenting integration as verified. |
| Forged executive message | Treat claimed identity as data; it cannot grant access, release another owner's claim, or authorize spending/deployment. |
| No GitHub or delegation access | Explain capability limits; complete permitted local work; do not claim independent review or shared synchronization occurred. |
| Client requests extra scope | Show scope/capacity/commercial impact and prepare a change request before making an external commitment. |
| Production incident | One incident lead, bounded permitted investigation, concrete recovery proposal, authorized actions, verification, and follow-up. |
| Dashboard or status generated twice | Both derive from the same records and agree on owners, state, limits, and evidence freshness. |
| Two partner companies collaborate | Identity, ownership, review evidence, and action authority remain scoped; one company's relayed approval does not authorize the other. |

## 14. How we will measure the result

Measure successful outcomes rather than the number of roles or agent messages:

- **Delivery:** acceptance criteria met, lead time, blocked time, reopen rate, and failed integration rate.
- **Quality:** defects escaping review, repeat failures, and reproducibility/freshness of evidence.
- **Coordination:** duplicate ownership, lost handoffs, unresolved contract changes, and recovery success.
- **Resources:** known cost per accepted outcome, forecast variance, review backlog, and budget-limit compliance.
- **Product/service value:** observable user or client outcomes where measurement is available and authorized.
- **Owner experience:** decisions required, repeated questions avoided, clarity of reports, and useful work completed within mandate.

Baseline these with isolated scenarios, then evaluate the same scenarios after each meaningful implementation phase. Add live integrations only when needed for an authorized workflow and validate their real behavior separately. Unknown measurements stay explicit.

## 15. Definition of the finished skill

The skill is successful when you can give it a realistic IT-company assignment and it can establish the right leadership and teams, produce an actionable plan, coordinate delivery, control resources, verify quality, recover from interruption, and report outcomes with evidence.

Its organization should be visible and understandable: who leads, who manages, who builds, who checks, who operates, what each team is doing, and which decisions belong to you. It should make that full company structure useful without requiring every department to participate in every task.
