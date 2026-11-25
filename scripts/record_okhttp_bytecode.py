#!/usr/bin/env python3
"""Record bounded static javap evidence for the pinned OkHttp WSS implementation."""

import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

from artifact_manifest import regular
from check_gradle_verification import inventory, read_metadata

COORDINATE = ("com.squareup.okhttp3", "okhttp", "4.12.1", "okhttp-4.12.1.jar")
CLASSES = tuple("okhttp3.internal.ws." + name for name in
                ("WebSocketReader", "RealWebSocket", "MessageInflater"))
MAX_JAR = 2 * 1024 * 1024
MAX_CLASS = 128 * 1024
MAX_REPORT = 2 * 1024 * 1024


def inspect_jar(path: Path, expected: str) -> tuple[bytes, list[dict[str, object]]]:
    """Verify the exact bytes before inspecting the requested class entries."""
    info = path.lstat()
    if not regular(info) or info.st_size > MAX_JAR:
        raise ValueError("Unsafe or oversized OkHttp JAR")
    with path.open("rb") as source:
        raw = source.read(MAX_JAR + 1)
    if len(raw) > MAX_JAR or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("OkHttp JAR digest mismatch")
    rows = []
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) > 10000:
            raise ValueError("Excessive JAR entries")
        for name in CLASSES:
            member = name.replace(".", "/") + ".class"
            matches = [info for info in infos if info.filename == member]
            if len(matches) != 1 or matches[0].file_size > MAX_CLASS:
                raise ValueError("Missing, duplicate or oversized WSS class")
            data = archive.read(matches[0])
            if not data.startswith(bytes.fromhex("cafebabe")):
                raise ValueError("Invalid class header")
            rows.append({"class": name, "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
    return raw, rows


def find_jar() -> Path:
    """Require one resolved JAR in the dedicated trusted Gradle cache."""
    home = Path(os.environ.get("GRADLE_USER_HOME") or Path.home() / ".gradle")
    directory = home / "caches/modules-2/files-2.1"
    directory = directory.joinpath(*COORDINATE[:3])
    matches = []
    for path in directory.glob("*/" + COORDINATE[3]):
        matches.append(path)
        if len(matches) > 1:
            raise ValueError("Ambiguous cached OkHttp JAR")
    if len(matches) != 1:
        raise ValueError("Pinned OkHttp JAR unavailable")
    return matches[0]


def disassemble(raw: bytes) -> bytes:
    """Invoke trusted JDK javap on a private copy of the hash-verified bytes."""
    with tempfile.TemporaryDirectory() as temporary:
        copy = Path(temporary) / COORDINATE[3]
        copy.write_bytes(raw)
        result = subprocess.run(["javap", "-c", "-p", "-classpath", str(copy), *CLASSES],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=30, check=True)
    if not 0 < len(result.stdout) <= MAX_REPORT:
        raise ValueError("Invalid javap output size")
    if any(name.encode("ascii") not in result.stdout for name in CLASSES):
        raise ValueError("Incomplete javap output")
    return result.stdout


def record(path: Path, metadata: Path, output: Path) -> None:
    """Write separate review evidence; do not claim semantic or publisher verification."""
    expected = inventory(read_metadata(metadata))[COORDINATE]
    raw, classes = inspect_jar(path, expected)
    report = disassemble(raw)
    data = {"schema": 1, "coordinate": ":".join(COORDINATE[:3]),
            "jar_sha256": expected, "classes": classes,
            "javap_sha256": hashlib.sha256(report).hexdigest(),
            "scope": "static-disassembly", "source_to_binary": "NOT_ESTABLISHED",
            "preallocation_bound": "REVIEW_REQUIRED"}
    output.mkdir(mode=0o700, exist_ok=False)
    (output / "javap.txt").write_bytes(report)
    (output / "summary.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")


def main() -> int:
    """Use the committed metadata and a fresh report directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        record(args.jar or find_jar(), args.metadata, args.output)
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile,
            subprocess.SubprocessError):
        print("FAIL: OKHTTP_BYTECODE_EVIDENCE_UNAVAILABLE", file=sys.stderr)
        return 1
    print("PASS: pinned OkHttp static disassembly captured; semantic review required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
