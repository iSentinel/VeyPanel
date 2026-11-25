#!/usr/bin/env python3
"""Create or compare deterministic SHA-256 manifests of artifact file trees."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any

MANIFEST = "artifact-files.sha256.json"
MAX_FILES = 20000
MAX_BYTES = 4 * 1024**3
MAX_ENTRIES = 40000
MAX_MANIFEST = 8 * 1024 * 1024
MAX_HASH_BYTES = MAX_BYTES + 64 * 1024 * 1024


def file_identity(info: os.stat_result) -> tuple[int, ...]:
    """Compare available file identity, size and modification metadata."""
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode)


def regular(info: os.stat_result) -> bool:
    """Refuse nonregular files and Windows reparse points."""
    return stat.S_ISREG(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400


def same_open_file(path_info: os.stat_result, handle_info: os.stat_result) -> bool:
    """Compare identities across APIs, accounting for documented Win32 differences."""
    if not regular(path_info) or not regular(handle_info):
        return False
    if os.name != "nt":
        return file_identity(path_info) == file_identity(handle_info)
    # CPython 3.12 path stat adds executable-extension bits and aliases
    # ctime to birthtime. Compare the explicit creation time and common bits.
    # Keep full identity checks within each API before/after the read.
    return (
        path_info.st_dev, path_info.st_ino, path_info.st_size,
        path_info.st_mtime_ns, path_info.st_birthtime_ns,
        path_info.st_mode & ~0o111,
    ) == (
        handle_info.st_dev, handle_info.st_ino, handle_info.st_size,
        handle_info.st_mtime_ns, handle_info.st_birthtime_ns,
        handle_info.st_mode & ~0o111,
    )


def hash_file(path: Path) -> str:
    """Hash a bounded regular file and detect observed mutation or replacement."""
    initial = path.lstat()
    if not regular(initial) or initial.st_size > MAX_HASH_BYTES:
        raise ValueError("Unsafe or oversized hash input")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        opened = os.fstat(source.fileno())
        if not same_open_file(initial, opened):
            raise ValueError("File changed before hashing")
        remaining = initial.st_size
        while remaining:
            block = source.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError("File truncated during hashing")
            digest.update(block)
            remaining -= len(block)
        if source.read(1) or file_identity(os.fstat(source.fileno())) != file_identity(opened):
            raise ValueError("File changed while hashing")
    if file_identity(path.lstat()) != file_identity(initial):
        raise ValueError("File replaced or changed while hashing")
    return digest.hexdigest()


def walk_error(error: OSError) -> None:
    """Never silently omit an unreadable subtree."""
    raise error


def safe_entry(path: str) -> bool:
    """Refuse ambiguous cross-platform paths, links and control characters."""
    return all(part not in ("", ".", "..") and not part.startswith(".")
               and not part.endswith((".", " "))
               and not any(ord(char) < 32 or char in '\\:*?"<>|' for char in part)
               for part in path.split("/"))


def collect(root: Path) -> dict[str, Any]:
    """Inventory regular files only; do not follow symlinks/reparse points."""
    if (not root.is_dir() or root.is_symlink()
            or getattr(root.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Expected regular artifact directory")
    rows, names, total = [], set(), 0
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for name in sorted(dirs + files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if (not safe_entry(relative) or path.is_symlink()
                    or getattr(info, "st_file_attributes", 0) & 0x400):
                raise ValueError("Unsafe artifact entry: " + relative)
            folded = relative.casefold()
            if folded in names:
                raise ValueError("Duplicate case-insensitive path: " + relative)
            names.add(folded)
            if len(names) > MAX_ENTRIES:
                raise ValueError("Artifact entry-count budget exceeded")
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Nonregular artifact entry: " + relative)
            if relative == MANIFEST:
                continue
            total += info.st_size
            if total > MAX_BYTES or len(rows) >= MAX_FILES:
                raise ValueError("Artifact size or file-count budget exceeded")
            digest = hash_file(path)
            if file_identity(path.lstat()) != file_identity(info):
                raise ValueError("Artifact changed while hashing: " + relative)
            rows.append({"path": relative, "bytes": info.st_size, "sha256": digest})
    if not rows:
        raise ValueError("Empty artifact")
    return {"schema": 1, "algorithm": "SHA-256",
            "files": sorted(rows, key=lambda row: row["path"])}


def entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate a manifest before accepting or comparing its declarations."""
    if (not isinstance(manifest, dict) or set(manifest) != {"schema", "algorithm", "files"}
            or type(manifest.get("schema")) is not int or manifest["schema"] != 1
            or manifest.get("algorithm") != "SHA-256"):
        raise ValueError("Unknown manifest schema or hash algorithm")
    rows = manifest["files"]
    if not isinstance(rows, list) or not 0 < len(rows) <= MAX_FILES:
        raise ValueError("Empty or excessive manifest entries")
    result, names = {}, set()
    total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("Invalid manifest entry fields")
        path, size, digest = row["path"], row["bytes"], row["sha256"]
        if (not isinstance(path, str) or not safe_entry(path)
                or path == MANIFEST or path.casefold() in names
                or type(size) is not int or size < 0
                or not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest)):
            raise ValueError("Invalid or duplicate manifest entry")
        names.add(path.casefold())
        total += size
        if total > MAX_BYTES:
            raise ValueError("Manifest exceeds byte budget")
        result[path] = row
    return result


