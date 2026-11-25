"""Regressions for recomputed upstream review evidence."""

import copy
import json
from pathlib import Path
import unittest

from check_upstream_review import report
from verify_upstream_review import verify


class VerifyReviewTests(unittest.TestCase):
    """Detect altered output without trusting the producer's status."""

    def setUp(self) -> None:
        """Read the reviewed five-repository baseline and derive a report."""
        self.base = (Path(__file__).resolve().parents[1] /
                     "config/upstream-review-baseline.json").read_bytes()
        self.actual = self.base
        self.claim = report(self.base, self.actual)

    def check(self) -> dict:
        """Verify a serialized claim against separate input bytes."""
        return verify(self.base, self.actual, json.dumps(self.claim).encode())

    def test_positive(self) -> None:
        """Accept an exact report including all five required repositories."""
        self.assertEqual(self.check()["status"], "UNCHANGED")
        self.assertEqual(len(self.check()["rows"]), 5)

    def test_changed_status(self) -> None:
        """Reject an invented review status or changed field."""
        self.claim["status"] = "REVIEW"
        with self.assertRaises(ValueError):
            self.check()

    def test_altered_inputs(self) -> None:
        """Even equivalent JSON with different bytes must match the input hash."""
        self.actual += b"\n"
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_extra_or_reordered_rows(self) -> None:
        """Require every row in the prescribed order and no extra rows."""
        original = copy.deepcopy(self.claim)
        for rows in (original["rows"][:-1], original["rows"] * 2,
                     list(reversed(original["rows"]))):
            self.claim = copy.deepcopy(original)
            self.claim["rows"] = rows
            with self.assertRaises(ValueError):
                self.check()

    def test_unknown_field_and_boolean_schema(self) -> None:
        """Reject extra fields and type confusion even if values compare equal."""
        self.claim["schema"] = True
        with self.assertRaises(ValueError):
            self.check()
        self.claim["schema"] = 1
        self.claim["extra"] = "fixture"
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_keys(self) -> None:
        """Strictly parse claimed report bytes before any semantic comparison."""
        raw = json.dumps(self.claim).replace('"schema": 1', '"schema": 2, "schema": 1')
        with self.assertRaises(ValueError):
            verify(self.base, self.actual, raw.encode())

    def test_error_is_not_unchanged(self) -> None:
        """A valid report describing incomplete data must retain ERROR."""
        actual = json.loads(self.base)
        del actual["repositories"]["ClassicOldSong/moonlight-android"]
        self.actual = json.dumps(actual).encode()
        self.claim = report(self.base, self.actual)
        self.assertEqual(self.check()["status"], "ERROR")
        self.claim["status"] = "UNCHANGED"
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
