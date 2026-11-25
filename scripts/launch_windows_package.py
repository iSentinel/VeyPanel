#!/usr/bin/env python3
"""Plan or explicitly launch the selected Windows package from verified bytes."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from artifact_manifest import MANIFEST
from stage_windows_package import digest, preflight
from windows_package_selection import (
    SHA, plain, read_state, root_path, selection_lock, verify_record,
)

DESKTOP = "VeyPanel.Desktop.exe"


def windows_runtime() -> bool:
    """Only a native Windows interpreter can activate the package."""
    return sys.platform == "win32"


def verified_target(root: Path, package: Path, expected: str) -> Path:
    """Bind selected files to the externally digest-pinned source archive."""
    if not SHA.fullmatch(expected):
        raise ValueError("Expected complete SHA-256")
    active = read_state(root)["active"]
    if active is None or active["package_sha256"] != expected:
        raise ValueError("Selected package does not match expected digest")
    directory = verify_record(root, active)
    plain(package)
    with package.open("rb") as source:
        if digest(source) != expected:
            raise ValueError("External SHA-256 mismatch")
        with zipfile.ZipFile(source) as archive:
            preflight(archive)
            if archive.read(MANIFEST) != (directory / MANIFEST).read_bytes():
                raise ValueError("Selected manifest differs from trusted archive")
            if digest(source) != expected:
                raise ValueError("Package changed during verification")
    exe = directory / DESKTOP
    plain(exe)
    return exe


def launch(root: Path, package: Path, expected: str,
           apply: bool = False) -> dict[str, str | bool | int]:
    """Reverify and launch only the fixed Desktop executable, without a shell."""
    root = root_path(root)
    if apply and not windows_runtime():
        raise ValueError("Activation requires native Windows")
    with selection_lock(root, apply):
        exe = verified_target(root, package, expected.lower())
        result = {"package_sha256": expected.lower(),
                  "executable": str(exe), "working_directory": str(exe.parent),
                  "started": False}
        if apply:
            process = subprocess.Popen([str(exe)], cwd=str(exe.parent), shell=False)
            result.update(started=True, pid=process.pid)
        return result


def main() -> int:
    """Default to a read-only launch plan; apply explicitly starts Desktop."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = launch(args.root, args.package, args.sha256, args.apply)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            AttributeError, zipfile.BadZipFile) as error:
        reason = "FILESYSTEM_OR_PROCESS_ERROR" if isinstance(error, OSError) else "PACKAGE_VALIDATION_FAILED"
        print(f"FAIL: package launcher: {reason}; check the private root and trusted archive",
              file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS: process created; readiness not established" if result["started"]
          else "PASS: dry-run; no process started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
