"""Regression coverage for independently reviewed mandatory offline cases."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from qa_case_inventory import compare_cases, discovered_cases, execution_passed, load_cases
from run_offline_qa import run_required_tests

CASES = ("test_fixture.Fixture.test_a", "test_fixture.Fixture.test_b")


class CaseInventoryTests(unittest.TestCase):
    """Refuse incomplete, ambiguous or unexecuted mandatory cases."""

    def test_valid_catalog(self) -> None:
        """Read exact sorted unique IDs from the independent registry."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps({"schema": 1, "cases": CASES}), encoding="utf-8")
            self.assertEqual(load_cases(path), CASES)

    def test_invalid_catalog(self) -> None:
        """Refuse duplicate, empty, unsorted and malformed case identities."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            for cases in ([], [CASES[0], CASES[0]], list(reversed(CASES)), ["private data"]):
                path.write_text(json.dumps({"schema": 1, "cases": cases}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_cases(path)

    def test_missing_case(self) -> None:
        """A subset of passing tests is not the required inventory."""
        report = compare_cases(CASES, [CASES[0]])
        self.assertEqual(report["missing"], [CASES[1]])
        self.assertEqual(report["status"], "FAIL")

    def test_duplicate_and_unexpected(self) -> None:
        """Duplicate execution cannot replace a missing case or expose raw IDs."""
        report = compare_cases(CASES, [CASES[0], CASES[0], "secret-canary"])
        self.assertEqual(report["duplicate_count"], 1)
        self.assertEqual(report["unexpected_count"], 2)
        self.assertEqual(report["status"], "FAIL")
        self.assertNotIn("secret-canary", json.dumps(report))

    def test_discovery(self) -> None:
        """Flatten nested suites without losing an individual case."""
        class Fixture(unittest.TestCase):
            def test_a(self):
                pass
            def test_b(self):
                pass
        suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Fixture)])
        self.assertEqual(len(discovered_cases(suite)), 2)

    def test_execution(self) -> None:
        """Require exact executed IDs, count and positive verdict for every case."""
        rows = dict.fromkeys(CASES, ("PASS", 0.0))
        self.assertTrue(execution_passed(CASES, rows, 2, True))
        self.assertFalse(execution_passed(CASES, rows, 2, False))
        self.assertFalse(execution_passed(CASES, rows, 3, True))
        rows[CASES[1]] = ("SKIPPED", 0.0)
        self.assertFalse(execution_passed(CASES, rows, 2, True))
        del rows[CASES[1]]
        self.assertFalse(execution_passed(CASES, rows, 1, True))

    def test_runner_missing_case(self) -> None:
        """The real runner refuses a subset before executing any test."""
        class Fixture(unittest.TestCase):
            def test_a(self):
                raise AssertionError("Incomplete suite executed")
        case = Fixture("test_a")
        with tempfile.TemporaryDirectory() as directory, patch(
                "run_offline_qa.load_cases", return_value=(case.id(), CASES[1])), patch(
                "run_offline_qa.unittest.defaultTestLoader.discover",
                return_value=unittest.TestSuite([case])):
            result, inventory, ok = run_required_tests(Path(directory))
            self.assertFalse(ok)
            self.assertEqual(result.testsRun, 0)
            self.assertEqual(inventory["missing"], [CASES[1]])
            report = json.loads((Path(directory) / "case-inventory.json").read_text())
            self.assertEqual(report["execution_status"], "FAIL")

    def test_runner_skipped_case(self) -> None:
        """A matching discovery set with a skipped mandatory test still fails."""
        class Fixture(unittest.TestCase):
            @unittest.skip("synthetic skip")
            def test_a(self):
                pass
        case = Fixture("test_a")
        with tempfile.TemporaryDirectory() as directory, patch(
                "run_offline_qa.load_cases", return_value=(case.id(),)), patch(
                "run_offline_qa.unittest.defaultTestLoader.discover",
                return_value=unittest.TestSuite([case])):
            result, inventory, ok = run_required_tests(Path(directory))
            self.assertFalse(ok)
            self.assertEqual(result.testsRun, 1)
            self.assertEqual(inventory["status"], "PASS")
            self.assertEqual(result.rows[case.id()][0], "SKIPPED")


if __name__ == "__main__":
    unittest.main()
