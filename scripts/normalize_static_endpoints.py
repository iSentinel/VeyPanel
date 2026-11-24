#!/usr/bin/env python3
"""Normalize generated static asset Last-Modified headers to a source epoch."""

import argparse
from email.utils import formatdate, parsedate_to_datetime
import json
from pathlib import Path
import sys

MAX_MANIFEST = 8 * 1024 * 1024


def normalize(data, epoch):
    """Replace only existing Last-Modified header values, never routes or ETags."""
    if not isinstance(epoch, int) or not 0 < epoch < 253402300799:
        raise ValueError("Invalid source epoch")
    if data.get("ManifestType") != "Publish" or not isinstance(data.get("Endpoints"), list):
        raise ValueError("Expected published static web asset endpoint manifest")
    endpoints = data["Endpoints"]
    if not 0 < len(endpoints) <= 20000:
        raise ValueError("Invalid endpoint count")
    value = formatdate(epoch, usegmt=True)
    headers = []
    for endpoint in endpoints:
        matches = [header for header in endpoint["ResponseHeaders"]
                   if header["Name"].casefold() == "last-modified"]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous Last-Modified header")
        if parsedate_to_datetime(matches[0]["Value"]).tzinfo is None:
            raise ValueError("Invalid Last-Modified date")
        headers.append(matches[0])
    for header in headers:
        header["Value"] = value
    return len(headers)


def main():
    """Write canonical JSON only after validating all header records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    try:
        if args.manifest.stat().st_size > MAX_MANIFEST:
            raise ValueError("Manifest exceeds size limit")
        data = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        count = normalize(data, args.epoch)
        args.manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8", newline="\n")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print(f"FAIL: static endpoint normalization: {error}", file=sys.stderr)
        return 1
    print(f"PASS: normalized {count} existing Last-Modified headers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
