#!/usr/bin/env python3
"""Collect public GitHub metadata for reviewed repositories, without credentials."""

import argparse
import http.client
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Callable
from urllib.parse import quote, unquote

from artifact_manifest import strict_json
from check_upstream_review import LABEL, REPOSITORIES
from upstream_observation_adapter import extract_row

MAX_RESPONSE = 1024 * 1024
REQUEST_SECONDS = 12
RUN_SECONDS = 180
ORIGIN = "api.github.com"
SUFFIX = re.compile(r"/(?:commits/|git/ref/tags/)((?:[A-Za-z0-9._~+-]|%[0-9A-F]{2}){1,384})")


def allowed_path(path: str) -> bool:
    """Admit only fixed repository metadata and reviewed GET endpoint shapes."""
    for repo in REPOSITORIES:
        prefix = "/repos/" + repo
        if path == prefix or path == prefix + "/releases/latest":
            return True
        match = SUFFIX.fullmatch(path[len(prefix):]) if path.startswith(prefix) else None
        if match:
            try:
                return segment(unquote(match[1], errors="strict")) == match[1]
            except (ValueError, UnicodeError):
                return False
    return False


def segment(value: Any) -> str:
    """Encode one bounded branch or tag reference, rejecting dot segments."""
    if not isinstance(value, str) or not LABEL.fullmatch(value):
        raise ValueError("Invalid upstream reference")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("Invalid upstream reference")
    return quote(value, safe="")


def fetch_bytes(path: str) -> bytes:
    """One fixed-origin verified HTTPS GET; no redirects or proxy delegation."""
    if not allowed_path(path):
        raise ValueError("Unreviewed upstream endpoint")
    connection = http.client.HTTPSConnection(ORIGIN, timeout=REQUEST_SECONDS)
    try:
        connection.request("GET", path, headers={"Accept": "application/vnd.github+json",
                           "User-Agent": "VeyPanel-upstream-review",
                           "X-GitHub-Api-Version": "2022-11-28"})
        with connection.getresponse() as response:
            if response.status != 200:
                raise ValueError("Upstream HTTP request refused")
            encoding = response.getheader("Content-Encoding", "identity")
            if encoding.lower() != "identity":
                raise ValueError("Unexpected upstream content encoding")
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Upstream response exceeds budget")
            return raw
    finally:
        connection.close()


def request_json(path: str, deadline: float) -> Any:
    """Enforce the wall-clock budget outside the socket/DNS worker process."""
    remaining = deadline - time.monotonic()
    if remaining <= 0 or not allowed_path(path):
        raise ValueError("Upstream request budget or endpoint invalid")
    child = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                            "--worker-path", path], capture_output=True,
                           timeout=min(REQUEST_SECONDS, remaining), check=False)
    if child.returncode or len(child.stdout) > MAX_RESPONSE or time.monotonic() > deadline:
        raise ValueError("Upstream request failed")
    return strict_json(child.stdout)


def collect_row(repo: str, get: Callable[[str], Any]) -> dict[str, Any]:
    """Collect five sequential API snapshots and normalize only complete rows."""
    if repo not in REPOSITORIES:
        raise ValueError("Unreviewed repository")
    prefix = "/repos/" + repo
    metadata = get(prefix)
    if not isinstance(metadata, dict) or metadata.get("full_name") != repo:
        raise ValueError("Upstream repository identity mismatch")
    branch = get(prefix + "/commits/" + segment(metadata.get("default_branch")))
    release = get(prefix + "/releases/latest")
    if not isinstance(release, dict):
        raise ValueError("Invalid upstream release")
    tag = segment(release.get("tag_name"))
    reference = get(prefix + "/git/ref/tags/" + tag)
    resolved = get(prefix + "/commits/" + tag)
    return extract_row(repo, metadata, branch, release, reference, resolved)


def collect(get: Callable[[str], Any]) -> tuple[dict[str, Any], bool]:
    """Omit failed rows and expose only fixed repository names in diagnostics."""
    rows = {}
    for repo in sorted(REPOSITORIES):
        try:
            rows[repo] = collect_row(repo, get)
        except (OSError, ValueError, http.client.HTTPException, subprocess.TimeoutExpired):
            print("ERROR: incomplete observation for " + repo, file=sys.stderr)
    return {"schema": 1, "repositories": rows}, set(rows) == REPOSITORIES


def main() -> int:
    """Write normalized JSON to stdout; return 1 for incomplete observation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-path", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_path is not None:
        try:
            sys.stdout.buffer.write(fetch_bytes(args.worker_path))
        except (OSError, ValueError, http.client.HTTPException):
            return 1
        return 0
    deadline = time.monotonic() + RUN_SECONDS
    document, complete = collect(lambda path: request_json(path, deadline))
    print(json.dumps(document, indent=2, sort_keys=True))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
