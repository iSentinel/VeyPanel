#!/usr/bin/env bash
set -euo pipefail
serial="$(adb get-serialno)"
[[ "$serial" == emulator-* ]] || { echo "FAIL: isolated emulator required"; exit 2; }
fixture="$(mktemp -d)"
pid=""
cleanup() {
  if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  adb -s "$serial" reverse --remove tcp:47861 >/dev/null 2>&1 || true
  rm -rf "$fixture"
}
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=VeyPanel isolated fixture CA' \
  -addext 'basicConstraints=critical,CA:TRUE' -addext 'keyUsage=critical,keyCertSign,cRLSign' \
  -keyout "$fixture/ca.key" -out "$fixture/ca.pem" >/dev/null 2>&1
openssl req -new -newkey rsa:2048 -nodes -subj '/CN=127.0.0.1' \
  -keyout "$fixture/server.key" -out "$fixture/server.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=IP:127.0.0.1' 'extendedKeyUsage=serverAuth' 'basicConstraints=critical,CA:FALSE' > "$fixture/extensions"
openssl x509 -req -in "$fixture/server.csr" -CA "$fixture/ca.pem" -CAkey "$fixture/ca.key" \
  -CAcreateserial -days 1 -extfile "$fixture/extensions" -out "$fixture/server.pem" >/dev/null 2>&1
python3 android/tests/transport_fixture.py "$fixture/server.pem" "$fixture/server.key" > "$fixture/server.log" 2>&1 &
pid=$!
for attempt in {1..30}; do
  if grep -Fq 'READY: isolated transport fixture' "$fixture/server.log"; then break; fi
  kill -0 "$pid"
  sleep 1
done
grep -Fq 'READY: isolated transport fixture' "$fixture/server.log"
status="$(curl --silent --show-error --max-time 5 --noproxy '*' --cacert "$fixture/ca.pem" \
  --output /dev/null --write-out '%{http_code}' https://127.0.0.1:47861/api/v1/telemetry)"
[[ "$status" == 401 ]] || { echo "FAIL: fixture readiness HTTP $status"; exit 1; }
echo 'PASS: fixture HTTPS readiness and unauthenticated denial'
adb -s "$serial" reverse tcp:47861 tcp:47861
adb -s "$serial" reverse --list
ca="$(openssl x509 -in "$fixture/ca.pem" -outform DER | base64 -w0)"
adb -s "$serial" install android/app/build/outputs/apk/debug/app-debug.apk
adb -s "$serial" install android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb -s "$serial" shell am instrument -w -r -e isolated true -e fixtureCa "$ca" com.veypanel.client.test/com.veypanel.client.StoreInstrumentation | tee runtime-smoke.log
grep -Fq 'PASS: AndroidKeyStore actual encryption' runtime-smoke.log
grep -Fq 'PASS: synthetic offline QR decode' runtime-smoke.log
grep -Fq 'PASS: Android extended telemetry fixture' runtime-smoke.log
grep -Fq 'PASS: Android bounded history fixture' runtime-smoke.log
grep -Fq 'PASS: Android Host history codec fixture' runtime-smoke.log
grep -Fq 'PASS: Android Activity diagnostics, AVC Surface preview and local touch probe' runtime-smoke.log
grep -Fq 'PASS: read-only Android video decoder API survey (no hardware guarantee)' runtime-smoke.log
grep -Fq 'PASS: Android local AVC self-test decodes original clip twice (emulator only)' runtime-smoke.log
grep -Fq 'PASS: Android MediaCodec delivered original AVC frame to test Surface (emulator only)' runtime-smoke.log
grep -Fq 'PASS: bounded TLS and persistent stream reject unknown CA and oversized frame; ping/pong, two samples, close, cancellation and drip-feed deadline' runtime-smoke.log
grep -Fq 'PASS: isolated HTTPS/WSS transport, TLS denial, fallback and revocation' runtime-smoke.log
grep -Eq '^INSTRUMENTATION_CODE: -1[[:space:]]*$' runtime-smoke.log
if grep -Fq 'FAIL:' runtime-smoke.log; then exit 1; fi
# Second phase: same trusted test CA, matching CN but deliberately wrong IP SAN.
# Stop only the owned positive fixture; preserve all first-phase result gates.
kill "$pid"
wait "$pid" || true
pid=""
openssl req -new -newkey rsa:2048 -nodes -subj '/CN=127.0.0.1' \
  -keyout "$fixture/wrong.key" -out "$fixture/wrong.csr" >/dev/null 2>&1
printf '%s\n' 'subjectAltName=IP:127.0.0.2' 'extendedKeyUsage=serverAuth' 'basicConstraints=critical,CA:FALSE' > "$fixture/wrong.extensions"
openssl x509 -req -in "$fixture/wrong.csr" -CA "$fixture/ca.pem" -CAkey "$fixture/ca.key" \
  -CAserial "$fixture/ca.srl" -days 1 -extfile "$fixture/wrong.extensions" -out "$fixture/wrong.pem" >/dev/null 2>&1
openssl verify -CAfile "$fixture/ca.pem" -purpose sslserver -verify_ip 127.0.0.2 "$fixture/wrong.pem" >/dev/null
if openssl verify -CAfile "$fixture/ca.pem" -purpose sslserver -verify_ip 127.0.0.1 "$fixture/wrong.pem" >/dev/null 2>&1; then
  echo 'FAIL: wrong-SAN fixture unexpectedly matches target'
  exit 1
fi
python3 android/tests/transport_fixture.py "$fixture/wrong.pem" "$fixture/wrong.key" wrong-san > "$fixture/wrong.log" 2>&1 &
pid=$!
for attempt in {1..30}; do
  if grep -Fq 'READY: isolated transport fixture' "$fixture/wrong.log"; then break; fi
  kill -0 "$pid"
  sleep 1
done
grep -Fq 'READY: isolated transport fixture' "$fixture/wrong.log"
adb -s "$serial" shell am instrument -w -r -e isolated true -e fixtureCa "$ca" -e transportPhase wrong-san com.veypanel.client.test/com.veypanel.client.StoreInstrumentation | tee runtime-wrong-san.log
grep -Fq 'PASS: trusted wrong-SAN rejected by HTTPS, WSS and bounded WSS' runtime-wrong-san.log
grep -Eq '^INSTRUMENTATION_CODE: -1[[:space:]]*$' runtime-wrong-san.log
if grep -Fq 'FAIL:' runtime-wrong-san.log; then exit 1; fi
kill -0 "$pid"
if grep -Fq 'FAIL:' "$fixture/wrong.log"; then
  echo 'FAIL: application request reached wrong-SAN fixture'
  exit 1
fi
echo 'PASS: no application request reached wrong-SAN fixture'
echo 'PASS: runtime result gate'
