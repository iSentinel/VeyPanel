# Resume checkpoint

2026-11-23 — Android 0.1.0-alpha.14; Windows 0.1.0-alpha.10.

## Verified and pending
- Alpha.12 final adaptive Android/Windows CI 45082029020 / 45082029025 PASS. Software-emulator run 45082028995 had actual Keystore, QR and extended schema PASS and INSTRUMENTATION_CODE -1, but final shell failed unmatched quote.
- Commit 483fa90b51f081420548174f4a7f82e1a8680717 rewrote shell gate and added bash -n, generated explicit emulator serial commands, validated reader/invitation before switching and preserves saved grant on invalid input or unrelated 401/403. Matching origin+token fixture. Android CI 45083538812 PASS, Windows 45083538920 PASS. Full emulator runtime 45083538875 PASS; actual Keystore, synthetic QR and extended telemetry with raw result gate verified. Activity interaction not exercised.
- History commit e1801115e6f155598dfb817133b0b195056ee1b2: RAM-only observed foreground samples, 900 points/900 seconds, CPU/RAM/GPU, codec/disk charts, 1/5/15 minutes, gap and reset semantics, clears on pause/switch/terminal denial. Build 45083699279 compiled but lint FAIL invalid literal view ID. Runtime history 45083699289 PASS.
- Transport commit 643e1da8d595324c29b98b3fbda2f2abd502e037: isolated CI loopback fixture with ephemeral generated CA/server certificate, IP SAN 10.0.2.2, test-only trust factory arguments, synthetic tokens, default unknown CA denial, actual REST/WSS trusted sample, invalid reader, stream closure then REST and simulated revocation. Not actual Windows Host or automated Activity fallback integration. Runtime 45083842554 in progress. Build 45083842492 FAIL (inspect log if needed). No default trust changes, no production secrets.
- Lint fix d40b5ef9fad4773368d0ab6e9a61b5704e5621d2 uses generated Android view IDs and separate range tags. Android 45083916217 in progress, runtime 45083916229 in progress, Windows 45083916312 in progress.
- Latest verified Android APK https://github.com/iSentinel/VeyPanel/actions/runs/45083538812/artifacts/14777663302; instrumentation https://github.com/iSentinel/VeyPanel/actions/runs/45083538812/artifacts/14777902825. Credential switching fix included; history and transport updates not in verified artifact. Debug signing.
- Windows Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45083699332/artifacts/14777903093; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45083699332/artifacts/14777913086. Unsigned.

## 2026-11-23 follow-up
- Confirmed Android build/lint 45083916217 PASS (debug APK artifact 14778382774) and Windows 45083916312 PASS.
- Android runtime 45083916229 FAIL: emulator booted and both apps installed; instrumentation returned ConnectException. The failing transport connection was previously reported under a generic Keystore label.
- Route correction: use explicit emulator-only adb reverse to the runner loopback fixture, an IP-SAN 127.0.0.1 certificate, host TLS/401 readiness probe, fixed artificial fixture sessions and phase-specific instrumentation results. Production link parser still rejects loopback; trust and hostname checks unchanged. Host shell syntax and fixture readiness locally checked; emulator retry not yet verified.
- Latest built APK: https://github.com/iSentinel/VeyPanel/actions/runs/45083916217/artifacts/14778382774 (history included; network runtime not accepted).

## Runtime offset correction
- Main build 45089770919 / Windows 45089771009 PASS. Runtime 45089770854 reached HTTPS but failed DateTimeParseException; Keystore, QR, telemetry and local history explicitly PASS.
- PR #1 branch build 45089886016 and Windows 45089886141 PASS. Runtime 45089879889 independently confirms Host history codec PASS, then fails the same transport timestamp parsing.
- Normalize wire timestamps using ISO_OFFSET_DATE_TIME to Instant for telemetry, enrollment expiry and resource ages. Keep explicit offsets mandatory and freshness checks unchanged. Retry runtime before accepting transport.

## Host History PR #1
- Android and Windows builds PASS; isolated codec assertions PASS before the transport offset failure. Main offset correction merged into development branch.
- Native explicit Host history refresh, same-origin bounded HTTPS, separate worker, generation/session guards, cancellation on pause/switch/Forget/terminal denial, numeric merge preferring local samples, and fixture history authorization/revocation assertions implemented; verification pending. Do not merge until build and runtime gates pass. Real Activity and Windows Host integration remains open.

