"""Regression fixtures for scoped and sanitized JUnit reporting."""

from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from run_offline_qa import EvidenceResult, write_junit


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


if __name__ == "__main__":
    unittest.main()
