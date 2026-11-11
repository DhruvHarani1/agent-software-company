"""Inbox delivery regressions; all GitHub responses are local fixtures."""
import argparse
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import inbox
from lib.github import GhError


NOW = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)


def comment(number=1, *, at=NOW, to="org-a/qa", sender="org-b/builder", extra=""):
    return {
        "id": number,
        "created_at": inbox.timestamp(at),
        "updated_at": inbox.timestamp(at),
        "html_url": f"https://github.com/owner/repo/issues/1#issuecomment-{number}",
        "body": f"[AGENT-MSG v1] type=question from={sender} to={to} ref=#1\n"
                "Question: Verify the contract?\nWhy it matters: Integration is pending.\n"
                "Recommendation: Review the supplied artifact.\nNeeded by: Next turn.\n" + extra,
    }


class InboxTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="inbox-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "state"

    def args(self, **overrides):
        values = dict(repo="owner/repo", org="org-a", agent="qa", since=None,
                      ack=False, no_save=False, state_dir=str(self.root))
        values.update(overrides)
        return argparse.Namespace(**values)

    def state_path(self, args=None):
        args = args or self.args()
        return inbox.state_path(args.state_dir, inbox.make_scope(args.repo, args.org, args.agent))

    def run_inbox(self, comments=(), *, args=None, now=NOW):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(inbox, "api_pages", return_value=list(comments)), patch.object(inbox, "utc_now", return_value=now):
            result = inbox.run(args or self.args(), output, errors)
        return result, output.getvalue(), errors.getvalue()

    def test_default_peek_displays_full_body_without_creating_state(self):
        item = comment(extra="Long evidence: " + "artifact detail " * 200)
        result, output, _ = self.run_inbox([item])
        self.assertEqual([item["id"]], [entry["id"] for entry in result])
        self.assertIn(item["body"], output)
        self.assertIn("nothing acknowledged", output)
        self.assertFalse(self.root.exists())

    def test_ack_deduplicates_overlap_and_peek_never_changes_state(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        before = self.state_path().read_bytes()
        result, _, _ = self.run_inbox([comment()], now=NOW + timedelta(seconds=10))
        self.assertEqual([], result)
        self.assertEqual(before, self.state_path().read_bytes())

    def test_midfetch_arrival_remains_eligible_on_next_read(self):
        initial = comment(at=NOW - timedelta(seconds=3))
        arriving = comment(2, at=NOW + timedelta(seconds=1))
        self.run_inbox([initial], args=self.args(ack=True), now=NOW)
        data = json.loads(self.state_path().read_text())
        self.assertEqual(initial["updated_at"], data["cursor"])
        endpoints = []

        def fetch(endpoint):
            endpoints.append(endpoint)
            since = inbox.parse_timestamp(parse_qs(urlsplit(endpoint).query)["since"][0])
            return [item for item in (initial, arriving) if inbox.parse_timestamp(item["updated_at"]) > since]

        with patch.object(inbox, "api_pages", side_effect=fetch), patch.object(inbox, "utc_now", return_value=NOW + timedelta(seconds=4)):
            result = inbox.run(self.args(ack=True), io.StringIO(), io.StringIO())
        self.assertEqual([2], [item["id"] for item in result])
        self.assertIn(inbox.timestamp(NOW - timedelta(seconds=3) - inbox.OVERLAP), endpoints[0])

    def test_same_timestamp_different_id_is_not_skipped(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        result, _, _ = self.run_inbox([comment(), comment(2)], now=NOW + timedelta(seconds=1))
        self.assertEqual([2], [item["id"] for item in result])

    def test_edited_living_message_and_same_second_content_change_are_delivered(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        edited = comment(extra="Additional evidence after the first delivery.")
        result, _, _ = self.run_inbox([edited], args=self.args(ack=True), now=NOW + timedelta(seconds=1))
        self.assertEqual([1], [item["id"] for item in result])
        edited["updated_at"] = inbox.timestamp(NOW + timedelta(seconds=2))
        edited["body"] += "\nAnother update."
        result, _, _ = self.run_inbox([edited], now=NOW + timedelta(seconds=3))
        self.assertEqual([1], [item["id"] for item in result])

    def test_state_is_separate_for_repo_org_agent_and_org_digest(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        scopes = [self.args(repo="owner/other"), self.args(org="org-c"),
                  self.args(agent="dev"), self.args(agent=None)]
        for args in scopes:
            with self.subTest(args=args):
                item = comment(to=args.org if args.agent is None else f"{args.org}/{args.agent}")
                result, _, _ = self.run_inbox([item], args=args)
                self.assertEqual([1], [entry["id"] for entry in result])
                self.assertNotEqual(self.state_path(), self.state_path(args))
        self.assertEqual(self.state_path(), self.state_path(self.args(repo="OWNER/REPO")))

    def test_same_org_handoffs_are_delivered_except_explicit_self_agent(self):
        items = [comment(1, sender="org-a/backend"),
                 comment(2, sender="org-a/qa"),
                 comment(3, to="org-a/dev"), comment(4, to="*")]
        result, _, _ = self.run_inbox(items)
        self.assertEqual([1, 4], [entry["id"] for entry in result])
        result, _, _ = self.run_inbox(items, args=self.args(agent=None))
        self.assertEqual([1, 2, 3, 4], [entry["id"] for entry in result])

    def test_final_page_message_is_delivered_using_shared_pagination(self):
        first_page = [comment(i, to="unrelated") for i in range(1, 101)]
        last_page = [comment(101)]
        with patch("lib.github.gh_json", return_value=[first_page, last_page]) as gh, patch.object(inbox, "utc_now", return_value=NOW):
            result = inbox.run(self.args(), io.StringIO(), io.StringIO())
        self.assertEqual([101], [entry["id"] for entry in result])
        self.assertIn("--paginate", gh.call_args.args[0])
        self.assertIn("--slurp", gh.call_args.args[0])

    def test_fetch_failure_preserves_prior_state_and_releases_lock(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        before = self.state_path().read_bytes()
        with patch.object(inbox, "api_pages", side_effect=GhError("rate limited")), patch.object(inbox, "utc_now", return_value=NOW):
            with self.assertRaises(GhError):
                inbox.run(self.args(ack=True), io.StringIO(), io.StringIO())
        self.assertEqual(before, self.state_path().read_bytes())
        self.assertFalse(self.state_path().with_suffix(".lock").exists())

    def test_malformed_response_cannot_advance_cursor(self):
        missing_update = comment()
        del missing_update["updated_at"]
        invalid_body = comment()
        invalid_body["body"] = 0
        for item in (missing_update, invalid_body):
            with self.subTest(item=item):
                with self.assertRaisesRegex(inbox.InboxError, "invalid GitHub comment"):
                    self.run_inbox([item], args=self.args(ack=True))
                self.assertFalse(self.state_path().exists())

    def test_corrupt_state_is_not_reset_or_fetched(self):
        path = self.state_path()
        path.parent.mkdir(parents=True)
        path.write_text("{corrupted", encoding="utf-8")
        with patch.object(inbox, "api_pages") as fetch:
            with self.assertRaisesRegex(inbox.InboxError, "state was not reset"):
                inbox.run(self.args(ack=True), io.StringIO(), io.StringIO())
        fetch.assert_not_called()
        self.assertEqual("{corrupted", path.read_text())

    def test_wrong_state_scope_is_rejected(self):
        self.run_inbox([], args=self.args(ack=True))
        data = json.loads(self.state_path().read_text())
        data["scope"]["repo"] = "other/repo"
        self.state_path().write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(inbox.InboxError, "scope mismatch"):
            self.run_inbox([])

    def test_atomic_replace_failure_preserves_state_and_cleans_temporary_file(self):
        self.run_inbox([], args=self.args(ack=True))
        before = self.state_path().read_bytes()
        with patch.object(inbox.os, "replace", side_effect=OSError("interrupted replace")):
            with self.assertRaises(OSError):
                self.run_inbox([comment()], args=self.args(ack=True))
        self.assertEqual(before, self.state_path().read_bytes())
        self.assertEqual([], list(self.state_path().parent.glob("*.tmp")))

    def test_broken_output_or_flush_does_not_acknowledge(self):
        class BrokenWrite(io.StringIO):
            def write(self, value):
                raise BrokenPipeError("reader closed")

        class BrokenFlush(io.StringIO):
            def flush(self):
                raise BrokenPipeError("reader closed before flush")

        for stream in (BrokenWrite(), BrokenFlush()):
            with self.subTest(stream=type(stream).__name__):
                with patch.object(inbox, "api_pages", return_value=[comment()]), patch.object(inbox, "utc_now", return_value=NOW):
                    with self.assertRaises(BrokenPipeError):
                        inbox.run(self.args(ack=True), stream, io.StringIO())
                self.assertFalse(self.state_path().exists())
                self.assertFalse(self.state_path().with_suffix(".lock").exists())

    def test_existing_lock_refuses_concurrent_ack_without_fetching(self):
        lock = self.state_path().with_suffix(".lock")
        lock.parent.mkdir(parents=True)
        lock.write_text("pid=other\n")
        with patch.object(inbox, "api_pages") as fetch:
            with self.assertRaisesRegex(inbox.InboxError, "already locked"):
                inbox.run(self.args(ack=True), io.StringIO(), io.StringIO())
        fetch.assert_not_called()
        self.assertEqual("pid=other\n", lock.read_text())

    def test_identifiers_cannot_escape_state_directory(self):
        invalid = [dict(org="../other"), dict(org="..\\other"), dict(agent="../../qa"),
                   dict(repo="owner/repo/other"), dict(repo="../repo"), dict(org="/absolute")]
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(inbox.InboxError):
                    self.run_inbox([], args=self.args(ack=True, **values))
        self.assertFalse(self.root.exists())

    def test_replay_ignores_dedupe_without_mutating_saved_state(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        before = self.state_path().read_bytes()
        result, _, _ = self.run_inbox([comment()], args=self.args(since="2026-11-11T00:00:00Z", no_save=True))
        self.assertEqual([1], [item["id"] for item in result])
        self.assertEqual(before, self.state_path().read_bytes())
        with self.assertRaisesRegex(inbox.InboxError, "replay-only"):
            self.run_inbox([], args=self.args(ack=True, since="2026-11-11T00:00:00Z"))

    def test_legacy_cursor_is_explained_and_never_imported(self):
        self.root.mkdir()
        legacy = self.root / "org-a.last"
        legacy.write_text("2099-01-01T00:00:00Z")
        result, _, errors = self.run_inbox([comment(at=NOW - timedelta(days=10))])
        self.assertEqual([1], [entry["id"] for entry in result])
        self.assertIn("Legacy cursor", errors)
        self.assertIn("not used", errors)
        self.assertEqual("2099-01-01T00:00:00Z", legacy.read_text())

    def test_duplicate_paginated_versions_deliver_latest_once(self):
        older = comment(extra="Old.")
        newer = comment(extra="New.", at=NOW + timedelta(seconds=1))
        result, output, _ = self.run_inbox([older, newer, older])
        self.assertEqual(1, len(result))
        self.assertIn("New.", output)
        self.assertNotIn("Old.", output)

    def test_invalid_protocol_is_warned_and_not_treated_as_a_message(self):
        item = comment()
        item["body"] = "[AGENT-MSG v1] type=claim from=org-b/dev to=* ref=#1 lease_until=nonsense\nTask: fixture\nPlan: fixture"
        result, _, errors = self.run_inbox([item])
        self.assertEqual([], result)
        self.assertIn("Ignored invalid/unsupported protocol comment", errors)

    def test_clock_regression_preserves_server_cursor_and_dedup(self):
        self.run_inbox([comment()], args=self.args(ack=True))
        result, _, _ = self.run_inbox([comment()], now=NOW - timedelta(hours=1), args=self.args(ack=True))
        self.assertEqual([], result)
        self.assertEqual(inbox.timestamp(NOW), json.loads(self.state_path().read_text())["cursor"])

    def test_ahead_local_clock_idle_ack_does_not_lose_later_server_message(self):
        # Server is at noon, but the client is ten minutes ahead. No server event
        # exists yet, so the empty acknowledgement cannot establish a watermark.
        self.run_inbox([], args=self.args(ack=True), now=NOW + timedelta(minutes=10))
        self.assertEqual(inbox.timestamp(inbox.EPOCH), json.loads(self.state_path().read_text())["cursor"])
        arriving = comment(at=NOW + timedelta(minutes=1))

        def fetch(endpoint):
            since = inbox.parse_timestamp(parse_qs(urlsplit(endpoint).query)["since"][0])
            return [arriving] if inbox.parse_timestamp(arriving["updated_at"]) > since else []

        with patch.object(inbox, "api_pages", side_effect=fetch), patch.object(inbox, "utc_now", return_value=NOW + timedelta(minutes=11)):
            result = inbox.run(self.args(ack=True), io.StringIO(), io.StringIO())
        self.assertEqual([1], [entry["id"] for entry in result])
        self.assertEqual(arriving["updated_at"], json.loads(self.state_path().read_text())["cursor"])

    def test_old_backlog_watermark_and_dedup_survive_empty_scans(self):
        old = comment(at=NOW - timedelta(days=30))
        self.run_inbox([old], args=self.args(ack=True), now=NOW)
        original = json.loads(self.state_path().read_text())
        self.assertEqual(old["updated_at"], original["cursor"])
        self.run_inbox([], args=self.args(ack=True), now=NOW + timedelta(days=1))
        idle = json.loads(self.state_path().read_text())
        self.assertEqual(original["cursor"], idle["cursor"])
        self.assertEqual(original["seen"], idle["seen"])
        result, _, _ = self.run_inbox([old], now=NOW + timedelta(days=1))
        self.assertEqual([], result)

    def test_future_observation_cannot_advance_past_prefetch_ceiling(self):
        future = comment(at=NOW + timedelta(days=1))
        self.run_inbox([future], args=self.args(ack=True), now=NOW)
        state = json.loads(self.state_path().read_text())
        self.assertEqual(inbox.timestamp(NOW), state["cursor"])
        self.assertIn("1", state["seen"])


if __name__ == "__main__":
    unittest.main()
