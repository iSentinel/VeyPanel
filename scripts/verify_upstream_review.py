#!/usr/bin/env python3
"""Recompute upstream report status and input bindings from exact snapshots."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from artifact_manifest import read_bounded, strict_json
from check_upstream_review import MAX_REPORT, report


def verify(baseline: bytes, observed: bytes, claimed: bytes) -> dict[str, Any]:
    """Require exact types, values, row order and input digests in the report."""
    expected = report(baseline, observed)
    supplied = strict_json(claimed)
    if json.dumps(supplied, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("Upstream review report mismatch")
    return expected


def main() -> int:
    """Verify supplied evidence only; exit 0 valid, 1 invalid or unavailable."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(*(read_bounded(path, MAX_REPORT) for path in
                          (args.baseline, args.observed, args.report)))
    except (OSError, ValueError, TypeError, RecursionError):
        print("FAIL: upstream review evidence invalid or unavailable", file=sys.stderr)
        return 1
    print(f"PASS: upstream review evidence matches inputs ({result['status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
