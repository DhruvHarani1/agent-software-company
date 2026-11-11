#!/usr/bin/env python3
"""Local company planning/coordination CLI. Standard library; no remote side effects."""
from __future__ import annotations

import argparse
import json
import sys
from lib import company_state as c


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", default=".", help="Existing project directory; state lives in .agent-company/")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Preview company configuration; --apply initializes local state only")
    init.add_argument("--name", default="Agent IT Company")
    init.add_argument("--mission", default="Deliver verified software outcomes within the owner's mandate.")
    init.add_argument("--preset", choices=c.PRESETS, default="startup")
    init.add_argument("--max-active", type=int)
    init.add_argument("--budget", type=float, default=100, help="Effort units, not currency or measured tokens")
    init.add_argument("--apply", action="store_true")
    org = sub.add_parser("org", help="Inspect role catalog; uses company snapshot if initialized")
    org.add_argument("--role")
    project = sub.add_parser("project")
    ps = project.add_subparsers(dest="operation", required=True)
    plan = ps.add_parser("plan", help="Record a project goal; does not invent or execute tasks")
    plan.add_argument("title")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--owner", default="md")
    task = sub.add_parser("task")
    ts = task.add_subparsers(dest="operation", required=True)
    add = ts.add_parser("add")
    add.add_argument("title")
    add.add_argument("--project", required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--acceptance", action="append", required=True)
    add.add_argument("--depends", action="append", default=[])
    add.add_argument("--path", action="append", default=[])
    add.add_argument("--estimate", type=float, default=1)
    ts.add_parser("queue", help="List readiness, dependency, capacity and budget reasons")
    show = ts.add_parser("show")
    show.add_argument("id")
    start = ts.add_parser("start", help="Record actual host assignment; does not spawn an agent")
    start.add_argument("id")
    start.add_argument("--actor", required=True)
    submit = ts.add_parser("submit")
    submit.add_argument("id")
    submit.add_argument("--revision", required=True)
    submit.add_argument("--artifact", required=True)
    submit.add_argument("--evidence", required=True)
    submit.add_argument("--actual", type=float)
    check = ts.add_parser("checkpoint")
    check.add_argument("id")
    check.add_argument("--next", required=True)
    check.add_argument("--blocked", action="store_true")
    park = ts.add_parser("park", help="Record a stopped worker; release capacity while preserving phase and incurred effort")
    park.add_argument("id")
    park.add_argument("--next", required=True)
    park.add_argument("--spent", type=float, required=True)
    park.add_argument("--basis", choices=["estimate", "measured"], default="estimate")
    move = ts.add_parser("transition", help="Record verified integration/release/closure, not execute it")
    move.add_argument("id")
    move.add_argument("state", choices=["integrated", "released", "closed"])
    move.add_argument("--evidence", required=True)
    transfer = ts.add_parser("handoff")
    transfer.add_argument("id")
    transfer.add_argument("--actor", required=True)
    transfer.add_argument("--evidence", required=True)
    review = sub.add_parser("review")
    rs = review.add_subparsers(dest="operation", required=True)
    begin = rs.add_parser("start")
    begin.add_argument("id")
    begin.add_argument("--reviewer", required=True)
    begin.add_argument("--estimate", type=float, default=1)
    finish = rs.add_parser("finish")
    finish.add_argument("id")
    finish.add_argument("--reviewer", required=True)
    finish.add_argument("--verdict", choices=["PASS", "CHANGES"], required=True)
    finish.add_argument("--revision", required=True)
    finish.add_argument("--evidence", required=True)
    finish.add_argument("--actual", type=float)
    resume = sub.add_parser("resume", help="Clear a reconciled blocker, preserving the delivery stage")
    resume.add_argument("id")
    decision = sub.add_parser("decision", help="Record a sourced decision, not create authorization")
    decision.add_argument("question")
    decision.add_argument("--outcome", required=True)
    decision.add_argument("--source", required=True)
    decision.add_argument("--owner", default="md")
    for command in ("status", "budget", "report"):
        sub.add_parser(command)
    return p


def execute(a):
    store = c.Store(a.workspace)
    if a.command == "init":
        state = c.initial_state(a.name, a.mission, a.preset, a.max_active, a.budget)
        if a.apply:
            return store.write(initial=state)
        return {"status": "preview-only", "name": state["name"], "mission": state["mission"], "preset": state["preset"],
                "limits": state["limits"], "departments": len(state["organization"]["departments"]),
                "roles": len(state["organization"]["roles"]), "destination": str(store.path),
                "notice": "Use --apply to write local state. No instruction files or external services are changed."}
    if a.command == "org":
        org = store.load()["organization"] if store.path.exists() else c.organization()
        if a.role:
            if a.role not in org["roles"]:
                raise c.CompanyError("Unknown role")
            return org["roles"][a.role]
        return org
    if a.command in {"status", "budget", "report"}:
        state = store.load()
        if a.command == "budget":
            return c.resources(state)
        if a.command == "report":
            return c.report(state)
        return {"name": state["name"], "revision": state["revision"], "projects": list(state["projects"].values()),
                "tasks": list(state["tasks"].values()), "resources": c.resources(state)}
    if a.command == "task" and a.operation in {"show", "queue"}:
        s = store.load()
        if a.operation == "show":
            return c.get_task(s, a.id)
        return [{"id": t["id"], "role": t["role"], "state": t["state"], "dispatchable": c.dispatch_reason(s, t) is None,
                 "reason": c.dispatch_reason(s, t)} for t in s["tasks"].values()]

    def mutate(s):
        if a.command == "project":
            return c.add_project(s, a.title, a.goal, a.owner)
        if a.command == "resume":
            return c.resume_task(s, a.id)
        if a.command == "decision":
            c.require_role(s, a.owner)
            result = {"id": f"D{len(s['decisions']) + 1:04d}", "question": c.text(a.question, "question"),
                      "outcome": c.text(a.outcome, "outcome"), "source": c.text(a.source, "source"), "owner": a.owner, "at": c.now()}
            s["decisions"].append(result)
            c.event(s, "decision-recorded", result["id"], result)
            return result
        if a.command == "review":
            if a.operation == "start":
                return c.start_review(s, a.id, a.reviewer, a.estimate)
            return c.review_task(s, a.id, a.reviewer, a.verdict, a.revision, a.evidence, a.actual)
        if a.operation == "add":
            return c.add_task(s, a.project, a.title, a.role, a.acceptance, a.depends, a.path, a.estimate)
        if a.operation == "start":
            return c.start_task(s, a.id, a.actor)
        if a.operation == "submit":
            return c.submit_task(s, a.id, a.revision, a.artifact, a.evidence, a.actual)
        if a.operation == "checkpoint":
            return c.checkpoint(s, a.id, a.next, a.blocked)
        if a.operation == "park":
            return c.park_task(s, a.id, a.next, a.spent, a.basis)
        if a.operation == "handoff":
            return c.handoff(s, a.id, a.actor, a.evidence)
        return c.transition(s, a.id, a.state, a.evidence)
    return store.write(mutate)


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        result = execute(a)
        print(result if isinstance(result, str) else json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (c.CompanyError, OSError) as exc:
        print(f"company: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
