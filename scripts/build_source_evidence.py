#!/usr/bin/env python3
"""Record the actual clean tracked Git checkout used by an artifact build."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r"[0-9a-f]{40}")
MAX_EPOCH = 253402300799


def git(root: Path, *args: str) -> str:
    """Read Git metadata without changing the repository."""
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", timeout=30, check=True)
    return result.stdout.strip()


def evidence(root: Path, expected: str) -> dict[str, str | int | bool]:
    """Require the actual checkout and tracked source state to match policy."""
    if not SHA.fullmatch(expected):
        raise ValueError("Expected a complete Git SHA-1 checkout ID")
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    epoch = int(git(root, "log", "-1", "--format=%ct", "HEAD"))
    if commit != expected or not SHA.fullmatch(tree):
        raise ValueError("Actual Git checkout does not match expected source")
    if not 0 < epoch < MAX_EPOCH:
        raise ValueError("Invalid commit timestamp")
    if git(root, "status", "--porcelain=v1", "--untracked-files=no"):
        raise ValueError("Tracked checkout contains uncommitted changes")
    return {
        "schema": 1,
        "git_commit": commit,
        "git_tree": tree,
        "source_commit_epoch_utc": epoch,
        "tracked_checkout_clean": True,
    }


def main() -> int:
    """Capture deterministic source metadata or compare it to an earlier capture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--expected-sha", default=os.environ.get("GITHUB_SHA"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        data = evidence(args.root, args.expected_sha or "")
        encoded = json.dumps(data, indent=2, sort_keys=True) + "\n"
        if args.verify:
            if args.output.read_bytes() != encoded.encode("utf-8"):
                raise ValueError("Checkout evidence changed since build began")
        else:
            args.output.write_bytes(encoded.encode("utf-8"))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"FAIL: build source evidence: {error}", file=sys.stderr)
        return 1
    print(f"PASS: clean tracked checkout {data['git_commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
