"""Reviewed offline test identities and exact discovery/execution acceptance."""

from collections import Counter
from pathlib import Path
import re
import unittest

from artifact_manifest import read_bounded, strict_json

MAX_CATALOG = 128 * 1024
MAX_CASES = 2000
CASE_ID = re.compile(r"test_[A-Za-z0-9_]+\.[A-Za-z_][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+")


def load_cases(path: Path) -> tuple[str, ...]:
    """Require a bounded, sorted and unique explicit inventory of case IDs."""
    data = strict_json(read_bounded(path, MAX_CATALOG))
    if (not isinstance(data, dict) or set(data) != {"schema", "cases"}
            or type(data["schema"]) is not int or data["schema"] != 1):
        raise ValueError("Invalid case inventory schema")
    cases = data["cases"]
    if (not isinstance(cases, list) or not 0 < len(cases) <= MAX_CASES
            or any(not isinstance(case, str) or len(case) > 256
                   or not CASE_ID.fullmatch(case) for case in cases)
            or cases != sorted(set(cases))):
        raise ValueError("Invalid case inventory identities")
    return tuple(cases)


def discovered_cases(suite: unittest.TestSuite) -> list[str]:
    """Flatten unittest discovery with a bounded iterative traversal."""
    stack = [iter(suite)]
    cases = []
    visited = 0
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        visited += 1
        if visited > MAX_CASES * 4 or len(stack) > 32:
            raise ValueError("Discovery traversal limit")
        if isinstance(item, unittest.TestSuite):
            stack.append(iter(item))
        else:
            cases.append(item.id())
            if len(cases) > MAX_CASES:
                raise ValueError("Discovery case limit")
    return cases


def compare_cases(expected: tuple[str, ...], actual: list[str]) -> dict[str, object]:
    """Report missing reviewed IDs and only counts for unexpected identities."""
    wanted, found = Counter(expected), Counter(actual)
    missing = list(sorted((wanted - found).elements()))
    unexpected = sum((found - wanted).values())
    duplicates = sum(max(0, count - 1) for count in found.values())
    return {"missing": missing, "unexpected_count": unexpected,
            "duplicate_count": duplicates, "expected_count": len(expected),
            "observed_count": len(actual),
            "status": "PASS" if not missing and not unexpected else "FAIL"}


def execution_passed(expected: tuple[str, ...], rows: dict[str, tuple[str, float]],
                     tests_run: int, successful: bool) -> bool:
    """Require each mandatory case to actually pass, with no extra outcomes."""
    return (successful and tests_run == len(expected)
            and set(rows) == set(expected)
            and all(status == "PASS" for status, _ in rows.values()))
