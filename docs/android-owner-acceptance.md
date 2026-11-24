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

## Alpha.16 decoder self-test (candidate)

Once alpha.16 CI produces an approved debug APK, open VeyPanel on Lenovo and
press **Run local AVC decode test**. Record the full codec name, whether Android
reports hardware acceleration, actual decoded buffer count and elapsed time.
This test uses only the bundled original two-frame clip; it does not establish
60 FPS performance or Windows streaming. The UI is protected by FLAG_SECURE;
transcribe displayed results rather than disabling screen security.

## Verified alpha.16 debug APK and local video self-test

    gh run download 45328031303 -R iSentinel/VeyPanel -n veypanel-android-monitor-debug -D veypanel-alpha16
    adb devices -l
    adb -s DEVICE_SERIAL install -r veypanel-alpha16/app-debug.apk

After installation, open VeyPanel, tap **Run local AVC decode test** and
record the codec name, whether Android reports it as hardware-accelerated,
decoded buffers and elapsed time. The prior alpha.15 instructions remain
historical. The alpha.16 debug APK is not release-signed and has not been
installed or validated on Lenovo TB-J607Z.

## Alpha.17 local picture preview (candidate)

Once the alpha.17 debug artifact passes Build, Lint and Android Runtime,
tap **Preview local AVC frame** on Lenovo and verify a red 64x64 test picture
appears in the embedded preview area. Record the displayed status and any
orientation, clipping or flicker. The original synthetic clip requires no PC
connection. Keep the test separate from real Windows video hardware acceptance.

## Verified alpha.17 local preview installation

Run on a trusted workstation with GitHub CLI and Android platform-tools:

    gh run download 45331269259 -R iSentinel/VeyPanel -n veypanel-android-monitor-debug -D veypanel-alpha17
    adb devices -l
    adb -s DEVICE_SERIAL install -r veypanel-alpha17/app-debug.apk
    adb -s DEVICE_SERIAL shell am start -n com.veypanel.client/.MainActivity

Use a real serial from `adb devices -l`. Tap **Preview local AVC frame**
and observe the embedded red test picture. It reports PASS only after a
TextureView update and decoded frame. Record actual codec status and preview
behavior on Lenovo. Do not interpret an emulator PASS as actual streaming,
hardware acceleration, stable 60 FPS or production signing.

## Alpha.18 local touch probe (candidate)

After loading the verified alpha.18 APK, tap **Preview local AVC frame** and
then tap the center and corners of its test image. The UI should display local
64x64 coordinates without connecting to the PC. Try a multi-finger touch:
it should say **multi-touch rejected**. Confirm the label **not sent to Windows**.
This is purely local motion-event validation; actual remote touchscreen control,
display rotation, accuracy and gesture policy are still unimplemented.
