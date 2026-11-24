#!/usr/bin/env python3
"""Compare signed APK bytes outside the structurally validated signing block."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

from verify_android_apk import verify

MAX_APK = 128 * 1024 * 1024
MAGIC = b"APK Sig Block 42"
V2 = 0x7109871A


def signing_bounds(data):
    """Validate a conventional non-ZIP64 APK central directory and v2 block."""
    end = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if end < 0 or len(data) - end < 22:
        raise ValueError("Missing ZIP end record")
    disk, central_disk, count_disk, count, size, offset, comment = struct.unpack_from(
        "<4H2IH", data, end + 4)
    if (disk or central_disk or count_disk != count or count == 0
            or count == 65535 or offset == 0xFFFFFFFF or size == 0xFFFFFFFF
            or end + 22 + comment != len(data) or offset + size != end
            or offset < 32 or data[offset - 16:offset] != MAGIC):
        raise ValueError("Unsupported ZIP directory or missing APK signing block")
    footer_size = struct.unpack_from("<Q", data, offset - 24)[0]
    start = offset - footer_size - 8
    if (footer_size < 24 or start < 0
            or struct.unpack_from("<Q", data, start)[0] != footer_size):
        raise ValueError("Invalid APK signing block size")
    validate_pairs(data, start + 8, offset - 24)
    return start, offset


def validate_pairs(data, cursor, end):
    """Require bounded, unique ID-value pairs including APK Signature v2."""
    ids = set()
    while cursor < end:
        if end - cursor < 12:
            raise ValueError("Truncated signing block pair")
        length, ident = struct.unpack_from("<QI", data, cursor)
        if length < 4 or length > end - cursor - 8 or ident in ids:
            raise ValueError("Invalid or duplicate signing block pair")
        ids.add(ident)
        cursor += 8 + length
    if cursor != end or V2 not in ids:
        raise ValueError("Missing APK v2 signing record")


def inspect(path):
    """Verify ZIP policy and read bounded signed APK bytes."""
    verify(path)
    if path.stat().st_size > MAX_APK:
        raise ValueError("APK exceeds comparison size limit")
    data = path.read_bytes()
    start, end = signing_bounds(data)
    return data, start, end


def compare(first, second):
    """Compare exact bytes without masking offsets, headers or ZIP content."""
    a, sa, ea = inspect(first)
    b, sb, eb = inspect(second)
    same_bounds = (sa, ea) == (sb, eb)
    outside = same_bounds and a[:sa] == b[:sb] and a[ea:] == b[eb:]
    return {
        "full_sha256": [hashlib.sha256(x).hexdigest() for x in (a, b)],
        "signing_block_bounds": [[sa, ea], [sb, eb]],
        "full_bytes_identical": a == b,
        "outside_signing_block_identical": outside,
        "signing_block_identical": a[sa:ea] == b[sb:eb],
        "signature_validation": "not-performed-by-this-comparator",
    }


def main():
    """Report complete and outside-signature equality separately."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    try:
        report = compare(args.first, args.second)
        print(json.dumps(report, indent=2))
        if not report["outside_signing_block_identical"]:
            print("FAIL: APK bytes differ outside identical signing block bounds")
            return 1
        print("PASS: APK bytes outside signing block match exactly")
        return 0
    except (OSError, ValueError, struct.error, zipfile.BadZipFile) as error:
        print(f"FAIL: APK comparison: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
