#!/usr/bin/env python3
"""Query OSV for reviewed public runtime package coordinates only."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import urllib.request

URL = "https://api.osv.dev/v1/querybatch"
MAX_RESPONSE = 8 * 1024 * 1024
MAX_COMPONENTS = 100
MAX_PAGES = 10


def load_queries(paths):
    """Extract exact Maven and NuGet versions from scoped inventories."""
    entries = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for component in data["components"]:
            purl = component["purl"]
            name, version = component["name"], component["version"]
            if purl.startswith("pkg:maven/"):
                package = {"ecosystem": "Maven",
                           "name": component["group"] + ":" + name}
            elif purl.startswith("pkg:nuget/"):
                package = {"ecosystem": "NuGet", "name": name}
            else:
                raise ValueError("Unsupported component ecosystem")
            if not name or not version or purl in entries:
                raise ValueError("Invalid or duplicate component")
            entries[purl] = {"package": package, "version": version}
    if not 0 < len(entries) <= MAX_COMPONENTS:
        raise ValueError("Invalid inventory size")
    return entries


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never send package coordinates to a redirected endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected OSV redirect")


def fetch(queries):
    """Send exact public package coordinates to the documented HTTPS API."""
    payload = json.dumps({"queries": queries}).encode("utf-8")
    request = urllib.request.Request(URL, data=payload,
                                     headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=25) as response:
        raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("OSV response exceeds size limit")
    return json.loads(raw)


def scan(entries, request=fetch):
    """Follow bounded pagination, reject incomplete or malformed responses."""
    findings = {purl: {} for purl in entries}
    pending = [(purl, query, None) for purl, query in entries.items()]
    seen_tokens = set()
    for _ in range(MAX_PAGES):
        queries = [dict(query, page_token=token) if token else query
                   for _, query, token in pending]
        results = request(queries)["results"]
        if not isinstance(results, list) or len(results) != len(pending):
            raise ValueError("Incomplete OSV batch response")
        following = []
        for (purl, query, _), result in zip(pending, results):
            if not isinstance(result, dict) or set(result) - {"vulns", "next_page_token"}:
                raise ValueError("Unexpected OSV result schema")
            vulns = result.get("vulns", [])
            if not isinstance(vulns, list):
                raise ValueError("Invalid OSV vulnerability list")
            for vuln in vulns:
                ident, modified = vuln["id"], vuln["modified"]
                if not isinstance(ident, str) or not ident or not isinstance(modified, str):
                    raise ValueError("Invalid advisory record")
                findings[purl][ident] = modified
            token = result.get("next_page_token")
            if token:
                if not isinstance(token, str) or (purl, token) in seen_tokens:
                    raise ValueError("Invalid or repeated OSV page token")
                seen_tokens.add((purl, token))
                following.append((purl, query, token))
        if not following:
            return findings
        pending = following
    raise ValueError("OSV pagination limit exceeded; audit incomplete")


def main():
    """Write a time-stamped advisory inventory, not a security approval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventories", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        entries = load_queries(args.inventories)
        results = scan(entries)
        report = {
            "source": URL, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "reviewed runtime package coordinates only",
            "components": [{"purl": key, "advisories": [
                {"id": ident, "modified": modified}
                for ident, modified in sorted(value.items())]}
                for key, value in sorted(results.items())],
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"FAIL: advisory audit incomplete: {error}", file=sys.stderr)
        return 1
    matches = sum(len(value) for value in results.values())
    print(f"PASS: queried {len(results)} components; {matches} advisory matches")
    print("NOTE: matches require review; no matches do not establish safety")
    return 0


if __name__ == "__main__":
    sys.exit(main())
