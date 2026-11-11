"""Local company ledger. No subprocesses, external writes, or agent spawning.

The host performs real work and records attestations here. This ledger validates
workflow consistency; it cannot authenticate a session ID or authorize actions.
"""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone


class CompanyError(ValueError):
    pass


PRESETS = {"founder": 1, "startup": 2, "full-company": 4}
STATES = {"ready", "in-progress", "review", "verified", "integrated", "released", "closed", "cancelled"}
ACCEPTED = {"verified", "integrated", "released", "closed"}
REVISIONS = re.compile(r"(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})\Z")
UNSET = object()


def now():
    return datetime.now(timezone.utc).isoformat()


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise CompanyError(f"{field} must be nonempty text")
    return value.strip()


def units(value, field="units"):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise CompanyError(f"{field} must be a finite nonnegative number")
    return value


def priority(value):
    if type(value) is not int or not 0 <= value <= 100:
        raise CompanyError("priority must be an integer from 0 to 100 (100 is highest)")
    return value


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError, ValueError) as exc:
        raise CompanyError(f"Cannot read valid JSON from {path.name}: {exc}") from exc


def organization():
    src = Path(__file__).resolve().parents[2] / "templates" / "organization.json"
    raw = load_json(src)
    roles = {}
    for executive in raw["executives"]:
        roles[executive["id"]] = dict(executive, department="leadership")
    for dept in raw["departments"]:
        common = {"department": dept["id"], "mission": dept["mission"], "outputs": dept["outputs"]}
        roles[dept["manager"]] = dict(common, id=dept["manager"], title=dept["title"] + " Manager", reports_to=dept["reports_to"])
        for role_id, title_ in dept["specialists"]:
            roles[role_id] = dict(common, id=role_id, title=title_, reports_to=dept["manager"])
    for role in roles.values():
        role["authority"] = "Only the owner's existing mandate and host permissions; title grants no permissions."
        role["inputs"] = ["scoped work item", "relevant decisions and contracts"]
        role["completion"] = "Acceptance evidence, limitations, and next action delivered to the accountable owner."
        role["escalation"] = role["reports_to"]
        seen = {role["id"]}
        parent = role["reports_to"]
        while parent != "owner":
            if parent not in roles or parent in seen:
                raise CompanyError("Invalid or cyclic organization reporting line")
            seen.add(parent)
            parent = roles[parent]["reports_to"]
    return {"schema_version": 1, "departments": raw["departments"], "roles": roles}


def initial_state(name, mission, preset="startup", max_active=None, budget=100):
    if preset not in PRESETS:
        raise CompanyError("Unknown company preset")
    limit = max_active if max_active is not None else PRESETS[preset]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise CompanyError("max_active must be a positive integer")
    units(budget, "budget")
    return {
        "schema_version": 1, "revision": 0, "name": text(name, "name"),
        "mission": text(mission, "mission"), "preset": preset, "created_at": now(),
        "limits": {"max_active": limit, "budget_units": budget, "unit": "effort"},
        "organization": organization(), "projects": {}, "tasks": {}, "squads": {}, "decisions": [],
        "resource_entries": [], "events": [],
        "external_actions": "No external actions are executed or authorized by this ledger."
    }


