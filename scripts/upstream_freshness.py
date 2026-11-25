"""Bind upstream observations to local source and bounded collection time."""

from datetime import datetime, timezone
import hashlib
import re
from typing import Any

from artifact_manifest import strict_json
from check_upstream_review import MAX_REPORT, REPOSITORIES, inventory, valid_row

MAX_AGE_SECONDS = 24 * 60 * 60
MAX_CLOCK_SKEW_SECONDS = 5
MAX_DURATION_MS = 185_000
SHA = re.compile(r"[0-9a-f]{40}")
UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")
FIELDS = {"schema", "git_commit", "git_tree", "started_utc", "finished_utc",
          "duration_ms", "observation_sha256", "complete"}


def timestamp(value: datetime) -> str:
    """Encode a UTC datetime at fixed microsecond precision."""
    if value.utcoffset() is None:
        raise ValueError("Expected timezone-aware timestamp")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_timestamp(value: Any) -> datetime:
    """Require canonical UTC text rather than implicit or local time."""
    if not isinstance(value, str) or not UTC.fullmatch(value):
        raise ValueError("Invalid UTC timestamp")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if timestamp(parsed) != value:
        raise ValueError("Noncanonical UTC timestamp")
    return parsed


def complete_observation(raw: bytes) -> bool:
    """Validate bounded observation structure and determine exact completeness."""
    if len(raw) > MAX_REPORT:
        raise ValueError("Observation exceeds budget")
    rows = inventory(strict_json(raw))
    if not all(map(valid_row, rows.values())):
        raise ValueError("Invalid observation row")
    return set(rows) == REPOSITORIES


def check_identity(value: Any) -> None:
    """Require a full nonzero Git SHA-1 identity."""
    if not isinstance(value, str) or not SHA.fullmatch(value) or value == "0" * 40:
        raise ValueError("Invalid Git identity")


def check_interval(start: datetime, end: datetime, duration_ms: int) -> None:
    """Require a bounded monotonic duration consistent with local UTC clocks."""
    if type(duration_ms) is not int or not 0 <= duration_ms <= MAX_DURATION_MS:
        raise ValueError("Invalid collection duration")
    elapsed = (end - start).total_seconds()
    if elapsed < 0 or abs(elapsed - duration_ms / 1000) > MAX_CLOCK_SKEW_SECONDS:
        raise ValueError("Inconsistent collection clocks")


def create_receipt(raw: bytes, commit: str, tree: str, start: datetime,
                   end: datetime, duration_ms: int) -> dict[str, Any]:
    """Bind exact observation bytes, local source and measured time interval."""
    check_identity(commit)
    check_identity(tree)
    started, finished = timestamp(start), timestamp(end)
    check_interval(parse_timestamp(started), parse_timestamp(finished), duration_ms)
    return {"schema": 1, "git_commit": commit, "git_tree": tree,
            "started_utc": started, "finished_utc": finished,
            "duration_ms": duration_ms, "observation_sha256": hashlib.sha256(raw).hexdigest(),
            "complete": complete_observation(raw)}


def verify_receipt(raw: bytes, receipt: bytes, commit: str, tree: str,
                   now: datetime) -> dict[str, Any]:
    """Refuse stale, future, incomplete or mismatched local evidence."""
    if len(receipt) > MAX_REPORT:
        raise ValueError("Receipt exceeds budget")
    check_identity(commit)
    check_identity(tree)
    data = strict_json(receipt)
    if not isinstance(data, dict) or set(data) != FIELDS or type(data["schema"]) is not int or data["schema"] != 1:
        raise ValueError("Invalid freshness receipt schema")
    start = parse_timestamp(data["started_utc"])
    end = parse_timestamp(data["finished_utc"])
    expected = create_receipt(raw, commit, tree, start, end, data["duration_ms"])
    if type(data["complete"]) is not bool or data != expected or not expected["complete"]:
        raise ValueError("Incomplete or mismatched observation receipt")
    clock = parse_timestamp(timestamp(now))
    age = (clock - start).total_seconds()
    if age > MAX_AGE_SECONDS or (end - clock).total_seconds() > MAX_CLOCK_SKEW_SECONDS:
        raise ValueError("Stale or future upstream observation")
    return expected
