# Android protected credentials / QR design

Status: alpha.11 credential store and explicit reconnect/forget implemented, CI and instrumentation pending; local QR scanner source implemented, CI and physical camera acceptance pending.

The default client holds a reader token in Activity memory, uses fixed private IPv4 HTTPS endpoints, verifies Android system/user CA trust and hostname, and only persists an encrypted reader record after opt-in. A user-added CA is an explicit trust choice, not certificate pinning. The owner must independently verify the intended CA and IP SAN. Debug APK is not production-signed.

## Remember access (next)
- User opt-in only. Store one reader session bound to its original origin under app-private storage, encrypted with a per-install AndroidKeyStore AES-GCM key. Use a fresh random IV, versioned envelope, fixed AAD and bounded fields. Never store raw token, owner token or invitation secret; no backups, export, logs or autofill.
- Use only the validated ReaderSession parser when loading; bound local saved age to at most 24 hours after save without extending server expiry. On auth denial, corruption, decryption failure or invalid clock, forget local session. TLS errors stop connection and require user verification, not insecure retry.
- Implement explicit Forget and Disconnect as distinct actions. Clear saved session when changing the PC or when user disables remembering. Serialize storage operations with lifecycle generation guard; do not persist abandoned enrollment results.
- Test AndroidKeyStore real encrypt/decrypt, fresh IV, corrupted ciphertext, wrong origin, key invalidation, expired/clock reset and explicit deletion using Android instrumentation; JVM policy fixtures alone cannot establish actual key storage behavior. Require device acceptance before calling it secure production storage.

## Camera QR
Review and pin scanner dependency/license first, prefer offline scanning and camera permission only when requested. Strictly parse the same invitation URL grammar as pasted links; never open arbitrary URLs. Require explicit claim action, display comparison code, and require PC owner approval. No camera frames or secrets exported. Verify deny permission, malformed/foreign QR, expiration, replay and trusted TLS on Lenovo. Do not bypass certificate validation.

## Gates
Actual tablet API level, Android Network Security Config behavior with intended CA, lifecycle/rotation, expiration and reconnect need emulator/physical acceptance. No video decoder or touchscreen forwarding yet. Native WSS should use this same validated private origin and revocable reader model. 

Implemented experimental camera integration using pinned ZXing Android Embedded 4.3.0 and Core 3.5.3. Explicit private scanner Activity, QR-only, no barcode image output, strict InvitationLink parsing, separate Connect action. License and notice bundled. Neither actual sensor permissions nor camera decoding are verified; review transitive dependencies before production redistribution.
