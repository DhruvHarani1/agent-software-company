import contextlib
import io
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.github import GhError, api_pages, gh_json
import claims
import radar


def event(cid, actor="alice", org="org-a", kind="claim", at="2026-11-11T12:00:00Z", extra="", until="2026-11-11T14:00:00Z"):
    attrs = " lease_until=" + until if kind == "claim" else ""
    body = "Task: repair\nPlan: repair then test" if kind == "claim" else "Task: repair\nState left: branch pushed\nWhy released: stale lease"
    return {"id": cid, "user": {"login": actor}, "created_at": at,
            "body": f"[AGENT-MSG v1] type={kind} from={org}/dev to=* ref=#1{attrs}{extra}\n{body}"}


class GithubTests(unittest.TestCase):
    def test_all_pages_flattened_and_non_array_failure(self):
        with patch("lib.github.gh_json", return_value=[[{"id": 1}], [{"id": 2}]]):
            self.assertEqual([x["id"] for x in api_pages("repos/o/r/issues")], [1, 2])
        with patch("lib.github.gh_json", return_value=[[{"id": 1}], {"error": "truncated"}]):
            with self.assertRaises(GhError):
                api_pages("repos/o/r/issues")

    def test_cli_failures_are_never_empty_success(self):
        with patch("lib.github.subprocess.run", return_value=SimpleNamespace(returncode=1, stdout="[]")):
            with self.assertRaises(GhError):
                gh_json(["api", "user"])
        with patch("lib.github.subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 30)):
            with self.assertRaises(GhError):
                gh_json(["api", "user"])
        with patch("lib.github.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="not JSON")):
            with self.assertRaises(GhError):
                gh_json(["api", "user"])


class ClaimsTests(unittest.TestCase):
    now = datetime(2026, 11, 11, 13, tzinfo=timezone.utc)
    bindings = {"org-a": {"alice"}, "org-b": {"bob"}}

    def reduce(self, events):
        return claims.evaluate_claims(events, 1, self.bindings, self.now)

    def test_spoofed_sender_cannot_release_or_renew_other_actor(self):
        rows, notes = self.reduce([event(1), event(2, actor="mallory", kind="release"), event(3, actor="mallory", extra=" claim_id=1")])
        self.assertEqual([row["id"] for row in rows], [1])
        self.assertTrue(notes)

    def test_owner_renews_then_releases_by_id(self):
        rows, notes = self.reduce([event(1), event(2, at="2026-11-11T13:00:00Z", extra=" claim_id=1", until="2026-11-11T16:00:00Z"),
                                   event(3, kind="release", at="2026-11-11T13:30:00Z", extra=" claim_id=1")])
        self.assertEqual(rows, [])
        self.assertEqual(notes, [])

    def test_pre_expiry_renewal_preserves_existing_priority(self):
        for extra in ("", " claim_id=1"):
            with self.subTest(extra=extra):
                rows, notes = self.reduce([
                    event(1),
                    event(2, actor="bob", org="org-b", at="2026-11-11T12:30:00Z", until="2026-11-11T15:00:00Z"),
                    event(3, at="2026-11-11T13:00:00Z", extra=extra, until="2026-11-11T16:00:00Z"),
                ])
                self.assertEqual([1, 2], [row["id"] for row in rows])
                self.assertEqual(rows[0]["latest_id"], 3)
                self.assertEqual(rows[0]["created"], datetime(2026, 11, 11, 12, tzinfo=timezone.utc))
                self.assertTrue(any("earliest verified event #1 wins" in note for note in notes))

    def test_post_expiry_fresh_claim_does_not_jump_a_competitor(self):
        rows, notes = claims.evaluate_claims([
            event(1, until="2026-11-11T13:00:00Z"),
            event(2, actor="bob", org="org-b", at="2026-11-11T13:10:00Z", until="2026-11-11T15:00:00Z"),
            event(3, at="2026-11-11T13:30:00Z", until="2026-11-11T16:00:00Z"),
        ], 1, self.bindings, datetime(2026, 11, 11, 14, tzinfo=timezone.utc))
        self.assertEqual([2, 3], [row["id"] for row in rows])
        self.assertEqual(rows[1]["created"], datetime(2026, 11, 11, 13, 30, tzinfo=timezone.utc))
        self.assertEqual(["live", "live"], [row["state"] for row in rows])
        self.assertTrue(any("earliest verified event #2 wins" in note for note in notes))

    def test_explicit_renewal_at_or_after_expiry_is_rejected(self):
        for renewal_at in ("2026-11-11T13:00:00Z", "2026-11-11T13:30:00Z"):
            with self.subTest(renewal_at=renewal_at):
                rows, notes = claims.evaluate_claims([
                    event(1, until="2026-11-11T13:00:00Z"),
                    event(2, at=renewal_at, extra=" claim_id=1", until="2026-11-11T16:00:00Z"),
                ], 1, self.bindings, datetime(2026, 11, 11, 14, tzinfo=timezone.utc))
                self.assertEqual([1], [row["id"] for row in rows])
                self.assertEqual(rows[0]["latest_id"], 1)
                self.assertEqual(rows[0]["state"], "STALE")
                self.assertTrue(any("expired claim cannot be renewed" in note for note in notes))

    def test_stale_takeover_targets_only_expired_claim(self):
        release = event(2, actor="bob", org="org-b", kind="release", at="2026-11-11T15:00:00Z", extra=" claim_id=1")
        self.assertEqual(self.reduce([event(1), release])[0], [])
        early = event(2, actor="bob", org="org-b", kind="release", at="2026-11-11T13:00:00Z", extra=" claim_id=1")
        self.assertEqual(len(self.reduce([event(1), early])[0]), 1)
        unverified = event(2, actor="guest", org="unknown", kind="release", at="2026-11-11T15:00:00Z", extra=" claim_id=1")
        self.assertEqual(len(self.reduce([event(1), unverified])[0]), 1)

    def test_unknown_identity_is_not_exclusive_and_naive_lease_does_not_crash(self):
        rows, notes = self.reduce([event(1, actor="guest", org="unknown"), event(2, until="2026-11-11T15:00:00")])
        self.assertEqual(rows[0]["state"], "UNVERIFIED")
        self.assertTrue(notes)

    def test_competing_claims_have_stable_order_and_cannot_erase_each_other(self):
        rows, notes = self.reduce([event(2, actor="bob", org="org-b"), event(1)])
        self.assertEqual([row["id"] for row in rows], [1, 2])
        self.assertTrue(any("earliest" in note for note in notes))

    def test_complete_issue_and_comment_pages_used(self):
        with patch("claims.api_pages", side_effect=[[{"number": 1, "title": "repair"}], [event(1)]]):
            rows, _ = claims.scan("owner/repo", self.bindings, self.now)
            self.assertEqual(rows[0]["issue"], 1)
        with patch("claims.api_pages", side_effect=GhError("page 2 unavailable")):
            with contextlib.redirect_stderr(io.StringIO()) as output:
                with patch("claims.load_bindings", return_value=(self.bindings, [])):
                    self.assertEqual(claims.main(["--repo", "owner/repo"]), 2)
            self.assertIn("ownership unknown", output.getvalue())


class RadarTests(unittest.TestCase):
    def api(self, endpoint):
        if "collaborators" in endpoint:
            return [{"login": "alice", "permissions": {"push": True}}]
        if "/commits" in endpoint or "/issues/comments" in endpoint:
            return []
        if "/pulls?" in endpoint:
            return [{"number": 9, "user": {"login": "alice"}, "body": "Agent-Org: peer", "title": "repair"}]
        if "/pulls/9/files" in endpoint:
            return [{"filename": "src/last-page.py"}]
        raise AssertionError(endpoint)

    def json(self, args):
        return {"login": "me"} if args[-1] == "user" else {"changed_files": 1}

    def test_pr_files_overlap_and_permission_failure_is_unknown(self):
        def api(endpoint):
            if "collaborators" in endpoint:
                raise GhError("no permission")
            return self.api(endpoint)
        with patch("radar.api_pages", side_effect=api), patch("radar.gh_json", side_effect=self.json):
            report = radar.scan("owner/repo", "mine")
        self.assertEqual(report["coverage"], "partial")
        self.assertEqual(report["teams"]["peer"]["tier"], "unknown")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            radar.render(report, ["src/**"])
        self.assertIn("OVERLAP", output.getvalue())

    def test_file_count_mismatch_is_partial_and_not_all_clear(self):
        with patch("radar.api_pages", side_effect=self.api), patch("radar.gh_json", side_effect=lambda args: {"login": "me"} if args[-1] == "user" else {"changed_files": 3001}):
            report = radar.scan("owner/repo", "mine")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            radar.render(report, ["unseen/**"])
        self.assertEqual(report["coverage"], "partial")
        self.assertIn("overlap unknown", output.getvalue())
        self.assertNotIn("no overlap observed", output.getvalue())

    def test_outgoing_hello_matches_exact_peer_not_substring(self):
        def api(endpoint):
            if "/issues/comments" in endpoint:
                return [{"user": {"login": "me"}, "body": "[AGENT-MSG v1] type=hello from=mine/boss to=peer-extra ref=#presence\nWho: us\nHow to talk: AAP\nAreas we touch: docs\nTrust: no authority"}]
            return self.api(endpoint)
        with patch("radar.api_pages", side_effect=api), patch("radar.gh_json", side_effect=self.json):
            self.assertFalse(radar.scan("owner/repo", "mine")["teams"]["peer"]["greeted"])


if __name__ == "__main__":
    unittest.main()
