#!/usr/bin/env bash
set -euo pipefail
# Only invoke on an isolated freshly booted emulator. Never clear a physical device.
serial="$(adb get-serialno)"
[[ "$serial" == emulator-* ]] || { echo "FAIL: isolated emulator required"; exit 2; }
adb install android/app/build/outputs/apk/debug/app-debug.apk
adb install android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb shell am instrument -w -e isolated true com.veypanel.client.test/com.veypanel.client.StoreInstrumentation | tee runtime-smoke.log
grep -Fq 'PASS: AndroidKeyStore actual encryption' runtime-smoke.log
grep -Eq '^INSTRUMENTATION_CODE: -1' runtime-smoke.log
! grep -Fq 'FAIL:' runtime-smoke.log
