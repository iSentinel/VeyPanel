"""Offline regression tests for bounded local upstream freshness receipts."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from upstream_freshness import create_receipt, verify_receipt, MAX_AGE_SECONDS


class FreshnessTests(unittest.TestCase):
    """Require exact source, digest, complete membership and time bounds."""

    def setUp(self) -> None:
        """Construct a complete synthetic observation from the reviewed baseline."""
        path = Path(__file__).resolve().parents[1] / "config/upstream-review-baseline.json"
        self.raw = path.read_bytes()
        self.commit = "a" * 40
        self.tree = "b" * 40
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.end = self.start + timedelta(seconds=2)
        self.now = self.end + timedelta(seconds=5)
        self.receipt = create_receipt(self.raw, self.commit, self.tree,
                                      self.start, self.end, 2000)

    def verify(self) -> dict:
        """Verify the current fixture using an explicit verification clock."""
        return verify_receipt(self.raw, json.dumps(self.receipt).encode(),
                              self.commit, self.tree, self.now)

    def test_complete(self) -> None:
        """Accept complete matching evidence and preserve the recorded identity."""
        self.assertEqual(self.verify(), self.receipt)

    def test_digest_mismatch(self) -> None:
        """Even whitespace-only observation changes invalidate the receipt."""
        self.raw += b"\n"
        with self.assertRaises(ValueError):
            self.verify()

    def test_source_mismatch(self) -> None:
        """Bind both exact commit and tree, not only one identity."""
        for field in ("git_commit", "git_tree"):
            original = self.receipt[field]
            self.receipt[field] = "c" * 40
            with self.assertRaises(ValueError):
                self.verify()
            self.receipt[field] = original

    def test_incomplete(self) -> None:
        """Preserve incomplete receipt evidence but never accept it as fresh."""
        data = json.loads(self.raw)
        del data["repositories"]["ClassicOldSong/Apollo"]
        self.raw = json.dumps(data).encode()
        self.receipt = create_receipt(self.raw, self.commit, self.tree,
                                      self.start, self.end, 2000)
        self.assertFalse(self.receipt["complete"])
        with self.assertRaises(ValueError):
            self.verify()

    def test_age_boundary(self) -> None:
        """Measure maximum age from the oldest collection instant."""
        self.now = self.start + timedelta(seconds=MAX_AGE_SECONDS)
        self.verify()
        self.now += timedelta(microseconds=1)
        with self.assertRaises(ValueError):
            self.verify()

    def test_future_boundary(self) -> None:
        """Allow only the explicit five-second local clock skew."""
        self.now = self.end - timedelta(seconds=5)
        self.verify()
        self.now -= timedelta(microseconds=1)
        with self.assertRaises(ValueError):
            self.verify()

    def test_clock_and_duration(self) -> None:
        """Reject backward UTC, inconsistent duration, booleans and overrun."""
        for duration in (True, -1, 185001, 8001):
            with self.assertRaises(ValueError):
                create_receipt(self.raw, self.commit, self.tree, self.start, self.end, duration)
        with self.assertRaises(ValueError):
            create_receipt(self.raw, self.commit, self.tree, self.end, self.start, 2000)

    def test_strict_schema(self) -> None:
        """Reject aliases, unknown fields, malformed UTC and duplicate keys."""
        for field, value in (("schema", True), ("complete", 1),
                             ("started_utc", "2026-01-01T00:00:00+00:00"), ("extra", 1)):
            original = dict(self.receipt)
            self.receipt[field] = value
            with self.assertRaises(ValueError):
                self.verify()
            self.receipt = original
        with self.assertRaises(ValueError):
            verify_receipt(self.raw, b'{"schema":1,"schema":1}', self.commit, self.tree, self.now)
