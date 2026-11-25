#!/usr/bin/env python3
"""Classify supplied upstream observations; never fetch or update dependencies."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from artifact_manifest import read_bounded, strict_json

MAX_REPORT = 65536
REPOSITORIES = frozenset({
    "ClassicOldSong/Apollo", "moonlight-stream/moonlight-android",
    "itkawa/screen-spawner", "LibreHardwareMonitor/LibreHardwareMonitor",
})
FIELDS = {"branch", "head", "release_id", "tag", "release_commit", "license",
          "archived"}
SHA = re.compile(r"[0-9a-f]{40}")
LABEL = re.compile(r"[A-Za-z0-9._/+@-]{1,128}")


def valid_row(row: Any) -> bool:
    """Require every reviewed metadata field with its exact type and bounds."""
    if not isinstance(row, dict) or set(row) != FIELDS:
        return False
    return (
        all(isinstance(row[key], str) and LABEL.fullmatch(row[key])
            for key in ("branch", "tag", "license"))
        and all(isinstance(row[key], str) and SHA.fullmatch(row[key])
                and row[key] != "0" * 40 for key in ("head", "release_commit"))
        and type(row["release_id"]) is int
        and 0 < row["release_id"] <= 2**63 - 1
        and type(row["archived"]) is bool
    )


def inventory(document: Any) -> dict[str, Any]:
    """Reject ambiguous schemas or unreviewed repository membership."""
    if (not isinstance(document, dict) or set(document) != {"schema", "repositories"}
            or type(document["schema"]) is not int or document["schema"] != 1
            or not isinstance(document["repositories"], dict)
            or set(document["repositories"]) - REPOSITORIES):
        raise ValueError("Invalid upstream inventory")
    return document["repositories"]


def classify(baseline: Any, observed: Any) -> list[dict[str, Any]]:
    """Distinguish changed, complete unchanged, and missing/invalid observations."""
    expected = inventory(baseline)
    actual = inventory(observed)
    if set(expected) != REPOSITORIES or not all(map(valid_row, expected.values())):
        raise ValueError("Invalid upstream baseline")
    results = []
    for repo in sorted(expected):
        row = actual.get(repo)
        if not valid_row(row):
            results.append({"repository": repo, "status": "ERROR", "changed": []})
            continue
        changed = sorted(key for key in FIELDS if row[key] != expected[repo][key])
        results.append({"repository": repo, "status": "REVIEW" if changed else "UNCHANGED",
                        "changed": changed})
    return results


def report(baseline: bytes, observed: bytes) -> dict[str, Any]:
    """Bind classification to the exact supplied byte snapshots."""
    rows = classify(strict_json(baseline), strict_json(observed))
    status = ("ERROR" if any(row["status"] == "ERROR" for row in rows) else
              "REVIEW" if any(row["status"] == "REVIEW" for row in rows) else
              "UNCHANGED")
    return {"schema": 1, "status": status, "rows": rows,
            "baseline_sha256": hashlib.sha256(baseline).hexdigest(),
            "observed_sha256": hashlib.sha256(observed).hexdigest()}


def main() -> int:
    """Emit a bounded review-only result; 0 unchanged, 2 review, 1 error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = report(read_bounded(args.baseline, MAX_REPORT),
                        read_bounded(args.observed, MAX_REPORT))
    except (OSError, ValueError, TypeError):
        print("ERROR: upstream evidence unavailable or invalid", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return {"UNCHANGED": 0, "REVIEW": 2, "ERROR": 1}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
