#!/usr/bin/env bash
set -euo pipefail
serial="$(adb get-serialno)"
[[ "$serial" == emulator-* ]] || { echo "FAIL: isolated emulator required"; exit 2; }
adb -s "$serial" install android/app/build/outputs/apk/debug/app-debug.apk
adb -s "$serial" install android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb -s "$serial" shell am instrument -w -r -e isolated true com.veypanel.client.test/com.veypanel.client.StoreInstrumentation | tee runtime-smoke.log
grep -Fq 'PASS: AndroidKeyStore actual encryption' runtime-smoke.log
grep -Fq 'PASS: synthetic offline QR decode' runtime-smoke.log
grep -Fq 'PASS: Android extended telemetry fixture' runtime-smoke.log
grep -Eq '^INSTRUMENTATION_CODE: -1[[:space:]]*$' runtime-smoke.log
if grep -Fq 'FAIL:' runtime-smoke.log; then exit 1; fi
echo 'PASS: runtime result gate'
