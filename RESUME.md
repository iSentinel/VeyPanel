# Resume checkpoint

2026-11-23 — Android 0.1.0-alpha.12; Windows 0.1.0-alpha.10.

## Verified and pending evidence
- Alpha.11 full Windows / Android build runs 45078273590 / 45078273565 PASS. Runtime 45078273557 booted API33 emulator, installed APKs and reached instrumentation PASS after actual AndroidKeyStore encrypt/decrypt/reopen/IV/tamper/missing key/forget and synthetic offline QR decode. Overall runtime FAIL: non-raw adb output omitted INSTRUMENTATION_CODE needed by shell gate. Do not report complete runtime CI PASS.
- Raw instrumentation fix b4c3fe52e4e5d6af6bc06f41caf989f8f3c29b1f: explicit -r, separate QR marker, result code and FAIL check. Android build 45081841167 PASS. Runtime reruns 45081841189 / 45081890597 failed at KVM preflight, never executed instrumentation.
- Android WSS commit 1f888da173b326569c83518da5c81bb6406eed65: Android CI 45081890582 PASS, including same-origin WSS URI fixture, APK and lint. Pinned OkHttp 4.12.1, Apache license asset, default platform TLS trust, no proxy/redirect, first token text frame, one sample slot, receive deadline 5.5s, REST retry window 15s, TLS errors stop, REST authorization denial forgets saved access. WSS closure triggers REST verification; native real HTTPS/WSS, fallback and revocation remain untested. Message limit after library materialization only, not a hard pre-allocation memory bound.
- Adaptive MonitorPanel and resource detail commit 51f56e51e6ae083a835f395015402d8ab8fd4b07: run 45081976468 APK/lint PASS; full CI pending. Responsive dp width, 1/2/3 columns, collapsible controls, RAM/IOPS/network/volumes and age-gated thermal/health; instrumented data fixture, visual/rotation acceptance pending.
- Runtime software fallback commit 7d4dc0f7257f682673ca62a255e4c67903ffc8e7: run 45082028995 in progress. Selects KVM where present, software emulation otherwise with 1200s boot limit. Mandatory raw result checks and resource fixture. No skipped tests counted PASS. Inspect actual result and failure logs on next turn.
- Verified Android package run 45081890582: https://github.com/iSentinel/VeyPanel/actions/runs/45081890582/artifacts/14777916143; test APK https://github.com/iSentinel/VeyPanel/actions/runs/45081890582/artifacts/14778130678. WSS source included; responsive layout not yet in this artifact. Debug signing only.
- Verified Windows package run 45081890586: Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45081890586/artifacts/14777159422; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45081890586/artifacts/14778190509. Unsigned alpha.10.

## Next
1. Confirm final adaptive build and emulator runtime result. Fix real failures with log evidence. Add actual Android trusted HTTPS/WSS test including revoked token, fallback, TLS denial and lifecycle, not simply schema fixtures. Review library receive allocation bounds and dependency audit. Review credential switch ordering: invalid pasted link currently clears previous saved record before validation; fix before declaring UI acceptance.
2. Add native monitor history/graphs and validate 2000x1200 landscape appearance, orientation and controls on Lenovo. Verify Keystore, camera scanning and certificate trust on target.
3. Native video / Display / Monitor / Hybrid; Apollo v0.4.6 and Intel Quick Sync physical PoC, signed driver and rollback watchdog before topology changes. No actual video stream or monitor mutation yet.
4. Full dependency license/security and original project license decisions, release signing, real storage power loss/thermal acceptance pending.
