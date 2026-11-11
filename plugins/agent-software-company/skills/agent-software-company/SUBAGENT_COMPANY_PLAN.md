# Plan: an IT company powered by subagents in one main chat

Date: 11 November 2026  
Status: approved design; initial native edition 1.0.0 implemented and validated. This document retains the design roadmap; current executable guidance is in the [edition skill](https://github.com/DhruvHarani1/agent-software-company-subagents).
Edition name: `agent-software-company-subagents`

Design requirement added during discussion: **the CEO owns organization design and agent management. Users provide product goals and constraints, not staffing commands, role lists or agent counts.**

## 1. What you want

You open **one main chat** and give your company a goal. The main assistant first understands the product, then decides what organization and specialist capacity that goal needs. It coordinates a company of real subagents: executives, managers, department teams and specialists. They delegate work, communicate internally, review each other and return results to the main assistant. You discuss progress and business decisions in that original chat.

You do not need to open separate CEO, CTO, frontend, backend or tester chats. The skill must not create or fork user-owned chats to represent employees. Subagents may have their own internal contexts, depending on the host, but those contexts are managed as delegated work rather than conversations you must operate.

Example request:

> “Build a customer portal where customers can see their invoices and request support. Keep me updated here.”

Expected result: the CEO discovers the requirements, decides whether research/design/frontend/backend/security/QA help is needed, chooses the team size and reporting structure, and uses actual native subagent tools. You do not have to ask for those roles or specify how many agents to launch. Giving itself several role names in one response does not count as running a team.

Role selection and agent-count controls may exist for optional overrides, but they must never be required to use the skill. Useful defaults come from product evidence, available runtime capacity and the existing mandate.

This document describes the **execution model** agreed during discussion. The existing [company blueprint](IT_COMPANY_BLUEPRINT.md) remains the broader organization and feature catalog. The first native edition implements CEO instructions, the host-tool bridge and durable lifecycle/evidence guards; the Python journal is not a standalone worker launcher. See the current edition and changelog for delivered scope and limitations.

## 2. Recommended version approach

Create a separate, clearly named subagent edition while preserving the existing general company skill.

| Edition | Purpose |
|---|---|
| Existing `agent-software-company` | General company roles, local ledger and optional cross-team/GitHub coordination. |
| Proposed `agent-software-company-subagents` | One main chat, native subagents, internal delegation, centralized reporting and runtime-aware scheduling. |

The new edition should reuse the tested organization, task, budget and evidence concepts. It should ship as a self-contained skill, with its own short entrypoint and relevant references. If implementation shares source helpers, packaging must include them; installation must not depend on an undocumented neighboring skill folder.

The name and entrypoint should make the distinction clear enough that users do not accidentally activate both editions. We should settle this packaging choice before creating another installed skill.

## 3. Organization: executives, managers and subteams

The existing catalog of 80 roles across 18 departments is a starting library of capabilities. The CEO selects, combines, specializes and evolves roles based on the product and current workload. It is not a fixed organization chart or a ceiling on useful specialties.

```text
You: human owner
|
Main chat: company coordinator / CEO
|
+-- MD / delivery subagent
|   +-- Project or department manager subagents
|       +-- Frontend, backend, data, platform specialist subagents
|
+-- CTO / architecture subagent
|   +-- Research and technical specialist subagents when useful
|
+-- Product / design subagents
+-- CFO / resource-planning subagent when needed
+-- Independent code-review and QA subagents
+-- Security subagent when the work needs it
```

This is an example reporting structure, not a requirement to run every layer at once. The CEO chooses the structure. A large initiative can use several management layers; a small fix can use the main coordinator, a builder subagent and a separate reviewer.

| Role | Responsibility in this edition |
|---|---|
| Main coordinator / CEO | Understand the product, design/evolve the organization, choose roles and worker counts, own dispatch and the user conversation, and remain accountable for the overall result. |
| MD / COO | Plan delivery, dependencies, milestones and manager handoffs; surface conflicts with recommendations. |
| CTO | Define technical direction, architecture and contracts; resolve engineering trade-offs. |
| CPO / product lead | Clarify user behavior, acceptance criteria, design and product priorities. |
| CFO / FinOps | Estimate resources, compare known usage and reservations, and recommend budget trade-offs. |
| Department manager | Split an agreed outcome into scoped work, manage interfaces and integrate specialist results. |
| Specialist | Complete one concrete assignment with artifacts, checks, limitations and a handoff. |
| Reviewer / QA / security | Evaluate relevant evidence independently and return findings tied to the tested revision. |

The coordinator consolidates questions for you. Subagents return their findings and unresolved decisions through the parent, rather than opening their own user conversations.

### 3.1 Product understanding before staffing

The CEO maintains a compact, evidence-based product model rather than selecting teams from a generic checklist. It reads the request, repository instructions, relevant code/docs, existing tests and available backlog. If an uncertainty actually needs investigation, it can assign a bounded discovery task itself.

The product model should cover:

- What the product does, who uses it, and the outcome requested now.
- Current stage: idea, prototype, active development, maintenance or incident.
- Architecture, stack, interfaces, dependencies and important ownership boundaries.
- Existing capabilities and real gaps; avoid creating a team to rebuild something already present.
- Relevant risk, unresolved assumptions, current delivery bottlenecks and available validation.
- Runtime capabilities, concurrency limits and known resource constraints.

Separate observed facts from assumptions. Ask the user only about missing information that materially changes the business outcome or exceeds the current mandate. The user should not have to resolve internal staffing decisions such as “Do we need a backend agent?”

### 3.2 CEO organization decision loop

```text
Understand product and requested outcome
  -> identify work, dependencies, uncertainty and risks
  -> identify the capabilities required
  -> compare with current roles, active workers and available capacity
  -> choose the smallest effective organization
  -> launch/delegate within the existing allocation
  -> inspect actual progress, quality, queues and blockers
  -> retain, specialize, duplicate, combine, reassign or retire workers
  -> verify whether the change improved delivery
```

This loop runs at meaningful planning, handoff, review and blocker events. It does not require continuous polling or a simulated management meeting for every action. The CEO can consult CTO, MD, CFO or quality specialists where their analysis would improve the decision; consulting every executive is not mandatory.

### 3.3 Decisions the CEO should make without staffing instructions

| Decision | Evidence the CEO uses | Expected action |
|---|---|---|
| Activate an existing role | A scoped deliverable needs that capability | Select a suitable role and assign a real worker. |
| Create a new specialty | Existing role profiles do not adequately cover a demonstrated product need | Draft a scoped role with inputs, outputs, ownership, limits and review criteria; use it within existing permissions. |
| Combine responsibilities | Compatible work is small enough that separate management/worker sessions add little value | Use one worker for those responsibilities while preserving assurance independence. |
| Split a role or team | One broad assignment has distinct outputs, contexts or ownership boundaries | Separate the work and define interfaces/handoffs. |
| Duplicate a worker role | Several independent ready assignments would benefit from parallel specialist capacity | Launch distinct workers with separate task/path ownership and real identities. |
| Add a manager | Coordination, interface changes or span of work is a real bottleneck | Delegate a concrete coordination outcome, with a limited management allocation. |
| Reassign or replace | Skills, availability or repeated observed results do not fit the assignment | Preserve evidence and authorship, reconcile current work, then hand off or retry. |
| Retire or park capacity | Work is complete, blocked, no longer needed or consuming resources without a useful outcome | Stop new assignments, reconcile live work and release confirmed resources. |
| Reorganize reporting or squads | Product boundaries or delivery dependencies changed | Update logical ownership and affected briefs while preserving task/history references. |

The CEO reports meaningful organization decisions and their reasons as part of progress. It should not ask for approval of routine internal staffing changes already within the mandate. Product/business scope changes, additional real spending or newly consequential external actions still follow the existing authority policy; creating a role cannot expand that authority.

A new role supplies a focused assignment and relevant context; it does not manufacture missing tools or expertise. Evaluate its actual artifacts and checks. Keep the logical organization separate from the live workforce: several roles can remain dormant while a small number of native workers execute the current plan.

The CEO may identify product architecture or process improvements, too. It should connect them to the requested outcome and evidence, use CTO/manager analysis where helpful, and distinguish an organization change from an unrelated product rewrite.

### 3.4 Duplicating agents must add real capacity

“Duplicate the frontend agent” means create another real worker with a separate assignment, not clone a name or give two workers the same open-ended task.

Before scaling, the CEO checks that:

1. Independent, ready work exists and its interfaces are sufficiently clear.
2. Ownership is split by concrete output/path or another enforceable work boundary.
3. Slots and resources are available without starving review or integration.
4. More workers address the bottleneck; they will not simply wait on the same unresolved decision.
5. The expected coordination cost is justified by a plausible delivery benefit.

For example, two frontend workers can own independent account and support screens once shared API/design contracts are agreed. If backend work is waiting for a business-rule decision, another backend worker may not help. The CEO should resolve or route that blocker and assign independent work instead.

Each duplicate has its own native ID, task, context and contribution history. Copying the useful role brief does not create independent review or copy approvals. Retire added capacity after the workload falls; do not preserve a large workforce just because it once existed.

### 3.5 Self-management without organizational churn

Organization changes should have a short recorded reason, supporting observations, expected benefit, affected work and a point to reassess the outcome. Use observed delays, conflicting ownership, rework, review backlog and resource usage; do not infer agent quality from confidence or polished status reports alone.

Prefer a proportionate adjustment before a company-wide reorganization. Keep one accountable owner for each outcome. Repeated role reshuffling without new evidence should stop in favor of completing the current plan or escalating the real blocker.

If review work becomes the bottleneck, shift available capacity toward independent evaluation before starting more implementation. Once the requested outcomes are accepted, finish or retire the remaining assignments through supported lifecycle operations. Do not generate unrelated tasks just to keep the company or its managers busy.

Version changed role profiles and preserve the briefs used for existing attempts. Communicate material assignment changes and obtain an actual worker acknowledgment before treating the new scope as active. A reorganization must not erase costs, failed attempts, contributor history, pending reviews or active ownership.

## 4. Native subagent execution

Use the host's real delegation tools for launching, messaging, inspecting, waiting for and interrupting subagents. For the current environment, those capabilities are exposed through the collaboration tools. The implementation must discover and validate the tools actually available where the skill runs.

The runtime contract should support:

| Capability | Required behavior |
|---|---|
| Launch | Submit a scoped assignment and return an actual native agent ID or a clear failure. |
| Acknowledge | Distinguish an accepted request from work that has actually started. |
| Message / follow-up | Send a clarification or next assignment to the intended real worker. |
| Inspect / wait | Observe completion, blockers, errors and relevant results without fabricated status. |
| Interrupt | Request a stop and report what the runtime actually confirms. |
| Reconcile | Compare runtime state, ledger ownership and files after interruption or restart. |

Do not use chat-creation/fork tools, separate accounts, hidden terminals running other chat clients, or independent chat windows as substitutes in this edition. GitHub can still be used for normal repository work when requested, but it is not required as the internal message bus for a native subagent company.

If native delegation is unavailable, report that limitation. Offer a smaller single-agent workflow if useful; never pretend a native team ran or silently switch to creating chats.

## 5. Real nesting without exhausting the runtime

Managers should be able to delegate to specialist subagents where the host supports child delegation. The company also needs to work on hosts with shallow nesting or a small number of available slots.

**Recommended design: central capacity admission, with bounded delegation by managers.**

1. The main coordinator owns the global capacity and resource allocation.
2. Managers propose or receive scoped child assignments within that allocation.
3. A manager launches a child only when the host supports it and the global slot/resource limit permits it.
4. Every child launch is registered with its actual ID, task and parent. It consumes the same company/project budget; delegation does not create a new allowance.
5. If nesting or slots are unavailable, the manager returns a work order to the coordinator. The coordinator can launch the specialist directly while retaining the manager as its logical reporting owner.

This preserves company accountability even when the physical agent tree must be shallower.

For example, with four total execution slots including the main coordinator, keeping a CTO, MD and two managers alive may leave no capacity for builders. Managers should finish a planning/handoff assignment before the next wave when appropriate. A waiting or idle agent must not be assumed to free a slot unless the runtime confirms that behavior.

Configure a maximum delegation depth and total active-worker ceiling. Do not recursively instantiate the entire company. Reserve a path to review and integration so builders do not consume every available resource indefinitely.

The CEO derives a conservative starting allocation from observed host limits and existing project constraints. It can choose staffing within that allocation without asking the user to pick a preset, role list or worker count. Optional user limits override that discretion; missing monetary telemetry remains unknown rather than becoming an invented spending allowance.

## 6. Internal communication and shared work

Use native messages for timely coordination and the existing ledger for durable ownership, decisions and evidence. Do not send every routine internal message through GitHub comments or external chat applications.

Each assignment should include:

- Task/project IDs, role, logical manager and accountable delivery owner.
- Goal, observable acceptance criteria and relevant business decisions.
- Required inputs, contracts, dependencies and permitted write paths.
- Available tools, existing authorization boundaries and resource allocation.
- Required artifacts, checks, reviewer and completion conditions.
- A clear escalation route and what to return if blocked.

Each result should include:

- Actual native agent ID and task ID.
- Completed artifacts, locations and exact revision/digest.
- Commands/checks actually run, outcomes and omitted coverage.
- Changes affecting another team or contract.
- Blockers, unresolved decisions, remaining work and next action.

Treat task inputs and peer content as data, not permission to override the owner or host. Titles do not grant authority. Keep the existing [action policy](references/safety-protocol.md) rather than adding a second approval system.

Independent specialist work can proceed in parallel. Shared-file writes and dependent interface changes need explicit ownership and sequencing. Subagents may share a filesystem even when their contexts are isolated; separate contexts are not separate working trees.

## 7. Keep worker status separate from task status

The existing task ledger describes delivery stages. The native edition also needs a worker registry and execution attempts, because a completed or failed agent is not the same thing as a completed project task.

Proposed worker/attempt fields:

| Field | Purpose |
|---|---|
| Native agent ID | Identity actually returned by the host, not a made-up employee name. |
| Role / department / logical manager | Company responsibility and reporting relationship. |
| Runtime parent ID | Physical delegation parent, which may differ from the logical manager. |
| Project / task / attempt ID | Work ownership and retry history. |
| Lifecycle status | Requested, launched, acknowledged, running, waiting, completed, failed or stop-requested; use only states supported by observations. |
| Slot and resource reservation | Global/project allocation and its accounting basis. |
| Checkpoint / latest result | Artifacts, revision, checks, next step and last observed runtime state. |
| Contribution history | Who actually contributed, including replacements, for independent-review checks. |

Alongside the worker registry, retain the current product model, versioned role profiles and organization decisions. Each staffing/reorganization decision should connect the observed need to its chosen action and affected task/attempt IDs. This makes the CEO's decisions explainable without making the user manage them manually.

A stopped builder does not automatically become a verified task. A manager's summary is not proof a child's checks ran. Recording an agent ID in a file does not launch it.

Prefer coordinator-owned durable writes for the first implementation: workers return structured results, and the coordinator commits task/attempt transitions through the existing atomic writer. This reduces competing ledger updates. Distributed writers can be considered later if real need justifies them.

## 8. Lifecycle and recovery

The core loop should be:

```text
User request
  -> product understanding and CEO-designed organization
  -> scoped plan and automatically selected roles
  -> ready work and available resources
  -> native launch + actual ID + acknowledgment
  -> scoped execution and coordination
  -> artifacts/check evidence
  -> independent native review
  -> integration and authorized delivery
  -> one consolidated report in the original chat
```

Wait through native completion/status tools where available. Avoid rapid polling and repeated whole-company summaries. Keep the parent responsive to your messages; new instructions must reach the affected workers and update their assignments.

On failure or interruption, preserve the attempt, inspect files and side effects, confirm whether the old worker is still active, and only then retry or reassign. A retry gets a new attempt identity and shares the original budget. Never start a second writer merely because the first has been silent.

After a parent-chat restart or context loss, stored IDs are historical references until reconciled with the runtime. They do not guarantee workers still exist or can be reattached. Resume artifacts and tasks if the original workers are unavailable.

Stopping work should stop new dispatch immediately and request interruption of relevant live descendants. Report any workers whose termination cannot be confirmed. A Python ledger cannot independently guarantee that a native worker has stopped.

## 9. Independent review

Use a real separate native evaluator for code review or QA. Preserve all contributors to the reviewed artifact; changing a builder's role name does not make it independent.

The reviewer receives the acceptance criteria, relevant raw artifacts and revision, environment and needed context. Ask it to assess the result rather than feeding it the builder's intended verdict. Record findings and checks against the exact submission. Reassess affected evidence after code, base, contract or environment changes.

If there is no spare slot, sequence review after the builder finishes. If independent execution is unavailable, report that gap; do not invent another identity to satisfy the ledger.

## 10. What you will see in the main chat

You should receive useful company updates rather than a transcript from every employee:

- Which teams are active and what outcome they own.
- What completed, with artifact/review evidence.
- Blockers and decisions that require you, with a recommendation.
- Resource limits, known usage and what remains uncertain.
- The next delivery step and any material change in scope.
- Significant staffing/structure changes, why the CEO chose them, and whether they helped.

Example update:

> “Product has defined the portal acceptance criteria. Backend and frontend are implementing the agreed API contract. I have queued an independent QA review of the integrated account, invoice and support flows, and will report the results here.”

Example autonomous staffing update:

> “The API contract is stable and two screens can proceed independently, so I added a second frontend worker and split ownership between account and support. I kept one review slot available. You don't need to assign those roles.”

You can ask “What is the CTO working on?”, “Show the backend team's blockers,” or “Stop this project” in the same chat. The coordinator answers from actual recorded/runtime state and takes permitted actions; it does not create a new chat for that question.

## 11. Features proposed for the first native edition

| Feature | Initial scope |
|---|---|
| Native execution adapter | Verified launch/message/status/wait/interrupt operations for one supported host. |
| Product understanding model | Goal, users, stage, architecture, existing capabilities, uncertainty and evidence that guide organization choices. |
| Autonomous organization designer | CEO chooses roles, managers, squads and worker counts from product/workload needs, without user staffing commands. |
| Adaptive role catalog | Reuse existing profiles and create scoped specialties when justified; version changes and preserve historical briefs. |
| Staffing and scaling decisions | Add, split, duplicate, combine, reassign, park and retire workers with ownership/resource checks. |
| Worker and attempt registry | Real IDs, physical/logical reporting, task binding and lifecycle history. |
| Company dispatcher | Dependency-, ownership-, slot- and budget-aware dispatch with centralized admission. |
| Executive/manager role briefs | Scoped responsibilities and structured delegation/results, loaded only when needed. |
| Specialist squads | Frontend/backend/research/platform and other relevant teams assembled per project. |
| Bounded nested delegation | Native child spawning where supported; coordinator-mediated work orders otherwise. |
| Internal handoffs | Reliable acknowledgments, result correlation, blockers and contract-change notices. |
| Independent review | Real evaluator, contributor separation, revision-bound evidence and rework. |
| Parent-chat steering | Update, stop and reprioritize assignments when you change direction. |
| Recovery and reporting | Checkpoints, retry history, runtime reconciliation and one consolidated owner view. |
| Organization decision history | Reasons, evidence, expected benefit and outcome checks for meaningful staffing/structure changes. |

Keep dashboards, additional providers, financial telemetry and background scheduling outside the first native release. They can build on a working executor later. The company operates while an actual host session is executing; skill instructions alone do not create an always-on service.

## 12. Implementation phases after discussion

| Phase | Deliverable | Gate before continuing |
|---|---|---|
| 1. Agree the edition | Entry point, autonomous CEO responsibilities, supported host and owner experience | We agree how the company should operate before creating the variant. |
| 2. Verify native capabilities | Minimal launch/message/wait/stop experiment in an isolated fixture | Actual IDs and observed lifecycle; no separate user-owned chats. |
| 3. Build one delivery squad | CEO derives a small team from a business-only request; workers/reviewer link to ledger attempts | A small task completes with real artifacts/evidence, without user role or count instructions. |
| 4. Add manager delegation | Manager planning/handoffs, nested children where supported, global slot admission | Works with both shallow and deeper runtime trees without deadlock. |
| 5. Expand and adapt departments | Research, design, engineering, QA/security and executive advice; scoped role creation, duplication and retirement | CEO changes team structure from observed need and teams integrate one shared outcome. |
| 6. Validate recovery and package | Stop/retry/restart behavior, documentation, fixtures and self-contained skill packaging | Acceptance scenarios below pass and limitations are documented. |

The existing role catalog and local ledger can be reused. The principal new work is the actual native execution/lifecycle layer; adding more role descriptions alone will not deliver this edition.

## 13. Acceptance scenarios

| Scenario | What must happen |
|---|---|
| Start a company assignment | Work runs from one parent chat; no chat-create/fork APIs are called. |
| User supplies only a business goal | CEO inspects product context, selects roles/counts and starts suitable work without requiring staffing commands. |
| Existing product already solves part of the request | CEO reuses that capability and avoids creating a duplicate team or rebuilding it blindly. |
| Small bug fix | A real builder and independent evaluator complete it without unnecessary executive layers. |
| Frontend/backend feature | Managers coordinate a shared contract; specialists produce an integrated result. |
| Independent work outgrows one specialist | CEO can launch another real worker, divide ownership, preserve review capacity and later release the extra capacity. |
| More workers would not resolve the blocker | CEO addresses the dependency/decision or assigns other work rather than duplicating agents automatically. |
| Review becomes the bottleneck | CEO shifts capacity toward independent evaluation before adding more implementation work. |
| Missing specialist profile | CEO creates a bounded product-relevant role and work contract without adding permissions or requiring the user to name the role. |
| Team structure changes mid-project | Version role/assignment changes, acknowledge handoffs and preserve costs, ownership and contributor history. |
| Workload drops or a department becomes unnecessary | CEO parks/retires confirmed idle capacity instead of keeping every role active. |
| Requested outcomes are complete | CEO winds down remaining assignments and reports evidence instead of inventing new work to sustain the organization. |
| Small slot limit | Excess work queues; planning layers do not keep all slots occupied and block delivery. |
| Nested spawning unavailable | Coordinator launches native specialists from manager work orders; reporting ownership stays visible. |
| Worker launch fails | No running worker is invented; reservations and task status are reconciled. |
| Manager or specialist fails | Preserve child ownership and evidence; inspect actual descendants before retrying. |
| Builder asks to approve itself | Independent-review gate rejects the contributor, regardless of its role label. |
| You change scope mid-run | Coordinator communicates the change to affected workers and reconciles the plan. |
| You say stop | No new assignments launch; stop requests propagate, and unconfirmed workers are reported. |
| Parent context is lost | Restore tasks/artifacts and reconcile real worker state; do not assume IDs are still live. |
| Tools/telemetry are missing | Report actual limitations and unknown cost; do not create substitute chats or fake observations. |

## 14. Choices for our discussion

My recommended starting choices are:

1. **A separate subagent edition**, so its execution promise is clear and the existing skill remains usable.
2. **An autonomous CEO in the main chat**, responsible for understanding the product and choosing/evolving roles, teams and staffing; the user supplies outcomes and optional constraints.
3. **Managers can delegate within a global allocation**, with coordinator-mediated dispatch when native nesting or slots are limited.
4. **Adaptive teams and specialties**, using the role catalog as a starting library and adding, duplicating, combining or retiring capacity when evidence supports it.
5. **One supported native host first**, validated with real lifecycle behavior before adding adapters for others.
6. **A working small squad before a full company simulation**, then expand the management layers and departments with evidence.

The user's requirement for CEO-owned organization and staffing is established. The first implementation now supports a small native-subagent company taking a business goal, selecting its staffing, executing real delegated work and obtaining independent review inside one main chat. Further host adapters, larger live management trees and additional automation should follow observed needs and the remaining roadmap.
