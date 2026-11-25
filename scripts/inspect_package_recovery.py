#!/usr/bin/env python3
"""Inspect interrupted package selection without removing or activating files."""

import argparse
import json
from pathlib import Path
import sys

from windows_package_selection import (
    LOCK, SHA, STATE, plain, present, read_state, root_path, verify_record,
)

MAX_ITEMS = 256
ERRORS = (OSError, ValueError, KeyError, TypeError, AttributeError)


def bounded_children(path: Path) -> list[Path]:
    """Inspect at most a bounded number of directory entries."""
    children = []
    for child in path.iterdir():
        if len(children) >= MAX_ITEMS:
            raise ValueError("Recovery inspection directory budget exceeded")
        children.append(child)
    return sorted(children, key=lambda child: child.name)


def inspect_record(root: Path, record: dict[str, str] | None) -> dict[str, str]:
    """Report integrity without trusting a damaged tree or running code."""
    if record is None:
        return {"status": "absent"}
    try:
        verify_record(root, record)
    except ERRORS:
        return {"status": "invalid", "package_sha256": record["package_sha256"]}
    return {"status": "verified", "package_sha256": record["package_sha256"]}


def inspect_versions(root: Path, referenced: set[str]) -> list[dict[str, str]]:
    """Classify digest directories but never adopt an unreferenced package."""
    path = root / "versions"
    if not present(path):
        return []
    plain(path, directory=True)
    result = []
    for child in bounded_children(path):
        if not SHA.fullmatch(child.name):
            result.append({"status": "unexpected-name"})
            continue
        try:
            plain(child, directory=True)
        except ERRORS:
            result.append({"status": "unsafe-path", "package_sha256": child.name})
            continue
        result.append({"status": "referenced" if child.name in referenced
                       else "unreferenced", "package_sha256": child.name})
    return result


def inspect(root: Path) -> dict[str, object]:
    """Return an advisory read-only snapshot; locks are never considered stale."""
    root = root_path(root)
    lock = root / LOCK
    locked = present(lock)
    items = bounded_children(root)
    temporary = sum(item.name.startswith(".selection-") and item.name != LOCK
                    for item in items)
    state_status = "absent"
    state = None
    if present(root / STATE):
        try:
            state = read_state(root)
            state_status = "readable"
        except ERRORS:
            state_status = "invalid"
    referenced = {record["package_sha256"] for record in
                  (state["active"], state["previous"]) if record} if state else set()
    active = inspect_record(root, state["active"]) if state else {"status": "unknown"}
    previous = inspect_record(root, state["previous"]) if state else {"status": "unknown"}
    versions = inspect_versions(root, referenced)
    needs_review = (locked or temporary > 0 or state_status == "invalid"
                    or any(row["status"] != "referenced" for row in versions)
                    or active["status"] == "invalid" or previous["status"] == "invalid")
    return {"schema": 1, "read_only": True, "lock_present": locked,
            "state_status": state_status, "temporary_state_count": temporary,
            "active": active, "previous": previous, "versions": versions,
            "manual_review_required": needs_review}


def main() -> int:
    """Report inspection results, returning 2 for manual review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.root)
    except ERRORS as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "INVALID_INSPECTION_STATE"
        print(f"FAIL: recovery inspection: {reason}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["manual_review_required"]:
        print("REVIEW: interrupted or inconsistent state; no changes made")
        return 2
    print("PASS: no recovery anomaly found; no changes made")
    return 0


if __name__ == "__main__":
    sys.exit(main())