def compare(first: dict[str, Any], second: dict[str, Any]) -> dict[str, list[str]]:
    """Compare exact file membership, sizes and hashes."""
    a, b = entries(first), entries(second)
    return {"added": sorted(b.keys() - a.keys()),
            "removed": sorted(a.keys() - b.keys()),
            "changed": sorted(key for key in a.keys() & b.keys() if a[key] != b[key])}


def read_bounded(path: Path, limit: int) -> bytes:
    """Read one bounded regular file snapshot and reject observed mutations."""
    info = path.lstat()
    if not regular(info) or info.st_size > limit:
        raise ValueError("Unsafe or oversized metadata")
    with path.open("rb") as source:
        opened = os.fstat(source.fileno())
        if not same_open_file(info, opened):
            raise ValueError("Metadata changed before reading")
        raw = source.read(limit + 1)
        if (len(raw) > limit or len(raw) != info.st_size
                or file_identity(os.fstat(source.fileno())) != file_identity(opened)):
            raise ValueError("Metadata changed while reading")
    if file_identity(path.lstat()) != file_identity(info):
        raise ValueError("Metadata changed after reading")
    return raw


def strict_json(raw: bytes) -> Any:
    """Decode UTF-8 JSON, rejecting duplicate keys and nonstandard constants."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Invalid JSON constant")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                          parse_constant=invalid_constant)
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds parser budget") from error


def load_manifest(path: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    """Validate and optionally hash the exact same bounded manifest bytes."""
    raw = read_bounded(path, MAX_MANIFEST)
    if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Selected manifest digest mismatch")
    result = strict_json(raw)
    entries(result)
    return result


def write_manifest(root: Path, report: dict[str, Any]) -> None:
    """Atomically replace a staging manifest; accepted artifacts stay immutable."""
    target = root / MANIFEST
    entries(report)
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(raw) > MAX_MANIFEST:
        raise ValueError("Manifest exceeds size budget")
    if target.exists() or target.is_symlink():
        if not regular(target.lstat()):
            raise ValueError("Unsafe existing manifest")
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".manifest-", delete=False) as output:
            temp = Path(output.name)
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, target)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def main() -> int:
    """Generate, verify or compare file manifests with explicit exit codes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("write", "verify", "compare"))
    parser.add_argument("path", type=Path)
    parser.add_argument("other", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "write":
            report = collect(args.path)
            write_manifest(args.path, report)
            print(f"PASS: recorded {len(report['files'])} artifact file hashes")
            return 0
        if args.mode == "verify":
            expected = load_manifest(args.path / MANIFEST)
            actual = collect(args.path)
        else:
            if args.other is None:
                raise ValueError("Two manifests required for comparison")
            expected = load_manifest(args.path)
            actual = load_manifest(args.other)
        difference = compare(expected, actual)
        print(json.dumps(difference, indent=2))
        if any(difference.values()):
            print("FAIL: artifact file differences detected")
            return 1
        print("PASS: exact file membership, sizes and SHA-256 match")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL: artifact manifest: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
