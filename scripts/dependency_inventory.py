#!/usr/bin/env python3
"""Convert resolved Maven or NuGet inventories to deterministic CycloneDX JSON."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

MAX_INPUT = 32 * 1024 * 1024
MAX_COMPONENTS = 10000


def field(value):
    """Reject malformed coordinates and control characters."""
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ValueError("Invalid component coordinate")
    if any(ord(char) < 33 or char in "/\\" for char in value):
        raise ValueError("Invalid component coordinate")
    return value


def component(kind, name, version, group=None):
    """Create a library component with a package URL."""
    name, version = field(name), field(version)
    namespace = field(group) if group is not None else None
    path = (quote(namespace, safe="") + "/" if namespace else "")
    purl = f"pkg:{kind}/{path}{quote(name, safe='')}@{quote(version, safe='')}"
    item = {"type": "library", "name": name, "version": version,
            "purl": purl, "bom-ref": purl}
    if namespace:
        item["group"] = namespace
    return item


def maven_components(data):
    """Map the selected Gradle runtime modules."""
    if not isinstance(data, list):
        raise ValueError("Expected Gradle module array")
    return [component("maven", row["name"], row["version"], row["group"])
            for row in data]


def nuget_components(data):
    """Map package entries in the restored Windows x64 target graph."""
    targets = data["targets"]
    keys = [key for key in targets if key.endswith("/win-x64")]
    if len(keys) != 1:
        raise ValueError("Expected exactly one win-x64 target")
    packages = []
    for coordinate, details in targets[keys[0]].items():
        if details.get("type") != "package":
            continue
        name, version = coordinate.split("/", 1)
        packages.append(component("nuget", name, version))
    return packages


def make_bom(data, kind, label):
    """Build a scoped inventory; do not invent licenses or dependency edges."""
    items = maven_components(data) if kind == "maven" else nuget_components(data)
    if not 0 < len(items) <= MAX_COMPONENTS:
        raise ValueError("Empty or excessive dependency inventory")
    refs = {item["purl"] for item in items}
    if len(refs) != len(items):
        raise ValueError("Duplicate resolved component")
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
            "metadata": {"component": {"type": "application", "name": field(label)}},
            "components": sorted(items, key=lambda item: item["purl"])}


def main():
    """Read bounded JSON and emit a stable, sorted BOM."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["maven", "nuget"])
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > MAX_INPUT:
            raise ValueError("Dependency report exceeds size budget")
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        bom = make_bom(data, args.kind, args.label)
        args.output.write_text(json.dumps(bom, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"FAIL: dependency inventory: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {len(bom['components'])} resolved {args.kind} components")
    return 0


if __name__ == "__main__":
    sys.exit(main())
