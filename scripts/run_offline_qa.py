#!/usr/bin/env python3
"""Run the common Python offline gate and publish scoped JSON/JUnit evidence."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from typing import TextIO

from code_audit import differences, load_baseline, scan
from qa_events import emit
from qa_case_inventory import compare_cases, discovered_cases, execution_passed, load_cases

ROOT = Path(__file__).resolve().parent.parent


class EvidenceResult(unittest.TestResult):
    """Capture sanitized outcomes; do not publish exception variables."""

    def __init__(self) -> None:
        """Initialize a single execution record per test."""
        super().__init__()
        self.rows: dict[str, tuple[str, float]] = {}
        self.started: dict[str, float] = {}

    def startTest(self, test: unittest.TestCase) -> None:
        """Start monotonic timing."""
        super().startTest(test)
        self.started[test.id()] = time.monotonic()

    def record(self, test: unittest.TestCase, status: str) -> None:
        """Record only case identity, status and elapsed seconds."""
        key = test.id()
        self.rows[key] = (status, time.monotonic() - self.started.get(key, time.monotonic()))

    def addSuccess(self, test: unittest.TestCase) -> None:
        """Record success."""
        super().addSuccess(test)
        self.record(test, "PASS")

    def addFailure(self, test: unittest.TestCase, err: tuple) -> None:
        """Record failure without exporting a traceback."""
        super().addFailure(test, err)
        self.record(test, "FAIL")

    def addError(self, test: unittest.TestCase, err: tuple) -> None:
        """Record error without exporting a traceback."""
        super().addError(test, err)
        self.record(test, "ERROR")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        """Record skip without exporting arbitrary reason text."""
        super().addSkip(test, reason)
        self.record(test, "SKIPPED")

    def addExpectedFailure(self, test: unittest.TestCase, err: tuple) -> None:
        """Expected failure is not positive acceptance evidence."""
        super().addExpectedFailure(test, err)
        self.record(test, "SKIPPED")

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        """Unexpected success is a failed expectation."""
        super().addUnexpectedSuccess(test)
        self.record(test, "FAIL")

    def addSubTest(self, test: unittest.TestCase, subtest: unittest.TestCase,
                   err: tuple | None) -> None:
        """Preserve failing subtests as failed parent cases."""
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(test, "FAIL")


def write_junit(path: Path, result: EvidenceResult, duration: float) -> None:
    """Write a JUnit suite containing actual recorded case outcomes."""
    rows = result.rows
    suite = ET.Element("testsuite", name="veypanel.python.offline",
                       tests=str(len(rows)),
                       failures=str(sum(s == "FAIL" for s, _ in rows.values())),
                       errors=str(sum(s == "ERROR" for s, _ in rows.values())),
                       skipped=str(sum(s == "SKIPPED" for s, _ in rows.values())),
                       time=f"{duration:.6f}")
    for name, (status, elapsed) in sorted(rows.items()):
        owner, _, method = name.rpartition(".")
        case = ET.SubElement(suite, "testcase", classname=owner, name=method,
                             time=f"{max(0, elapsed):.6f}")
        if status != "PASS":
            tag = {"FAIL": "failure", "ERROR": "error", "SKIPPED": "skipped"}[status]
            ET.SubElement(case, tag, message="See scoped test result")
    ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)


def git_value(*args: str) -> str:
    """Read exact checkout metadata with a bounded command."""
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


def write_json(path: Path, data: dict) -> None:
    """Write a unique evidence file, refusing overwrite."""
    with path.open("x", encoding="utf-8") as output:
        json.dump(data, output, indent=2, sort_keys=True)
        output.write("\n")


def run_required_tests(output: Path) -> tuple[EvidenceResult, dict[str, object], bool]:
    """Fail closed on missing, duplicate or skipped mandatory cases."""
    expected = load_cases(ROOT / "config/python-qa-cases.json")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "scripts"), pattern="test_*.py")
    inventory = compare_cases(expected, discovered_cases(suite))
    result = EvidenceResult()
    start = time.monotonic()
    if inventory["status"] == "PASS":
        suite.run(result)
    write_junit(output / "python-results.xml", result, time.monotonic() - start)
    ok = inventory["status"] == "PASS" and execution_passed(
        expected, result.rows, result.testsRun, result.wasSuccessful())
    write_json(output / "case-inventory.json", {"schema": 1, **inventory,
               "execution_status": "PASS" if ok else "FAIL"})
    return result, inventory, ok


def run(output: Path, events: TextIO | None = None) -> bool:
    """Run source gate and tests, preserving both independent results."""
    output.mkdir(mode=0o700, exist_ok=False)
    start = time.monotonic()
    utc = datetime.now(timezone.utc).isoformat()
    audit_start = time.monotonic()
    rows = scan(ROOT)
    delta = differences(rows, load_baseline(ROOT / "config/code-audit-baseline.json"))
    audit_ok = not any(delta.values())
    write_json(output / "code-audit.json", {"schema": 1, "findings": rows,
                                          **delta, "status": "PASS" if audit_ok else "FAIL"})
    emit(events, "audit", "PASS" if audit_ok else "FAIL", time.monotonic() - audit_start)
    test_start = time.monotonic()
    result, inventory, tests_ok = run_required_tests(output)
    passed = sum(status == "PASS" for status, _ in result.rows.values())
    emit(events, "tests", "PASS" if tests_ok else "FAIL", time.monotonic() - test_start)
    ok = audit_ok and tests_ok
    report_start = time.monotonic()
    write_json(output / "summary.json", {
        "schema": 1, "scope": "python-offline", "status": "PASS" if ok else "FAIL",
        "started_utc": utc, "duration_seconds": time.monotonic() - start,
        "git_commit": git_value("rev-parse", "HEAD"), "git_tree": git_value("rev-parse", "HEAD^{tree}"),
        "tracked_checkout_clean": not git_value("status", "--porcelain", "--untracked-files=no"),
        "python": platform.python_version(), "platform": platform.system(),
        "audit_status": "PASS" if audit_ok else "FAIL", "debt_count": len(rows),
        "required_cases": inventory["expected_count"], "inventory_status": inventory["status"],
        "tests_run": result.testsRun, "passed": passed, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses),
        "native_windows": "NOT_RUN", "native_android": "NOT_RUN", "hardware": "NOT_RUN",
    })
    emit(events, "report", "PASS", time.monotonic() - report_start)
    return ok


def main() -> int:
    """Require a fresh private output directory and return nonzero on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--log-events", action="store_true", help="Write closed JSONL stage events to stderr")
    args = parser.parse_args()
    events = sys.stderr if args.log_events else None
    started = time.monotonic()
    try:
        ok = run(args.output, events)
    except (OSError, ValueError, SyntaxError, KeyError, TypeError,
            AttributeError, subprocess.SubprocessError) as error:
        if events is not None:
            emit(events, "run", "ERROR", time.monotonic() - started)
        else:
            print("FAIL: offline QA: " + type(error).__name__, file=sys.stderr)
        return 1
    emit(events, "run", "PASS" if ok else "FAIL", time.monotonic() - started)
    print("PASS: scoped Python offline QA" if ok else "FAIL: scoped Python offline QA")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
