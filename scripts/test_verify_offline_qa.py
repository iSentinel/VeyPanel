"""Negative fixtures for independent offline QA report verification."""

import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from verify_offline_qa import verify

CASES = ("test_fixture.Fixture.test_a", "test_fixture.Fixture.test_b")
COMMIT, TREE = "a" * 40, "b" * 40


class VerifyEvidenceTests(unittest.TestCase):
    """Reject missing, inconsistent or nonpassing reports."""

    def setUp(self) -> None:
        """Create one isolated internally consistent synthetic report set."""
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.summary = {
            "schema": 1, "scope": "python-offline", "status": "PASS",
            "audit_status": "PASS", "inventory_status": "PASS",
            "git_commit": COMMIT, "git_tree": TREE, "tracked_checkout_clean": True,
            "debt_count": 0, "required_cases": 2, "tests_run": 2, "passed": 2,
            "errors": 0, "failures": 0, "skipped": 0, "expected_failures": 0,
            "unexpected_successes": 0, "native_windows": "NOT_RUN",
            "native_android": "NOT_RUN", "hardware": "NOT_RUN", "duration_seconds": 1.0}
        self.write("summary.json", self.summary)
        self.write("case-inventory.json", {"schema": 1, "status": "PASS",
                   "execution_status": "PASS", "expected_count": 2, "observed_count": 2,
                   "missing": [], "unexpected_count": 0, "duplicate_count": 0})
        self.write("code-audit.json", {"schema": 1, "status": "PASS",
                   "findings": [], "new": [], "resolved": []})
        self.suite = ET.Element("testsuite", name="veypanel.python.offline", tests="2",
                                errors="0", failures="0", skipped="0", time="1.0")
        for identity in CASES:
            owner, _, method = identity.rpartition(".")
            ET.SubElement(self.suite, "testcase", classname=owner, name=method, time="0.5")
        self.save_xml()

    def write(self, name: str, value: dict) -> None:
        """Write one synthetic JSON report."""
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def save_xml(self) -> None:
        """Write the fixture XML."""
        ET.ElementTree(self.suite).write(self.root / "python-results.xml", encoding="utf-8")

    def check(self) -> None:
        """Run the independent validator using the reviewed fixture identities."""
        verify(self.root, CASES, [], COMMIT, TREE)

    def test_valid(self) -> None:
        """Accept a complete consistent evidence set."""
        self.check()

    def test_missing(self) -> None:
        """Reject missing report files."""
        (self.root / "case-inventory.json").unlink()
        with self.assertRaises(OSError):
            self.check()

    def test_wrong_checkout(self) -> None:
        """Reject a report belonging to another checkout."""
        self.summary["git_tree"] = "c" * 40
        self.write("summary.json", self.summary)
        with self.assertRaises(ValueError):
            self.check()

    def test_boolean_count(self) -> None:
        """Reject JSON boolean aliases for numeric fields."""
        self.summary["errors"] = False
        self.write("summary.json", self.summary)
        with self.assertRaises(ValueError):
            self.check()

    def test_duplicate_case(self) -> None:
        """Equal JUnit counts cannot hide a missing mandatory case."""
        self.suite[1].attrib.update(self.suite[0].attrib)
        self.save_xml()
        with self.assertRaises(ValueError):
            self.check()

    def test_skipped_case(self) -> None:
        """Reject a skipped case even when aggregate counts claim success."""
        ET.SubElement(self.suite[0], "skipped")
        self.save_xml()
        with self.assertRaises(ValueError):
            self.check()

    def test_audit_mismatch(self) -> None:
        """Do not trust a declared PASS when exact debt identities differ."""
        self.write("code-audit.json", {"schema": 1, "status": "PASS", "new": [],
                   "resolved": [], "findings": [{"path": "x", "symbol": "y",
                   "rule": "annotation", "detail": "missing return"}]})
        with self.assertRaises(ValueError):
            self.check()

    def test_unsupported_xml(self) -> None:
        """Refuse DTD input without interpreting entity definitions."""
        path = self.root / "python-results.xml"
        path.write_bytes(b"<!DOCTYPE testsuite []>" + path.read_bytes())
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
