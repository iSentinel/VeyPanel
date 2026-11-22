# VeyPanel native Android monitor (alpha.10)

Early Monitor-only Java Activity, Android 8+ (API 26), compile/target SDK 35, AGP 8.7.3 and Gradle 8.9, JDK 17. Pinned initial toolchain, not a claim of current Play Store compliance. Build with `gradle -p android :app:assembleDebug :app:lintDebug`. Debug-signed APK is for isolated development testing only.

1. Configure standalone Windows Host LAN HTTPS using the specific RFC1918 address and a certificate with that exact IP SAN.
2. Independently verify the intended PC certificate/CA. Android must trust its issuer. The app explicitly accepts Android system and user-installed trust anchors for this app only; ordinary TLS hostname and chain verification remain enabled. Do not install unknown CAs or bypass trust errors.
3. Create a reader link in the local owner dashboard, privately transfer it, paste into the native client and Connect. No HTTP, redirect, public IP, arbitrary path, proxy or token query parameter. No owner API.
4. CPU/RAM/GPU/video codec and disk throughput are polled with HTTPS REST approximately once a second after each completed request. Missing/stale metrics show N/A. Polling is suspended when the Activity pauses. Auth/TLS errors terminate the session. Credentials remain in Activity memory; no backup or saved view state for link. No background service or telemetry upload.

Pasted two-step invitation links are supported: Connect claims once, shows the comparison code, then Check owner approval redeems only after the PC owner approves. The invitation is bound to the original HTTPS origin; no automatic retries of claim/finish. A failed or interrupted exchange requires a new invitation. Camera QR scanning, Android Keystore, persistent reconnect, native WSS, video, touchscreen forwarding and tablet layout acceptance are future milestones. The first app is not a replacement for Apollo/Moonlight yet. No emulator or real tablet results until tests actually run. Android trust model reference: https://developer.android.com/privacy-and-security/security-config ; toolchain: https://developer.android.com/build/releases/agp-8-7-0-release-notes .

## Build evidence

Initial Android CI 45067435606 passed JVM fixtures but failed SDK setup (sdkmanager missing). Corrected run 45067558759 successfully compiled the native Monitor APK and passed lint. Native invitation increment 45067632914: CI PASS. Latest verified debug artifact: https://github.com/iSentinel/VeyPanel/actions/runs/45067632914/artifacts/14772126862. No emulator/physical execution verified. See ../docs/android-credential-design.md for future persistence requirements.

## Android alpha.11 saved access

Select Remember access before connecting; after the first fresh authorized sample the app saves an encrypted reader record using AndroidKeyStore AES-GCM. Connect saved access is explicit. Disconnect leaves a previously saved grant intact; Forget deletes the local key and record, not the server grant. Revoke on the PC to invalidate that grant. Local saved access expires at most 24 hours after saving; Host expiry remains authoritative. No backup or owner/invitation persistence. If forget fails, clear app data before reuse. Real Keystore and lifecycle testing is pending.

The instrumentation APK is built by `gradle -p android :app:assembleDebugAndroidTest`. Run only on an isolated test installation (refuses existing credentials): `adb shell am instrument -w -e isolated true com.veypanel.client.test/com.veypanel.client.StoreInstrumentation`. Require explicit PASS and successful instrumentation result. No emulator/device execution yet.

## Local QR camera preview

Press Scan invitation QR and grant camera access if desired. Only a syntactically valid private HTTPS VeyPanel invitation is inserted into the password-style input; press Connect explicitly to claim it. No general URL opening, automatic redemption, frame upload or image capture result. Uses pinned ZXing Android Embedded 4.3.0 and ZXing Core 3.5.3 (Apache-2.0, embedded license/NOTICE assets). Camera and permission handling need actual Lenovo acceptance; transitive dependency/license/security review remains open. Pasting a link is an alternative.

Separate Android runtime smoke CI boots an isolated API 33 emulator and executes actual Keystore checks and a synthetic QR encoder/decoder test. The test script refuses non-emulator devices. Camera scanning itself is not covered. Build CI and runtime CI are distinct.

Verified alpha.11 builds: Keystore 45078027152 and ordered storage operations/instrumentation APK 45078101699, both PASS. QR 45078196387: CI PASS. Latest complete Android package https://github.com/iSentinel/VeyPanel/actions/runs/45078196387/artifacts/14776016903; isolated instrumentation APK https://github.com/iSentinel/VeyPanel/actions/runs/45078196387/artifacts/14776310972. Actual Android runtime run 45078273557: in progress. No real camera or Lenovo acceptance.
