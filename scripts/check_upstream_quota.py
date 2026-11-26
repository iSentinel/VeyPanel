#!/usr/bin/env python3
"""Check public API capacity before starting a hosted upstream observation."""

import argparse
import http.client
import subprocess
import sys
import time
from typing import Any, Callable

from check_upstream_review import REPOSITORIES
from collect_upstream_review import REQUEST_SECONDS, request_json

REQUIRED = 5 * len(REPOSITORIES)


def remaining_quota(document: Any) -> int:
    """Validate the core quota, refusing missing or inconsistent counts."""
    if not isinstance(document, dict):
        raise ValueError("Invalid quota document")
    resources = document.get("resources")
    core = resources.get("core") if isinstance(resources, dict) else None
    if not isinstance(core, dict):
        raise ValueError("Invalid core quota")
    limit, remaining = core.get("limit"), core.get("remaining")
    if (type(limit) is not int or type(remaining) is not int
            or not 0 <= remaining <= limit <= 1_000_000 or limit == 0):
        raise ValueError("Invalid quota counts")
    return remaining


def preflight(get: Callable[[str, float], Any] = request_json) -> int:
    """Make one bounded public quota request; do not retry or reserve capacity."""
    return remaining_quota(get("/rate_limit", time.monotonic() + REQUEST_SECONDS))


def main() -> int:
    """Return 0 for sufficient observed capacity, 1 for unavailable, 2 for low."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        remaining = preflight()
    except (OSError, ValueError, http.client.HTTPException, subprocess.SubprocessError):
        print("ERROR: public upstream quota unavailable", file=sys.stderr)
        return 1
    if remaining < REQUIRED:
        print(f"BLOCKED: public upstream quota {remaining}/{REQUIRED} required", file=sys.stderr)
        return 2
    print(f"PASS: public upstream quota {remaining}/{REQUIRED} required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
