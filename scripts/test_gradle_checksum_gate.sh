#!/usr/bin/env bash
# Prove Gradle rejects a deliberately incorrect artifact digest, then restore.
set -euo pipefail
cd "$(dirname "$0")/../android"
metadata=gradle/verification-metadata.xml
backup=$(mktemp)
log=$(mktemp)
cp "$metadata" "$backup"
cleanup() {
    cp "$backup" "$metadata"
    rm -f "$backup" "$log"
}
trap cleanup EXIT
gradle --no-daemon --dependency-verification strict :app:resolveDebugRuntimeArtifacts
python3 - "$metadata" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()
pattern = r'(<artifact name="core-3\.5\.3\.jar">\s*<sha256 value=")[0-9a-f]{64}(")'
text, count = re.subn(pattern, lambda m: m[1] + "0" * 64 + m[2], text)
if count != 1:
    raise SystemExit("Expected precisely one ZXing checksum to modify")
path.write_text(text)
PY
if gradle --no-daemon --dependency-verification strict :app:resolveDebugRuntimeArtifacts >"$log" 2>&1; then
    echo 'FAIL: Gradle accepted an incorrect dependency checksum'
    exit 1
fi
if ! grep -qi 'dependency verification failed' "$log" || ! grep -Fq 'core-3.5.3.jar' "$log"; then
    cat "$log"
    echo 'FAIL: Gradle failed for an unrelated reason'
    exit 1
fi
echo 'PASS: Gradle rejected the deliberately incorrect ZXing artifact SHA-256'
