#!/usr/bin/env python3
"""Native contender for the isolated C#-owned maintenance lease fixture."""

import argparse
import os
from pathlib import Path
import sys
import tempfile

from windows_maintenance_lease import lease
from windows_package_selection import root_path


def fixture_path(path: Path, temporary: Path) -> Path:
    """Accept only the fixed file in an isolated direct temporary child."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Invalid fixture path")
    parent = root_path(path.parent).resolve(strict=True)
    if (path.name != "admission.fixture"
            or not parent.name.startswith("veypanel-lease-")
            or os.path.normcase(str(parent.parent)) != os.path.normcase(str(temporary.resolve(strict=True)))):
        raise ValueError("Invalid fixture scope")
    # Do not resolve the held leaf; the lease adapter validates it before open.
    return parent / path.name


def main() -> int:
    """Return zero admitted, two busy, one unavailable; never print paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("mode", choices=("shared", "exclusive"))
    args = parser.parse_args()
    try:
        if sys.platform != "win32":
            raise RuntimeError("Native Windows required")
        path = fixture_path(args.path, Path(tempfile.gettempdir()))
        with lease(path, args.mode == "exclusive") as admitted:
            return 0 if admitted else 2
    except (OSError, ValueError, RuntimeError):
        print("FAIL: native lease contender unavailable", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