## Verified merged history baseline
- Offset correction main 060afe9: Android build 45090572022, Windows 45090572076 and Android runtime 45090572041 PASS.
- History PR head 2cfcbeb: Android build/lint 45090687195, Windows 45090687370 and isolated runtime 45090682478 PASS. Raw instrumentation result -1 and final gate PASS including codec/merge, HTTPS/WSS, TLS rejection, fallback and revocation. PR #1 merged as f5632a8.
- Android alpha.13 debug APK: https://github.com/iSentinel/VeyPanel/actions/runs/45090687195/artifacts/14780468583 . No physical tablet, Activity interaction or live Windows Host transport acceptance claimed.

## Android alpha.14 diagnostics PR #2
- PR branch adds foreground connection counters and fixed event categories, collapsed diagnostics UI, JVM fixtures, and isolated Activity startup/toggle/disconnected-history test. Terminal denial retains counters for troubleshooting; new session, pause and disconnect reset them. No logging of host or token.
- First alpha.14 Android build 45091118899 PASS; extended Activity runtime retry pending. Do not merge until updated build and runtime pass. Real session switch/reconnect and production CA/Host acceptance still pending.
- WSS callback size checks remain post-allocation in OkHttp. Do not claim a strict pre-allocation bound until the transport can enforce frame and fragmented-message budgets prior to buffering.

## Verified alpha.14 diagnostics baseline
- PR #2 head 36fd2e1: Android build 45091283003, Windows 45091282989 and runtime 45091277957 PASS. Raw result -1, actual Activity launch/toggle/disconnected history gate and prior transport fixtures PASS. Merged as 0e46e9d.
- Debug APK: https://github.com/iSentinel/VeyPanel/actions/runs/45091283003/artifacts/14781567158 . Physical UI, live reconnect, camera, actual Windows Host TLS/WSS still pending.
- Next: Host outbound frame limit and Android pre-buffer frame parser design/tests, then bounded transport integration; no claim that OkHttp currently enforces a pre-allocation limit.

## WSS bounds PR #3
- Host serialized outbound message byte gate (1 MiB), isolated Android uncompressed frame-header and message assembly prototype, strict UTF-8, continuation/control and frame count tests. PR #3 pending CI; current OkHttp path unchanged, no production inbound allocation limit claimed.
- Next transport gate: security review of bounded handshake/TLS, close validation and absolute read deadlines before integration; add actual adversarial TLS fixture. No hardware or native video changes.

## Verified WSS bounds baseline
- PR #3 head c126db7: Windows 45092513666 PASS including outbound byte cap, Android 45092513667 PASS including header/aggregate/UTF-8 JVM fixtures, runtime 45092508834 PASS including previous Activity/transport gates. Merged as bb40f3f.
- Production Android WSS pre-allocation protection still pending; do not equate prototype tests with live transport acceptance.

## Bounded upgrade PR #4
- Bounded upgrade headers (8 KiB), RFC accept-key and masked auth/control encoder, JVM positive and negative fixtures; isolated actual TLS prototype with endpoint identification and absolute close watchdog, valid sample, unknown CA and oversized header. CI awaiting verification. Production client unchanged; do not merge as production transport.
- Remaining: close validation, ping/pong, continuous stream deadlines and cancellation, actual user CA integration, security review, then production integration.

## Verified bounded upgrade baseline
- PR #4 head fdb9949: Windows 45093130787 PASS, Android 45093130783 PASS, runtime 45093126068 PASS including bounded TLS unknown-CA and oversized-header rejection. Merged as experimental transport only.
- Current production Android client still uses OkHttp; full streaming integration pending.

## Bounded WSS controls PR #5
- Close status/UTF-8 validation, masked pong and close reply, two consecutive samples over isolated TLS, and cancellation of a blocked read by closing the underlying socket. New fixtures and CI gates added; runtime not yet verified.
- Production integration requires continuous operation deadlines, stale/revoked handling, correct default/user CA acceptance and review. Keep current OkHttp path unchanged until verified.

## Verified bounded controls baseline
- PR #5 head 891ff0d: Android CI 45096636484 PASS, Windows CI 45096636517 PASS and Android runtime smoke 45096631311 PASS. PR merged as f2b6e7e.
- Isolated bounded TLS prototype covers ping/pong, two consecutive messages, close validation and blocked read cancellation. MainActivity still uses OkHttp and production inbound allocation bounds are not yet enforced.
- Next: persistent bounded stream using platform SSL, absolute read watchdog and generation-safe cancellation; verify with fixture before considering MainActivity switch.

## Android alpha.15 read-only video codec survey candidate
- Enumerate regular AVC/HEVC/AV1 decoders via MediaCodecList, API29+ hardware classification, declared 720p/1080p/2560x1600 at 60 FPS capabilities, and explicit N/A on absent API data. No codec instances, streaming or driver changes.
- On-demand UI inventory and emulator instrumentation report only declared capabilities; physical Lenovo/video decode acceptance remains pending.

