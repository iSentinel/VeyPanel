#!/usr/bin/env python3
"""Validate the structure and strictness of captured Gradle SHA-256 metadata."""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{https://schema.gradle.org/dependency-verification}"
HEX = re.compile(r"[0-9a-fA-F]{64}")
MAX_SIZE = 8 * 1024 * 1024


def read_metadata(path):
    """Read bounded XML and forbid declarations that introduce entities."""
    if path.stat().st_size > MAX_SIZE:
        raise ValueError("Verification metadata exceeds size budget")
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("XML declarations are not allowed")
    return ET.fromstring(raw)


def check_configuration(root):
    """Reject broad trust exemptions and require metadata verification."""
    config = root.find(NS + "configuration")
    if config is None or config.findtext(NS + "verify-metadata") != "true":
        raise ValueError("Gradle metadata verification must be enabled")
    for name in ("trusted-artifacts", "trusted-keys", "ignored-keys"):
        node = config.find(NS + name)
        if node is not None and len(node):
            raise ValueError("Unexpected Gradle trust exemption: " + name)


def artifact_hash(artifact):
    """Require one SHA-256 digest and no alternatives or ignored keys."""
    hashes = artifact.findall(NS + "sha256")
    if len(hashes) != 1 or not HEX.fullmatch(hashes[0].get("value", "")):
        raise ValueError("Expected one valid SHA-256 per artifact")
    if len(artifact) != 1 or len(hashes[0]):
        raise ValueError("Unexpected alternative digest or trust exception")
    return hashes[0].get("value").lower()


def inventory(root):
    """Return canonical artifact-to-hash records for cross-run comparison."""
    if root.tag != NS + "verification-metadata":
        raise ValueError("Unexpected verification metadata root")
    check_configuration(root)
    records = {}
    components = root.find(NS + "components")
    if components is None or not len(components):
        raise ValueError("No verification components")
    for component in components:
        if component.tag != NS + "component":
            raise ValueError("Unexpected verification component")
        coordinate = tuple(component.get(key, "") for key in ("group", "name", "version"))
        if not all(coordinate) or not len(component):
            raise ValueError("Empty component coordinate or artifacts")
        for artifact in component:
            name = artifact.get("name")
            if artifact.tag != NS + "artifact" or not name:
                raise ValueError("Invalid verification artifact")
            key = (*coordinate, name)
            if key in records:
                raise ValueError("Duplicate artifact record")
            records[key] = artifact_hash(artifact)
    return records


def require_runtime(records, baseline):
    """Require verification coverage of the observed debug runtime coordinates."""
    expected = {(item["group"], item["name"], item["version"])
                for item in baseline["components"]}
    if not expected or expected - {key[:3] for key in records}:
        raise ValueError("Verification metadata misses a runtime component")


def main():
    """Check metadata and optionally compare another independent build capture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        records = inventory(read_metadata(args.metadata))
        require_runtime(records, json.loads(args.baseline.read_text(encoding="utf-8")))
        if args.compare and records != inventory(read_metadata(args.compare)):
            raise ValueError("Independent verification captures differ")
    except (OSError, ValueError, ET.ParseError, KeyError, TypeError) as error:
        print(f"FAIL: Gradle verification metadata: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(records)} SHA-256 artifact records; runtime coordinates covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
