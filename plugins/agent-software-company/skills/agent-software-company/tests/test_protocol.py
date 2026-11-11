import contextlib
import io
import sys
import unittest
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.protocol import addressed, parse_message, parse_timestamp, validate_message
import lint_message


def claim(lease="2026-11-11T14:00:00Z", extra=""):
    return f"[AGENT-MSG v1] type=claim from=org-a/dev to=* ref=#1 lease_until={lease}{extra}\nTask: regression\nPlan: reproduce and repair"


class ProtocolTests(unittest.TestCase):
    def test_known_message_returns_shared_shape_and_complete_body(self):
        text = claim() + "\nEvidence: detail\n    preserved indentation"
        result = parse_message(text)
        self.assertEqual(result["from"], "org-a/dev")
        self.assertEqual(result["attrs"]["lease_until"], "2026-11-11T14:00:00Z")
        self.assertIn("    preserved indentation", result["body"])

    def test_malformed_or_naive_lease_is_rejected(self):
        for lease in ("nonsense", "2026-11-11T14:00:00", "2026-11-11"):
            with self.subTest(lease=lease):
                self.assertIsNone(parse_message(claim(lease)))
                self.assertTrue(validate_message(claim(lease)))

    def test_timestamp_normalizes_offset(self):
        value = parse_timestamp("2026-11-11T15:30:00+05:30")
        self.assertEqual(value.hour, 10)
        self.assertEqual(value.tzinfo, timezone.utc)

    def test_unknown_and_duplicate_fields_never_route(self):
        self.assertIsNone(parse_message(claim().replace("type=claim", "type=execute")))
        self.assertIsNone(parse_message(claim(extra=" lease_until=2026-11-11T15:00:00Z")))
        self.assertIsNotNone(parse_message(claim(extra=" future_hint=safe")))

    def test_recipient_matching_is_exact_and_org_digest_includes_agents(self):
        self.assertTrue(addressed("org-a/qa", "org-a"))
        self.assertFalse(addressed("org-ab/qa", "org-a"))
        self.assertTrue(addressed("org-a/qa", "org-a", "qa"))
        self.assertFalse(addressed("org-a/dev", "org-a", "qa"))
        self.assertTrue(addressed("*", "org-a", "qa"))

    def test_review_requires_full_matching_hash_and_valid_verdict(self):
        sha = "a" * 40
        text = f"[AGENT-MSG v1] type=review from=org-a/qa to=org-a/dev ref=#1 sha={sha}\nVerdict: PASS\nCommit SHA: {sha}\nChecks: 3/3\nRed proof: 1/1\nProblems: none"
        self.assertEqual(validate_message(text), [])
        self.assertIsNone(parse_message(text.replace("sha=" + sha, "sha=abcdef0")))
        self.assertIsNone(parse_message(text.replace("Commit SHA: " + sha, "Commit SHA: " + "b" * 40)))
        self.assertIsNone(parse_message(text.replace("Verdict: PASS", "Verdict: APPROVE")))

    def test_empty_sections_do_not_pass(self):
        self.assertTrue(validate_message(claim().replace("Plan: reproduce and repair", "Plan:")))

    def test_style_is_warning_and_cli_still_succeeds(self):
        text = claim() + "\nNotes: just " + "evidence " * 300
        self.assertEqual(lint_message.lint(text), [])
        self.assertTrue(lint_message.style_warnings(text))
        previous = sys.stdin
        try:
            sys.stdin = io.StringIO(text)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(lint_message.main([]), 0)
            self.assertIn("warning:", output.getvalue())
        finally:
            sys.stdin = previous


if __name__ == "__main__":
    unittest.main()
