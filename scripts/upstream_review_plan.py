"""Derive deterministic review requirements from exact upstream report inputs."""

import hashlib
from typing import Any

from check_upstream_review import MAX_REPORT
from verify_upstream_review import verify

ACTIONS = {
    "archived": ("repository-maintenance", "replacement-assessment"),
    "branch": ("branch-identity", "source-delta"),
    "head": ("source-delta", "compatibility", "security"),
    "license": ("license-text", "redistribution"),
    "release_id": ("release-identity", "release-notes", "artifact-provenance"),
    "tag": ("release-identity", "release-notes", "artifact-provenance"),
    "release_commit": ("release-identity", "source-delta", "artifact-provenance",
                       "compatibility", "security"),
}


def review_plan(baseline: bytes, observed: bytes, claimed: bytes) -> dict[str, Any]:
    """Reject incomplete evidence and emit review requirements, never approval."""
    if any(len(raw) > MAX_REPORT for raw in (baseline, observed, claimed)):
        raise ValueError("Upstream review plan input exceeds budget")
    result = verify(baseline, observed, claimed)
    if result["status"] not in ("UNCHANGED", "REVIEW"):
        raise ValueError("Incomplete upstream review evidence")
    rows = []
    for row in result["rows"]:
        if row["status"] != "REVIEW":
            continue
        requirements = {"regression-test-plan", "owner-review"}
        for field in row["changed"]:
            requirements.update(ACTIONS[field])
        rows.append({"repository": row["repository"], "changed": row["changed"],
                     "required_reviews": sorted(requirements)})
    return {"schema": 1, "status": result["status"], "adoption_authorized": False,
            "baseline_sha256": result["baseline_sha256"],
            "observed_sha256": result["observed_sha256"],
            "report_sha256": hashlib.sha256(claimed).hexdigest(), "rows": rows}
