#!/usr/bin/env python3
"""Collect license evidence from checksum-verified resolved dependency files."""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from check_gradle_verification import inventory, read_metadata

MAX_XML = 2 * 1024 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024
MAX_NOTICE = 2 * 1024 * 1024


def digest(path, algorithm):
    """Hash the exact cached artifact with a bounded streaming reader."""
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
        raise ValueError("Missing or oversized dependency file: " + path.name)
    result = hashlib.new(algorithm)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result


def parse_xml(raw):
    """Read bounded XML without DTD or entity declarations."""
    if len(raw) > MAX_XML or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Unsafe or oversized package XML")
    return ET.fromstring(raw)


def maven_licenses(raw):
    """Return explicit POM declarations; do not infer inherited licenses."""
    root = parse_xml(raw)
    return [{key: item.findtext("{*}" + key) for key in ("name", "url")}
            for item in root.findall("{*}licenses/{*}license")]


def nuget_licenses(raw):
    """Return literal NuGet license metadata without resolving URLs."""
    root = parse_xml(raw)
    metadata = root.find("{*}metadata")
    if metadata is None:
        raise ValueError("Missing NuGet package metadata")
    result = [{"type": item.get("type"), "value": item.text}
              for item in metadata.findall("{*}license")]
    url = metadata.findtext("{*}licenseUrl")
    if url:
        result.append({"type": "legacy-url", "value": url})
    return result


def is_notice(name):
    """Identify candidate license/notice entries by basename."""
    basename = name.rsplit("/", 1)[-1].casefold()
    return basename.startswith(("license", "licence", "notice", "copying",
                                "third-party-notices", "thirdpartynotices"))


def archive_evidence(path, read_nuspec=False):
    """Record candidate document hashes and optional NuGet declarations."""
    notices, declarations = [], []
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 50000:
            raise ValueError("Excessive package archive entries")
        nuspecs = [i for i in entries if not i.is_dir()
                   and i.filename.lower().endswith(".nuspec")]
        if read_nuspec:
            if len(nuspecs) != 1 or nuspecs[0].file_size > MAX_XML:
                raise ValueError("Expected one bounded NuGet nuspec")
            declarations = nuget_licenses(archive.read(nuspecs[0]))
        for entry in entries:
            if entry.is_dir() or not is_notice(entry.filename):
                continue
            if entry.file_size > MAX_NOTICE:
                raise ValueError("Oversized license document")
            data = archive.read(entry)
            notices.append({"path": entry.filename, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    return {"declared_licenses": declarations,
            "notice_files": sorted(notices, key=lambda row: row["path"])}


def maven_record(component, records, cache):
    """Inspect only artifacts whose SHA-256 matches committed Gradle metadata."""
    coordinate = tuple(component[key] for key in ("group", "name", "version"))
    directory = cache.joinpath(*coordinate)
    files = []
    for key, expected in sorted(records.items()):
        if key[:3] != coordinate:
            continue
        name = key[3]
        if Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError("Invalid artifact basename")
        matches = sorted(directory.glob("*/" + name))
        if not matches:
            files.append({"name": name, "state": "not-in-cache"})
            continue
        for path in matches:
            if digest(path, "sha256").hexdigest() != expected:
                raise ValueError("Cached Gradle artifact hash mismatch: " + name)
        path = matches[0]
        item = {"name": name, "state": "verified", "sha256": expected}
        if name.endswith(".pom"):
            if path.stat().st_size > MAX_XML:
                raise ValueError("Oversized Maven POM")
            item["declared_licenses"] = maven_licenses(path.read_bytes())
        elif name.endswith((".jar", ".aar")):
            item.update(archive_evidence(path))
        files.append(item)
    if not any(item["state"] == "verified" for item in files):
        raise ValueError("No verified cache evidence for " + component["purl"])
    return {"purl": component["purl"], "artifacts": files}


def signed_content_hash(path):
    """Use the pinned SDK to verify the signature and compute NuGet contentHash."""
    env = dict(os.environ, DOTNET_CLI_UI_LANGUAGE="en-US")
    result = subprocess.run(
        ["dotnet", "nuget", "verify", str(path), "--verbosity", "normal"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=120, check=False)
    if result.returncode != 0:
        raise ValueError("NuGet signature verification failed: " + path.name)
    values = re.findall(r"(?m)^[ \t]*Content hash:[ \t]*([A-Za-z0-9+/]+={0,2})[ \t]*$", result.stdout)
    if len(values) != 1 or len(base64.b64decode(values[0], validate=True)) != 64:
        raise ValueError("Missing or ambiguous NuGet content hash: " + path.name)
    return values[0]


def nuget_content_hash(path):
    """Distinguish signed package content hash from raw archive SHA-512."""
    raw = digest(path, "sha512").digest()
    with zipfile.ZipFile(path) as archive:
        signed = ".signature.p7s" in archive.namelist()
    value = signed_content_hash(path) if signed else base64.b64encode(raw).decode("ascii")
    if raw != digest(path, "sha512").digest():
        raise ValueError("NuGet archive changed during verification")
    return value, base64.b64encode(raw).decode("ascii"), signed


def nuget_record(component, lock, cache):
    """Inspect actual NuGet archive only after matching the lock content hash."""
    name, version = component["name"], component["version"]
    entry = lock["dependencies"]["net10.0"][name]
    if entry["resolved"] != version:
        raise ValueError("NuGet lock version differs from baseline")
    stem = name.lower() + "." + version.lower()
    path = cache / name.lower() / version.lower() / (stem + ".nupkg")
    actual, raw_hash, signed = nuget_content_hash(path)
    if actual != entry["contentHash"]:
        raise ValueError("NuGet package SHA-512 mismatch: " + name)
    item = {"name": path.name, "state": "verified",
            "nuget_content_hash_sha512_base64": actual,
            "archive_sha512_base64": raw_hash,
            "signature_verified": signed}
    item.update(archive_evidence(path, read_nuspec=True))
    return {"purl": component["purl"], "artifacts": [item]}


def main():
    """Build a scoped JSON evidence report; never make a license conclusion."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("maven", "nuget"))
    parser.add_argument("baseline", type=Path)
    parser.add_argument("verification", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    try:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
        if args.kind == "maven":
            cache = args.cache or Path(os.environ.get("GRADLE_USER_HOME",
                Path.home() / ".gradle")) / "caches/modules-2/files-2.1"
            records = inventory(read_metadata(args.verification))
            rows = [maven_record(c, records, cache) for c in baseline["components"]]
        else:
            cache = args.cache or Path(os.environ.get("NUGET_PACKAGES",
                Path.home() / ".nuget/packages"))
            lock = json.loads(args.verification.read_text(encoding="utf-8-sig"))
            rows = [nuget_record(c, lock, cache) for c in baseline["components"]]
        if not rows:
            raise ValueError("Empty dependency evidence")
        report = {"scope": baseline["metadata"]["component"]["name"],
                  "license_conclusion": "not-reviewed", "components": rows}
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError,
            zipfile.BadZipFile, RuntimeError, subprocess.SubprocessError) as error:
        print(f"FAIL: dependency license evidence: {error}", file=sys.stderr)
        return 1
    print(f"PASS: captured license evidence for {len(rows)} components; review pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
