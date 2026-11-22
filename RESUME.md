# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.10.

## Verified evidence
- Alpha.9 ACL/reparse full CI 45066313328 PASS: unexpected file and directory ACL rejected, actual symlink/reparse store directory rejected, zero Host build warnings/errors. DPAPI restart/revocation and history tests passed. Physical power loss/rollback not established.
- Alpha.10 history/CSV commit 01161a96aa9cffd38b30eddf798f54b0e116c0b9, Windows run 45067318280 completed successfully, zero Host build warnings/errors. Numeric-only CSV, UTC/invariant culture/null fixtures, authorized CSV and revoked CSV denied. Browser range selection and codec/disk graphs implemented; interactive acceptance pending. Full CSV up to 900 points, selection affects chart only. Verified Windows Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45067318280/artifacts/14772037040 ; Host https://github.com/iSentinel/VeyPanel/actions/runs/45067318280/artifacts/14771364607 (unsigned alpha).
- Initial native Android Java Monitor commit 98ec01a0882978cd28b44b4f058ef3a99c5b3aec: run 45067435606 JVM fixtures PASS, SDK setup FAIL because sdkmanager absent from PATH, APK not built. Fixed e9fc02f58c6abfd1d7448c738bd253bdbc3b98ca with pinned android-actions/setup-android v4.0.2 and explicit SDK checks. Corrected Android run 45067558759 completed successfully (assembleDebug and lintDebug, debug APK artifact). Java17, min API26, target/compile35, AGP8.7.3/Gradle8.9. Private HTTPS reader links only, default hostname verification, system/user CA trust, no HTTP/proxy/redirect, memory-only session. REST monitoring pauses in background; no physical/emulator acceptance.
- Native pasted invitation increment 16cebf1ad6bd2ce0305d74b6cd8fb586a12eac0f: Android run 45067632914 CI PASS. Same-origin claim/finish, owner comparison code, no automatic replay. Camera scanning and AndroidKeyStore not implemented. Latest verified APK https://github.com/iSentinel/VeyPanel/actions/runs/45067632914/artifacts/14772126862 (debug-signed; pasted invitation source included).
- Android credential / QR design: docs/android-credential-design.md. No persistence implementation yet.

## Next
1. Confirm latest Android invitation CI, verify actual APK, add Android instrumentation acceptance of link parser/transport and lifecycle. On Lenovo test trusted IP SAN certificate, actual HTTPS telemetry and pasted enrollment. Debug signing only; no production or Play compliance claim.
2. Implement optional AndroidKeyStore-protected reader credentials and offline QR camera scanning with dependency review, then native WSS. See credential design.
3. Continue native video / Display / Monitor / Hybrid. Real Apollo v0.4.6, signed driver, Intel Quick Sync, Mirror/Extend 2000x1200 @60 Hz and recovery watchdog remain physical acceptance gates. No video or monitor mutation yet.
4. Physical storage power-loss/rollback, GPU/CPU temperatures and actual SSD reliability remain unverified. No automatic trust bypass, firewall changes, driver installation or real pairing performed. Original source license undecided.

Final Windows run 45067632917 completed successfully on the same source as native Android invitation. Verified Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45067632917/artifacts/14771433377; Host https://github.com/iSentinel/VeyPanel/actions/runs/45067632917/artifacts/14771951910.

Alpha.11 Android: optional app-private no-backup encrypted reader record (AndroidKeyStore AES-256-GCM, per-save key, random IV, fixed AAD, validated origin and local max 24h age). Save after first successful authorized telemetry, explicit reconnect/forget, auth denial deletes saved access, no owner/invitation storage. JVM record policy fixtures. Actual Keystore and lifecycle instrumentation pending. CI pending. Windows remains alpha.10.
