#!/usr/bin/env python3
"""Qualify Python-owned sharing handles against isolated C# smoke contenders."""

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from windows_maintenance_lease import lease


def probe(assembly: Path, path: Path, mode: str, expected: int) -> None:
    """Run only the trusted smoke assembly with bounded captured output."""
    result = subprocess.run(
        ["dotnet", str(assembly), "--maintenance-lease-probe", str(path), mode],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=15, check=False,
    )
    if result.returncode != expected:
        raise RuntimeError("Cross-language lease result mismatch")


def exercise(assembly: Path, path: Path) -> None:
    """Verify both ownership modes and unchanged bytes across processes."""
    path.write_bytes(b"VP")
    with lease(path, False) as admitted:
        if not admitted:
            raise RuntimeError("Python shared lease refused")
        probe(assembly, path, "shared", 0)
        probe(assembly, path, "exclusive", 2)
        print("PASS: Python shared lease admits C# runtime and blocks maintenance")
    with lease(path, True) as admitted:
        if not admitted:
            raise RuntimeError("Python exclusive lease refused")
        probe(assembly, path, "shared", 2)
        probe(assembly, path, "exclusive", 2)
        print("PASS: Python exclusive lease blocks C# runtime and maintenance")
    probe(assembly, path, "shared", 0)
    probe(assembly, path, "exclusive", 0)
    if path.read_bytes() != b"VP":
        raise RuntimeError("Lease fixture bytes changed")
    print("PASS: cross-language lease release and unchanged bytes")


def main() -> int:
    """Run native Windows interop only with a trusted compiled smoke assembly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", required=True, type=Path)
    args = parser.parse_args()
    try:
        assembly = args.assembly.resolve(strict=True)
        if sys.platform != "win32" or assembly.name != "VeyPanel.Smoke.dll":
            raise ValueError("Native Windows smoke assembly required")
        with tempfile.TemporaryDirectory(prefix="veypanel-lease-") as temporary:
            exercise(assembly, Path(temporary).absolute() / "admission.fixture")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print("FAIL: isolated cross-language maintenance lease", file=sys.stderr)
        return 1
    print("PASS: isolated cross-language maintenance lease")
    return 0


if __name__ == "__main__":
    sys.exit(main())
