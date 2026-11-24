#!/usr/bin/env python3
"""Check aapt APK identity and permissions against reviewed Gradle settings."""

import argparse
import re
import sys
from pathlib import Path

MAX_REPORT = 256 * 1024
ALLOWED = frozenset({
    "android.permission.INTERNET",
    "android.permission.CAMERA",
})
PACKAGE = re.compile(
    r"^package:\s+name='([^']+)'\s+versionCode='(\d+)'\s+versionName='([^']+)'")
PERMISSION = re.compile(
    r"^uses-permission:\s+name='([^']+)'$")


def gradle_value(text: str, key: str) -> str:
    """Read a single simple Android Gradle property, rejecting ambiguity."""
    matches = re.findall(r"(?m)^\s*" + re.escape(key)
                         + r"\s+(?:'([^']+)'|(\d+))\s*$", text)
    if len(matches) != 1:
        raise ValueError("Gradle property missing or ambiguous: " + key)
    return next(value for value in matches[0] if value)


def badging_value(text: str, key: str) -> str:
    """Read one aapt SDK declaration."""
    pattern = r"(?m)^" + re.escape(key) + r":'(\d+)'$"
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise ValueError("APK SDK declaration missing or ambiguous: " + key)
    return matches[0]


def check_permissions(badging: str) -> tuple[str, ...]:
    """Require exactly the two unconditional reviewed permissions."""
    names = set()
    for line in badging.splitlines():
        line = line.strip()
        if not line.startswith("uses-permission"):
            continue
        match = PERMISSION.fullmatch(line)
        if match is None:
            raise ValueError("Unsupported or malformed APK permission declaration")
        name = match.group(1)
        if name in names:
            raise ValueError("Duplicate APK permission: " + name)
        names.add(name)
    forbidden = names - ALLOWED
    if forbidden:
        raise ValueError("Unexpected APK permissions: " + ", ".join(sorted(forbidden)))
    missing = ALLOWED - names
    if missing:
        raise ValueError("Missing APK permissions: " + ", ".join(sorted(missing)))
    return tuple(sorted(names))


def check_badging(badging: str, gradle: str) -> tuple[str, str, tuple[str, ...]]:
    """Ensure the built package matches source and least-privilege policy."""
    packages = [match.groups() for line in badging.splitlines()
                if (match := PACKAGE.match(line))]
    if len(packages) != 1:
        raise ValueError("Expected exactly one APK package declaration")
    package, code, version = packages[0]
    expected = (
        gradle_value(gradle, "applicationId"),
        gradle_value(gradle, "versionCode"),
        gradle_value(gradle, "versionName"),
    )
    if (package, code, version) != expected:
        raise ValueError("APK identity/version differs from Gradle")
    for apk_key, gradle_key in (("sdkVersion", "minSdk"),
                                ("targetSdkVersion", "targetSdk")):
        if badging_value(badging, apk_key) != gradle_value(gradle, gradle_key):
            raise ValueError("APK SDK policy differs from Gradle")
    permissions = check_permissions(badging)
    return package, version, permissions


def main() -> int:
    """Validate bounded input and print deterministic PASS/FAIL output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("badging", type=Path, help="aapt dump badging output")
    parser.add_argument("gradle", type=Path, help="Android app build.gradle")
    args = parser.parse_args()
    try:
        if args.badging.stat().st_size > MAX_REPORT:
            raise ValueError("APK metadata report exceeds size budget")
        badging = args.badging.read_text(encoding="utf-8")
        gradle = args.gradle.read_text(encoding="utf-8")
        package, version, permissions = check_badging(badging, gradle)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: APK identity: {error}", file=sys.stderr)
        return 1
    print(f"PASS: APK identity: {package} · {version}")
    print("Permissions: " + ", ".join(permissions))
    print("NOTE: Policy checks do not imply trusted release signing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
