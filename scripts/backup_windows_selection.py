#!/usr/bin/env python3
"""Copy verified selection metadata and original archives into a fresh backup."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any
import zipfile

from artifact_manifest import (
    MANIFEST, MAX_HASH_BYTES, file_identity, hash_file, read_bounded,
    regular, same_open_file, strict_json,
)
from inspect_package_recovery import bounded_children
from plan_windows_maintenance import plan
from stage_windows_package import preflight
from windows_package_selection import (
    MAX_STATE, SHA, STATE, present, root_path, validate_state,
)

RECEIPT = "backup-receipt.json"


def destination_path(root: Path, destination: Path) -> Path:
    """Require a fresh destination outside the installation tree."""
    if ".." in destination.parts:
        raise ValueError("Parent traversal is not allowed")
    destination = destination.absolute()
    root_path(destination.parent)
    if destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError("Backup must be outside the installation")
    if present(destination):
        raise ValueError("Backup destination already exists")
    return destination


def write_exclusive(path: Path, data: bytes) -> None:
    """Flush a new file without replacing any previous backup data."""
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def copy_archive(source: Path, target: Path, expected: str) -> None:
    """Stream bounded source bytes into a new file and verify readback."""
    initial = source.lstat()
    if not regular(initial) or not 0 < initial.st_size <= MAX_HASH_BYTES:
        raise ValueError("Unsafe archive source")
    digest = hashlib.sha256()
    with source.open("rb") as incoming, target.open("xb") as outgoing:
        opened = os.fstat(incoming.fileno())
        if not same_open_file(initial, opened):
            raise ValueError("Archive changed before copying")
        remaining = initial.st_size
        while remaining:
            block = incoming.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError("Archive truncated during copying")
            outgoing.write(block)
            digest.update(block)
            remaining -= len(block)
        if incoming.read(1) or file_identity(os.fstat(incoming.fileno())) != file_identity(opened):
            raise ValueError("Archive changed during copying")
        outgoing.flush()
        os.fsync(outgoing.fileno())
    if file_identity(source.lstat()) != file_identity(initial) or digest.hexdigest() != expected:
        raise ValueError("Archive identity or hash changed")
    if hash_file(target) != expected:
        raise ValueError("Backup archive readback mismatch")


def verify_contents(directory: Path, expected: dict[str, Any], raw: bytes) -> None:
    """Verify copied selection bytes and original archive manifests."""
    if read_bounded(directory / STATE, MAX_STATE) != raw:
        raise ValueError("Backup metadata readback mismatch")
    state = strict_json(raw)
    validate_state(state)
    if state != expected:
        raise ValueError("Backup selection mismatch")
    for record in (state["active"], state["previous"]):
        if record is None:
            continue
        digest = record["package_sha256"]
        archive_path = directory / (digest + ".zip")
        if hash_file(archive_path) != digest:
            raise ValueError("Backup archive digest mismatch")
        with zipfile.ZipFile(archive_path) as archive:
            preflight(archive)
            if hashlib.sha256(archive.read(MANIFEST)).hexdigest() != record["manifest_sha256"]:
                raise ValueError("Backup archive manifest mismatch")
        if hash_file(archive_path) != digest:
            raise ValueError("Backup archive changed during verification")


def backup(root: Path, archives: dict[str, Path], destination: Path,
           apply: bool = False, expected_plan: str | None = None) -> dict[str, Any]:
    """Dry-run by default; copy only after explicit review of the source plan."""
    root = root_path(root)
    destination = destination_path(root, destination)
    if apply != (expected_plan is not None):
        raise ValueError("Apply requires the reviewed plan SHA-256")
    if expected_plan is not None and not SHA.fullmatch(expected_plan):
        raise ValueError("Invalid plan SHA-256")
    raw = read_bounded(root / STATE, MAX_STATE)
    observed = plan(root, archives)
    if read_bounded(root / STATE, MAX_STATE) != raw:
        raise ValueError("Selection changed before backup")
    binding = {"schema": 1, "source_plan_sha256": observed["plan_sha256"],
               "state_sha256": hashlib.sha256(raw).hexdigest(),
               "destination": os.path.normcase(str(destination))}
    binding["destination"] = hashlib.sha256(binding["destination"].encode()).hexdigest()
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    result = {"schema": 1, "plan_sha256": digest,
              "source_plan_sha256": observed["plan_sha256"],
              "destination_sha256": binding["destination"],
              "selection_sha256": binding["state_sha256"],
              "archive_count": len(archives), "created": False,
              "maintenance_admitted": False, "restored": False}
    if not apply:
        return result
    if expected_plan != digest:
        raise ValueError("Backup plan changed")
    return create_backup(root, archives, destination, observed, raw, result)


def create_backup(root: Path, archives: dict[str, Path], destination: Path,
                  observed: dict[str, Any], raw: bytes,
                  result: dict[str, Any]) -> dict[str, Any]:
    """Create a fresh copy and finalize only after source and copy verification."""
    destination.mkdir(mode=0o700)
    write_exclusive(destination / STATE, raw)
    for key, source in sorted(archives.items()):
        copy_archive(source, destination / (key + ".zip"), key)
    verify_contents(destination, observed["selection"], raw)
    if plan(root, archives) != observed:
        raise ValueError("Source changed during backup")
    if read_bounded(root / STATE, MAX_STATE) != raw:
        raise ValueError("Source selection changed during backup")
    result["created"] = True
    write_exclusive(destination / RECEIPT, json.dumps(result, sort_keys=True).encode() + b"\n")
    verify_backup(destination, result["plan_sha256"])
    return result


def receipt_binding(receipt: object, raw: bytes, expected_plan: str) -> tuple[str, str]:
    """Recompute the receipt binding against a separately retained plan."""
    if not isinstance(receipt, dict):
        raise ValueError("Invalid backup receipt")
    source_plan = receipt.get("source_plan_sha256")
    destination_digest = receipt.get("destination_sha256")
    if not all(isinstance(value, str) and SHA.fullmatch(value)
               for value in (source_plan, destination_digest)):
        raise ValueError("Invalid backup binding")
    binding = {"schema": 1, "source_plan_sha256": source_plan,
               "state_sha256": hashlib.sha256(raw).hexdigest(), "destination": destination_digest}
    if hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest() != expected_plan:
        raise ValueError("Backup plan binding mismatch")
    return source_plan, destination_digest


def verify_backup(directory: Path, expected_plan: str) -> dict[str, Any]:
    """Check a completed copy against its separately retained plan digest."""
    directory = root_path(directory)
    receipt = strict_json(read_bounded(directory / RECEIPT, MAX_STATE))
    raw = read_bounded(directory / STATE, MAX_STATE)
    state = strict_json(raw)
    validate_state(state)
    records = [record for record in (state["active"], state["previous"]) if record]
    source_plan, destination_digest = receipt_binding(receipt, raw, expected_plan)
    wanted = {"schema": 1, "plan_sha256": expected_plan,
              "source_plan_sha256": source_plan, "destination_sha256": destination_digest,
              "selection_sha256": hashlib.sha256(raw).hexdigest(),
              "archive_count": len(records), "created": True,
              "maintenance_admitted": False, "restored": False}
    if (not SHA.fullmatch(expected_plan) or not isinstance(receipt, dict)
            or set(receipt) != set(wanted) or any(type(receipt[k]) is not type(v)
            or receipt[k] != v for k, v in wanted.items())):
        raise ValueError("Invalid backup receipt")
    names = {STATE, RECEIPT} | {record["package_sha256"] + ".zip" for record in records}
    if {child.name for child in bounded_children(directory)} != names:
        raise ValueError("Unexpected backup entries")
    verify_contents(directory, state, raw)
    return receipt


def main() -> int:
    """Use an explicit copy or read-only verification subcommand."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("copy", help="Plan or copy verified selection archives")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--destination", type=Path, required=True)
    create.add_argument("--archive", nargs=2, action="append", required=True)
    create.add_argument("--plan-sha256")
    create.add_argument("--apply", action="store_true")
    check = sub.add_parser("verify", help="Verify an existing backup")
    check.add_argument("--directory", type=Path, required=True)
    check.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            result = verify_backup(args.directory, args.plan_sha256)
        else:
            archives = {digest.lower(): Path(path) for digest, path in args.archive}
            if len(archives) != len(args.archive):
                raise ValueError("Duplicate archive digest")
            result = backup(args.root, archives, args.destination, args.apply, args.plan_sha256)
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            RuntimeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_ERROR" if isinstance(error, OSError) else "BACKUP_REFUSED"
        print(f"FAIL: {reason}; preserve partial backup for private review", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    print("PASS: backup checked" if result["created"] else "PASS: read-only backup plan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
