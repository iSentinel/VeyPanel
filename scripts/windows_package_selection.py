#!/usr/bin/env python3
"""Select verified side-by-side packages without starting any executable."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile

from artifact_manifest import MANIFEST, collect, compare, hash_file
from stage_windows_package import stage

STATE = "selection.json"
LOCK = ".selection-lock"
MAX_STATE = 8192
SHA = re.compile(r"[0-9a-f]{64}")


def plain(path, directory=False):
    """Require a non-reparse regular file or directory."""
    info = path.lstat()
    if (path.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400
            or not (path.is_dir() if directory else path.is_file())):
        raise ValueError("Unsafe selection path: " + str(path))


def present(path):
    """Detect even a dangling symbolic link."""
    return path.exists() or path.is_symlink()


def root_path(root):
    """Use an existing private directory, refusing links and parent traversal."""
    if ".." in root.parts:
        raise ValueError("Parent traversal is not allowed")
    root = root.absolute()
    for path in (root, *root.parents):
        plain(path, directory=True)
    return root


def record_valid(record):
    """Validate both digest fields before using a version directory."""
    return (isinstance(record, dict)
            and set(record) == {"package_sha256", "manifest_sha256"}
            and all(isinstance(value, str) and SHA.fullmatch(value)
                    for value in record.values()))


def read_state(root):
    """Reject malformed state or uninitialized roots containing versions."""
    path = root / STATE
    versions = root / "versions"
    if present(versions):
        plain(versions, directory=True)
    if not present(path):
        if present(versions) and any(versions.iterdir()):
            raise ValueError("Unreferenced versions require manual inspection")
        return {"schema": 1, "active": None, "previous": None}
    plain(path)
    if path.stat().st_size > MAX_STATE:
        raise ValueError("Selection state exceeds size budget")
    data = json.loads(path.read_bytes())
    if (not isinstance(data, dict) or set(data) != {"schema", "active", "previous"}
            or type(data["schema"]) is not int or data["schema"] != 1
            or not record_valid(data["active"])
            or (data["previous"] is not None and not record_valid(data["previous"]))
            or (data["previous"] is not None and
                data["active"]["package_sha256"] == data["previous"]["package_sha256"])):
        raise ValueError("Invalid selection state")
    return data


def version_path(root, package_sha):
    """Resolve a digest-derived path only within the versions directory."""
    if not SHA.fullmatch(package_sha):
        raise ValueError("Expected complete SHA-256")
    return root / "versions" / package_sha


def verify_record(root, record):
    """Verify a selected tree against the manifest hash stored in state."""
    if not record_valid(record):
        raise ValueError("Invalid version record")
    path = version_path(root, record["package_sha256"])
    plain(path.parent, directory=True)
    plain(path, directory=True)
    manifest = path / MANIFEST
    plain(manifest)
    if hash_file(manifest) != record["manifest_sha256"]:
        raise ValueError("Selected manifest digest mismatch")
    if any(compare(json.loads(manifest.read_bytes()), collect(path)).values()):
        raise ValueError("Selected package files differ")
    return path


@contextmanager
def selection_lock(root, apply):
    """Serialize cooperating writers; fail closed after abrupt interruption."""
    lock = root / LOCK
    if not apply:
        if present(lock):
            raise ValueError("Selection is locked; inspect interrupted operation")
        yield
        return
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise ValueError("Selection is locked; inspect interrupted operation") from error
    try:
        yield
    finally:
        lock.rmdir()


def write_state(root, state):
    """Flush a new state file and atomically replace the old selection."""
    encoded = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".selection-",
                                         delete=False) as output:
            name = Path(output.name)
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, root / STATE)
    finally:
        if name is not None:
            name.unlink(missing_ok=True)


def select(root, package, expected, apply):
    """Stage a new package or verify an already selected identical package."""
    root = root_path(root)
    expected = expected.lower()
    destination = version_path(root, expected)
    with selection_lock(root, apply):
        state = read_state(root)
        active = state["active"]
        if active is not None:
            verify_record(root, active)
            if active["package_sha256"] == expected:
                # The supplied archive must still match the requested digest.
                if hash_file(package) != expected:
                    raise ValueError("External SHA-256 mismatch")
                return state
        if present(destination):
            raise ValueError("Version already exists; use rollback or inspect orphan")
        # Dry-run preflights against a nonexistent path under an existing parent.
        probe = destination if present(destination.parent) else root / expected
        stage(package, expected, probe, dry_run=True)
        if not apply:
            return {"schema": 1, "candidate_sha256": expected, "active": active}
        destination.parent.mkdir(exist_ok=True)
        plain(destination.parent, directory=True)
        stage(package, expected, destination, dry_run=False)
        record = {"package_sha256": expected,
                  "manifest_sha256": hash_file(destination / MANIFEST)}
        verify_record(root, record)
        updated = {"schema": 1, "active": record, "previous": active}
        write_state(root, updated)
        return updated


def rollback(root, apply):
    """Verify the prior version before switching the selection atomically."""
    root = root_path(root)
    with selection_lock(root, apply):
        state = read_state(root)
        previous = state["previous"]
        if previous is None:
            raise ValueError("No previous selection")
        verify_record(root, previous)
        updated = {"schema": 1, "active": previous, "previous": state["active"]}
        if apply:
            write_state(root, updated)
        return updated


def status(root):
    """Resolve and verify the selected version without starting it."""
    root = root_path(root)
    with selection_lock(root, False):
        state = read_state(root)
        if state["active"] is not None:
            verify_record(root, state["active"])
        return state


def main():
    """Default to dry-run; explicit apply only changes selection metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("select")
    install.add_argument("package", type=Path)
    install.add_argument("--sha256", required=True)
    for command in (install, sub.add_parser("rollback")):
        modes = command.add_mutually_exclusive_group()
        modes.add_argument("--dry-run", action="store_true")
        modes.add_argument("--apply", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.action == "select":
            result = select(args.root, args.package, args.sha256, args.apply)
        elif args.action == "rollback":
            result = rollback(args.root, args.apply)
        else:
            result = status(args.root)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            AttributeError, zipfile.BadZipFile) as error:
        print(f"FAIL: package selection: {error}", file=sys.stderr)
        return 1
    print("PASS: package selection; no application started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
