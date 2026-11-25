#!/usr/bin/env python3
"""Reconstruct absent selection metadata from one explicitly trusted staged package."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

from artifact_manifest import MANIFEST, hash_file
from inspect_package_recovery import bounded_children
from stage_windows_package import preflight
from windows_package_selection import (
    LOCK, SHA, STATE, plain, present, read_state, root_path,
    selection_lock, verify_record, version_path, write_state,
)


def check_root(root: Path, expected: str, apply: bool) -> Path:
    """Refuse existing state, ambiguous roots, leftover locks and temp files."""
    allowed = {"versions", LOCK} if apply else {"versions"}
    if present(root / STATE):
        raise ValueError("Existing selection state requires separate reconciliation")
    if {child.name for child in bounded_children(root)} != allowed:
        raise ValueError("Unexpected root entries require manual review")
    versions = root / "versions"
    plain(versions, directory=True)
    if [child.name for child in bounded_children(versions)] != [expected]:
        raise ValueError("Expected exactly one explicitly selected version")
    directory = version_path(root, expected)
    plain(directory, directory=True)
    return directory


def trusted_record(root: Path, directory: Path, package: Path,
                   expected: str) -> dict[str, str]:
    """Bind the complete staged tree to the externally pinned original ZIP."""
    plain(package)
    if package.resolve().is_relative_to(root.resolve()):
        raise ValueError("Trusted archive must be outside installation root")
    if hash_file(package) != expected:
        raise ValueError("External SHA-256 mismatch")
    with zipfile.ZipFile(package) as archive:
        preflight(archive)
        manifest_digest = hashlib.sha256(archive.read(MANIFEST)).hexdigest()
    if hash_file(package) != expected:
        raise ValueError("Archive changed during verification")
    record = {"package_sha256": expected, "manifest_sha256": manifest_digest}
    if verify_record(root, record) != directory:
        raise ValueError("Unexpected staged directory")
    return record


def plan(root: Path, package: Path, expected: str,
         apply: bool = False) -> tuple[dict[str, object], str]:
    """Build a deterministic root-bound selection plan without mutating payloads."""
    directory = check_root(root, expected, apply)
    record = trusted_record(root, directory, package, expected)
    state = {"schema": 1, "active": record, "previous": None}
    identity = root.stat()
    binding = {"schema": 1, "operation": "recover-first-install",
               "root": os.path.normcase(str(root)), "device": identity.st_dev,
               "inode": identity.st_ino, "state_before": "absent", "state": state}
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return state, hashlib.sha256(encoded).hexdigest()


def recover(root: Path, package: Path, expected: str, apply: bool = False,
            expected_plan: str | None = None) -> dict[str, object]:
    """Recheck the plan under the cooperating lock; only write missing metadata."""
    root = root_path(root)
    expected = expected.lower()
    if not SHA.fullmatch(expected):
        raise ValueError("Expected complete SHA-256")
    if apply and (expected_plan is None or not SHA.fullmatch(expected_plan)):
        raise ValueError("Apply requires the prior plan SHA-256")
    if not apply and expected_plan is not None:
        raise ValueError("Plan SHA-256 is only accepted with apply")
    with selection_lock(root, apply):
        state, plan_sha = plan(root, package, expected, apply)
        if apply:
            if expected_plan != plan_sha:
                raise ValueError("Recovery plan changed")
            check_root(root, expected, True)
            write_state(root, state)
            if read_state(root) != state:
                raise ValueError("Recovery readback failed; reconcile before retry")
            verify_record(root, state["active"])
        return {"schema": 1, "plan_sha256": plan_sha, "selection": state,
                "applied": apply, "started": False}


def main() -> int:
    """Default to dry-run; apply only an explicitly reviewed plan."""
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
        result = recover(args.root, args.package, args.sha256,
                         args.apply, args.plan_sha256)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            AttributeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "RECOVERY_REFUSED"
        print(f"FAIL: {reason}; inspect private state before retry", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS: selection metadata restored" if args.apply else "PASS: read-only recovery plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
