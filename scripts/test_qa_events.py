"""Validate the closed QA event schema and safe serialization."""

from datetime import datetime
from io import StringIO
import json
import unittest

from qa_events import emit, event


class QaEventTests(unittest.TestCase):
    """Exercise explicit stage/status, duration and output boundaries."""

    def test_schema(self) -> None:
        """Use exactly the documented keys and a UTC timestamp."""
        row = event("audit", "PASS", 0.1234567)
        self.assertEqual(set(row), {"schema", "timestamp_utc", "level", "event",
                                    "stage", "status", "reason", "duration_seconds"})
        self.assertEqual(row["reason"], "AUDIT_MATCH")
        self.assertEqual(row["duration_seconds"], 0.123457)
        self.assertEqual(datetime.fromisoformat(str(row["timestamp_utc"])).utcoffset().total_seconds(), 0)

    def test_secret_canary(self) -> None:
        """Reject arbitrary strings without echoing the supplied value."""
        target = StringIO()
        with self.assertRaisesRegex(ValueError, "^Invalid QA event stage/status$"):
            emit(target, "secret-canary", "PASS", 0)
        self.assertEqual(target.getvalue(), "")
        with self.assertRaisesRegex(ValueError, "^Invalid QA event stage/status$"):
            emit(target, "run", "secret-canary", 0)
        self.assertEqual(target.getvalue(), "")

    def test_invalid_duration(self) -> None:
        """Reject Boolean, non-finite and out-of-budget durations."""
        for value in (True, -1, float("nan"), float("inf"), 86401, 10**500, "1"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Invalid QA event duration"):
                    event("run", "PASS", value)

    def test_invalid_pair(self) -> None:
        """Reject a known status that is not valid for the requested stage."""
        with self.assertRaisesRegex(ValueError, "Invalid QA event stage/status"):
            event("report", "FAIL", 1)

    def test_jsonl(self) -> None:
        """Write exactly one object per line to the supplied sink."""
        target = StringIO()
        emit(target, "tests", "FAIL", 0.1)
        emit(target, "run", "ERROR", 0.2)
        rows = [json.loads(line) for line in target.getvalue().splitlines()]
        self.assertEqual([row["reason"] for row in rows], ["TESTS_FAILED", "EXECUTION_ERROR"])

    def test_disabled(self) -> None:
        """The optional sink may be absent."""
        self.assertIsNone(emit(None, "run", "PASS", 0))


if __name__ == "__main__":
    unittest.main()
