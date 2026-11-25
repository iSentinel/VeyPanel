#!/usr/bin/env python3
"""Independently verify accepted offline QA evidence against a reviewed checkout."""

import argparse
import math
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET

from artifact_manifest import read_bounded, strict_json
from code_audit import differences, load_baseline
from qa_case_inventory import compare_cases, load_cases
from run_offline_qa import git_value

MAX_REPORT = 2 * 1024 * 1024


def read_report(path: Path) -> dict[str, Any]:
    """Read strict bounded JSON with an exact version marker."""
    data = strict_json(read_bounded(path, MAX_REPORT))
    if not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != 1:
        raise ValueError("Invalid report schema")
    return data


def require_fields(data: dict[str, Any], fields: dict[str, Any]) -> None:
    """Check both value and type to reject boolean/numeric aliases."""
    if any(type(data.get(key)) is not type(value) or data.get(key) != value
           for key, value in fields.items()):
        raise ValueError("Report fields disagree")


def duration(value: object) -> None:
    """Require a finite nonnegative duration within one day."""
    if type(value) not in (float, int) or not 0 <= value <= 86400 or not math.isfinite(value):
        raise ValueError("Invalid report duration")


def verify_junit(path: Path, expected: tuple[str, ...]) -> None:
    """Require exact successful case identities and consistent suite counts."""
    raw = read_bounded(path, MAX_REPORT)
    # Only UTF-8 writer output is supported; no DTD or entity declarations.
    source = raw.decode("utf-8")
    declaration = "<?xml version='1.0' encoding='utf-8'?>"
    content = source[len(declaration):] if source.startswith(declaration) else source
    if "<!" in content or "<?" in content or "\x00" in content:
        raise ValueError("Unsupported XML declaration")
    suite = ET.fromstring(source)
    if (suite.tag != "testsuite" or suite.attrib.get("name") != "veypanel.python.offline"
            or set(suite.attrib) != {"name", "tests", "failures", "errors", "skipped", "time"}
            or (suite.text or "").strip() or (suite.tail or "").strip()):
        raise ValueError("Unexpected JUnit suite")
    require_fields(suite.attrib, {"tests": str(len(expected)), "failures": "0",
                                  "errors": "0", "skipped": "0"})
    duration(float(suite.attrib["time"]))
    identities = []
    for case in suite:
        if (case.tag != "testcase" or len(case) or (case.text or "").strip()
                or (case.tail or "").strip()
                or set(case.attrib) != {"classname", "name", "time"}):
            raise ValueError("Nonpassing or invalid JUnit case")
        identities.append(case.attrib["classname"] + "." + case.attrib["name"])
        duration(float(case.attrib["time"]))
    if compare_cases(expected, identities)["status"] != "PASS":
        raise ValueError("JUnit case inventory mismatch")


def verify(directory: Path, expected: tuple[str, ...], baseline: list[dict],
           commit: str, tree: str) -> None:
    """Cross-check four actual reports against independent source expectations."""
    count = len(expected)
    summary = read_report(directory / "summary.json")
    require_fields(summary, {
        "scope": "python-offline", "status": "PASS", "audit_status": "PASS",
        "inventory_status": "PASS", "git_commit": commit, "git_tree": tree,
        "tracked_checkout_clean": True, "debt_count": len(baseline),
        "required_cases": count, "tests_run": count, "passed": count,
        "errors": 0, "failures": 0, "skipped": 0, "expected_failures": 0,
        "unexpected_successes": 0, "unattributed_outcomes": 0, "native_windows": "NOT_RUN",
        "native_android": "NOT_RUN", "hardware": "NOT_RUN"})
    duration(summary["duration_seconds"])
    inventory = read_report(directory / "case-inventory.json")
    require_fields(inventory, {
        "status": "PASS", "execution_status": "PASS", "expected_count": count,
        "observed_count": count, "missing": [], "unexpected_count": 0, "duplicate_count": 0})
    audit = read_report(directory / "code-audit.json")
    require_fields(audit, {"status": "PASS", "new": [], "resolved": []})
    if not isinstance(audit.get("findings"), list) or any(differences(audit["findings"], baseline).values()):
        raise ValueError("Audit baseline identity mismatch")
    verify_junit(directory / "python-results.xml", expected)


def main() -> int:
    """Verify evidence against the current checkout without modifying reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parent.parent
        if git_value("status", "--porcelain", "--untracked-files=no"):
            raise ValueError("Tracked checkout is dirty")
        verify(args.report, load_cases(root / "config/python-qa-cases.json"),
               load_baseline(root / "config/code-audit-baseline.json"),
               git_value("rev-parse", "HEAD"), git_value("rev-parse", "HEAD^{tree}"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as error:
        print("FAIL: offline QA evidence: " + type(error).__name__, file=sys.stderr)
        return 1
    print("PASS: offline QA evidence matches required cases and current checkout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
