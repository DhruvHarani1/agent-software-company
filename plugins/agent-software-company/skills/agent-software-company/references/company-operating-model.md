# Company operating model

The human owner supplies the business mandate and action boundaries. The company organizes expertise and delivery within that mandate. The included local kernel records coordination; the host performs actual work. Follow the canonical [safety policy](safety-protocol.md).

## Leadership and reporting

```text
Human owner
  CEO
    MD / COO: delivery operations, support, knowledge
    CTO: research, architecture, engineering, data, platform
    CPO: product requirements and design
    CFO / FinOps: estimates, resource accounting, cost trade-offs
    Quality Director: independent review and QA
    CISO: security/privacy assessment and escalation
    Growth Director: commercial research and draft launch material
```

`templates/organization.json` defines eight executive roles, eighteen department managers and their specialists: **80 roles total**. `company.py org` expands the catalog into role cards with reporting line, mission, inputs, outputs, completion expectations and escalation. A role card is reusable guidance, not a running worker or authority grant.

| Department | Manager | Specialist examples / main output |
|---|---|---|
| Product and business analysis | `product-manager` | Business/requirements/domain analysts; testable requirements. |
| Research and innovation | `research-manager` | Technical/market researchers, prototype engineer; sourced feasibility findings. |
| UX, UI and design | `design-manager` | UX/UI, accessibility, design systems; usable interface contracts. |
| Architecture | `principal-architect` | Solution/API/data architects; boundaries and decisions. |
| Frontend engineering | `frontend-manager` | Frontend/component/client integration; client behavior and evidence. |
| Backend engineering | `backend-manager` | Backend/integration/authorization; service behavior and tests. |
| Data and database | `data-manager` | Database/data/analytics engineering; schema and data-quality plans. |
| Mobile and desktop | `application-manager` | Mobile/desktop engineers; platform behavior and packaging. |
| Applied AI and ML | `ai-manager` | AI/evaluation engineers, ML scientist; evaluated behavior and limits. |
| Platform, DevOps and SRE | `platform-manager` | DevOps/SRE/release/developer experience; reproducible delivery and recovery. |
| Independent code review | `review-lead` | Code/architecture reviewers; revision-bound assessment. |
| QA and testing | `qa-manager` | Functional/automation/performance testing; reproducible evidence. |
| Security and privacy | `security-manager` | AppSec/dependencies/privacy; confirmed risks and remediation checks. |
| Project/program delivery | `delivery-director` | Program/project managers, coordinator; integrated outcome and dependencies. |
| Customer success/support | `support-manager` | Support/technical support/feedback; triage and reproduction. |
| Finance and FinOps | `finance-manager` | FinOps/project estimation; estimates versus accounted or measured resources. |
| Growth and commercial | `growth-manager` | Sales/marketing/content; sourced proposals and launch drafts. |
| Agent operations/knowledge | `knowledge-manager` | Technical writing, curation, agent operations, compliance support; reusable project memory. |

Department ownership keeps expertise and standards consistent. A temporary delivery squad combines the necessary specialists around one project, with one accountable project owner. Requests need not pass through every executive. A frontend/backend task should agree an API contract before parallel editing; review and QA can report independently of the builder.

## Size and assignment

- **Founder:** one active assignment by default; one person/session may combine compatible management functions.
- **Startup:** two active assignments by default; commonly build then independent review, or two non-conflicting specialists.
- **Full company:** four active assignments by default; departments coordinate multiple dependent work items.

All presets retain the same role catalog; they do not spawn more people or change authorization. `--max-active` and `--budget` override initial limits. Respect lower host/tool/resource limits. Do not claim independent review if no separate evaluator is available; leave that evidence missing and report it.

`task start --actor` and `review start --reviewer` record actual host identities. The operator must obtain them from real host assignments. The ledger does not authenticate strings or start sessions; using a different invented ID to disguise a contributor defeats the operating model even if a string check would pass.

## Work and local state

The canonical local record is `.agent-company/state.json` under an existing project workspace. It contains the organization snapshot, projects, tasks, decisions, resource entries and event history. A project records its goal and accountable role. A task records role, acceptance, dependencies, paths, estimates, actual assignments, contributors, submissions, reviews and checkpoints.

The supported delivery states are `ready` → `in-progress` → `review` → `verified` → `integrated` → `released` → `closed`; a CHANGES verdict returns to `ready`. A verified non-release artifact may close directly. Blocked/parked conditions preserve delivery phase rather than pretending work has restarted from scratch. See [workflows](company-workflows.md) for supported commands; do not infer a command from an internal state name.

Dependencies become available after the predecessor is verified or later. If the dependent task needs a deployed API rather than a reviewed contract, reflect that in task scope/acceptance and the actual delivery plan; the generic dependency check alone cannot prove deployment. Literal relative file/directory paths support conservative active-build overlap checks. They are advisory ownership declarations, not filesystem locks or sandbox permissions.

Build and review assignments reserve capacity and estimated effort. Completion accounts an estimate unless `--actual` supplies measured units. Parking records spent units separately and releases remaining reservation only after the actual worker is stopped. Budget output separates accounted estimates, measured units, current reservations and remaining allowance; currency cost is unknown. It is not automatic token/cloud billing telemetry, and actual effort can exceed an estimate.

Writes use an exclusive lock and atomic replacement. Initialization is preview-first and idempotent; it does not overwrite an existing company or host instructions. Preserve state and snapshots for recovery. Investigate locks/corruption instead of deleting them or reconstructing fictional progress.

## Separate local and shared records

| Record | Scope | Mechanism |
|---|---|---|
| `.agent-company/` | Local planning/execution attestations | `company.py`; no automatic GitHub synchronization. |
| `.agents/` | Owner-reviewed cross-team agreements | Repository files and normal review process. |
| GitHub issues/PRs/comments | Shared work/evidence when authorized | Host tools or explicit operator action, not company CLI. |
| `.agents-state/` | Local scoped inbox acknowledgment | `inbox.py`; not owner decisions or task completion. |

Cross-team cooperation is optional and uses [interop](interop-protocol.md). None of these records overrides actual host/user authority.

## Implemented versus future

Implemented: role catalog and cards, local projects/tasks, dependency/capacity/path/budget checks, actual assignment records, revision-bound submission/review, contributor exclusion, decisions, checkpoints, park/resume/handoff, status and Markdown report.

Still future: persistent worker spawning, external dashboards, automatic reminders/schedulers, automatic token/cloud telemetry, runtime/provider adapters, client contracts/invoicing and automated client-portfolio allocation. Multiple project records already exist; they do not constitute automatic portfolio optimization or an autonomous company service.
