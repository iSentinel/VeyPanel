"""Offline regressions for public quota admission; no live API calls."""

import contextlib
import io
import subprocess
import time
import unittest
from unittest.mock import MagicMock, patch

import check_upstream_quota as quota
import collect_upstream_review as collector


class QuotaTests(unittest.TestCase):
    """Validate strict quota counts and one-shot fail-closed admission."""

    def test_exact_endpoint(self) -> None:
        """Allow only the exact public quota endpoint, not variants."""
        self.assertTrue(collector.allowed_path("/rate_limit"))
        for path in ("/rate_limit/", "/rate_limit?x=1", "/rate_limit/extra"):
            self.assertFalse(collector.allowed_path(path))

    def test_valid_counts(self) -> None:
        """Accept zero remaining and the exact maximum required budget."""
        for value in (0, quota.REQUIRED, 60):
            self.assertEqual(quota.remaining_quota({"resources": {"core": {
                "limit": 60, "remaining": value}}}), value)
        self.assertEqual(quota.REQUIRED, 25)

    def test_invalid_counts(self) -> None:
        """Reject booleans, strings, negatives and contradictory quota counts."""
        for limit, remaining in ((0, 0), (60, 61), (60, -1), (True, 1),
                                 (60, False), ("60", 25), (60, "25")):
            with self.assertRaises(ValueError):
                quota.remaining_quota({"resources": {"core": {
                    "limit": limit, "remaining": remaining}}})

    def test_invalid_structure(self) -> None:
        """Refuse absent or malformed core quota data."""
        for data in (None, [], {}, {"resources": []}, {"resources": {"core": {}}}):
            with self.assertRaises(ValueError):
                quota.remaining_quota(data)

    def test_single_request(self) -> None:
        """Use one request and the existing monotonic transport deadline."""
        get = MagicMock(return_value={"resources": {"core": {"limit": 60, "remaining": 25}}})
        before = time.monotonic()
        self.assertEqual(quota.preflight(get), 25)
        get.assert_called_once()
        path, deadline = get.call_args.args
        self.assertEqual(path, "/rate_limit")
        self.assertGreaterEqual(deadline, before)
        self.assertLessEqual(deadline, time.monotonic() + quota.REQUEST_SECONDS)

    def test_cli_capacity(self) -> None:
        """Differentiate sufficient quota from insufficient quota."""
        with patch.object(quota.sys, "argv", ["quota"]):
            for remaining, expected in ((25, 0), (24, 2), (0, 2)):
                with patch.object(quota, "preflight", return_value=remaining), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(quota.main(), expected)

    def test_cli_unavailable(self) -> None:
        """Fail closed and redact arbitrary exception values."""
        with patch.object(quota.sys, "argv", ["quota"]), contextlib.redirect_stderr(io.StringIO()) as errors:
            for error in (ValueError("private canary"), subprocess.TimeoutExpired("worker", 1)):
                with patch.object(quota, "preflight", side_effect=error):
                    self.assertEqual(quota.main(), 1)
            self.assertNotIn("private canary", errors.getvalue())

    def test_workflow_order(self) -> None:
        """Require preflight before collection and retain manual-only triggering."""
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / ".github/workflows/upstream-watch.yml"
        text = path.read_text(encoding="utf-8")
        self.assertLess(text.index("python3 scripts/check_upstream_quota.py"),
                        text.index("run_upstream_watch_ci.py collect"))
        self.assertNotIn("  schedule:", text)
        self.assertNotIn("continue-on-error:", text)
