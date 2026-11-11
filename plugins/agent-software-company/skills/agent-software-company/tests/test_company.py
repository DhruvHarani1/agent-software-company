"""Observable coordination, resource, persistence and command-line behavior."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from lib import company_state as c

REV = "a" * 40


class CompanyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.s = c.initial_state("Fixture Company", "Deliver an integrated portal", budget=10)
        self.project = c.add_project(self.s, "Portal", "Customer can see their own account")["id"]

    def task(self, title="API", role="backend-engineer", **kw):
        return c.add_task(self.s, self.project, title, role, ["Expected behavior is demonstrated"], **kw)["id"]

    def submit(self, task_id, actor="builder"):
        c.start_task(self.s, task_id, actor)
        c.submit_task(self.s, task_id, REV, "test-output.txt", "Fixture checks: 4 passed")

    def verify(self, task_id):
        c.start_review(self.s, task_id, "reviewer", estimate=1)
        c.review_task(self.s, task_id, "reviewer", "PASS", REV, "Independent fixture check: 4 passed")

    def test_full_stack_dependency_and_independent_acceptance(self):
        api = self.task(paths=["server/api"], estimate=2)
        ui = self.task("Account UI", "frontend-engineer", depends=[api], paths=["client/account"], estimate=2)
        with self.assertRaisesRegex(c.CompanyError, "dependencies"):
            c.start_task(self.s, ui, "frontend-session")
        self.submit(api)
        with self.assertRaisesRegex(c.CompanyError, "contributor"):
            c.start_review(self.s, api, "builder")
        c.start_review(self.s, api, "reviewer")
        with self.assertRaisesRegex(c.CompanyError, "revision"):
            c.review_task(self.s, api, "reviewer", "PASS", "b" * 40, "Wrong revision")
        c.review_task(self.s, api, "reviewer", "PASS", REV, "Independent 4/4")
        c.start_task(self.s, ui, "frontend-session")
        c.submit_task(self.s, ui, REV, "ui-checks.txt", "UI and API integration: 3/3")
        self.verify(ui)
        c.transition(self.s, ui, "integrated", "Combined revision passes integration suite")
        c.transition(self.s, ui, "closed", "Local acceptance complete; no external deployment requested")
        self.assertEqual(self.s["tasks"][ui]["state"], "closed")
        self.assertEqual(c.resources(self.s)["accounted"], 6)
        self.assertEqual(c.resources(self.s)["measured"], 0)
        self.assertEqual(c.resources(self.s)["currency_cost"], "unknown")

    def test_shared_paths_capacity_and_budget_are_enforced(self):
        a = self.task(paths=["shared"], estimate=4)
        b = self.task(paths=["SHARED/config.json"], estimate=4)
        c.start_task(self.s, a, "a")
        with self.assertRaisesRegex(c.CompanyError, "overlaps"):
            c.start_task(self.s, b, "b")
        self.s["tasks"][b]["paths"] = ["elsewhere"]
        c.start_task(self.s, b, "b")
        third = self.task(estimate=4)
        with self.assertRaisesRegex(c.CompanyError, "capacity"):
            c.start_task(self.s, third, "c")
        c.submit_task(self.s, a, REV, "artifact", "actual check output", actual=6)
        with self.assertRaisesRegex(c.CompanyError, "budget"):
            c.start_review(self.s, a, "qa")
        self.assertEqual(c.resources(self.s)["remaining"], 0)

    def test_checkpoint_and_handoff_preserve_phase_and_authorship(self):
        task = self.task()
        c.start_task(self.s, task, "old-session")
        c.checkpoint(self.s, task, "Inspect API test result then finish implementation", blocked=True)
        self.assertEqual(self.s["tasks"][task]["state"], "in-progress")
        c.handoff(self.s, task, "replacement-session", "Inspected dirty files; old host session confirmed stopped")
        c.resume_task(self.s, task)
        c.submit_task(self.s, task, REV, "artifact", "tests pass")
        with self.assertRaisesRegex(c.CompanyError, "contributor"):
            c.start_review(self.s, task, "old-session")
        c.start_review(self.s, task, "review-session")
        c.checkpoint(self.s, task, "Re-run failing integration scenario", blocked=True)
        result = c.resume_task(self.s, task)
        self.assertEqual(result["task"]["state"], "review")
        self.assertEqual(result["task"]["checkpoint"]["review_assignment"]["actor"], "review-session")

    def test_changes_require_new_submission_and_new_review(self):
        task = self.task()
        self.submit(task)
        c.start_review(self.s, task, "reviewer")
        c.review_task(self.s, task, "reviewer", "CHANGES", REV, "Forbidden role can access endpoint")
        with self.assertRaises(c.CompanyError):
            c.transition(self.s, task, "closed", "Cannot skip checks")
        c.start_task(self.s, task, "builder")
        c.submit_task(self.s, task, "b" * 40, "artifact", "Allowed and forbidden role checks pass")
        self.assertEqual(self.s["tasks"][task]["state"], "review")

    def test_terminal_task_cannot_resume_old_checkpoint(self):
        task = self.task()
        c.start_task(self.s, task, "builder")
        c.checkpoint(self.s, task, "Finish implementation")
        c.submit_task(self.s, task, REV, "artifact", "Checks pass")
        self.verify(task)
        c.transition(self.s, task, "closed", "Accepted local result")
        with self.assertRaisesRegex(c.CompanyError, "terminal"):
            c.resume_task(self.s, task)

    def test_reviewer_can_contribute_later_but_cannot_review_own_rework(self):
        task = self.task()
        self.submit(task)
        c.start_review(self.s, task, "reviewer")
        c.review_task(self.s, task, "reviewer", "CHANGES", REV, "Needs a targeted correction")
        c.start_task(self.s, task, "reviewer")
        c.validate(self.s)
        c.submit_task(self.s, task, "b" * 40, "artifact", "Correction tested")
        with self.assertRaisesRegex(c.CompanyError, "contributor"):
            c.start_review(self.s, task, "reviewer")
        c.start_review(self.s, task, "another-evaluator")
        c.review_task(self.s, task, "another-evaluator", "PASS", "b" * 40, "Independent rework verification")
        c.validate(self.s)

    def test_invalid_estimates_and_owned_paths(self):
        for value in [float("nan"), float("inf"), -1, True]:
            with self.assertRaises(c.CompanyError):
                self.task(estimate=value)
        for path in ["../other", "C:/outside", "/root", "**/*.py"]:
            with self.assertRaises(c.CompanyError):
                self.task(paths=[path])

    def test_full_catalog_is_available_without_activating_workers(self):
        org = self.s["organization"]
        self.assertEqual(len(org["departments"]), 18)
        for role in ["ceo", "md", "cto", "cfo", "frontend-engineer", "backend-engineer", "devops-engineer", "qa-tester"]:
            self.assertIn(role, org["roles"])
        self.assertEqual(c.resources(self.s)["active"], 0)

    def test_park_releases_slot_preserves_effort_and_resume_rechecks(self):
        self.s["limits"]["max_active"] = 1
        a = self.task(estimate=4, paths=["api"])
        b = self.task(estimate=1, paths=["docs"])
        c.start_task(self.s, a, "builder")
        c.park_task(self.s, a, "Confirmed worker stopped; waiting for contract", 1, "measured")
        self.assertEqual(c.resources(self.s)["reserved"], 0)
        self.assertEqual(c.resources(self.s)["accounted"], 1)
        c.start_task(self.s, b, "writer")
        with self.assertRaisesRegex(c.CompanyError, "capacity"):
            c.resume_task(self.s, a)
        c.submit_task(self.s, b, REV, "docs", "Docs checked")
        c.resume_task(self.s, a)
        self.assertEqual(c.resources(self.s)["reserved"], 3)
        c.submit_task(self.s, a, REV, "api", "Tests passed")
        self.assertEqual(c.resources(self.s)["accounted"], 5)
        c.validate(self.s)

    def test_review_handoff_does_not_rewrite_history(self):
        task = self.task()
        self.submit(task)
        c.start_review(self.s, task, "reviewer-a")
        original = copy.deepcopy(self.s["events"])
        c.handoff(self.s, task, "reviewer-b", "Prior review session ended; files reconciled")
        self.assertEqual(self.s["events"][:-1], original)
        self.assertEqual(self.s["events"][-2]["detail"]["actor"], "reviewer-a")

    def test_corrupt_workflow_and_accounting_fail_validation(self):
        task = self.task()
        original = copy.deepcopy(self.s)
        self.s["tasks"][task]["state"] = "verified"
        with self.assertRaisesRegex(c.CompanyError, "submission"):
            c.validate(self.s)
        self.s = original
        self.s["resource_entries"].append({"units": 1})
        with self.assertRaises(c.CompanyError):
            c.validate(self.s)

    def test_corrupt_company_decision_and_checkpoint_fail_cleanly(self):
        task = self.task()
        base = copy.deepcopy(self.s)
        del self.s["name"]
        with self.assertRaises(c.CompanyError):
            c.validate(self.s)
        self.s = copy.deepcopy(base)
        self.s["decisions"] = [{"id": "D0001"}]
        with self.assertRaises(c.CompanyError):
            c.validate(self.s)
        self.s = copy.deepcopy(base)
        self.s["tasks"][task]["checkpoint"] = {"at": c.now()}
        with self.assertRaises(c.CompanyError):
            c.validate(self.s)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="agent-company-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = c.Store(self.root)
        self.initial = c.initial_state("Fixture", "Prove persistence")

    def test_idempotent_init_preserves_existing_work(self):
        self.store.write(initial=self.initial)
        self.store.write(lambda s: c.add_project(s, "Work", "Keep this"))
        before = self.store.path.read_bytes()
        result = self.store.write(initial=c.initial_state("Other", "Must not overwrite"))
        self.assertEqual(result["status"], "already-initialized")
        self.assertEqual(before, self.store.path.read_bytes())

    def test_failed_write_preserves_state_and_cleans_own_lock(self):
        self.store.write(initial=self.initial)
        before = self.store.path.read_bytes()
        with patch.object(c.os, "replace", side_effect=OSError("simulated full disk")):
            with self.assertRaises(OSError):
                self.store.write(lambda s: c.add_project(s, "Unsaved", "Must not be partly saved"))
        self.assertEqual(before, self.store.path.read_bytes())
        self.assertFalse(self.store.lock.exists())

    def test_lock_and_corruption_never_reset_work(self):
        self.store.write(initial=self.initial)
        self.store.lock.write_text("other writer", encoding="utf-8")
        with self.assertRaisesRegex(c.CompanyError, "locked"):
            self.store.write(lambda s: None)
        self.store.lock.unlink()
        self.store.path.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(c.CompanyError, "valid JSON"):
            self.store.load()

    def test_cli_preview_and_docs_only_work_need_no_external_service(self):
        cli = [sys.executable, "-B", str(SCRIPTS / "company.py"), "--workspace", str(self.root)]
        preview = subprocess.run(cli + ["init", "--name", "Docs"], capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(self.store.directory.exists())
        for args in [
            ["init", "--name", "Docs", "--apply"],
            ["project", "plan", "Documentation", "--goal", "Clarify setup"],
            ["task", "add", "Edit setup", "--project", "P0001", "--role", "technical-writer", "--acceptance", "Setup steps are accurate", "--path", "README.md"],
            ["task", "start", "T0001", "--actor", "host-writer"],
            ["task", "submit", "T0001", "--revision", "sha256:" + "1" * 64, "--artifact", "README.md", "--evidence", "Instructions exercised locally"],
            ["review", "start", "T0001", "--reviewer", "host-reviewer"],
            ["review", "finish", "T0001", "--reviewer", "host-reviewer", "--verdict", "PASS", "--revision", "sha256:" + "1" * 64, "--evidence", "Independent instructions check"],
            ["task", "transition", "T0001", "closed", "--evidence", "Local document accepted"],
            ["report"],
        ]:
            result = subprocess.run(cli + args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[closed]", result.stdout)
        self.assertEqual(self.store.load()["tasks"]["T0001"]["state"], "closed")


if __name__ == "__main__":
    unittest.main()