## Bounded WSS candidate status
- PR #6 has merged into main after runtime PASS. BoundedTelemetryStream is available but MainActivity still uses OkHttp pending separate production transport acceptance.


## Synthetic AVC MediaCodec smoke
- PR #8 head ade33df: Android build 45153234091 PASS and exact-head runtime 45153552741 PASS. Original 64x64 two-frame AVC MP4 is decoded with MediaExtractor and MediaCodec on the emulator; physical hardware and streaming remain untested. Combined mainline CI after merging PR #9 pending.

## WSS feed abstraction
- PR #9 head b1611f3: Android build 45153409806, Windows CI 45153409950 and runtime 45153400342 PASS; merged as 64647b3.
- MainActivity stores TelemetryFeed but still constructs the reviewed OkHttp client. No default transport switch, trust weakening or display mutation.


## Next
1. Verify history and transport raw CI and latest build. Fix any failures with logs. Test actual Activity switching, pause/reconnect, forget and live Windows Host TLS/WSS, including revocation and fallback. Fixture trust injection is not production system/user CA integration. Review WSS message pre-allocation bounds and dependency audit.
2. Verify Android UI and camera on Lenovo TB-J607Z; add Host history synchronization and diagnostics. Continue native video / Display/Monitor/Hybrid and touch. Real Apollo/Intel Quick Sync PoC, signed driver and independent rollback watchdog before display mutation.
3. No physical streaming or display changes performed. Real storage power loss, sensors, dependency audit, licenses and release signing remain open.

## Verified bounded-stream candidate (2026-11-23)
- PR #6 head f7121ee: Android CI 45150815811 PASS, Windows CI 45150815933 PASS, Android runtime 45150808675 PASS. Merged as deb7982; read-only candidate does not change production OkHttp.
- The fixture checks two messages, ping/pong, invalid frame, unknown CA, socket cancellation and absolute timeout under drip-feed. Actual Windows Host/Lenovo integration and security review remain required before the production switch.
- Android 0.1.0-alpha.14 continues as the mainline version; separate video codec survey alpha.15 is under PR #7.

## Verified Android alpha.15 video decoder survey (2026-11-23)
- PR #7 head d05f127, merge 65338d8. Android CI 45151764750 PASS, Windows CI 45151764974 PASS, emulator runtime 45151759925 PASS. Version 0.1.0-alpha.15.
- Debug APK artifact 14806213555 from Android CI 45151764750 (app-debug.apk). Local codec report checks declared AVC/HEVC/AV1 and 720p/1080p/2560x1600 at 60 FPS; does not start a decoder and does not establish real hardware performance.
- Actual 64x64 AVC decode instrumentation under PR #8 remains pending. Lenovo tablet, Windows Quick Sync, Apollo and display acceptance unverified.

- Alpha.16 initial Android CI 45327692507 failed at javac: invalid `VideoCapabilities.areSizeSupported`; corrected to public `areSizeAndRateSupported(64,64,30)`; later full CI PASS.
- Alpha.16 Activity instrumentation clicks the local AVC self-test button and waits for an on-screen PASS and re-enabled button, in addition to direct repeated decode.

## Verified alpha.16 local video self-test (2026-11-24)
- PR #10 head c7f44d2: Android build/lint 45328031303 PASS, Windows 45328031480 PASS, Android runtime 45328022894 PASS. Merged as f7a9af8.
- Debug APK 45328031303 artifact 14890334063. No 60 FPS, Surface rendering, Apollo/Quick Sync or physical tablet acceptance.

## Touch geometry preparation
- Added pure TouchMapping for stage 0.6: contain-fit letterbox checks, 0/90/180/270 inverse transforms, negative-origin Windows desktop and fail-closed invalid dimensions. Initial Windows CI 45328378092 PASS; combined CI after main sync pending.
- No native pointer injection, network control, paired input authorization, display mutation or physical tablet acceptance. A fresh target identity and owner-confirmed input channel are prerequisites.

- Added matching Android TouchMath and JVM fixture suite for the same 17 Windows synthetic vectors; CI pending. No touch listeners or input forwarding.

## Verified touch geometry checkpoint (2026-11-24)
- PR #11 head b171a02: Windows 45328777756 and 45328771499 PASS, Android 45328777846 and 45328771419 PASS, Android runtime 45328771479 PASS. Merged as dbde6d4.
- 17 matching synthetic cases in C# TouchMapping and pure Java TouchMath; no actual input listeners/network, target revalidation or Lenovo acceptance. Next safe stage: session-bound identity/freshness gate before any prospective control channel.

