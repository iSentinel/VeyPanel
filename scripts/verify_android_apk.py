#!/usr/bin/env python3
"""Offline sanity and integrity verification for one built Android APK."""

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

MAX_ARCHIVE = 128 * 1024 * 1024
MAX_UNPACKED = 512 * 1024 * 1024
MAX_ENTRIES = 20000
REQUIRED = {"AndroidManifest.xml", "classes.dex", "resources.arsc"}
NOTICES = {
    "assets/third-party/OkHttp-LICENSE.txt",
    "assets/third-party/README.txt",
    "assets/third-party/ZXing-Android-Embedded-COPYING.txt",
    "assets/third-party/ZXing-Core-LICENSE.txt",
    "assets/third-party/ZXing-Core-NOTICE.txt",
}


def safe_name(name: str) -> bool:
    """Reject unsafe or ambiguous archive paths."""
    parts = name.split("/")
    return (bool(name) and not name.startswith("/")
            and chr(92) not in name and chr(0) not in name
            and all(part not in ("", ".", "..") for part in parts)
            and not any(ord(char) < 32 for char in name)
            and ":" not in name)


def inspect_archive(archive: zipfile.ZipFile) -> tuple[int, int]:
    """Validate ZIP metadata before decompression or CRC checks."""
    entries = archive.infolist()
    names = [item.filename for item in entries]
    if not entries or len(entries) > MAX_ENTRIES:
        raise ValueError("Invalid APK file count")
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("Duplicate APK archive entry")
    if not REQUIRED.issubset(names):
        raise ValueError("APK is missing essential Android entries")
    if not NOTICES.issubset(names):
        raise ValueError("APK is missing third-party license notices")
    total = 0
    for item in entries:
        if not safe_name(item.filename.removesuffix("/")):
            raise ValueError("Invalid APK entry name")
        if item.flag_bits & 1:
            raise ValueError("Encrypted APK entry")
        if (item.external_attr >> 16) & 0xF000 == 0xA000:
            raise ValueError("APK symlink entry")
        if item.file_size > MAX_ARCHIVE:
            raise ValueError("Oversized APK entry")
        total += item.file_size
        if total > MAX_UNPACKED:
            raise ValueError("APK unpacked size exceeds budget")
    return len(entries), total


def sha256_file(path: Path) -> str:
    """Hash a file without loading the full APK into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path) -> tuple[int, int, str]:
    """Reject malformed, oversized or CRC-invalid APK archives."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("APK must be an ordinary file")
    size = path.stat().st_size
    if size <= 0 or size > MAX_ARCHIVE:
        raise ValueError("APK size outside permitted budget")
    with zipfile.ZipFile(path, "r") as archive:
        entries, unpacked = inspect_archive(archive)
        if archive.testzip() is not None:
            raise ValueError("APK entry checksum mismatch")
    return entries, unpacked, sha256_file(path)


def main() -> int:
    """Print a PASS/FAIL summary with stable exit codes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="Signed APK to verify offline")
    args = parser.parse_args()
    try:
        count, unpacked, digest = verify(args.apk)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(f"FAIL: APK integrity: {error}", file=sys.stderr)
        return 1
    print(f"PASS: APK archive: {count} entries; {unpacked} uncompressed bytes")
    print(f"SHA256: {digest}")
    print("NOTE: ZIP integrity is not proof of trusted signing or device acceptance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
