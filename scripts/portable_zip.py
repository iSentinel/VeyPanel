#!/usr/bin/env python3
"""Create and verify a deterministic unsigned portable Windows ZIP."""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import stat
import sys
import zipfile

from artifact_manifest import (
    MANIFEST, MAX_BYTES, MAX_FILES, MAX_MANIFEST, collect, compare, entries,
    hash_file, read_bounded, safe_entry, strict_json,
)

STAMP = (1980, 1, 1, 0, 0, 0)
RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])$", re.I)


def windows_path(name):
    """Reject Windows device names in addition to ambiguous paths."""
    return safe_entry(name) and all(
        not RESERVED.fullmatch(part.split(".", 1)[0].rstrip(" "))
        for part in name.split("/"))


def read_manifest(root):
    """Read and validate the complete source artifact inventory."""
    raw = read_bounded(root / MANIFEST, MAX_MANIFEST)
    manifest = strict_json(raw)
    if any(compare(manifest, collect(root)).values()):
        raise ValueError("Source artifact manifest mismatch")
    return manifest, raw


def zip_info(name, size):
    """Set all archive metadata explicitly; use no compression dependency."""
    if not windows_path(name):
        raise ValueError("Unsafe Windows archive name: " + name)
    info = zipfile.ZipInfo(name, STAMP)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_STORED
    info.file_size = size
    return info


def write_zip(root, output):
    """Create a new ZIP only from a verified source, never overwrite."""
    manifest, raw = read_manifest(root)
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError("Output must be outside source tree")
    rows = entries(manifest)
    names = sorted([*rows, MANIFEST])
    if any(not windows_path(name) for name in names):
        raise ValueError("Unsafe Windows archive path")
    with output.open("xb") as target:
        try:
            with zipfile.ZipFile(target, "w", allowZip64=True) as archive:
                for name in names:
                    if name == MANIFEST:
                        archive.writestr(zip_info(name, len(raw)), raw)
                    else:
                        size = rows[name]["bytes"]
                        with (root / name).open("rb") as source:
                            with archive.open(zip_info(name, size), "w") as dest:
                                shutil.copyfileobj(source, dest, 1024 * 1024)
            target.flush()
            verify_zip(output)
        except BaseException:
            target.close()
            output.unlink()
            raise


def validate_members(archive):
    """Require unique safe regular files, canonical order and bounded size."""
    infos = archive.infolist()
    names = [info.filename for info in infos]
    folded = {name.casefold() for name in names}
    if (not 1 < len(infos) <= MAX_FILES + 1 or len(folded) != len(names)
            or names != sorted(names) or MANIFEST not in names):
        raise ValueError("Invalid ZIP file membership or order")
    total = 0
    for info in infos:
        name = info.filename
        parents = name.split("/")
        if (not windows_path(name) or any(
                "/".join(parents[:i]).casefold() in folded for i in range(1, len(parents)))
                or info.is_dir() or info.flag_bits & 1
                or info.compress_type != zipfile.ZIP_STORED
                or info.date_time != STAMP
                or info.external_attr != (stat.S_IFREG | 0o644) << 16):
            raise ValueError("Unsafe or noncanonical ZIP entry: " + name)
        total += info.file_size
        if total > MAX_BYTES + MAX_MANIFEST:
            raise ValueError("ZIP exceeds size budget")
    if archive.getinfo(MANIFEST).file_size > MAX_MANIFEST:
        raise ValueError("ZIP manifest exceeds size budget")
    return names


def read_zip_metadata(archive: zipfile.ZipFile, name: str, limit: int) -> bytes:
    """Read a bounded embedded metadata member and require its declared length."""
    info = archive.getinfo(name)
    if not 0 <= info.file_size <= limit:
        raise ValueError("Oversized embedded metadata")
    with archive.open(info) as source:
        raw = source.read(limit + 1)
    if len(raw) > limit or len(raw) != info.file_size:
        raise ValueError("Embedded metadata size mismatch")
    return raw


def verify_zip(path):
    """Verify every archived file against its embedded SHA-256 manifest."""
    with zipfile.ZipFile(path) as archive:
        names = validate_members(archive)
        rows = entries(strict_json(read_zip_metadata(archive, MANIFEST, MAX_MANIFEST)))
        if set(names) != set(rows) | {MANIFEST}:
            raise ValueError("ZIP membership differs from manifest")
        for name, row in rows.items():
            if archive.getinfo(name).file_size != row["bytes"]:
                raise ValueError("ZIP file size differs: " + name)
            digest = hashlib.sha256()
            with archive.open(name) as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != row["sha256"]:
                raise ValueError("ZIP file hash differs: " + name)
    return len(rows)


def main():
    """Write or verify an archive with explicit success and failure codes."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    write = sub.add_parser("write")
    write.add_argument("source", type=Path)
    write.add_argument("archive", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("archive", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "write":
            write_zip(args.source, args.archive)
        count = verify_zip(args.archive)
        print(f"PASS: {count} files match embedded SHA-256 manifest")
        print(f"SHA256: {hash_file(args.archive)}")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            zipfile.BadZipFile) as error:
        print(f"FAIL: portable ZIP: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
