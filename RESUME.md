# Resume checkpoint

2026-11-23 — Android 0.1.0-alpha.11; Windows 0.1.0-alpha.10.

## Verified evidence
- Previous Windows and Android CI 45067632917 / 45067632914 PASS. History/CSV, DPAPI and Host invitation remain verified in CI.
- Android opt-in Keystore implementation 5e1dc264cdb163a7b70f1b2ae16682dbe8e3049d, CI 45078027152 PASS. SavedReader origin and age/expiry fixtures passed; APK and lint successful. AES-256-GCM per-save key, random IV, app-private no-backup encrypted record; local forget and explicit reconnect. Default memory-only.
- Ordered storage operations and instrumentation APK 58e96b379b60b1fc74f34d3576cd8ce67b02b6a7, CI 45078101699 PASS. Both APKs and lint built. Actual storage execution not implied by build. Static serialized worker and revision guards prevent stale callbacks from undoing newer explicit actions; accepted save can complete after pause.
- QR scanner increment 0ff86151e652aaed88a0802e0f20d2cb6eb91e84, run 45078196387: CI PASS. Pinned ZXing Android Embedded 4.3.0 and Core 3.5.3; license/NOTICE assets, internal secure scanner Activity, QR-only, no image output, strict InvitationLink validation, explicit Connect before claim. No physical permission/camera test; transitive dependency/license and security review pending.
- Emulator CI and synthetic decoder 095d0f57eef0ded80b1edd26ab95950c6a0f305f, Android build 45078273565 in progress; actual runtime run 45078273557 in progress at checkpoint. API33 isolated emulator only; KVM required; no physical device cleanup.
- Verified Android debug APK https://github.com/iSentinel/VeyPanel/actions/runs/45078196387/artifacts/14776016903; test APK https://github.com/iSentinel/VeyPanel/actions/runs/45078196387/artifacts/14776310972. Scanner source included.
- Windows CI 45078101692 PASS (unchanged alpha.10); Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45078101692/artifacts/14775624354; Host https://github.com/iSentinel/VeyPanel/actions/runs/45078101692/artifacts/14775579528.

## Next
1. Verify remaining QR build and runtime CI, inspect logs, fix any real instrumentation/runner failures. Add Activity lifecycle, forget and actual HTTPS transport tests; physical camera/permissions on Lenovo. No claim of hardware-backed Keystore or physical security acceptance.
2. Native WSS client with same HTTPS trust and origin policy, bounded sessions, revocation/reconnect and REST fallback. Expand native resource metrics and responsive landscape Monitor layout for Lenovo TB-J607Z 2000x1200.
3. Native video and Display/Hybrid, Apollo/Quick Sync hardware acceptance, signed driver and independent rollback watchdog before actual topology mutation. No display mutation, drivers, physical pairing or streaming performed.
4. Debug APK only; original source license remains owner decision. Full dependency redistribution audit, signing and physical power-loss/storage/thermal acceptance pending.

2026-11-23: runtime run 45078273557 booted and installed both APKs, reached instrumentation PASS after runStore and runQr. Shell gate failed because adb am instrument lacked -r and did not emit INSTRUMENTATION_CODE. Added raw mode and separate explicit QR success marker, retained status/FAIL checks. Corrected CI pending.

Alpha.12 Android WSS source: pinned OkHttp 4.12.1 with license asset, fixed WSS origin/path from validated reader URI, platform TLS trust/hostname verification, no proxy or redirect, first text frame token only, one latest-sample slot, 5.5s sample deadline, 15s fallback before WSS retry. TLS errors stop; other closure checks HTTPS REST and only REST 401/403 invalidates credentials. Pause closes socket and generation guard discards callbacks. Message length checked after library materialization; hostile-message memory limit not established. CI and live Android transport pending; Windows unchanged.

Alpha.12 MonitorPanel adaptive 1/2/3-column layout uses available dp width, compact collapsible connection controls, preserves Activity session on listed orientation/screen changes. Adds memory capacity, IOPS, network interfaces, volumes and freshness-gated provider thermal/storage health details with capped rows. N/A for absent/invalid data. Added instrumentation data fixture; actual UI/rotation/physical display acceptance pending.
