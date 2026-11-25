"""Normalize reviewed GitHub API snapshots without network or pin changes."""

from typing import Any

from check_upstream_review import REPOSITORIES, valid_row


def extract_row(repo: str, metadata: Any, branch_commit: Any, release: Any,
                tag_ref: Any, resolved_commit: Any) -> dict[str, Any]:
    """Require repository identity and corroborated direct release commit."""
    if repo not in REPOSITORIES or not all(isinstance(value, dict) for value in
            (metadata, branch_commit, release, tag_ref, resolved_commit)):
        raise ValueError("Invalid upstream API snapshot")
    license_info = metadata.get("license")
    target = tag_ref.get("object")
    tag = release.get("tag_name")
    if (metadata.get("full_name") != repo or not isinstance(license_info, dict)
            or release.get("draft") is not False
            or release.get("prerelease") is not False or not isinstance(tag, str)
            or tag_ref.get("ref") != "refs/tags/" + tag
            or not isinstance(target, dict) or target.get("type") != "commit"
            or target.get("sha") != resolved_commit.get("sha")):
        raise ValueError("Upstream identity or release evidence mismatch")
    row = {"branch": metadata.get("default_branch"), "head": branch_commit.get("sha"),
           "release_id": release.get("id"), "tag": tag,
           "release_commit": target.get("sha"), "license": license_info.get("spdx_id"),
           "archived": metadata.get("archived")}
    if not valid_row(row):
        raise ValueError("Invalid upstream metadata row")
    return row
