#!/usr/bin/env python3
"""Qualify Python-owned sharing handles against isolated C# smoke contenders."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from windows_maintenance_lease import Identity, identified_lease, lease


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



def identity_probe(assembly: Path, path: Path, identity: Identity, expected: int) -> None:
    """Compare the held file identity without publishing identifiers."""
    environment = dict(os.environ, TEMP=str(path.parent.parent), TMP=str(path.parent.parent))
    result = subprocess.run(
        [str(assembly), "--maintenance-identity-probe", str(path),
         f"{identity[0]:08x}{identity[1]:016x}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=15, check=False, env=environment,
    )
    if result.returncode != expected:
        print(f"FAIL: identity contender expected={expected} actual={result.returncode}",
              file=sys.stderr)
        raise RuntimeError("Cross-language identity mismatch")


def check_refusal(path: Path, expected: Identity, reason: str) -> None:
    """Require stale or unsafe identity refusal rather than admission."""
    try:
        with identified_lease(path, False, expected):
            raise RuntimeError("Invalid lease identity admitted")
    except ValueError as error:
        if str(error) != reason:
            raise RuntimeError("Unexpected identity refusal category") from None
        return


def exercise_identity(assembly: Path, path: Path) -> None:
    """Compare real handles across languages and reject stale identity and aliases."""
    replacement = path.with_name("replacement.fixture")
    replacement.write_bytes(b"VP")
    with identified_lease(path, False) as original:
        if original is None:
            raise RuntimeError("Identity observation busy")
        identity_probe(assembly, path, original, 0)
        wrong = (original[0] ^ 1, original[1])
        identity_probe(assembly, path, wrong, 12)
        check_refusal(path, wrong, "Lease handle identity mismatch")
    alias = path.with_name("alias.fixture")
    os.link(path, alias)
    try:
        check_refusal(path, original, "Unsafe lease handle identity")
        identity_probe(assembly, path, original, 4)
    finally:
        alias.unlink()
    os.replace(replacement, path)
    check_refusal(path, original, "Lease handle identity mismatch")
    identity_probe(assembly, path, original, 12)
    with identified_lease(path, True) as current:
        if current is None or current == original:
            raise RuntimeError("Replacement identity unavailable")
    with identified_lease(path, False, current) as observed:
        if observed != current:
            raise RuntimeError("Expected identity not admitted")
        identity_probe(assembly, path, current, 0)
    if path.read_bytes() != b"VP":
        raise RuntimeError("Identity fixture bytes changed")
    print("PASS: cross-language expected identity, alias and replacement refusal")

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
            path = Path(temporary).resolve(strict=True) / "admission.fixture"
            exercise(assembly, path)
            exercise_identity(assembly, path)
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