## Touch target binding gate (CI pending)
- Separate pure TouchBindingGuard rejects absent/expired or changed topologies, changed session generation, monitor identity mismatch, black-bar hits, duplicate targets and coordinate overflow; derives desktop rect from active CCD source mode. Synthetic Windows CI pending.
- No touch injection, input network endpoint, remote authorization or display topology change. Target PC/tablet hardware acceptance pending.

## Verified touch target binding checkpoint (2026-11-24)
- PR #12 head bb4e9bb: Windows CI 45329353667 and 45329347615 PASS, merged as 0b0ca24. TouchBindingGuard validates fresh and equivalent complete CCD snapshots, exact LUID/target identity, source geometry, session generation and letterboxing; still no input injection.
- Hardware streaming, touch control, virtual display and driver rollback remain untested and disabled.

## Android AVC Surface-output stage (CI pending)
- Isolated Android instrumentation creates a local SurfaceTexture/Surface, configures a MediaCodec AVC decoder against the original bundled two-frame clip, waits for at least one Surface frame-available callback and verifies clean EOS/resource disposal. CI/runtime pending. No main app video renderer or Windows streaming enabled.
- Surface smoke uses API26 detached SurfaceTexture(false) rather than texture name 0; Android SDK API reference confirms no initial GL attachment is required. CI pending.

## Verified Android Surface-output smoke (2026-11-24)
- PR #13 head 8206814: Windows CI 45329953682/45329948364, Android build 45329953560/45329948294, Android runtime 45329948361 PASS. Merged as 6034990.
- Test-only MediaCodec decodes local AVC clip into detached SurfaceTexture and verifies frame-available callback and EOS. No production SurfaceView, Windows desktop stream or physical Lenovo hardware test yet.
- Next: owner-visible local preview with lifecycle cancellation, then physical tablet/Intel Quick Sync and Apollo pairing acceptance.

## Android alpha.17 local Surface preview (PR candidate)
- On-demand TextureView in the native Activity, original bundled red 64x64 two-frame AVC. LocalAvcSurfacePreview shares the implementation with isolated SurfaceDecodeSmoke; Activity instrumentation clicks preview and checks the visible in-app result.
- Worker is cancelled on pause or Surface loss; generation/revision guards drop stale completions. MainActivity still uses OkHttp WSS; no Windows capture, Apollo pairing, display mutation or touch input. CI and actual Lenovo preview acceptance pending.
- Preview completion is now gated on both decoded Surface output and an actual TextureView update callback (2 s bounded post-decode wait), while Android UI smoke scrolls it into view. CI required.

## Verified Android alpha.17 local Surface preview (2026-11-24)
- PR #14 head f5c0802: Android CI 45331269259/45331261006 PASS, Windows CI 45331269544/45331261072 PASS and runtime 45331261314 PASS. Raw instrumentation includes visible Surface preview gate and final INSTRUMENTATION_CODE:-1. Merged as 9b8ba93.
- Debug APK artifact 14892161712 from run 45331269259. Android version 0.1.0-alpha.17. Local preview requires both AVC Surface output and an actual TextureView update; cancels on foreground pause or Surface loss.
- The original local red clip is not a Windows stream. Lenovo visual, camera, Apollo/Quick Sync, display mode and hardware latency acceptance remain pending.

## Android alpha.18 local preview touch diagnostics (CI pending)
- LocalTouchProbe projects touch-up coordinates on synthetic 64x64 preview via existing TouchMath; multi-pointer, letterbox/outside and invalid inputs rejected. Text stays on-device in RAM and explicitly states not sent to Windows.
- MainActivity attaches a listener only to the local TextureView. JVM and Activity tests cover center touch, bounds and nonforwarding. No input network protocol, Windows injection, privileges or display mutations. Physical Lenovo acceptance remains open.

## Verified Android alpha.18 local touch probe (2026-11-24)
- PR #15 head 11f6eda: Android CI 45331898798/45331893717 PASS, Windows CI 45331898833/45331893745 PASS, Android runtime 45331893810 PASS with Activity local touch probe and prior TLS/history/AVC gates. Merged as 683e5b7.
- Debug APK artifact 14892476862 from run 45331898798; version 0.1.0-alpha.18. All touch readings are local synthetic 64x64 values, no network input or Windows injection. Actual Lenovo gestures, rotations and physical video remain pending.

## Android debug APK integrity gate (CI pending)
- Introduced offline stdlib verify_android_apk.py: bounded ZIP file/entry counts, no traversal/duplicates/encryption/symlinks, required Android manifest/DEX/resources, CRC and SHA256. Six fixtures PASS locally; earlier saved debug APK also PASS (not a signature guarantee).
- Android CI now runs verifier tests, validates built APK and requires apksigner verification, publishing text evidence beside debug APK. No release signing or physical device install attempted. CI pending.
