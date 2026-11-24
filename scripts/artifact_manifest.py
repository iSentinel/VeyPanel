#!/usr/bin/env python3
"""Create or compare deterministic SHA-256 manifests of artifact file trees."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

MANIFEST = "artifact-files.sha256.json"
MAX_FILES = 20000
MAX_BYTES = 4 * 1024**3


def hash_file(path):
    """Hash a regular file in bounded chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_entry(path):
    """Refuse ambiguous cross-platform paths, links and control characters."""
    return all(part not in ("", ".", "..") and not part.endswith((".", " "))
               and not any(ord(char) < 32 or char in '\\:*?"<>|' for char in part)
               for part in path.split("/"))


def collect(root):
    """Inventory regular files only; do not follow symlinks/reparse points."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Expected regular artifact directory")
    rows, names, total = [], set(), 0
    for directory, dirs, files in os.walk(root, followlinks=False):
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
            if path.stat().st_size != info.st_size:
                raise ValueError("Artifact changed while hashing: " + relative)
            rows.append({"path": relative, "bytes": info.st_size, "sha256": digest})
    if not rows:
        raise ValueError("Empty artifact")
    return {"schema": 1, "algorithm": "SHA-256",
            "files": sorted(rows, key=lambda row: row["path"])}


def compare(first, second):
    """Compare exact file membership, sizes and hashes."""
    if first.get("schema") != 1 or second.get("schema") != 1:
        raise ValueError("Unknown manifest schema")
    if first.get("algorithm") != "SHA-256" or second.get("algorithm") != "SHA-256":
        raise ValueError("Unknown hash algorithm")
    a = {row["path"]: row for row in first["files"]}
    b = {row["path"]: row for row in second["files"]}
    if not a or not b or len(a) != len(first["files"]) or len(b) != len(second["files"]):
        raise ValueError("Empty or duplicate manifest entries")
    return {"added": sorted(b.keys() - a.keys()),
            "removed": sorted(a.keys() - b.keys()),
            "changed": sorted(key for key in a.keys() & b.keys() if a[key] != b[key])}


def main():
    """Generate, verify or compare file manifests with explicit exit codes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("write", "verify", "compare"))
    parser.add_argument("path", type=Path)
    parser.add_argument("other", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "write":
            report = collect(args.path)
            (args.path / MANIFEST).write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"PASS: recorded {len(report['files'])} artifact file hashes")
            return 0
        if args.mode == "verify":
            expected = json.loads((args.path / MANIFEST).read_text(encoding="utf-8"))
            actual = collect(args.path)
        else:
            if args.other is None:
                raise ValueError("Two manifests required for comparison")
            expected = json.loads(args.path.read_text(encoding="utf-8"))
            actual = json.loads(args.other.read_text(encoding="utf-8"))
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