def _reparse(path):
    if path.is_symlink():
        return True
    return bool(path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


class Store:
    def __init__(self, workspace):
        self.root = Path(workspace).resolve()
        if not self.root.is_dir():
            raise CompanyError("Workspace must be an existing directory")
        self.directory = self.root / ".agent-company"
        self.path = self.directory / "state.json"
        self.lock = self.directory / "write.lock"

    def safe(self):
        for path in (self.directory, self.path, self.lock):
            if _reparse(path):
                raise CompanyError("Company state paths must not be links or reparse points")

    def load(self):
        self.safe()
        if not self.path.is_file():
            raise CompanyError("Company not initialized; preview `init`, then use `init --apply`")
        state = load_json(self.path)
        validate(state)
        return state

    def write(self, callback=None, initial=None):
        self.safe()
        self.directory.mkdir(exist_ok=True)
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise CompanyError("Company state is locked. Inspect the running writer; never remove a live lock.") from exc
        tmp_name = None
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"pid": os.getpid(), "created_at": now()}))
            if initial is not None:
                if self.path.exists():
                    current = self.load()
                    return {"status": "already-initialized", "name": current["name"], "revision": current["revision"]}
                state, result = copy.deepcopy(initial), {"status": "initialized", "name": initial["name"]}
            else:
                state = self.load()
                result = callback(state)
                state["revision"] += 1
            validate(state)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.directory, prefix=".state-", suffix=".tmp", delete=False) as handle:
                tmp_name = handle.name
                json.dump(state, handle, indent=2, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
            tmp_name = None
            return result
        finally:
            if tmp_name is not None:
                Path(tmp_name).unlink(missing_ok=True)
            self.lock.unlink(missing_ok=True)


def validate(s):
    if not isinstance(s, dict) or s.get("schema_version") != 1:
        raise CompanyError("Unsupported company state schema")
    try:
        text(s["name"], "company name")
        text(s["mission"], "company mission")
        if s["preset"] not in PRESETS or s["limits"]["unit"] != "effort":
            raise CompanyError("Invalid preset or resource unit")
        for key in ("events", "decisions", "resource_entries"):
            if not isinstance(s[key], list):
                raise CompanyError(f"Invalid {key}")
        if isinstance(s["revision"], bool) or not isinstance(s["revision"], int) or s["revision"] < 0:
            raise CompanyError("Invalid state revision")
        if not isinstance(s["projects"], dict) or not isinstance(s["tasks"], dict):
            raise CompanyError("Invalid project/task registry")
        units(s["limits"]["budget_units"], "budget")
        if isinstance(s["limits"]["max_active"], bool) or not isinstance(s["limits"]["max_active"], int) or s["limits"]["max_active"] < 1:
            raise CompanyError("Invalid capacity")
        roles = s["organization"]["roles"]
        for key, project in s["projects"].items():
            if project["id"] != key or not re.fullmatch(r"P[0-9]{4,}", key) or project["owner"] not in roles:
                raise CompanyError("Invalid project record")
            text(project["title"], "project title")
            text(project["goal"], "project goal")
            priority(project.get("priority", 50))
            if project.get("budget_units") is not None:
                units(project["budget_units"], "project budget")
        if not isinstance(s.get("squads", {}), dict):
            raise CompanyError("Invalid squad registry")
        for key, squad in s.get("squads", {}).items():
            if squad["id"] != key or not re.fullmatch(r"S[0-9]{4,}", key) or squad["project"] not in s["projects"]:
                raise CompanyError("Invalid squad record")
            text(squad["title"], "squad title")
            if not isinstance(squad["members"], list) or squad["lead"] not in squad["members"]:
                raise CompanyError("Squad lead must be a member")
            if len(set(squad["members"])) != len(squad["members"]) or any(r not in roles for r in squad["members"]):
                raise CompanyError("Invalid squad role membership")
        for key, t in s["tasks"].items():
            if t["id"] != key or not re.fullmatch(r"T[0-9]{4,}", key):
                raise CompanyError("Invalid task ID")
            if t["state"] not in STATES or t["project"] not in s["projects"] or t["role"] not in roles:
                raise CompanyError("Invalid task references or state")
            text(t["title"], "task title")
            units(t["estimate"], "task estimate")
            units(t["remaining_estimate"], "remaining estimate")
            priority(t.get("priority", 50))
            if t.get("squad") is not None:
                squad = s.get("squads", {}).get(t["squad"])
                if not squad or squad["project"] != t["project"] or t["role"] not in squad["members"]:
                    raise CompanyError("Task squad must match project and include its role")
            if not isinstance(t["parked"], bool):
                raise CompanyError("Invalid parked flag")
            if t["blocked"] is not None:
                text(t["blocked"], "blocker")
            if not isinstance(t["acceptance"], list) or not t["acceptance"]:
                raise CompanyError("Missing acceptance criteria")
            for criterion in t["acceptance"]:
                text(criterion, "acceptance")
            if not isinstance(t["depends"], list) or key in t["depends"]:
                raise CompanyError("Invalid dependency list")
            if any(d not in s["tasks"] for d in t["depends"]):
                raise CompanyError("Unknown task dependency")
            if not isinstance(t["paths"], list) or normalize_paths(t["paths"]) != t["paths"]:
                raise CompanyError("Invalid owned paths")
            if not isinstance(t["contributors"], list) or not isinstance(t["submissions"], list) or not isinstance(t["reviews"], list):
                raise CompanyError("Invalid task history")
            for actor in t["contributors"]:
                text(actor, "contributor")
            if t["actor"] is not None and t["actor"] not in t["contributors"]:
                raise CompanyError("Task actor missing from contributor history")
            for submission in t["submissions"]:
                if not REVISIONS.fullmatch(submission["revision"]) or submission["actor"] not in t["contributors"]:
                    raise CompanyError("Invalid submission revision or contributor")
                text(submission["artifact"], "artifact")
                text(submission["evidence"], "submission evidence")
            for review in t["reviews"]:
                if not isinstance(review["contributors"], list) or any(a not in t["contributors"] for a in review["contributors"]):
                    raise CompanyError("Invalid review contributor snapshot")
                if review["verdict"] not in {"PASS", "CHANGES"} or review["reviewer"] in review["contributors"]:
                    raise CompanyError("Invalid independent review")
                text(review["reviewer"], "reviewer")
                text(review["evidence"], "review evidence")
                if not any(x["revision"] == review["revision"] for x in t["submissions"]):
                    raise CompanyError("Review names an unknown revision")
            assignment = t["review_assignment"]
            if assignment is not None:
                if t["state"] != "review" or assignment["actor"] in t["contributors"]:
                    raise CompanyError("Invalid review assignment")
                text(assignment["actor"], "review actor")
                units(assignment["estimate"], "review estimate")
            if t["state"] == "in-progress" and not t["actor"]:
                raise CompanyError("Active work must name its contributor")
            if t["state"] in {"review", *ACCEPTED} and not t["submissions"]:
                raise CompanyError("Review/accepted state requires a submission")
            if t["state"] in ACCEPTED and (not t["reviews"] or t["reviews"][-1]["verdict"] != "PASS" or
                                            t["reviews"][-1]["revision"] != t["submissions"][-1]["revision"] or
                                            t["reviews"][-1]["reviewer"] in t["contributors"]):
                raise CompanyError("Accepted state requires a current independent PASS")
            if t["parked"] and not (t["state"] == "in-progress" or assignment):
                raise CompanyError("Only an assignment may be parked")
            if t["checkpoint"] is not None:
                cp = t["checkpoint"]
                if not isinstance(cp, dict) or cp["state"] not in STATES:
                    raise CompanyError("Invalid checkpoint")
                text(cp["next"], "checkpoint next action")
                text(cp["at"], "checkpoint timestamp")
                if not isinstance(cp["paths"], list):
                    raise CompanyError("Invalid checkpoint paths")
        visiting, visited = set(), set()
        def walk(key):
            if key in visiting:
                raise CompanyError("Cyclic task dependencies")
            if key in visited:
                return
            visiting.add(key)
            for dep in s["tasks"][key]["depends"]:
                walk(dep)
            visiting.remove(key)
            visited.add(key)
        for key in s["tasks"]:
            walk(key)
        for entry in s["resource_entries"]:
            units(entry["units"])
            if entry["basis"] not in {"estimate", "measured"} or entry["task"] not in s["tasks"]:
                raise CompanyError("Invalid resource entry")
        for record in s["decisions"]:
            if not re.fullmatch(r"D[0-9]{4,}", record["id"]) or record["owner"] not in roles:
                raise CompanyError("Invalid decision record")
            for field in ("question", "outcome", "source", "at"):
                text(record[field], f"decision {field}")
            if record.get("project") is not None and record["project"] not in s["projects"]:
                raise CompanyError("Unknown decision project")
        for record in s["events"]:
            if type(record["id"]) is not int or record["id"] < 1 or not isinstance(record["detail"], dict):
                raise CompanyError("Invalid event record")
            for field in ("at", "kind", "target"):
                text(record[field], f"event {field}")
    except (KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise CompanyError("Incomplete or corrupt company state; restore a known snapshot") from exc


def event(s, kind, target, detail):
    s["events"].append({"id": len(s["events"]) + 1, "at": now(), "kind": kind, "target": target, "detail": copy.deepcopy(detail)})


def get_task(s, task_id):
    if task_id not in s["tasks"]:
        raise CompanyError(f"Unknown task {task_id}")
    return s["tasks"][task_id]


def require_role(s, role):
    if role not in s["organization"]["roles"]:
        raise CompanyError(f"Unknown role {role}; use `org` to inspect the catalog")


def next_id(records, prefix):
    return f"{prefix}{max((int(key[1:]) for key in records), default=0) + 1:04d}"


def add_project(s, title, goal, owner="md", priority_value=50, budget_units=None):
    require_role(s, owner)
    priority(priority_value)
    if budget_units is not None:
        units(budget_units, "project budget")
    project_id = next_id(s["projects"], "P")
    s["projects"][project_id] = {"id": project_id, "title": text(title, "title"), "goal": text(goal, "goal"), "owner": owner,
                                 "priority": priority_value, "budget_units": budget_units}
    event(s, "project-created", project_id, {"owner": owner})
    return s["projects"][project_id]


def normalize_paths(paths):
    result = []
    for path in paths:
        path = text(path, "path").replace("\\", "/")
        if path.startswith("/") or ":" in path or ".." in path.split("/") or any(ch in path for ch in "*?["):
            raise CompanyError("Owned paths must be relative file/directory paths, not traversal or globs")
        cleaned = "/".join(p for p in path.split("/") if p not in ("", ".")).casefold()
        if not cleaned:
            raise CompanyError("A path must identify a file or directory")
        result.append(cleaned)
    return sorted(set(result))


def add_task(s, project, title, role, acceptance, depends=(), paths=(), estimate=1, priority_value=50, squad=None):
    if project not in s["projects"]:
        raise CompanyError("Unknown project")
    require_role(s, role)
    if not acceptance:
        raise CompanyError("At least one observable acceptance criterion is required")
    for dependency in depends:
        get_task(s, dependency)
    priority(priority_value)
    if squad is not None:
        group = s.get("squads", {}).get(squad)
        if not group or group["project"] != project or role not in group["members"]:
            raise CompanyError("Task squad must match project and include its role")
    task_id = next_id(s["tasks"], "T")
    task = {"id": task_id, "project": project, "title": text(title, "title"), "role": role,
            "acceptance": [text(a, "acceptance") for a in acceptance], "depends": list(dict.fromkeys(depends)),
            "paths": normalize_paths(paths), "estimate": units(estimate, "estimate"), "state": "ready",
            "priority": priority_value, "squad": squad,
            "blocked": None, "parked": False, "remaining_estimate": estimate, "actor": None, "contributors": [],
            "submissions": [], "reviews": [], "review_assignment": None, "checkpoint": None}
    s["tasks"][task_id] = task
    event(s, "task-created", task_id, {"role": role})
    return task


def resources(s):
    accounted = sum(e["units"] for e in s["resource_entries"])
    measured = sum(e["units"] for e in s["resource_entries"] if e["basis"] == "measured")
    estimated = sum(e["units"] for e in s["resource_entries"] if e["basis"] == "estimate")
    reserved = sum(t["remaining_estimate"] for t in s["tasks"].values() if t["state"] == "in-progress" and not t["parked"])
    reserved += sum(t["review_assignment"]["estimate"] for t in s["tasks"].values() if t.get("review_assignment") and not t["parked"])
    limit = s["limits"]["budget_units"]
    return {"unit": s["limits"]["unit"], "limit": limit, "accounted": accounted, "measured": measured,
            "estimated": estimated, "reserved": reserved, "remaining": limit - accounted - reserved,
            "currency_cost": "unknown", "active": sum((t["state"] == "in-progress" or bool(t.get("review_assignment"))) and not t["parked"] for t in s["tasks"].values()),
            "max_active": s["limits"]["max_active"]}


def project_resources(s, project_id):
    if project_id not in s["projects"]:
        raise CompanyError("Unknown project")
    scoped = copy.copy(s)
    scoped["tasks"] = {key: t for key, t in s["tasks"].items() if t["project"] == project_id}
    scoped["resource_entries"] = [e for e in s["resource_entries"] if e["task"] in scoped["tasks"]]
    result = resources(scoped)
    limit = s["projects"][project_id].get("budget_units")
    result.update(project=project_id, limit=limit,
                  remaining=None if limit is None else limit - result["accounted"] - result["reserved"])
    return result


def budget_reason(s, project_id, estimate):
    if resources(s)["remaining"] < estimate:
        return "company budget limit"
    available = project_resources(s, project_id)["remaining"]
    if available is not None and available < estimate:
        return "project budget limit"
    return None


def update_project(s, project_id, source, reason, **changes):
    if project_id not in s["projects"]:
        raise CompanyError("Unknown project")
    text(source, "decision source")
    text(reason, "change reason")
    if not changes or any(key not in {"title", "goal", "owner", "priority", "budget_units"} for key in changes):
        raise CompanyError("No supported project changes")
    proposed = dict(s["projects"][project_id])
    for key, value in changes.items():
        if key in {"title", "goal"}:
            value = text(value, key)
        elif key == "owner":
            require_role(s, value)
        elif key == "priority":
            priority(value)
        elif key == "budget_units" and value is not None:
            units(value, "project budget")
            used = project_resources(s, project_id)
            if value < used["accounted"] + used["reserved"]:
                raise CompanyError("Project budget cannot be below accounted effort plus reservations")
        proposed[key] = value
    s["projects"][project_id] = proposed
    event(s, "project-updated", project_id, {"changes": changes, "source": source, "reason": reason})
    return proposed


def update_limits(s, source, reason, budget_units=UNSET, max_active=UNSET):
    text(source, "decision source")
    text(reason, "change reason")
    current = resources(s)
    proposed = dict(s["limits"])
    if budget_units is UNSET and max_active is UNSET:
        raise CompanyError("Specify a budget or capacity change")
    if budget_units is not UNSET:
        units(budget_units, "company budget")
        if budget_units < current["accounted"] + current["reserved"]:
            raise CompanyError("Company budget cannot be below accounted effort plus reservations")
        proposed["budget_units"] = budget_units
    if max_active is not UNSET:
        if type(max_active) is not int or max_active < max(1, current["active"]):
            raise CompanyError("Capacity must be positive and cover all active assignments")
        proposed["max_active"] = max_active
    s["limits"] = proposed
    event(s, "limits-updated", "company", {"limits": proposed, "source": source, "reason": reason})
    return {"limits": proposed, "notice": "Recorded configuration only; source must be checked against the actual owner mandate."}


def add_squad(s, title, project, lead, members):
    if project not in s["projects"]:
        raise CompanyError("Unknown project")
    require_role(s, lead)
    for member in members:
        require_role(s, member)
    registry = s.setdefault("squads", {})
    squad_id = next_id(registry, "S")
    registry[squad_id] = {"id": squad_id, "title": text(title, "squad title"), "project": project, "lead": lead,
                           "members": list(dict.fromkeys([lead, *members]))}
    event(s, "squad-created", squad_id, registry[squad_id])
    return registry[squad_id]


def update_task(s, task_id, source, reason, **changes):
    t = get_task(s, task_id)
    text(source, "decision source")
    text(reason, "change reason")
    supported = {"title", "role", "acceptance", "depends", "paths", "estimate", "priority", "squad"}
    if not changes or set(changes) - supported:
        raise CompanyError("No supported task changes")
    if t["state"] in {"closed", "cancelled"}:
        raise CompanyError("Cannot change a terminal task")
    scope_changes = set(changes) - {"priority"}
    has_history = bool(t["contributors"] or t["submissions"] or t["reviews"] or
                       any(e["task"] == task_id for e in s["resource_entries"]))
    if scope_changes and (t["state"] != "ready" or has_history):
        raise CompanyError("Scope edits require an unstarted ready task; create follow-up work after execution")
    proposed_state = copy.deepcopy(s)
    proposed = proposed_state["tasks"][task_id]
    for key, value in changes.items():
        if key in {"title", "role"}:
            value = text(value, key)
        elif key == "paths":
            value = normalize_paths(value)
        elif key == "estimate":
            units(value, "task estimate")
            proposed["remaining_estimate"] = value
        elif key == "priority":
            priority(value)
        elif key in {"depends", "acceptance"}:
            value = list(value)
        proposed[key] = value
    validate(proposed_state)
    s["tasks"][task_id] = proposed
    event(s, "task-updated", task_id, {"changes": changes, "source": source, "reason": reason})
    return proposed


def cancel_task(s, task_id, source, reason):
    t = get_task(s, task_id)
    text(source, "decision source")
    text(reason, "cancellation reason")
    if t["state"] in ACCEPTED or t["state"] == "cancelled":
        raise CompanyError("Accepted or terminal work cannot be cancelled; record follow-up work instead")
    if (t["state"] == "in-progress" or t.get("review_assignment")) and not t["parked"]:
        raise CompanyError("Stop the actual worker and park with incurred effort before cancellation")
    t["state"] = "cancelled"
    t["parked"] = False
    t["blocked"] = None
    t["review_assignment"] = None
    event(s, "task-cancelled", task_id, {"source": source, "reason": reason})
    return t


def dispatch_plan(s, max_items=None):
    """Advisory batch of compatible build work, never an actual assignment."""
    if max_items is not None and (type(max_items) is not int or max_items < 1):
        raise CompanyError("max_items must be a positive integer")
    simulated = copy.deepcopy(s)
    selected, deferred = [], []
    ordered = sorted(s["tasks"].values(), key=lambda t: (-s["projects"][t["project"]].get("priority", 50),
                                                       -t.get("priority", 50), int(t["id"][1:])))
    for task in ordered:
        if task["state"] != "ready":
            continue
        reason = dispatch_reason(simulated, simulated["tasks"][task["id"]])
        if reason is None and max_items is not None and len(selected) >= max_items:
            reason = "batch size limit"
        record = {"id": task["id"], "project": task["project"], "role": task["role"], "squad": task.get("squad"),
                  "project_priority": s["projects"][task["project"]].get("priority", 50), "priority": task.get("priority", 50)}
        if reason:
            deferred.append(dict(record, reason=reason))
        else:
            selected.append(record)
            simulated["tasks"][task["id"]].update(state="in-progress", remaining_estimate=task["estimate"])
    review_waiting = [{"id": t["id"], "project": t["project"], "contributors": list(t["contributors"])}
                      for t in ordered if t["state"] == "review" and not t["review_assignment"] and not t["blocked"]]
    return {"ledger_revision": s["revision"], "selected": selected, "deferred": deferred,
            "reviews_waiting": review_waiting,
            "notice": "Advisory build batch only; review work still needs capacity and an independent host worker. Re-read before starting; no worker was launched."}


def overlaps(left, right):
    return any(a == b or a.startswith(b + "/") or b.startswith(a + "/") for a in left for b in right)


def dispatch_reason(s, t):
    if t["state"] != "ready" or t["blocked"]:
        return "not ready or explicitly blocked"
    waiting = [d for d in t["depends"] if s["tasks"][d]["state"] not in ACCEPTED or s["tasks"][d]["blocked"]]
    if waiting:
        return "dependencies not accepted: " + ", ".join(waiting)
    budget = resources(s)
    if budget["active"] >= budget["max_active"]:
        return "capacity full"
    reason = budget_reason(s, t["project"], t["estimate"])
    if reason:
        return reason
    for other in s["tasks"].values():
        if other["state"] == "in-progress" and not other["parked"] and overlaps(other["paths"], t["paths"]):
            return "path ownership overlaps " + other["id"]
    return None


def start_task(s, task_id, actor):
    t = get_task(s, task_id)
    actor = text(actor, "actual host actor/session ID")
    reason = dispatch_reason(s, t)
    if reason:
        raise CompanyError(reason)
    if actor_busy(s, actor):
        raise CompanyError("Actor already has active work")
    t.update(state="in-progress", actor=actor, remaining_estimate=t["estimate"], parked=False)
    if actor not in t["contributors"]:
        t["contributors"].append(actor)
    event(s, "task-started", task_id, {"actor": actor})
    return t


def actor_busy(s, actor):
    return any(not x["parked"] and ((x["state"] == "in-progress" and x["actor"] == actor) or
               (x.get("review_assignment") and x["review_assignment"]["actor"] == actor)) for x in s["tasks"].values())


def start_review(s, task_id, reviewer, estimate=1):
    t = get_task(s, task_id)
    reviewer = text(reviewer, "reviewer host session ID")
    estimate = units(estimate, "review estimate")
    if t["state"] != "review" or t["blocked"] or t.get("review_assignment"):
        raise CompanyError("Task is not available for review")
    if reviewer in t["contributors"]:
        raise CompanyError("A contributor cannot independently review this task")
    budget = resources(s)
    if budget["active"] >= budget["max_active"]:
        raise CompanyError("capacity full")
    reason = budget_reason(s, t["project"], estimate)
    if reason:
        raise CompanyError(reason)
    if actor_busy(s, reviewer):
        raise CompanyError("Actor already has active work")
    t["review_assignment"] = {"actor": reviewer, "estimate": estimate}
    event(s, "review-started", task_id, t["review_assignment"])
    return t


def checkpoint(s, task_id, note, blocked=False):
    t = get_task(s, task_id)
    if t["state"] in {"cancelled", "closed"}:
        raise CompanyError("Cannot checkpoint a terminal task")
    t["checkpoint"] = {"at": now(), "state": t["state"], "actor": t["actor"],
                       "review_assignment": copy.deepcopy(t.get("review_assignment")),
                       "submission": copy.deepcopy(t["submissions"][-1]) if t["submissions"] else None,
                       "paths": t["paths"], "next": text(note, "next action")}
    if blocked:
        t["blocked"] = text(note, "blocker")
    event(s, "checkpoint", task_id, {"state": t["state"], "blocked": bool(t["blocked"])})
    return t


def resume_task(s, task_id):
    t = get_task(s, task_id)
    if t["state"] in {"closed", "cancelled"}:
        raise CompanyError("Cannot resume a terminal task")
    if not t["checkpoint"]:
        raise CompanyError("No checkpoint to inspect; reconcile actual work before resuming")
    if t["parked"]:
        budget = resources(s)
        estimate = t["remaining_estimate"] if t["state"] == "in-progress" else t["review_assignment"]["estimate"]
        actor = t["actor"] if t["state"] == "in-progress" else t["review_assignment"]["actor"]
        if budget["active"] >= budget["max_active"]:
            raise CompanyError("capacity full")
        reason = budget_reason(s, t["project"], estimate)
        if reason:
            raise CompanyError(reason)
        if actor_busy(s, actor):
            raise CompanyError("Actor already has active work")
        if t["state"] == "in-progress":
            if any(s["tasks"][dep]["state"] not in ACCEPTED or s["tasks"][dep]["blocked"] for dep in t["depends"]):
                raise CompanyError("dependencies not accepted")
            for other in s["tasks"].values():
                if other["id"] != task_id and other["state"] == "in-progress" and not other["parked"] and overlaps(other["paths"], t["paths"]):
                    raise CompanyError("path ownership overlaps " + other["id"])
        t["parked"] = False
    t["blocked"] = None
    event(s, "resume-requested", task_id, {"state": t["state"], "next": t["checkpoint"]["next"]})
    return {"task": t, "notice": "State preserved. Inspect files, revision, host session and evidence before continuing; no worker was spawned."}


def submit_task(s, task_id, revision, artifact, evidence, actual=None):
    t = get_task(s, task_id)
    if t["state"] != "in-progress" or t["blocked"] or t["parked"]:
        raise CompanyError("Only unblocked active work can be submitted")
    if not REVISIONS.fullmatch(revision):
        raise CompanyError("revision must be a full lowercase Git SHA or sha256:<64 hex> artifact digest")
    evidence = text(evidence, "check evidence")
    amount = t["remaining_estimate"] if actual is None else units(actual, "actual units")
    t["submissions"].append({"revision": revision, "artifact": text(artifact, "artifact"), "evidence": evidence,
                              "actor": t["actor"], "at": now()})
    s["resource_entries"].append({"task": task_id, "units": amount, "basis": "estimate" if actual is None else "measured", "at": now()})
    t["state"] = "review"
    event(s, "task-submitted", task_id, {"revision": revision})
    return t


def review_task(s, task_id, reviewer, verdict, revision, evidence, actual=None):
    t = get_task(s, task_id)
    if t["state"] != "review" or t["blocked"] or t["parked"]:
        raise CompanyError("Task must be in unblocked review")
    reviewer = text(reviewer, "reviewer host session ID")
    if reviewer in t["contributors"]:
        raise CompanyError("A contributor cannot record an independent review of this task")
    if not t.get("review_assignment") or t["review_assignment"]["actor"] != reviewer:
        raise CompanyError("Start a review assignment for this reviewer before recording its result")
    if verdict not in {"PASS", "CHANGES"}:
        raise CompanyError("Verdict must be PASS or CHANGES")
    if revision != t["submissions"][-1]["revision"]:
        raise CompanyError("Review revision does not match the latest submission")
    record = {"reviewer": reviewer, "verdict": verdict, "revision": revision, "evidence": text(evidence, "review evidence"),
              "contributors": list(t["contributors"]), "at": now()}
    amount = t["review_assignment"]["estimate"] if actual is None else units(actual, "actual units")
    s["resource_entries"].append({"task": task_id, "phase": "review", "units": amount,
                                  "basis": "estimate" if actual is None else "measured", "at": now()})
    t["review_assignment"] = None
    t["reviews"].append(record)
    t["state"] = "verified" if verdict == "PASS" else "ready"
    event(s, "task-reviewed", task_id, record)
    return t


def park_task(s, task_id, note, spent, basis="estimate"):
    t = get_task(s, task_id)
    spent = units(spent, "incurred effort")
    if basis not in {"estimate", "measured"}:
        raise CompanyError("Invalid effort basis")
    if t["parked"] or not (t["state"] == "in-progress" or t.get("review_assignment")):
        raise CompanyError("Only an active assignment can be parked")
    checkpoint(s, task_id, note, blocked=True)
    if t["state"] == "in-progress":
        t["remaining_estimate"] = max(0, t["remaining_estimate"] - spent)
    else:
        t["review_assignment"]["estimate"] = max(0, t["review_assignment"]["estimate"] - spent)
    s["resource_entries"].append({"task": task_id, "phase": t["state"], "units": spent, "basis": basis, "at": now()})
    t["parked"] = True
    event(s, "assignment-parked", task_id, {"spent": spent, "basis": basis, "state": t["state"]})
    return t


def handoff(s, task_id, actor, evidence):
    t = get_task(s, task_id)
    actor = text(actor, "replacement host session ID")
    evidence = text(evidence, "handoff reconciliation evidence")
    if actor_busy(s, actor):
        raise CompanyError("Replacement actor already has active work")
    if t["state"] == "in-progress":
        old_actor = t["actor"]
        t["actor"] = actor
        if actor not in t["contributors"]:
            t["contributors"].append(actor)
    elif t.get("review_assignment"):
        if actor in t["contributors"]:
            raise CompanyError("Contributor cannot take over independent review")
        old_actor = t["review_assignment"]["actor"]
        t["review_assignment"]["actor"] = actor
    else:
        raise CompanyError("Only an active assignment can be handed off")
    event(s, "assignment-handed-off", task_id, {"from": old_actor, "to": actor, "evidence": evidence})
    return t


def transition(s, task_id, state, evidence):
    t = get_task(s, task_id)
    allowed = {"verified": {"integrated", "closed"}, "integrated": {"released", "closed"}, "released": {"closed"}}
    if t["blocked"] or state not in allowed.get(t["state"], set()):
        raise CompanyError("Invalid transition; verification and relevant evidence are required")
    event(s, "task-transition", task_id, {"from": t["state"], "to": state, "evidence": text(evidence, "transition evidence")})
    t["state"] = state
    return t


def report(s):
    lines = [f"# {s['name']}", "", s["mission"], "", "## Resources", "", json.dumps(resources(s), sort_keys=True), "", "## Delivery", ""]
    for project in s["projects"].values():
        lines.append(f"- {project['id']} {project['title']} — accountable: {project['owner']}")
        for t in s["tasks"].values():
            if t["project"] == project["id"]:
                blocker = t["blocked"]
                if t["state"] == "ready" and not blocker:
                    blocker = dispatch_reason(s, t)
                lines.append(f"  - {t['id']} [{t['state']}] {t['title']} ({t['role']}); actor: {t['actor'] or 'unassigned'}" + (f"; blocked: {blocker}" if blocker else ""))
    lines += ["", "## Decisions", ""]
    lines += [f"- {d['id']}: {d['question']} — {d['outcome']} (source: {d['source']})" for d in s["decisions"]] or ["- No decisions recorded."]
    lines += ["", "Evidence and session IDs are operator attestations. This ledger does not execute workers, checks, releases, purchases or external messages."]
    return "\n".join(lines)
