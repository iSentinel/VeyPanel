#!/usr/bin/env python3
"""Qualify Python-owned sharing handles against isolated C# smoke contenders."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from windows_maintenance_lease import lease


def probe(assembly: Path, path: Path, mode: str, expected: int) -> None:
    """Run only the trusted smoke assembly with bounded captured output."""
    # Python and .NET may choose different temporary directories by default.
    environment = dict(os.environ, TEMP=str(path.parent.parent), TMP=str(path.parent.parent))
    result = subprocess.run(
        [str(assembly), "--maintenance-lease-probe", str(path), mode],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=15, check=False, env=environment,
    )
    if result.returncode != expected:
        print(f"FAIL: contender mode={mode} expected={expected} actual={result.returncode}",
              file=sys.stderr)
        raise RuntimeError("Cross-language lease result mismatch")


def exercise(assembly: Path, path: Path) -> None:
    """Verify both ownership modes and unchanged bytes across processes."""
    path.write_bytes(b"VP")
    print("STAGE: uncontended fixture admission", flush=True)
    probe(assembly, path, "shared", 0)
    probe(assembly, path, "exclusive", 0)
    print("STAGE: Python shared owner", flush=True)
    with lease(path, False) as admitted:
        if not admitted:
            raise RuntimeError("Python shared lease refused")
        probe(assembly, path, "shared", 0)
        probe(assembly, path, "exclusive", 2)
        print("PASS: Python shared lease admits C# runtime and blocks maintenance")
    print("STAGE: Python exclusive owner", flush=True)
    with lease(path, True) as admitted:
        if not admitted:
            raise RuntimeError("Python exclusive lease refused")
        probe(assembly, path, "shared", 2)
        probe(assembly, path, "exclusive", 2)
        print("PASS: Python exclusive lease blocks C# runtime and maintenance")
    print("STAGE: released owner", flush=True)
    probe(assembly, path, "shared", 0)
    probe(assembly, path, "exclusive", 0)
    if path.read_bytes() != b"VP":
        raise RuntimeError("Lease fixture bytes changed")
    print("PASS: cross-language lease release and unchanged bytes")


def main() -> int:
    """Run native Windows interop only with a trusted compiled smoke apphost."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly", required=True, type=Path)
    args = parser.parse_args()
    try:
        assembly = args.assembly.resolve(strict=True)
        if sys.platform != "win32" or assembly.name != "VeyPanel.Smoke.exe":
            raise ValueError("Native Windows smoke apphost required")
        with tempfile.TemporaryDirectory(prefix="veypanel-lease-") as temporary:
            exercise(assembly, Path(temporary).resolve(strict=True) / "admission.fixture")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        # Only fixed exception categories, never raw messages or fixture paths.
        category = ("OS" if isinstance(error, OSError) else
                    "TIMEOUT" if isinstance(error, subprocess.TimeoutExpired) else
                    "VALIDATION" if isinstance(error, ValueError) else "FIXTURE")
        print(f"FAIL: isolated cross-language maintenance lease ({category})", file=sys.stderr)
        return 1
    print("PASS: isolated cross-language maintenance lease")
    return 0


if __name__ == "__main__":
    sys.exit(main())
