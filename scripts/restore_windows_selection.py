#!/usr/bin/env python3
"""Reconstruct a verified package selection in a new private directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
import zipfile

from artifact_manifest import read_bounded, strict_json
from backup_windows_selection import destination_path, verify_backup, write_exclusive
from inspect_package_recovery import bounded_children
from plan_windows_maintenance import plan
from recover_first_install import trusted_record
from stage_windows_package import stage
from windows_package_selection import MAX_STATE, SHA, STATE, root_path, validate_state, version_path


def read_backup(directory: Path, expected: str) -> tuple[bytes, dict[str, Any]]:
    """Bind parsed state to the verified receipt and separately retained digest."""
    receipt = verify_backup(directory, expected)
    raw = read_bounded(directory / STATE, MAX_STATE)
    if hashlib.sha256(raw).hexdigest() != receipt["selection_sha256"]:
        raise ValueError("Backup selection changed")
    state = strict_json(raw)
    validate_state(state)
    return raw, state


def archive_set(directory: Path, state: dict[str, Any]) -> dict[str, Path]:
    """Derive archive paths only from the exact validated selection."""
    return {record["package_sha256"]: directory / (record["package_sha256"] + ".zip")
            for record in (state["active"], state["previous"]) if record}


def restore_plan(directory: Path, backup_sha: str, destination: Path,
                 raw: bytes, state: dict[str, Any]) -> dict[str, Any]:
    """Bind backup metadata, destination path and existing parent identity."""
    parent = destination.parent.stat()
    binding = {"schema": 1, "operation": "restore-selection",
               "backup_plan_sha256": backup_sha, "backup": os.path.normcase(str(directory)),
               "destination": os.path.normcase(str(destination)),
               "parent_device": parent.st_dev, "parent_inode": parent.st_ino,
               "selection_sha256": hashlib.sha256(raw).hexdigest()}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    return {"schema": 1, "plan_sha256": digest, "selection": state,
            "restored": False, "started": False, "maintenance_admitted": False}


def extract_versions(destination: Path, archives: dict[str, Path],
                     state: dict[str, Any]) -> None:
    """Stage only pinned archives and verify each selected tree."""
    destination.mkdir(mode=0o700)
    (destination / "versions").mkdir(mode=0o700)
    for record in (state["active"], state["previous"]):
        if record is None:
            continue
        digest = record["package_sha256"]
        target = version_path(destination, digest)
        stage(archives[digest], digest, target, dry_run=False)
        if trusted_record(destination, target, archives[digest], digest) != record:
            raise ValueError("Restored version differs from backup selection")
    if {child.name for child in bounded_children(destination)} != {"versions"}:
        raise ValueError("Unexpected restore root entries")
    if {child.name for child in bounded_children(destination / "versions")} != set(archives):
        raise ValueError("Unexpected restored version entries")


def restore(directory: Path, backup_sha: str, destination: Path,
            apply: bool = False, expected_plan: str | None = None) -> dict[str, Any]:
    """Default to verification only; apply a reviewed plan to a fresh root."""
    directory = root_path(directory)
    destination = destination_path(directory, destination)
    if not SHA.fullmatch(backup_sha) or apply != (expected_plan is not None):
        raise ValueError("Expected backup digest and explicit restore plan for apply")
    raw, state = read_backup(directory, backup_sha)
    result = restore_plan(directory, backup_sha, destination, raw, state)
    if not apply:
        return result
    if expected_plan != result["plan_sha256"]:
        raise ValueError("Restore plan changed")
    archives = archive_set(directory, state)
    # Retain the parent identity check immediately before creating the new root.
    if restore_plan(directory, backup_sha, destination, raw, state) != result:
        raise ValueError("Restore destination changed")
    extract_versions(destination, archives, state)
    if read_backup(directory, backup_sha) != (raw, state):
        raise ValueError("Backup changed during restore")
    write_exclusive(destination / STATE, raw)
    if read_bounded(destination / STATE, MAX_STATE) != raw:
        raise ValueError("Restored selection readback failed")
    if plan(destination, archives)["selection"] != state:
        raise ValueError("Restored inventory differs")
    result["restored"] = True
    return result


def main() -> int:
    """Use fixed exit codes; never expose private paths in diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--backup-plan-sha256", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--plan-sha256")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = restore(args.directory, args.backup_plan_sha256, args.destination,
                         args.apply, args.plan_sha256)
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            RuntimeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "RESTORE_REFUSED"
        print(f"FAIL: {reason}; preserve incomplete destination for review", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    print("PASS: restored package selection" if result["restored"] else "PASS: read-only restore plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
