#!/usr/bin/env python3
"""Compare resolved component coordinates with a reviewed CI baseline."""

import argparse
import json
import sys
from pathlib import Path

MAX_REPORT = 8 * 1024 * 1024
MAX_COMPONENTS = 10000


def read_json(path):
    """Load bounded UTF-8 JSON."""
    if path.stat().st_size > MAX_REPORT:
        raise ValueError("Inventory exceeds size budget")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def coordinates(bom):
    """Extract a validated, unique package-URL set for one inventory scope."""
    if bom.get("bomFormat") != "CycloneDX" or bom.get("specVersion") != "1.5":
        raise ValueError("Expected CycloneDX 1.5 component inventory")
    scope = bom["metadata"]["component"]["name"]
    if not isinstance(scope, str) or not scope:
        raise ValueError("Missing inventory scope")
    components = bom["components"]
    if not isinstance(components, list) or not 0 < len(components) <= MAX_COMPONENTS:
        raise ValueError("Empty or excessive component inventory")
    urls = set()
    for item in components:
        url = item["purl"]
        if (not isinstance(url, str) or not url.startswith(("pkg:maven/", "pkg:nuget/"))
                or "@" not in url or len(url) > 1024 or url in urls
                or any(ord(char) < 33 for char in url)):
            raise ValueError("Invalid or duplicate component package URL")
        urls.add(url)
    return scope, urls


def compare(baseline, actual):
    """Return additions and removals; refuse unrelated inventory scopes."""
    expected_scope, expected = coordinates(baseline)
    actual_scope, current = coordinates(actual)
    if expected_scope != actual_scope:
        raise ValueError("Dependency inventory scope differs")
    return sorted(current - expected), sorted(expected - current)


def main():
    """Report drift with stable exit codes; never rewrite a baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    try:
        added, removed = compare(read_json(args.baseline), read_json(args.actual))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"FAIL: dependency baseline: {error}", file=sys.stderr)
        return 1
    for item in added:
        print(f"ADDED: {item}")
    for item in removed:
        print(f"REMOVED: {item}")
    if added or removed:
        print("FAIL: resolved dependency drift; review the baseline before changing it")
        return 1
    print("PASS: resolved component coordinates match reviewed baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
