#!/usr/bin/env python3
"""Collect and verify a source-bound, review-only upstream evidence bundle."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable

from artifact_manifest import read_bounded
from build_source_evidence import evidence
from check_upstream_review import MAX_REPORT, report
from collect_upstream_review import RUN_SECONDS, collect, request_json
from upstream_freshness import create_receipt, parse_timestamp, verify_receipt
from verify_upstream_review import verify

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "config/upstream-review-baseline.json"


def utc_now() -> datetime:
    """Read the local UTC clock, not a remote trusted clock."""
    return datetime.now(timezone.utc)


def encode(value: dict[str, Any]) -> bytes:
    """Serialize deterministic bounded JSON evidence."""
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_REPORT:
        raise ValueError("Upstream evidence exceeds budget")
    return raw


def write_new(path: Path, raw: bytes) -> None:
    """Refuse to overwrite any existing evidence file."""
    with path.open("xb") as stream:
        stream.write(raw)


def run(output: Path, expected_commit: str,
        get: Callable[[str], Any] | None = None) -> str:
    """Collect once into a fresh directory; bind actual source before and after."""
    source = evidence(ROOT, expected_commit)
    baseline = read_bounded(BASELINE, MAX_REPORT)
    output.mkdir(mode=0o700, exist_ok=False)
    start, tick = utc_now(), time.monotonic()
    deadline = tick + RUN_SECONDS
    document, complete = collect(get or (lambda path: request_json(path, deadline)))
    duration = round((time.monotonic() - tick) * 1000)
    end = utc_now()
    observed = encode(document)
    receipt = create_receipt(observed, str(source["git_commit"]),
                             str(source["git_tree"]), start, end, duration)
    result = report(baseline, observed)
    if (receipt["complete"] != complete or (result["status"] != "ERROR") != complete
            or evidence(ROOT, expected_commit) != source
            or read_bounded(BASELINE, MAX_REPORT) != baseline):
        raise ValueError("Inconsistent collection or changed source")
    write_new(output / "baseline.json", baseline)
    write_new(output / "observed.json", observed)
    write_new(output / "report.json", encode(result))
    write_new(output / "receipt.json", encode(receipt))
    return result["status"]


def verify_bundle(directory: Path, expected_commit: str, expected_tree: str,
                  now: datetime) -> str:
    """Require exact files, approved baseline, fresh observation and valid report."""
    expected = {"baseline.json", "observed.json", "report.json", "receipt.json"}
    if (directory.is_symlink() or not directory.is_dir()
            or getattr(directory.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("Unsafe upstream evidence directory")
    names = set()
    for item in directory.iterdir():
        if item.name not in expected or item.name in names:
            raise ValueError("Unexpected upstream evidence files")
        names.add(item.name)
    if names != expected:
        raise ValueError("Incomplete upstream evidence files")
    baseline, observed, claimed, receipt = (read_bounded(directory / name, MAX_REPORT)
        for name in ("baseline.json", "observed.json", "report.json", "receipt.json"))
    source = evidence(ROOT, expected_commit)
    if source["git_tree"] != expected_tree or baseline != read_bounded(BASELINE, MAX_REPORT):
        raise ValueError("Unapproved source or baseline")
    verify_receipt(observed, receipt, expected_commit, expected_tree, now)
    return verify(baseline, observed, claimed)["status"]


def main() -> int:
    """Return 0 unchanged, 2 review required, or 1 invalid/incomplete evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    collect_parser = commands.add_parser("collect", help="Create fresh local evidence")
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--expected-commit", required=True)
    verifier = commands.add_parser("verify", help="Verify complete fresh evidence")
    verifier.add_argument("--directory", type=Path, required=True)
    verifier.add_argument("--expected-commit", required=True)
    verifier.add_argument("--expected-tree", required=True)
    verifier.add_argument("--now", help="Explicit canonical UTC verification clock")
    args = parser.parse_args()
    try:
        if args.action == "collect":
            status = run(args.output, args.expected_commit)
        else:
            now = parse_timestamp(args.now) if args.now else utc_now()
            status = verify_bundle(args.directory, args.expected_commit, args.expected_tree, now)
    except (OSError, ValueError, subprocess.SubprocessError):
        print("ERROR: upstream evidence unavailable or invalid", file=sys.stderr)
        return 1
    print(status)
    return {"UNCHANGED": 0, "REVIEW": 2, "ERROR": 1}[status]


if __name__ == "__main__":
    sys.exit(main())
