"""Offline regression fixtures for review-only upstream action plans."""

import hashlib
import json
from pathlib import Path
import unittest

from check_upstream_review import FIELDS, MAX_REPORT, report
from upstream_review_plan import ACTIONS, review_plan


class ReviewPlanTests(unittest.TestCase):
    """Require exact report inputs and deterministic nonauthorizing review actions."""

    def setUp(self) -> None:
        """Use the committed reviewed baseline as synthetic fixture data."""
        root = Path(__file__).resolve().parents[1]
        self.baseline = (root / "config/upstream-review-baseline.json").read_bytes()
        self.observation = json.loads(self.baseline)
        self.repo = "ClassicOldSong/Apollo"

    def inputs(self) -> tuple[bytes, bytes, bytes]:
        """Generate the exact classifier report for the current fixture."""
        observed = json.dumps(self.observation, sort_keys=True).encode()
        claimed = json.dumps(report(self.baseline, observed), sort_keys=True).encode()
        return self.baseline, observed, claimed

    def test_unchanged(self) -> None:
        """Unchanged metadata creates no review tasks and never authorizes adoption."""
        result = review_plan(*self.inputs())
        self.assertEqual(result["status"], "UNCHANGED")
        self.assertEqual(result["rows"], [])
        self.assertIs(result["adoption_authorized"], False)

    def test_field_coverage(self) -> None:
        """Every classified field has an explicit review mapping."""
        self.assertEqual(set(ACTIONS), FIELDS)
        values = {"archived": True, "branch": "next", "head": "a" * 40,
                  "license": "MIT", "release_id": 1, "tag": "v99",
                  "release_commit": "b" * 40}
        for field, value in values.items():
            with self.subTest(field=field):
                self.observation = json.loads(self.baseline)
                self.observation["repositories"][self.repo][field] = value
                result = review_plan(*self.inputs())
                self.assertEqual(result["status"], "REVIEW")
                self.assertEqual(result["rows"][0]["changed"], [field])
                self.assertEqual(result["rows"][0]["required_reviews"], sorted(
                    set(ACTIONS[field]) | {"regression-test-plan", "owner-review"}))
                self.assertIs(result["adoption_authorized"], False)

    def test_multiple_changes(self) -> None:
        """Deduplicate and sort actions without changing the repository ordering."""
        rows = self.observation["repositories"]
        rows[self.repo]["head"] = "a" * 40
        rows[self.repo]["release_commit"] = "b" * 40
        rows["itkawa/screen-spawner"]["license"] = "MIT"
        plan = review_plan(*self.inputs())
        self.assertEqual([row["repository"] for row in plan["rows"]],
                         [self.repo, "itkawa/screen-spawner"])
        actions = plan["rows"][0]["required_reviews"]
        self.assertEqual(actions, sorted(set(actions)))
        self.assertIn("artifact-provenance", actions)

    def test_missing_rows(self) -> None:
        """Incomplete evidence dominates changes and cannot produce an action plan."""
        del self.observation["repositories"][self.repo]
        self.observation["repositories"]["itkawa/screen-spawner"]["license"] = "MIT"
        with self.assertRaises(ValueError):
            review_plan(*self.inputs())

    def test_forged_report(self) -> None:
        """Refuse an altered classifier status or changed-field list."""
        self.observation["repositories"][self.repo]["head"] = "a" * 40
        baseline, observed, claimed = self.inputs()
        data = json.loads(claimed)
        data["rows"][0]["changed"] = []
        with self.assertRaises(ValueError):
            review_plan(baseline, observed, json.dumps(data).encode())

    def test_exact_digests(self) -> None:
        """Bind all three exact byte sequences, including report whitespace."""
        baseline, observed, claimed = self.inputs()
        result = review_plan(baseline, observed, claimed + b"\n")
        for key, raw in (("baseline_sha256", baseline), ("observed_sha256", observed),
                         ("report_sha256", claimed + b"\n")):
            self.assertEqual(result[key], hashlib.sha256(raw).hexdigest())

    def test_budget(self) -> None:
        """Reject oversized inputs before parsing any content."""
        inputs = list(self.inputs())
        for index in range(3):
            oversized = inputs.copy()
            oversized[index] = b" " * (MAX_REPORT + 1)
            with self.assertRaises(ValueError):
                review_plan(*oversized)

    def test_no_raw_values(self) -> None:
        """Expose only fixed identities and actions rather than upstream values."""
        self.observation["repositories"][self.repo]["branch"] = "private-canary"
        self.assertNotIn("private-canary", json.dumps(review_plan(*self.inputs())))
