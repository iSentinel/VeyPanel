#!/usr/bin/env python3
"""Seal and verify complete review-only upstream watch evidence for CI."""

import argparse
from pathlib import Path
import subprocess
import sys

from artifact_manifest import MANIFEST, collect, compare, load_manifest, write_manifest
from build_source_evidence import evidence
from run_upstream_watch import ROOT, run, utc_now, verify_bundle

ACCEPTED = {"UNCHANGED": 0, "REVIEW": 2}


def verify_sealed(output: Path, commit: str, tree: str) -> str:
    """Verify exact archive membership, file hashes and fresh source-bound evidence."""
    if (output.is_symlink() or not output.is_dir()
            or getattr(output.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Unsafe upstream archive")
    names = set()
    for item in output.iterdir():
        if item.name not in {"bundle", MANIFEST} or item.name in names:
            raise ValueError("Unexpected upstream archive entry")
        names.add(item.name)
    if names != {"bundle", MANIFEST}:
        raise ValueError("Incomplete upstream archive")
    expected = load_manifest(output / MANIFEST)
    if any(compare(expected, collect(output)).values()):
        raise ValueError("Upstream archive manifest mismatch")
    status = verify_bundle(output / "bundle", commit, tree, utc_now())
    if status not in ACCEPTED:
        raise ValueError("Unaccepted upstream review status")
    return status


def execute(output: Path, commit: str, tree: str) -> str:
    """Collect once, refuse incomplete evidence, then seal and reverify readback."""
    if evidence(ROOT, commit)["git_tree"] != tree:
        raise ValueError("Unexpected source tree")
    output.mkdir(mode=0o700, exist_ok=False)
    status = run(output / "bundle", commit)
    if status not in ACCEPTED:
        raise ValueError("Incomplete upstream collection")
    if verify_bundle(output / "bundle", commit, tree, utc_now()) != status:
        raise ValueError("Upstream collection and verification disagree")
    write_manifest(output, collect(output))
    if verify_sealed(output, commit, tree) != status:
        raise ValueError("Sealed upstream evidence disagrees")
    return status


def main() -> int:
    """Return 0 unchanged, 2 review required, or 1 failed evidence gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("collect", "verify"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-tree", required=True)
    args = parser.parse_args()
    try:
        operation = execute if args.action == "collect" else verify_sealed
        status = operation(args.output, args.expected_commit, args.expected_tree)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        print("ERROR: upstream CI evidence gate failed", file=sys.stderr)
        return 1
    print(status)
    return ACCEPTED[status]


if __name__ == "__main__":
    sys.exit(main())
