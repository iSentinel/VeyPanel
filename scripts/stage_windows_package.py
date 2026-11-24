#!/usr/bin/env python3
"""Preflight and stage a digest-pinned portable package without activating it."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

from artifact_manifest import MANIFEST, collect, compare, entries
from portable_zip import MAX_MANIFEST, validate_members

REQUIRED = {"VeyPanel.Desktop.exe", "VeyPanel.Desktop.dll",
            "host/VeyPanel.Host.exe", "host/VeyPanel.Host.dll",
            "build-source.json", "host/build-source.json", "host/" + MANIFEST}


def digest(source):
    """Hash the open archive and reset its position."""
    source.seek(0)
    result = hashlib.sha256()
    for block in iter(lambda: source.read(1024 * 1024), b""):
        result.update(block)
    source.seek(0)
    return result.hexdigest()


def checked_manifest(archive, name):
    """Load bounded embedded manifest data."""
    if archive.getinfo(name).file_size > MAX_MANIFEST:
        raise ValueError("Oversized embedded manifest")
    return entries(json.loads(archive.read(name)))


def preflight(archive):
    """Validate archive layout, nested Host identity and every payload hash."""
    names = validate_members(archive)
    rows = checked_manifest(archive, MANIFEST)
    if not REQUIRED <= rows.keys() or set(names) != rows.keys() | {MANIFEST}:
        raise ValueError("Invalid Desktop package membership")
    host = checked_manifest(archive, "host/" + MANIFEST)
    expected = {name[5:]: dict(row, path=name[5:])
                for name, row in rows.items()
                if name.startswith("host/") and name != "host/" + MANIFEST}
    if host != expected:
        raise ValueError("Nested Host manifest mismatch")
    for name in ("build-source.json", "host/build-source.json"):
        if archive.getinfo(name).file_size > 65536:
            raise ValueError("Oversized source evidence")
    if archive.read("build-source.json") != archive.read("host/build-source.json"):
        raise ValueError("Host and Desktop source evidence differs")
    directories = {}
    for name in names:
        parts = name.split("/")
        for index in range(1, len(parts)):
            parent = "/".join(parts[:index])
            if directories.setdefault(parent.casefold(), parent) != parent:
                raise ValueError("Case-ambiguous directory")
    for name, row in rows.items():
        if archive.getinfo(name).file_size != row["bytes"]:
            raise ValueError("Package file size mismatch: " + name)
        with archive.open(name) as source:
            result = hashlib.sha256()
            for block in iter(lambda: source.read(1024 * 1024), b""):
                result.update(block)
        if result.hexdigest() != row["sha256"]:
            raise ValueError("Package file hash mismatch: " + name)
    return names, rows


def check_destination(destination):
    """Only allow a new directory below an existing non-reparse parent."""
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination already exists")
    for parent in destination.parents:
        if (not parent.is_dir() or parent.is_symlink()
                or getattr(parent.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Unsafe or missing destination ancestor")
    return destination


def extract_verified(archive, names, destination):
    """Write exclusively into a newly created isolated directory."""
    destination.mkdir(exist_ok=False)
    try:
        for name in names:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
        for root in (destination, destination / "host"):
            manifest = json.loads((root / MANIFEST).read_bytes())
            if any(compare(manifest, collect(root)).values()):
                raise ValueError("Extracted tree does not match manifest")
    except Exception:
        shutil.rmtree(destination)
        raise


def stage(package, expected, destination, dry_run=True):
    """Require external digest; never run binaries or modify an existing tree."""
    if not re.fullmatch("[0-9a-fA-F]{64}", expected):
        raise ValueError("Expected complete SHA-256")
    destination = check_destination(destination)
    with package.open("rb") as source:
        if digest(source) != expected.lower():
            raise ValueError("External SHA-256 mismatch")
        with zipfile.ZipFile(source) as archive:
            names, rows = preflight(archive)
            required = sum(archive.getinfo(name).file_size for name in names)
            if shutil.disk_usage(destination.parent).free < required:
                raise ValueError("Insufficient free space")
            if digest(source) != expected.lower():
                raise ValueError("Package changed during preflight")
            if not dry_run:
                extract_verified(archive, names, destination)
                if digest(source) != expected.lower():
                    shutil.rmtree(destination)
                    raise ValueError("Package changed during staging")
    return len(rows)


def main():
    """Default to read-only preflight; require explicit --apply for staging."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        count = stage(args.package, args.sha256, args.destination, not args.apply)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            zipfile.BadZipFile) as error:
        print(f"FAIL: package staging: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {'staged' if args.apply else 'dry-run'}; {count} verified files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
