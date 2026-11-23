# VeyPanel Android alpha.15 owner acceptance

Current verified evidence: Android build 45151764750 and emulator runtime 45151759925 PASS.
The app is **debug-signed**. This is not a release build or a hardware acceptance.

## Inspect on Lenovo TB-J607Z

Commands to review the device and install the verified alpha.15 debug build
from a trusted development workstation with GitHub CLI and Android platform-tools:

    gh run download 45151764750 -R iSentinel/VeyPanel -n veypanel-android-monitor-debug -D veypanel-apk
    adb devices -l
    adb -s DEVICE_SERIAL install -r veypanel-apk/app-debug.apk

Use the actual device serial from `adb devices -l` in place of DEVICE_SERIAL.
No root or bypass of Android security settings is required.

Open VeyPanel, tap **Inspect video decoders** and record the displayed AVC,
HEVC and AV1 codec entries and 720p/1080p/tablet-resolution 60 FPS declarations.
These are API capability reports, **not** video throughput or decode proof.
No hardware PASS should be recorded until actual streaming and rendering are
measured, including frame loss, latency, rotation, battery and thermals.

## Separate gates

- QR scanning: physical camera/permission handling, malformed code, owner approval.
- Real Windows Host telemetry: user-installed owner-verified CA, IP-SAN, WSS/REST
  fallback, grant revocation, sleep/wake and reconnect.
- Video: original test clip decode on the tablet, then actual authenticated
  stream from a verified encoder to the device.
- Display modes: no topology changes without a saved snapshot, owner consent
  and an independently tested rollback path; no unsigned driver bypass.
- Release: signed packages, dependency and redistribution review, upgrade and
  uninstall tests.

The Activity uses Android FLAG_SECURE, so a screenshot may be unavailable;
transcribe the decoder report instead. Do not share pairing tokens or QR links.
