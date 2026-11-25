"""Offline regression cases for upstream metadata classification."""

import copy
import hashlib
import json
from pathlib import Path
import unittest

from check_upstream_review import classify, report


class UpstreamReviewTests(unittest.TestCase):
    """Check complete evidence, drift, and fail-closed invalid inputs."""

    def setUp(self) -> None:
        """Read the reviewed repository baseline; create a separate observation."""
        path = Path(__file__).resolve().parents[1] / "config/upstream-review-baseline.json"
        self.base = json.loads(path.read_text(encoding="utf-8"))
        self.current = copy.deepcopy(self.base)
        self.repo = "ClassicOldSong/Apollo"

    def result(self) -> dict:
        """Classify exact encoded evidence bytes."""
        return report(json.dumps(self.base).encode(), json.dumps(self.current).encode())

    def test_unchanged(self) -> None:
        """All five complete matching observations are unchanged."""
        result = self.result()
        self.assertEqual(result["status"], "UNCHANGED")
        self.assertEqual(len(result["rows"]), 5)
        self.assertTrue(all(row["status"] == "UNCHANGED" for row in result["rows"]))

    def test_changed_fields(self) -> None:
        """Review release retargeting even if the tag and release ID are unchanged."""
        row = self.current["repositories"][self.repo]
        row["release_commit"] = "a" * 40
        row["archived"] = True
        result = self.result()
        self.assertEqual(result["status"], "REVIEW")
        changed = next(item for item in result["rows"] if item["repository"] == self.repo)
        self.assertEqual(changed["changed"], ["archived", "release_commit"])

    def test_missing_observation(self) -> None:
        """Never infer unchanged for a missing required repository."""
        del self.current["repositories"][self.repo]
        self.assertEqual(self.result()["status"], "ERROR")

    def test_invalid_observations(self) -> None:
        """Incomplete, invalid and ambiguous values are errors, not drift."""
        for field, value in (("head", "0"*40), ("release_id", True),
                             ("archived", 0), ("license", ""), ("tag", None)):
            self.current = copy.deepcopy(self.base)
            self.current["repositories"][self.repo][field] = value
            self.assertEqual(self.result()["status"], "ERROR")

    def test_error_precedence(self) -> None:
        """An incomplete observation dominates otherwise valid drift."""
        self.current["repositories"][self.repo]["tag"] = "v2"
        del self.current["repositories"]["itkawa/screen-spawner"]
        self.assertEqual(self.result()["status"], "ERROR")

    def test_unknown_repository(self) -> None:
        """Reject an unexpected repository without echoing its content."""
        self.current["repositories"]["fixture/unreviewed"] = {}
        with self.assertRaises(ValueError):
            classify(self.base, self.current)

    def test_invalid_baseline(self) -> None:
        """A missing baseline row is not an observation error."""
        del self.base["repositories"][self.repo]
        with self.assertRaises(ValueError):
            classify(self.base, self.current)

    def test_duplicate_json_and_digest(self) -> None:
        """Reject duplicate keys; bind report to exact valid input bytes."""
        raw = json.dumps(self.base).encode()
        self.assertEqual(report(raw, raw)["observed_sha256"], hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            report(raw, b'{"schema":1,"schema":1,"repositories":{}}')

    def test_artemis_required(self) -> None:
        """Require the distinct Artemis repository rather than Moonlight alone."""
        del self.current["repositories"]["ClassicOldSong/moonlight-android"]
        result = self.result()
        self.assertEqual(result["status"], "ERROR")
        row = next(item for item in result["rows"]
                   if item["repository"] == "ClassicOldSong/moonlight-android")
        self.assertEqual(row["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
