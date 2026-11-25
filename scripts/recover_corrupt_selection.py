#!/usr/bin/env python3
"""Reconcile bounded corrupt selection metadata in an isolated single-version root."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
import zipfile

from artifact_manifest import read_bounded, strict_json
from inspect_package_recovery import bounded_children
from recover_first_install import trusted_record
from windows_package_selection import (
    LOCK, MAX_STATE, SHA, STATE, plain, read_state, root_path,
    selection_lock, validate_state, verify_record, version_path, write_state,
)

BACKUP = ".selection-corrupt-backup"


def check_root(root: Path, expected: str, locked: bool,
               backup: bool = False) -> Path:
    """Allow only the exact single-version maintenance layout."""
    allowed = {"versions", STATE}
    if locked:
        allowed.add(LOCK)
    if backup:
        allowed.add(BACKUP)
    if {child.name for child in bounded_children(root)} != allowed:
        raise ValueError("Unexpected root entries require manual review")
    versions = root / "versions"
    plain(versions, directory=True)
    if [child.name for child in bounded_children(versions)] != [expected]:
        raise ValueError("Expected exactly one explicitly selected version")
    directory = version_path(root, expected)
    plain(directory, directory=True)
    return directory


def corrupt_bytes(root: Path) -> bytes:
    """Require actual invalid schema or syntax, not a read or integrity error."""
    raw = read_bounded(root / STATE, MAX_STATE)
    try:
        validate_state(strict_json(raw))
    except ValueError:
        return raw
    raise ValueError("Existing valid metadata cannot be repaired by this tool")


def plan(root: Path, package: Path, expected: str,
         locked: bool) -> tuple[dict[str, Any], bytes, str]:
    """Bind the proposed state and original corrupt bytes to this root."""
    directory = check_root(root, expected, locked)
    raw = corrupt_bytes(root)
    record = trusted_record(root, directory, package, expected)
    state = {"schema": 1, "active": record, "previous": None}
    identity = root.stat()
    binding = {"schema": 1, "operation": "repair-corrupt-selection",
               "root": os.path.normcase(str(root)), "device": identity.st_dev,
               "inode": identity.st_ino, "original_sha256": hashlib.sha256(raw).hexdigest(),
               "state": state}
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return state, raw, hashlib.sha256(encoded).hexdigest()


def preserve(root: Path, raw: bytes) -> None:
    """Create a private non-overwriting backup and verify its exact bytes."""
    target = root / BACKUP
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(target, flags, 0o600), "wb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    if read_bounded(target, MAX_STATE) != raw:
        raise ValueError("Backup readback failed; manual review required")


def apply_repair(root: Path, expected: str, raw: bytes,
                 state: dict[str, Any]) -> None:
    """Preserve old bytes before replacement; retain any backup on failure."""
    check_root(root, expected, True)
    if corrupt_bytes(root) != raw:
        raise ValueError("Corrupt state changed")
    preserve(root, raw)
    check_root(root, expected, True, backup=True)
    if corrupt_bytes(root) != raw:
        raise ValueError("Corrupt state changed after backup")
    write_state(root, state)
    if read_state(root) != state:
        raise ValueError("Repair readback failed; manual review required")
    verify_record(root, state["active"])


def repair(root: Path, package: Path, expected: str, apply: bool = False,
           expected_plan: str | None = None) -> dict[str, Any]:
    """Plan by default; explicitly apply only a previously reviewed plan."""
    root = root_path(root)
    expected = expected.lower()
    if not SHA.fullmatch(expected):
        raise ValueError("Expected complete SHA-256")
    if apply and (expected_plan is None or not SHA.fullmatch(expected_plan)):
        raise ValueError("Apply requires the prior plan SHA-256")
    if not apply and expected_plan is not None:
        raise ValueError("Plan SHA-256 is only accepted with apply")
    with selection_lock(root, apply):
        state, raw, digest = plan(root, package, expected, apply)
        if apply:
            if digest != expected_plan:
                raise ValueError("Recovery plan changed")
            apply_repair(root, expected, raw, state)
        return {"schema": 1, "plan_sha256": digest,
                "original_sha256": hashlib.sha256(raw).hexdigest(),
                "selection": state, "backup_name": BACKUP,
                "applied": apply, "started": False}


def main() -> int:
    """Expose fixed failure reasons without returning corrupt data or paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--plan-sha256")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = repair(args.root, args.package, args.sha256, args.apply, args.plan_sha256)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            AttributeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "REPAIR_REFUSED"
        print(f"FAIL: {reason}; inspect private state and retained backup", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS: metadata repaired; retain backup for manual review" if args.apply
          else "PASS: read-only repair plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
