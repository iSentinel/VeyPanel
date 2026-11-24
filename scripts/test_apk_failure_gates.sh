#!/usr/bin/env bash
# Verify real rejecting commands remain failures when their output is recorded.
set -euo pipefail
if [[ $# -ne 4 ]]; then
    echo "Usage: $0 APK BADGING GRADLE APKSIGNER" >&2
    exit 2
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
apk=$1
badging=$2
gradle=$3
signer=$4
printf 'not an APK\n' > "$work/invalid.apk"
grep -v "^uses-permission: name='android.permission.CAMERA'$" "$badging" > "$work/missing-camera.txt"
reject() {
    local label=$1 expected=$2
    shift 2
    local result=0
    "$@" 2>&1 | tee "$work/$label.txt" || result=$?
    if [[ $result -eq 0 || ! -s "$work/$label.txt" ]] || ! grep -qiF "$expected" "$work/$label.txt"; then
        echo "FAIL: negative $label gate did not reject as expected" >&2
        return 1
    fi
    echo "PASS: negative $label gate propagated rejection ($result)"
}
python3 scripts/verify_android_apk.py "$apk" >/dev/null
"$signer" verify "$apk"
python3 scripts/check_android_badging.py "$badging" "$gradle" >/dev/null
reject archive 'FAIL: APK integrity' python3 scripts/verify_android_apk.py "$work/invalid.apk"
reject identity 'Missing APK permissions: android.permission.CAMERA' python3 scripts/check_android_badging.py "$work/missing-camera.txt" "$gradle"
reject signing '' "$signer" verify "$work/invalid.apk"
