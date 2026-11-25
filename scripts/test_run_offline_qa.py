"""Regression fixtures for scoped and sanitized JUnit reporting."""

from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from unittest.mock import patch
import xml.etree.ElementTree as ET

from run_offline_qa import EvidenceResult, main, write_junit


class EvidenceTests(unittest.TestCase):
    """Check actual recorded outcomes and safe report fields."""

    def test_junit_failure_and_success(self) -> None:
        """Retain failure without exposing arbitrary exception contents."""
        class Fixture(unittest.TestCase):
            def test_success(self):
                self.assertTrue(True)

            def test_failure(self):
                self.fail("secret-canary")

        result = EvidenceResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(Fixture).run(result)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.xml"
            write_junit(path, result, 1.0)
            data = path.read_text()
            suite = ET.fromstring(data)
            self.assertEqual(suite.get("tests"), "2")
            self.assertEqual(suite.get("failures"), "1")
            self.assertNotIn("secret-canary", data)

    def test_skip(self) -> None:
        """Preserve skip as a separate outcome, not success."""
        class Fixture(unittest.TestCase):
            @unittest.skip("fixture")
            def test_skip(self):
                pass

        result = EvidenceResult()
        unittest.defaultTestLoader.loadTestsFromTestCase(Fixture).run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual([value[0] for value in result.rows.values()], ["SKIPPED"])

    def test_cli_error_event(self) -> None:
        """Emit a safe execution error without exception text or stdout."""
        out, err = StringIO(), StringIO()
        with patch("sys.argv", ["qa", "--output", "unused", "--log-events"]):
            with patch("run_offline_qa.run", side_effect=OSError("secret-canary")):
                with redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(main(), 1)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(json.loads(err.getvalue())["reason"], "EXECUTION_ERROR")
        self.assertNotIn("secret-canary", err.getvalue())

    def test_cli_failed_gate_event(self) -> None:
        """A failed gate keeps its exit code and separates human/JSON output."""
        out, err = StringIO(), StringIO()
        with patch("sys.argv", ["qa", "--output", "unused", "--log-events"]):
            with patch("run_offline_qa.run", return_value=False):
                with redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(main(), 2)
        self.assertEqual(out.getvalue(), "FAIL: scoped Python offline QA\n")
        self.assertEqual(json.loads(err.getvalue())["reason"], "RUN_FAILED")

    def test_subtest_skip_privacy(self) -> None:
        """Export the parent identity rather than arbitrary subtest parameters."""
        class Fixture(unittest.TestCase):
            def test_case(self):
                with self.subTest(private="secret-canary"):
                    self.skipTest("private skip reason")
        case = Fixture("test_case")
        result = EvidenceResult((case.id(),))
        unittest.TestSuite([case]).run(result)
        self.assertEqual(set(result.rows), {case.id()})
        self.assertEqual(result.rows[case.id()][0], "SKIPPED")
        self.assertEqual(result.unattributed, 0)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.xml"
            write_junit(path, result, 1.0)
            self.assertNotIn("secret-canary", path.read_text())
            self.assertNotIn("private skip reason", path.read_text())

    def test_unattributed_fixture_failure(self) -> None:
        """Keep setup failure counts without inventing a case or exposing its ID."""
        class Fixture(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise RuntimeError("secret-canary")
            def test_case(self):
                pass
        case = Fixture("test_case")
        result = EvidenceResult((case.id(),))
        unittest.TestSuite([case]).run(result)
        self.assertEqual(result.testsRun, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.unattributed, 1)
        self.assertEqual(result.rows, {})

    def test_failure_priority(self) -> None:
        """A later success cannot overwrite an already nonpassing case."""
        case = unittest.FunctionTestCase(lambda: None)
        result = EvidenceResult((case.id(),))
        result.startTest(case)
        result.record(case, "ERROR")
        result.record(case, "SKIPPED")
        result.record(case, "PASS")
        result.stopTest(case)
        self.assertEqual(result.rows[case.id()][0], "ERROR")

    def test_unreviewed_identity(self) -> None:
        """Refuse a changed runtime identity instead of publishing it."""
        case = unittest.FunctionTestCase(lambda: None)
        result = EvidenceResult(("reviewed.case",))
        unittest.TestSuite([case]).run(result)
        self.assertEqual(result.rows, {})
        self.assertEqual(result.unattributed, 1)


if __name__ == "__main__":
    unittest.main()
