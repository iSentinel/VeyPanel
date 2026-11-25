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


if __name__ == "__main__":
    unittest.main()
