# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.9.

## Verified
- Alpha.8 QR / enrollment full Windows CI 45064630788 PASS; grant codec 45064798561 PASS. Camera/browser acceptance on Lenovo still pending.
- ProtectedGrantStore 8663d6b3485af0a8c2c1c5d7b0ba75ba3d392227 and live registry a1f457f9448f7e457710f3d0a4aaf81e34eea354: initial runs 45065935377 / 45066022926 failed because fixture did not catch expected InvalidDataException for pending marker. DPAPI, lock, reopen/corruption and registry failure tests had passed preceding that assertion.
- Fix/process smoke 32c5bf6904da72cd5d21e9e8a824f643e3f83515: full Windows CI 45066141473 PASS, 0 Host build warnings/errors. Verified DPAPI ciphertext, exclusive lock, corruption refusal, registry reload, revoke-all, failed write disables live readers, actual published Host kill/restart after acknowledged issuance and revocation, old owner rejected, dirty-marker startup exits 1. Standalone opt-in VEYPANEL_PERSIST_GRANTS=1, default and managed Host RAM-only; no initial LAN grant in persistent mode.
- History commit 94f71a636aa137a90c9e562457e35187c17487f5: CI PASS in run 45066230888. Compact authorized RAM-only 900-second / 900-point history with CPU/RAM/GPU/codec and disk metrics; chart manual refresh; no external storage or export. Real UI unverified.
- ACL/reparse hardening ad873fa613b29cf41a24d6cda9c4b4dd0f1b9980: fixtures PASS; remaining CI in progress in run 45066313328. Explicit file ACL verification and isolated negative fixtures. Inspect logs for actual symlink fixture status.
- Latest verified package run 45066230888: Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45066230888/artifacts/14771392646; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45066230888/artifacts/14771123290. Unsigned alpha.

## Next
1. Confirm history/ACL CI results and actual fixture labels. Fix any failures. Review store recovery/reset UX; test abrupt crash during write and real power loss separately. Failed writes reject mutations and disable readers, but a failure before writing the pending marker may leave old on-disk state; do not automatically restart or restore backups. DPAPI is not rollback protection against same-user/admin or restoration of old valid ciphertext.
2. Continue history graphs/export and Android telemetry receiver with HTTPS trust, secure token storage and QR pairing. Real tablet browser and camera behavior unverified.
3. Physical acceptance: Lenovo TB-J607Z, Intel Arc, CPU/GPU thermal sensors, actual SSD reliability metrics, Apollo v0.4.6 Quick Sync, Mirror/Extend 2000x1200 @60 Hz. Keep topology mutation disabled until rollback watchdog and hardware acceptance. No driver installation, display mutation, actual pairing or streaming performed. Original project license decision remains open.

Alpha.10: full ACL CI 45066313328 PASS including actual reparse path rejection. Added bounded numeric-only CSV export, reader revocation checks, codec/disk history charts and 1/5/15-minute visual window. Full CSV remains 15 minutes max. CI pending. Next: native Android read-only monitor.

Alpha.10 Android increment: initial native Java Monitor Activity and strict private HTTPS reader link parser, Android system/user CA trust with hostname verification, no redirects/proxy or cleartext, bounded REST polling and null/freshness rules. Session memory only; no native QR or Keystore yet. JVM fixtures and separate debug APK/lint CI added, pending execution. No physical Lenovo test.

Alpha.10 Windows history/CSV full CI 45067318280 passed. Native Android policy fixtures passed in run 45067435606, but APK build was skipped because sdkmanager was not on runner PATH. Added pinned android-actions/setup-android v4.0.2 and explicit API 35/build-tools checks. Corrected APK CI pending. No APK produced by initial run.

Alpha.10 native enrollment: strict pasted one-time invitation link parser with fixed original HTTPS origin, bounded claim/finish POST, comparison code, explicit owner approval and memory-only reader handoff. No automatic exchange replay; interrupted or failed claim/finish needs a new link. JVM URL fixtures added, real client transport and APK CI pending. No camera or keystore yet.
