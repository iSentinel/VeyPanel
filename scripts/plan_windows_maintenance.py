#!/usr/bin/env python3
"""Inspect a complete retained installation without admitting maintenance."""

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
    MAX_STATE, SHA, STATE, plain, root_path, selection_lock, validate_state, version_path,
)


def inventory(root: Path, state: dict[str, Any]) -> list[dict[str, str]]:
    """Require only selected versions and no unknown root entries."""
    if {child.name for child in bounded_children(root)} != {"versions", STATE}:
        raise ValueError("Unexpected root entries require review")
    records = [record for record in (state["active"], state["previous"]) if record]
    if not records:
        raise ValueError("No selected installation")
    versions = root / "versions"
    plain(versions, directory=True)
    if {child.name for child in bounded_children(versions)} != {
            record["package_sha256"] for record in records}:
        raise ValueError("Unexpected or missing retained versions")
    return records


def plan(root: Path, archives: dict[str, Path]) -> dict[str, Any]:
    """Bind exact metadata and retained versions to external trusted archives."""
    root = root_path(root)
    if not archives or len(archives) > 2 or any(not SHA.fullmatch(key) for key in archives):
        raise ValueError("Expected one or two complete archive digests")
    with selection_lock(root, False):
        raw = read_bounded(root / STATE, MAX_STATE)
        state = strict_json(raw)
        validate_state(state)
        records = inventory(root, state)
        if set(archives) != {record["package_sha256"] for record in records}:
            raise ValueError("Explicit archive set must match all retained versions")
        identity = root.stat()
        for record in records:
            digest = record["package_sha256"]
            if trusted_record(root, version_path(root, digest), archives[digest], digest) != record:
                raise ValueError("Selection differs from trusted archive")
        if read_bounded(root / STATE, MAX_STATE) != raw or inventory(root, state) != records:
            raise ValueError("Installation changed during observation")
        # Recheck the advisory writer lock as well; this is not a held lease.
        with selection_lock(root, False):
            current = root.stat()
        if (identity.st_dev, identity.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("Installation root changed")
        binding = {"schema": 1, "operation": "maintenance-inventory",
                   "root": os.path.normcase(str(root)), "device": identity.st_dev,
                   "inode": identity.st_ino, "state_sha256": hashlib.sha256(raw).hexdigest(),
                   "selection": state}
        encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {"schema": 1, "status": "INVENTORY_VERIFIED",
                "plan_sha256": hashlib.sha256(encoded).hexdigest(),
                "selection": state, "read_only": True,
                "process_state": "NOT_CHECKED", "maintenance_admitted": False,
                "removed": False}


def main() -> int:
    """Accept explicit digest/path pairs; never expose raw paths on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", nargs=2, action="append", required=True,
                        metavar=("SHA256", "ZIP"))
    args = parser.parse_args()
    try:
        archives = {}
        if len(args.archive) > 2:
            raise ValueError("Too many archives")
        for digest, path in args.archive:
            key = digest.lower()
            if key in archives:
                raise ValueError("Duplicate archive digest")
            archives[key] = Path(path)
        result = plan(args.root, archives)
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            RuntimeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "INVENTORY_REFUSED"
        print(f"FAIL: {reason}; review private installation", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS: read-only inventory; maintenance NOT admitted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
