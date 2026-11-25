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
- Added explicit Android CI path triggers for both APK verifier scripts and negative fixtures for Windows-style and double-slash archive paths. Runtime still unchanged.\n
## Verified Android APK artifact gate (2026-11-24)
- PR #16 head 249d3fb: Android CI 45332888028/45332880903 PASS; Windows CI 45332888086/45332880902 PASS; merged as 2e30498.
- Offline verifier policy includes eight positive/negative fixtures and bounded ZIP/CRC/SHA256. CI requires Android apksigner verification (debug APK v2 signature, one signer), publishes apk-integrity.txt and apk-signing.txt with app-debug.apk. Artifact 14893015165 from 45332888028.
- This is not trusted release signing, physical install, actual Lenovo decode or reproducible release acceptance. Next release preflight: compare APK manifest package, min/target SDK, version and permissions to reviewed Gradle configuration.

## Android APK identity/permission preflight (CI pending)
- Added check_android_badging.py, six synthetic package/SDK/permission tests (14 combined verifier fixtures PASS locally), and Android CI aapt dump badging gate comparing packaged package ID/version/min/target SDK to source build.gradle.
- Strict permission allowlist begins with INTERNET, CAMERA, VIBRATE, FLASHLIGHT and ACCESS_NETWORK_STATE; unreviewed permissions cause CI failure, not silent trust escalation. APK badging/identity reports are bundled with integrity and debug signature reports. CI pending; Android permissions are not production signed or physically tested.

- Confirmed from actual PR #17 debug artifact 14892926089 / Android run 45333371769: app ID com.veypanel.client, alpha.18, only CAMERA and INTERNET permissions, APK v2 debug signature PASS. Tightened allowlist to these two; other permission requests require explicit future approval. CI retry pending.

## Verified Android APK identity and permissions (2026-11-24)
- PR #17 head b07c41a, Android CI 45333601381/45333593892 PASS, Windows CI 45333601475/45333593891 PASS; merged as c056d8d.
- Verified packaged ID com.veypanel.client, version 0.1.0-alpha.18, minSdk 26, targetSdk 35, exactly CAMERA and INTERNET permissions; allowlist tightened to those two. APK v2 debug signature verified, not production signed.
- GitHub debug APK artifact 14892847988 from run 45333601381 includes APK, ZIP/SHA256/signing/badging/identity reports. No actual Lenovo installation or hardware streaming acceptance.
- Next critical gates: actual Windows Host/Intel Quick Sync and Lenovo tablet connection, owner-trusted CA, camera/touch/decoder/sleep/rotation, safe display mutation with independent rollback, release signing and dependency audit. Gateway access currently only Proxmox, so hardware PASS cannot be claimed.

## Android third-party license packaging guard (CI pending)
- Source audit: Android ZXing Embedded 4.3.0, ZXing Core 3.5.3, OkHttp 4.12.1 pinned; app license/NOTICE assets exist and were present in actual alpha.18 debug APK. Windows Host packages pinned, Codecrete MIT license bundled, NuGetAudit enabled.
- APK verifier now requires five known Android third-party license/notice assets; updated fixtures include missing-notice negative. CI pending. This does not establish transitive lockfiles/SBOM or production redistribution acceptance.

## Verified third-party license archive gate (2026-11-24)
- PR #18 head f1037b8: Android CI 45334220672/45334212229 PASS, Windows CI 45334220748/45334212121 PASS; merged as fe43f31.
- APK verifier requires five bundled ZXing/OkHttp license/NOTICE assets. Actual signed debug APK artifact 14892659707 from run 45334220672 includes verification reports. Full Gradle/NuGet transitive dependency lockfiles and SBOM are still absent, and physical hardware and release signing remain pending.

## Resolved dependency inventory candidate
- Gradle selected debug runtime modules and restored Windows Host win-x64 NuGet package target converted to sorted CycloneDX 1.5 component inventories; six offline fixtures PASS. CI pending. No claim of exhaustive SBOM, trusted build or dependency lock.

## Verified resolved component inventory (2026-11-24)
- PR #19 head 5da1856, Android CI 45363577089/45363566720 PASS, Windows CI 45363577252/45363566718 PASS, Android runtime 45363566687 PASS; merged as 8a2e239.
- Actual artifacts inspected: 10 Maven components in Android runtime; two NuGet packages in Windows Host win-x64 restore target. CycloneDX component-only inventory is not a complete release SBOM.
- Next: enforce post-resolution component coordinate baselines copied from these successful artifacts; native lockfiles, artifact hashes, complete license and advisory review remain separate tasks.

## Dependency drift gate candidate
- Captured 10 Android and 2 Windows package URLs from actual passing PR #19 build artifacts. Eight local drift fixtures PASS; CI pending. This rejects post-resolution coordinate changes without pretending to be a native package lock.

## Verified dependency drift gate (2026-11-24)
- PR #20 head 3a759ad; Android CI 45364210959/45364200175 and Windows CI 45364210957/45364200218 PASS; merged as e24a1ff.
- Android ten-component and Windows two-package baselines now enforced after resolution. Eight local comparator fixtures passed.
- Next: validate native Gradle runtime lock with Gradle 8.9 and capture genuine NuGet lockfile generated by restore, then enforce NuGet locked mode.

## Native dependency lock candidate
- Gradle runtime lock derived from observed ten Maven coordinates; strict locking enabled, CI must reproduce identical state with --write-locks. Windows restore uses --use-lock-file and publishes actual generated candidate; NuGet locked mode remains pending.

## Verified native Gradle lock and NuGet capture (2026-11-24)
- PR #21 head 1260f6e; Android CI 45364765561/45364754303, Windows CI 45364765530/45364754053, runtime 45364754109 PASS; merged as 7f30b4d.
- Strict debugRuntimeClasspath lock confirmed by Gradle regeneration and runtime acceptance on emulator. Other configurations and artifact verification hashes remain outside scope.
- Windows-generated lock candidate artifact 14905543319 from run 45364754053 contains two packages, both valid SHA-512 contentHash values. Next: enable native NuGet locked mode for Host and verify restore/build/publish CI.

## NuGet locked mode candidate
- Original lockfile from run 45364754053 artifact 14905543319 is committed. Host enables RestorePackagesWithLockFile and RestoreLockedMode. CI explicitly restores win-x64 with --locked-mode and checks the lockfile remains unchanged. CI pending; no complete reproducible release claim.

- Initial PR #22 Windows runs 45365416506/45365405289 failed NU1004 during self-contained win-x64 publish: the generated lock represented only net10.0. Declare Host RuntimeIdentifiers=win-x64 and generate a candidate explicitly on the Windows runner. Temporary unlocked generation is not eligible for merge and must be removed after capturing the candidate.

- Corrected RID-aware lock from CI run 45369999676 artifact 14908917225 adds net10.0/win-x64 with no package/version/hash changes. Temporary generation removed. Strict restore/build/self-contained publish and integration CI must pass before merge.

## Verified NuGet locked mode (2026-11-24)
- PR #22 head 8d6d22c, Windows CI 45370338307 and 45370350526 PASS, merged as 1bfe1ea.
- Initial NU1004 at self-contained publish corrected using explicit RuntimeIdentifiers=win-x64 and genuine SDK-generated net10.0/win-x64 lock section, preserving both package SHA-512 hashes. Temporary unlocked capture removed; strict restore/build/publish and lockfile diff passed.
- Next: enforce Gradle artifact checksum verification from matching build captures, with negative checksum test. Complete upstream provenance, runtime packs, SDK pinning, production signing and physical acceptance remain open.

## Gradle artifact verification candidate (2026-11-24)
- PR #23 captures from Android runs 45370100108 and 45370108991 are byte-identical (metadata SHA-256 895024f250298a8b6be73c214f50546e442a9fb7d2d8440e09a5eaa2520f26c0); 395 SHA-256 artifact records, all ten runtime component coordinates covered, no trust exemptions.
- Strict mode replaces temporary metadata generation in Android CI and runtime workflow. Five offline policy fixtures pass. A Gradle negative test changes only the expected ZXing core JAR checksum temporarily, requires the correct artifact verification failure, restores metadata and verifies no Git diff.
- Combined CI pending. The capture is trust-on-first-use, not independent upstream attestation or complete production SBOM.

## Verified Gradle SHA-256 verification (2026-11-24)
- PR #23 head 6fd97f1; Android CI 45371001724, Windows CI 45371001725/45370988170 and exact-head Android runtime 45371079169 PASS; merged as 690f679.
- 395 matching CI-captured artifact hashes committed, strict Gradle verification enabled in ordinary Android build and runtime. Actual incorrect ZXing core digest rejected in CI; metadata restored. Local Python fixtures 35/35 PASS. This is trust-on-first-use, not upstream publisher attestation.
- Next: pin observed SDK/JDK/Gradle versions and publish toolchain evidence; complete release signing, transitive license audit and physical hardware gates remain open.

## Exact build toolchain candidate
- Successful CI logs confirm .NET SDK 10.0.404 (45370338307), Temurin 17.0.21+9 (45370100108), Gradle 8.9 and Windows Python 3.12.10. Pin exact .NET SDK in global.json, disable roll-forward, require exact JDK and Gradle and Windows Python in workflows; publish build-toolchain.txt. CI pending. Toolchain pins do not make runner images or Android SDK/platform-tools immutable.

## Verified exact build toolchain (2026-11-24)
- PR #24 head 52de029, Android CI 45371848490/45371834687, Windows CI 45371848232/45371834360 and runtime 45371834290 PASS; merged as b81dedb.
- Exact .NET 10.0.404, Temurin JDK 17.0.21+9, Gradle 8.9 and Windows Python 3.12.10 enforced. Actual Android artifact 14909028136 confirms API35 revision 2, build-tools 35.0.0 and platform-tools 37.0.3. Runner image and SDK distribution are not immutable.
- Next: collect literal license declarations and notice hashes from verified runtime packages, then review missing/transitive notice obligations and release provenance.

## Runtime license evidence candidate
- Added checksum-gated Maven/NuGet archive inspection and seven offline fixtures, including tampered package rejection. CI publishes dependency-license-evidence.json with literal declarations and notice hashes. No inferred SPDX conclusion or legal approval; full license review pending.

- Initial PR #25 Android CI 45372580810/45372571558 PASS; Windows 45372580801/45372571530 failed because raw signed nupkg SHA-512 differs from NuGet contentHash. Use pinned SDK dotnet nuget verify for signed packages (native content hash and signature validation), keep raw archive hash separately, and preserve strict lock comparison. CI retry pending.

## Verified runtime license evidence (2026-11-24)
- PR #25 head 8ddb734, Android 45377626137/45377614152 and Windows 45377626247/45377613953 PASS; merged as 27472b8. 45/45 local Python fixtures PASS.
- Initial raw nupkg hash failure corrected with native dotnet nuget verify for signed packages and strict contentHash comparison. Actual Windows report confirms signature verification for both packages and MIT declarations; ProtectedData includes THIRD-PARTY-NOTICES.TXT. Android report covers ten Maven components.
- Supplemental exact Maven POM sources resolve missing declarations for ZXing Core (parent POM matches Gradle metadata), OkHttp and both Okio modules (external POM hashes not in existing metadata). All ten Maven components declare Apache 2.0 directly or via ZXing parent; two NuGet components declare MIT. No conclusion of complete license or redistribution compliance.
- Android artifact 14912750984, Host artifact 14912666175. PR #26 independently captures time-stamped OSV runtime advisory snapshots.

## Runtime advisory audit candidate
- Public OSV querybatch collector with bounded response/pagination validation, six offline tests PASS. First live query 2026-11-24 covered 12 runtime package coordinates and returned zero matches. CI workflow and artifact publication pending; no full security approval or app networking changes.

## Verified runtime advisory audit (2026-11-24)
- PR #26 exact HEAD 8353025: OSV CI 45378191048/45378182750, Android CI 45378182940 and Windows CI 45378191025/45378182772 PASS; merged as 5643653.
- Actual time-stamped CI artifact 14911593443 contains 12 exact runtime package coordinates and zero advisory matches at collection time. No full vulnerability coverage or security approval; findings require review. Combined local Python tests 51/51 PASS.
- Next: record exact artifact file membership and SHA-256, independently compare two builds of the same commit, and investigate reproducibility differences before release signing.

## Artifact reproducibility preflight candidate
- Ten artifact-manifest fixtures PASS. Actual downloaded Host (360 files) and Android (8 files) inventory verification PASS. Same-HEAD PR #25 builds show all 25 decompressed APK entries match but full APK hashes differ; 356/360 Host files match, four differ. Evidence JSON saved; CI staging/manifest publication pending, no byte-identical release claim.

## Verified artifact manifests (2026-11-24)
- PR #27 head 4441e8e; Android CI 45378711150/45378700597, Windows CI 45378711008/45378700546 PASS; merged as 6584fa9.
- Downloaded Android/Host/Desktop artifacts independently verified all 8/360/834 files against published SHA-256 manifests. All 1202 file entries match.
- Follow-up inspection of PR #25 APKs: 1027 different raw bytes, all within identical-sized APK signing blocks [1782490,1786586); all bytes outside match. This does not verify signer identity or establish byte-identical APKs.
- Prior comparison used PR and push workflow headSha; Windows PR checkout log identifies synthetic merge abd2c66, so exact source commit equality is not established. Static web assets Last-Modified varies between runs. Next: explicit checkout SHA/tree evidence and independent same-checkout Windows reproduction; separate APK signing block comparison.

## APK exact-checkout reproduction candidate
- Six structural comparator fixtures PASS. Actual PR #25 APKs match exactly outside validated signing blocks (not signature authentication). New isolated two-runner Android workflow explicitly checks out the same github.sha, verifies both APK signatures and compares checkout SHA/tree and outside-block bytes; CI pending.

## Verified Android exact-checkout reproduction (2026-11-24)
- PR #28 head 485c020; exact reproduction run 45403501445 (build a, build b, compare all PASS), Windows CI 45403485262/45403501661 PASS; merged as 96fb3b9.
- Both APKs built from actual checkout 0c70d781e4dea4e547b2de5ea728ec50800c536e, tree 03b1d9eebedd65606ed081fcea124938c08bf966. Both APK v2 signatures verified by apksigner. Equal bytes outside signing blocks; complete hashes differ. Comparison artifact 14924837063, build artifacts 14924343368/14923579078.
- Six new comparator fixtures, 67/67 local Python tests. Windows exact-checkout reproduction is PR #29; preserve raw differences and validate experimental normalized output separately.

## Windows exact-checkout reproduction candidate
- Prior static asset JSON differs only in 50 Last-Modified values; diagnostic normalization produces identical JSON, six local fixtures PASS. New dedicated Windows CI builds identical checkout twice with locked packages and pinned SDK, captures raw and normalized inventories, smoke tests normalized output, and compares all normalized files without excluding binaries. Ordinary Windows CI unchanged. CI pending.

- Initial experiment 45403857956 failed checkout text comparison due CRLF, corrected in b59102b. Run 45403914865 PASS: both independent builds used checkout 66bffb0772aa75d7928c5e66366274456d36f890, tree 66556a5676f414d26588adb0db5bb2eef84b2ce0; raw 356/357 identical, only static endpoint JSON differs; normalized 357/357 identical, both runtime smoke tests passed. Comparison artifact 14922904731. Final combined HEAD CI pending.

## Verified Windows exact-checkout reproduction (2026-11-24)
- PR #29 final HEAD 3cc40d9: reproduction 45404314553 (both builds and comparison PASS), Windows CI 45404301160/45404314462 PASS; merged as b186b92.
- Actual identical checkout d3cead4a81edfd9f6cf788bbf62a3b131d550af7, tree 9255f186e8913a6568a5e6b1be513769030e780a. Raw 356/357 files identical, only static web asset endpoints JSON changed; normalized 357/357 identical, including DLL/EXE/PDB; both Host runtime smoke tests passed. Comparison artifact 14923894198.
- Initial CRLF checkout evidence failure corrected. Experiment confirms unsigned Host output reproduction with explicitly normalized timestamp metadata, not ordinary artifact byte equality, Desktop reproduction, Authenticode, or complete installer reproduction.
- Next: record actual clean tracked source checkout in ordinary artifacts (build-source.json); then evaluate adopting validated deterministic publication settings. Hardware and production signing remain open.

## Build source evidence candidate
- Capture actual clean tracked Git checkout SHA/tree/epoch before build and verify unchanged before publishing Android/Host/Desktop artifact manifests. Six local Git repository fixtures and CLI verification PASS. CI pending; no signed attestation claim.

## Verified build source evidence
- PR #30 head 64784fe; Android CI 45404957532/45404941001, Windows CI 45404957357/45404941193 PASS; merged as 138695e.
- Downloaded Android, Host and Desktop artifacts independently verified. All record actual checkout 7c4d5a67940fbbc97144500b0d72d334dd93d3de and tree c8df57d8256d3b2c2afa87f0e411b4dcac632fef. No signed attestation claim.
- Next: adopt tested CI deterministic Host publish settings, keep raw static endpoint evidence separate, validate actual ordinary publication and its integration tests.

## Deterministic Host ordinary publication candidate
- Apply prior verified experimental settings to ordinary Windows Host CI publish. Preserve raw and normalized endpoint JSON with checkout evidence in a separate manifest-protected artifact. Existing Host integrations and Desktop bundling exercise normalized output. CI pending; no local installer, Desktop reproduction, or signing claim.

## Verified ordinary deterministic Host CI publication
- PR #31 head 614e369, Windows CI 45411446910/45411465466 PASS, merged as bc5aedb.
- Actual publication evidence artifact 14929330243 independently verified: all 50 Last-Modified values use recorded source epoch; all non-timestamp fields preserved. Host artifact 14928032295, Desktop artifact 14928551984. Existing Host integration gates passed.
- Ordinary CI publication now uses tested settings; local commands unchanged. Next independent Desktop exact-checkout experiment includes complete experimental bundle with verified embedded Host, without runner-specific reports. Interactive WPF and physical hardware remain open.

## Desktop exact-checkout reproduction candidate
- Two independent Windows runners build Desktop and normalized Host with pinned SDK and ContinuousIntegrationBuild, verify nested Host manifest and run Host smoke. Compare the complete experimental bundle inventory without masking any differing files. Interactive WPF, physical display/touch and signing acceptance remain separate.

## Verified Desktop exact-checkout reproduction
- PR #32 head 5cfe007, reproduction 45412111245 and Windows CI 45412093869/45412111080 PASS, merged as 4a3612d.
- Actual checkout 65f5cfc1082bc2deb4c6ef083806ec59c45ab625, tree e0df7e6d91729adcb6abea6b6aef958a8a33b2b2. Both independent experimental Desktop bundles contain 832 identical files. Downloaded inventories and comparison artifact 14928461490 confirm equality. Host smoke passed; no interactive WPF acceptance.
- Next: portable deterministic Windows ZIP packaging with file verification and independent archive reproduction. Installer and signing remain separate.

## Portable Windows ZIP candidate
- Eight new ZIP fixtures PASS (87/87 total). Two local packages of downloaded PR #30 Desktop artifact match all 836 manifest files and exact archive SHA-256 1b2b42cea8899257b967c8ad24c631cd0b22c2bfc11a51c2b006c29182434e88. CI adds independent archive reproduction, Windows extraction and ordinary portable artifact publication. Unsigned; no installer or hardware acceptance claim.

## Verified portable Windows ZIP
- PR #33 head 0879d46, Desktop reproduction 45412991876 and Windows CI 45412992120/45412976488 PASS, merged as de36627.
- Independent experimental ZIP SHA-256 17e9ea417213dda5aa1d56c237df4baa9db3d1b247192f960d341d2c11c6aebc matches on both runners. Actual ordinary portable artifact 14931435132 downloaded and independently verified: 836 files, SHA-256 58ea65c2093f2af20924c77250e619d17d464a1f3108da21f83732019d3ef2ce.
- Next: digest-pinned package preflight and isolated side-by-side staging with dry-run; no system mutation or execution.

## Digest-pinned Windows staging candidate
- Default read-only package preflight, explicit --apply into a new directory below an existing non-reparse parent. Verify full archive digest, file hashes, nested Host manifest, matching valid source evidence, disk space and extracted tree. Nine offline fixtures; no activation, overwrite, registry or service changes. Windows CI pending.

## Verified Windows package staging
- PR #34 head acdac46, Windows CI 45426452023/45426432998 PASS, merged as eb5d51c. Actual CI log confirms dry-run and staging of 836 files, both extracted manifests match.
- Next: side-by-side verified package selection with an atomic state record, explicit rollback and no process launch or system mutation. Power-loss recovery and uninstall remain separate.

## Side-by-side package selection candidate
- Digest-derived version directories, atomic selection.json with active/previous records and pinned manifest hashes, exclusive cooperating writer lock, dry-run default. Thirteen fixtures, 109/109 total local tests PASS. Real PR #30 repack and PR #33 portable ZIP selected in sequence and rolled back; both versions and ZIPs retained. Windows CI tests real first selection/idempotence and synthetic upgrade/rollback. No process launch, migration, automatic orphan deletion or physical power-loss guarantee.

## Verified side-by-side selection
- PR #35 head 90c0951, Windows CI 45428020239/45427999735 PASS, merged cbe863f. Local 109 fixtures and real package A/B rollback were verified previously. Next: correct CI pipeline failure propagation before further release acceptance; launcher and recovery remain open.

## Fail-closed release gate correction candidate
- Audit found implicit bash -e report pipelines without pipefail in Android CI/runtime and Android/Windows reproduction. Explicit bash shell policy now used in five relevant workflows; intentional negative step requires failure outcome. Exact unconditional CAMERA/INTERNET permissions required, duplicate/unsupported declarations and colon/trailing-separator APK paths rejected. Seven added fixtures, 116 total tests PASS; actual downloaded APK and badging PASS. Real negative archive and identity commands through tee rejected locally; apksigner negative case requires CI. Previously downloaded Android and Windows reproduction evidence independently rechecked. No claim that old CI statuses alone established failure propagation. Launcher/recovery remain next.

## Verified fail-closed CI correction
- PR #36 head a29feaf, merged e35bf8c; all 14 jobs across eight workflow runs PASS. Android CI 45433922627/45433944680 includes mandatory negative pipeline outcome and archive/identity/signing rejection step; job step conclusions independently checked, raw negative log unavailable on latest query.
- Runtime 45433922633, Android reproduction 45433945066, Host reproduction 45433944945, Desktop/ZIP reproduction 45433944815 and Windows CI 45433922629/45433944858 PASS.
- Next: publish locally prepared verified-package launcher, then interrupted-state recovery. Full physical acceptance and signing remain open.

## Engineering policy adoption candidate (2026-11-25)
- Source baseline 012d49c3628789d00acd0d67d75a4e0180990cd6; user-provided portable policy v1.0 universal sections adopted without unrelated profile/provenance. AGENTS, canonical standards, adoption gap register ENG-01–15, security/architecture, test catalog and roadmap updated. Existing approval boundaries unchanged.
- Initial AST inventory: 469 findings (345 annotations, 123 docstrings, 1 length). Exact 22 resolved in build_source_evidence and its tests; 447 remain. New auditor and QA runner fixtures introduce no findings. The baseline is a migration inventory, not full compliance.
- Local Python 3.13.5: 124 unittest cases PASS, common runner summary/JUnit/code audit emitted; native/hardware NOT_RUN in this scope. Initial run was a dirty development checkout, clean committed rerun required.
- PR #37 head 0df6f83: Windows CI 45509910174/45509902471 PASS; remains open until adoption integration. Recovery worktree /tmp/veypanel-recovery head f907af6 local only. Do not inflate baseline for new launcher/recovery debt; bring them into compliance before merge.
- Latest main Android runtime 45509804749 failed at dependency resolution (Maven HTTP 429), instrumentation NOT_RUN. One bounded rerun requested; no dependency or TLS change. PR #36 runtime had passed earlier.
- Next: run clean common QA, publish development review branch and check CI; independently fix high-priority manifest bounds/mutation and launcher/recovery debt. No production deployment, release, signing, visibility or Confluence publication.

### Adoption CI portability regression
- Initial PR #38 Windows CI 45514689128/45514677681 failed the new shared gate. Downloaded JUnit from 45514689128 (artifact 14975773912) identified test_backslash_path, 123/124 PASS; AST exact gate PASS. Windows zipfile normalizes backslashes on writing/reading. Fixture now writes the raw forbidden byte into local/central ZIP names; verifier checks orig_filename against normalized filename, and rejects NUL truncation. Twelve APK fixtures and the saved actual APK passed locally. Eighteen more exact test-module debt entries removed, 429 remain. New CI required; no assertion weakened.
- Main Android runtime run 45509804749 bounded rerun completed SUCCESS after initial Maven HTTP 429. No dependency or TLS change.

## Verified engineering policy adoption
- PR #38 head e8f1acdfb4a2d6b77e8aff308384a2c740825431, merge 3cb4477; all ten jobs passed. Windows 45515007864/45515015460, Android 45515008002/45515015606, Android reproduction 45515015403, Desktop reproduction 45515015433 PASS.
- Downloaded Windows and Android common QA evidence from 45515007864 and 45515015606 independently checked: 125/125 executed PASS, zero skips, exact debt baseline 429, no new/stale findings, clean actual checkouts e8f1acd and 523b1f2, identical tree 3cec1b97688d439917fcfbbba811a98e038d49d0, Python 3.12.10.
- Next: manifest integrity hardening; rebase candidate f7fe6a5 and validate before review. PR #37 launcher and local recovery candidate must pass the new debt gate without increasing the baseline.

## Manifest integrity hardening candidate
- Branch dev/manifest-integrity-hardening based on adoption PR #38. Six new tests for unreadable subtree, same-size mutation, entry count, manifest read bound, strict schema and atomic replacement failure; 34 exact debt identities removed, 395 remaining. Prior Android/Host/Desktop manifests and ordinary portable ZIP verify with hardened code. Existing staging manifest replacement remains supported; accepted artifacts must not be overwritten. No hostile concurrent tree, independent inventory or physical durability claim. Windows CI pending; do not merge before adoption gate.

### Manifest Windows portability correction
- PR #39 initial Windows 45515644679/45515652582 failed, 31 errors in common QA; downloaded JUnit confirms 100/131 PASS and no new/stale AST findings. Windows/ Desktop reproduction 45515652447/45515652277 logs explicitly report File changed before hashing, comparisons NOT_RUN.
- CPython v3.12.10 source Modules/posixmodule.c (win32_xstat/update_st_mode_from_path) and Python/fileutils.c (_Py_fstat_noraise) reviewed: path stat adds executable extension mode bits and aliases deprecated ctime to birthtime. Cross-API Windows comparison uses exact device/file identity, size, mtime, birthtime, common mode bits; full before/after comparisons remain within each API. No timestamp tolerance or blanket fallback. New cross-API and actual executable/manifest reopen fixtures. Local QA PASS; corrected Windows CI required.

## Verified manifest hardening checkpoint
- PR #39 head 2065821abd160d4684a0afd970ba3045b6c4bc5c merged 3565f75. All ten CI jobs PASS; Windows 45516193643/45516181304, Android 45516193786/45516181388, Host reproduction 45516194018, Desktop/ZIP reproduction 45516193647.
- Independently downloaded Windows QA artifact 14978715316: 133/133, zero skips, exact debt 395, no new/stale findings, clean checkout 684ccdf389c025c89393419dde47231bbb96ca8d tree 6900ee7c0a91d622f30714d3a4492da2100df2f4. Normalized Host comparison downloaded and verified. First failing attempt and CPython cross-API correction retained above.
- Next: safe QA event branch, then Host smoke secret capture and request logging review. Launcher PR #37 must be verified against current main; no physical activation or release approval.

## Scoped safe QA event candidate
- Branch dev/safe-qa-events based on manifest PR #39. Optional --log-events produces allowlisted audit/tests/report/run JSONL on stderr, no arbitrary text/path fields, existing exit contracts preserved. Eight new regressions cover invalid fields/duration, secret canaries, failure/error exit semantics. Full local Python QA pending clean committed rerun; no new AST debt. Targeted logging audit recorded in docs/qa-event-logging.md. No general secret redaction or Host logging acceptance.

## Verified QA event checkpoint
- PR #40 head 34c05a868b62b8c258cd66cba0b9b12f9ab23f3c merged e0c1c3b. Windows 45516846055/45516854427 and Android 45516846052/45516854500 PASS. Downloaded Windows report confirms 141/141, zero skips, clean checkout a9ed009de2fc1c7fc38e8e66c3a358b1a81eb21a, tree 4b723ed640bb65715950a6142f3c5c3203a8d066, debt 395, exact delta empty.
- PR #41 77dc4ce and PR #37 cf59419 previously passed all eight/three jobs respectively; integrate current main and recheck before merge. Next independent P0: framework request logging and synthetic credential canary.

## Host smoke capture integration
- PR #41 head 77dc4ce: Windows 45517055826/45517062834, Host reproduction 45517062962, Desktop reproduction 45517063056, all eight jobs PASS. Merge current main 2f4b7a9 with QA events, preserve documentation checkpoints. Combined-source CI required.
- No raw temporary logs, owned pipe capture and fixed errors; all telemetry assertions retained. Synthetic fixture and actual Windows smoke ran in prior CI. No historical public leak established.

## Verified Host smoke capture
- PR #41 head 78bc723a9fc486159705677830019fdff7789a55 merged b3d4ebf. All nine combined-source jobs PASS: Windows 45518031667/45518021242, Android 45518021295, Host reproduction 45518031645, Desktop reproduction 45518031818. GitHub API confirms both private bootstrap fixture and actual published Host smoke steps succeeded.
- Pending independent candidates: PR #42 8ebbc1b default framework log privacy, PR #43 e506c6a experimental WSS state with JVM/emulator checks. Both clean local Python QA 141/141; native CI required. PR #37 cf59419 passed three jobs against older main; integrate current main before merge. No release or hardware approval.

## Launcher integration after private capture
- PR #37 head cf59419 passed Android 45517140638 and Windows 45517140681/45517148453 against manifest-hardened main. Merge current main bf88748, preserving verified PR #40 and #41 checkpoints. No baseline increase, native CI required on new combined source. Existing ten Launcher regressions include a safe CLI error canary; actual WPF activation remains NOT_RUN.

## Verified Launcher and current review queue
- PR #37 head c2d16ba2ad97c834f5c2053b77b9370699bf5695 merged 2262808. Previous two HTTP 500 pushes reconciled with remote ref, later ordinary push succeeded. Android 45518966093, Windows 45518965990/45518972862 PASS. Downloaded actual Windows QA/JUnit confirms 151/151, no skips, clean checkout a7d7bff848809f254b96cd3ee95bbc47a861ba40 tree ed829ccb6f717aa7ccc0572728c64884259adec7, exact debt 395. API confirms actual launch-plan step success; no interactive WPF process launch.
- PR #42 initial head 8ebbc1b eight jobs PASS, request log privacy step confirmed. Integrated head 11fcda1 with accepted private Host capture; seven jobs passed at latest check, final Windows 45519057018 still pending. Main has advanced, verify combined current source before acceptance.
- PR #43 head e506c6a all eight jobs PASS, including Android runtime 45518421728 and native JVM checks; integration conflict pending. Experimental transport remains separate from production OkHttp.
- PR #44 d7cd94a, local preview tap lifecycle and queued Surface wrapper cleanup, local Python 141/141; Android native and emulator 45519270817 pending. Texture/codec destruction ownership and reused-texture callback generation still open.
- Recovery engineering worktree /tmp/veypanel-recovery-adoption, branch dev/recovery-engineering-adoption head 8f456da. Eleven fixtures, clean local Python QA 152/152, exact debt 395. Actual isolated two-version root read-only inspection verified both trees, no lock/temp state. Hold local until review queue clears, then integrate current main and run Windows CI. No automatic recovery mutation.
- Next: finish PR #42 and #43 integration, then PR #44 and Recovery; do not rebaseline or bypass native checks. No release or physical acceptance.

## Combined review queue candidate
- Base main be72db0. Integrate exact reviewed heads PR #42 11fcda109268d2d9272da524fa2a37287b69209e, PR #43 e506c6ad29776d12bb81da3a3ed067e7e87e881a, PR #44 d7cd94a68b4b8d57c52e4035a654141266350b58, and local recovery 8f456da68edbd98a009bbde8302e5dd264e742f8 with merge ancestry retained. Each original PR passed all eight jobs before integration (42 Windows 45519049770/45519057018 plus Host/Desktop reproduction; 43 runtime 45518421728; 44 runtime 45519270817 and APK reproduction 45519279517).
- Conflicts limited to ROADMAP/RESUME and adjacent workflow insertions. Preserve main checkpoints, both JVM fixtures, Host privacy, private bootstrap, Launcher and Recovery steps. Recovery has eleven offline fixtures; actual two-package root inspected earlier. All combined local Python 162/162, clean checkout 72e0382, debt 395, no new/stale findings. Fresh combined CI mandatory before merge; original PRs remain in ancestry, no independent hardware or release claim.
- Next independent stage: SurfaceTexture ownership and callback generation; no more main updates until the combined candidate is verified unless another required safety fix intervenes.

## Verified combined integration
- PR #45 head d6b9d031bb3cc41d4cd69c578302ba661a267f14 merged 5bb550570217b7fb23bb7aa54d1a4d3ce8b5b3ce; all fourteen jobs PASS, original PRs #42/#43/#44 included in ancestry, no open PRs after merge.
- Windows 45520009361/45520017767, Android 45520008959/45520017783, Android runtime 45520008901, Android reproduction 45520017761, Host reproduction 45520017812, Desktop reproduction 45520017785. API confirms mandatory private bootstrap, framework privacy, Launcher, recovery inspection and Android runtime steps passed.
- Downloaded Windows QA/JUnit independently verified: actual checkout 6c0cd97a40ad7350a3f7b6bc5d09a37eb6376298 tree 44dd53c8d86ae40ee60762b6314a53639a2ff729, 162/162, zero skips, debt 395, no new/stale entries.
- Next: integrate texture ownership candidate 56d5f14, inspect production transport limitations and explicit recovery prerequisites. No physical or release approval.

## Texture ownership candidate
- Base d6b9d03 PR #45, branch dev/preview-texture-ownership. One-use lease coordinates queued/active/completed worker and framework destroy; worker releases detached texture after Surface/codec cleanup. New TextureView per preview prevents stale view callbacks, actual repeated Activity preview regression plus pure JVM fixture. Native CI not yet run; hold locally until combined PR #45 acceptance. No native codec deadline or hardware proof.

- Integrated accepted main 94a97f7; preserve previous native acceptance and run fresh combined-source CI before merge.

## Verified texture lifecycle checkpoint
- PR #46 head e1eb3770e46e287d13659182923accf18c31e6cc merged cc88ceb4ccffd5b81d97fdb65cfa40db4de498f4; Windows 45522615825/45522605890, Android 45522615901/45522605822, runtime 45522605967 PASS.
- Reproduction 45522615996 initial build(b) failed dependency resolution HTTP 429, compare NOT_RUN. One bounded failed-job rerun passed both builds and comparison. Downloaded artifact 14980618698 confirms bytes outside signing block identical; full SHA-256 differs. No signature verification claim from comparator. All eight CI jobs now PASS. Post-PR #45 main jobs also PASS.
- Next candidates: WSS mailbox and strict CRLF/provenance audit 8373d4a, explicit first-install recovery b885fab. Local 162/162 and 174/174 respectively, native NOT_RUN. Real isolated prior package 836 files recovered metadata-only. Integrate candidates with current main and require fresh combined-source CI; no release or physical acceptance.

## Combined WSS and first-install recovery candidate
- Base main 23337a8, integrate 8373d4ac5d60ee9d89ba30fd1c7d36b78a02da95 and b885fab5f57c37b83bc9ceece23d140f61d955fb; preserve merge ancestry. Adjacent Android JVM workflow conflict resolved retaining both LocalPreviewLease and LatestTelemetryMailbox fixtures; Windows recovery steps retained.
- Mailbox preserves first terminal cause, bounded 5.5s wait and 5s receipt age, immediate cancellation notification and single-reader admission. Experimental upgrade rejects bare CR/LF. Candidate upstream reader reviewed; exact artifact mapping unverified, pinned JAR unchanged, no claim of compromise or pre-allocation memory protection.
- First-install recovery requires externally trusted ZIP, sole verified staged version and absent selection state, explicit plan-bound apply; no lock clearing or payload mutation. Twelve offline regressions and real isolated root /tmp/veypanel-real-recovery-taa3omny with 836 files PASS, full inventory unchanged. Actual Windows CI step required.
- Combined offline QA must PASS, exact debt remains 395. Android JVM/runtime/reproduction and Windows package integration mandatory before merge. No real activation, deployment, signing or hardware approval.

## Verified production mailbox and first-install recovery
- PR #47 head 9d0efcd87076af98459a42ab691fc78afe3860ed merged 37a07f54288d2a109debecf6c796eb368c02fbac; all eight jobs PASS. Windows 45524079522/45524086257, Android 45524079599/45524086341, runtime 45524079540, APK reproduction 45524086309.
- Downloaded Windows common QA/JUnit verified 174/174, zero skips, clean checkout ac79e39bd05fc33d14e4b43888c2f8338f928886 tree 2087f51f0a471a895916ce9e5da075b0252ae952, debt 395, empty exact delta. API confirms explicit first-install recovery, read-only recovery and launch plan steps PASS.
- Next: bounded strict selection metadata and single-read manifest identity, independent exact OkHttp binary inspection. No production deployment or physical approval.

## Strict selection metadata candidate
- Base 8e05309, dev/strict-selection-metadata. Reuse bounded metadata reads with Windows cross-API identity checks, strict UTF-8 JSON (duplicate keys, nonstandard constants and parser nesting errors refused), hash and parse one manifest snapshot, validate populated state before atomic write. Safe CLI categories, no raw exception. Six new regressions, 19 selection tests; exactly 66 baseline identities removed from selection module and fixtures, no new debt, remaining 329.
- Local all Python 180/180 PASS; prior actual Android/Host/Desktop manifests verified, two-version selection status PASS, recovered 836-file root read-only inspection and digest-bound Launcher dry-run PASS. No process started. Native Windows CI required. Private quiescent root assumption, no atomic multi-file snapshot or hostile concurrent writer claim.

## Verified strict selection metadata
- PR #48 head ad8d573f548af655c6beee6f7d8116eaa9519445 merged; all ten CI jobs PASS. Windows 45526120102/45526112914, Android 45526120152/45526113208, Desktop reproduction 45526120154, Host reproduction 45526120110. Downloaded Windows QA/JUnit artifact 14981299564 confirms 180/180, zero skips, exact debt 329, clean checkout dc3620b5380cc4953b7cdfc1a3058f2fcbd8917f tree 1545e627f4acc9bbe4f9ad23e8774d200ced5fb2.
- Next: integrate exact OkHttp binary evidence candidate; no production transport switch or physical acceptance.
## Exact OkHttp binary evidence candidate
- Base 8e05309, dev/okhttp-bytecode-evidence. Retrieved exact Maven JAR /tmp/veypanel-okhttp-binary.rvPGKJ/okhttp-4.12.1.jar (791976 bytes), SHA256 matches committed verification metadata; three relevant class hashes recorded in docs/production-stream-mailbox.md. No JDK on Proxmox. Add bounded verified snapshot and fixed javap evidence CLI, seven synthetic fixtures, Android CI separate manifest-verified report using existing Gradle cache. No library execution, dependency changes, publisher/source correspondence or memory-bound claim. Hold for integration after PR #48; actual javap NOT_RUN until native CI.

## Verified exact OkHttp bytecode
- PR #49 head 1cd4351a908a16f53b1cc66fa0c876fb538352de merged 21ae0810d27d6102c09ad36c510d9bef0b7165fa. Android 45538593486/45538600268, Windows 45538593570/45538600321 all PASS. Downloaded Windows QA 187/187, zero skips, debt 329, checkout 70a100f82d874caaaedf42c93dd68c00dccb57ce tree e83a7f9ef3fb7938c1fe97419158c89fd84ae039. Downloaded static evidence manifest PASS; same source checkout, exact previously observed JAR/class hashes. javap SHA256 466678aea09667809a9967670f6df217b0a75fa8c2f78c4e40885a0c0a2845be.
- Manual review: WebSocketReader.readMessage offset 39 readFully to messageFrameBuffer with frameLength; continuation loop accumulates data. readMessageFrame offsets 47 readMessage, 97 optional inflate, 113 readUtf8, 116 callback; RealWebSocket.onReadMessage offset 16 invokes application listener. MessageInflater.inflate offset 101 readOrInflate with Long.MAX_VALUE, loop based on compressed input consumption. Application text limit is post-assembly, not a preallocation bound. No source-to-binary or publisher provenance claim.
- Next: independent constrained corrupt-selection reconciliation; production transport migration requires trust and fallback qualification. No deployment or hardware approval.

## Corrupt selection reconciliation candidate
- Base 7d97566, dev/corrupt-selection-recovery. Require one trusted staged version, bounded malformed existing state, no prior backup/extra entries/lock; bind original digest and root to dry-run plan. Explicit apply exclusively creates and verifies .selection-corrupt-backup before atomic replacement, verifies readback and payload; no backup deletion or activation. Twelve regressions PASS. Actual isolated root /tmp/veypanel-real-corrupt-repair-owgkzd19 recovered metadata, exact backup retained and full 836-file inventory unchanged. Manual-review exit intentionally retained for backup; never export corrupt bytes. Windows CI prepared, no real user installation modified, private quiescent root assumption. Multi-version, process fencing, physical durability and retention remain open.

## Verified corrupt selection reconciliation
- PR #50 head da9af7872e7f8a01936e783f4dbdb04a74d43ddf merged 788d7a64337a919053767d02e23a7640988a7733. Windows 45541941069/45541947941 PASS, API confirms mandatory explicit corrupt-selection backup, first-install recovery, read-only recovery and Launcher checks.
- Independently downloaded Windows QA/JUnit: 199/199, no skips, exact debt 329, clean checkout 07dced31742028ac981ca7e05b61c7a29c5e7f95 tree 5ed892bdf1d35764d1d8a88a0a216b3c74f150df, no new/stale identities.
- Next: isolated trusted-CA/wrong-SAN qualification of all three client transports; production bounded transport still not selected. User CA on hardware and process fencing remain open.

## Trusted wrong-SAN transport candidate
- Base 0feac5e, dev/transport-wrong-san. Add second isolated emulator phase with same CA, matching CN and wrong IP SAN; three client transports must reject with TLS classification. Negative fixture marks any parsed request, gate requires none. Existing positive/unknown-CA, oversized frame, cancellation and fallback assertions retained. Local OpenSSL identity and observer controls, Bash syntax, Python compilation and exact AST PASS; native emulator mandatory. No production switch, trust bypass or user CA acceptance.

## Verified trusted wrong-SAN transport acceptance
- PR #51 head 1a718dcea58daf6613751cce24430f02268e9f29 merged 73d97b62d8f0b9d2daab5675455fef09ee8bbb02. Windows 45542683025/45542689760, Android 45542682976/45542689764, runtime 45542682969 and reproduction 45542689769, all eight jobs PASS.
- Downloaded actual Windows QA/JUnit: 199/199, zero skips, debt 329, clean checkout a9f74c75b01ffa012bcfd4a534e0c8a12bc614cf tree 1e2aab8aacab45ff8e354f857704b111a72dbe3e, no new/stale entries. Runtime log confirms three trusted wrong-SAN rejections and no application request reached negative fixture.
- Next: integrate TLS classification candidate 2483609 and required Python inventory 43e624b. The registry reconciles prior 199 actual Windows IDs plus eight explicit fixtures; local 207/207. Fresh combined CI mandatory. User-installed CA, Activity-level terminal behavior and preallocation memory mitigation remain open. No production transport change or hardware approval.

## Shared TLS failure classification candidate
- Base 0feac5e, dev/transport-tls-classification. Audit found direct-only SSLException catches in REST/history and unconditional fallback on synchronous WSS constructor RuntimeException. Share existing eight-cause classifier; recognized TLS errors terminal in all four paths, existing denial and ordinary network retry behavior retained. JVM fixture covers wrapped/direct and non-TLS/null/cyclic/depth cases; no message inspection. Hold locally pending PR #51 integration. No native acceptance yet, no production transport switch. Deeper causes and end-to-end Activity fallback/user CA remain open.

## Required Python case inventory candidate
- Base 0feac5e, dev/required-python-case-inventory. Previous gate accepted any nonempty successful discovered subset. Reconcile initial 199 identities with accepted PR #50 Windows JUnit, explicitly add eight registry fixtures (207 required). Strict bounded registry, exact discovery before execution, exact executed PASS verdict, no auto regeneration. case-inventory.json and additive summary fields; missing suite not executed, skip fails. Android workflow triggers updated. Native common QA required; no new AST debt expected. Hold independent candidate while PR #51 runs.

## Combined TLS classification and required QA candidate
- Base main be41a44, integrate 248360911acdb741fa904e4775fdd4005f85e125 and 43e624b79f4746ff94cffd09c87d85edd0d5b44d with merge ancestry. Resolve only documentation conflicts, preserve mandatory TLS SAN and runtime gates, all prior JVM fixtures and new inventory workflow triggers. Combined 207 required cases; fresh native Windows, Android, emulator and APK reproduction CI mandatory.
- Next: verify exact combined CI/JUnit inventory and shared TLS JVM fixture. User CA, Activity-level fallback, pre-allocation WSS memory bound, process fencing and safe uninstall remain open. No deployment, release or physical approval.

## Verified shared TLS classification and required cases
- PR #52 head d31eaf8262c83c3f64413545dd98e31d874430cb merged 35bfe9ca1a529e2ea3836f0a4e751142a07f829f. Windows 45543260057/45543267158, Android 45543259959/45543267283, runtime 45543260051, reproduction 45543267230, all eight CI jobs PASS.
- Independently downloaded Android and Windows QA reports: each 207/207, zero skips, exact required JUnit identities, inventory PASS, debt 329, clean checkout 1d32fcad9a0e34c44bd9aa47c33a7d56671021c8 tree 079b9d92915ad64837b3f134d54c4ffbebac4417. Native client policy fixture step PASS, runtime log confirms trusted wrong-SAN denial and no parsed HTTP requests.
- Next candidate dev/qa-report-verification f250d7f includes 7c0d90d independent report verification and Activity TLS smoke. Local 215/215, verifier and four-file manifest PASS; native CI required. No owner CA, concurrent history, preallocation mitigation, deployment or hardware claim.

## Independent offline QA verification candidate
- Base PR #52 d31eaf8, dev/qa-report-verification. Read-only bounded verifier cross-checks summary, inventory, audit and JUnit with current clean tracked Git commit/tree, reviewed cases and exact baseline. Reject missing/nonpassing/duplicate cases, wrong source, boolean counts, mismatched debt and XML DTD. Eight new explicit fixtures, registry 215. Both Windows/Android common gates verify then write/reopen artifact manifest before successful upload; failed gate evidence remains diagnostic. No native evidence or publisher authentication claim. Hold local pending #52; actual CI required after integration.

## Activity terminal TLS candidate
- On dev/qa-report-verification after 7c0d90d, add androidTest-only reflection admission of synthetic loopback session to actual MainActivity polling. No production changes. Negative phase uses production trust (unknown CA or wrong identity), require terminal UI, one WSS attempt, no fallback/REST errors/samples, cleared session/stream, disabled history, and stable state after 3.5s. Existing trusted wrong-SAN and server no-request checks remain mandatory. Native emulator NOT_RUN locally; no owner CA or concurrent history qualification.

## Verified QA reports and Activity terminal TLS
- PR #53 head ef0495c1a4d7a1e909dfd3eb53f93f725035a9cd merged f473688d3409e69615567a8cfa28605ee9e1679c. Windows 45543711121/45543716791, Android 45543711045/45543716776, runtime 45543711027, reproduction 45543716782; all eight jobs PASS.
- Downloaded actual Android and Windows QA evidence: both four-file manifests verify, independent report verifier PASS, 215/215, exact debt 329, checkout 67ab755b210064177f15d496a5a9b09ad98f6309 tree 2f12b3767592e638d85d3b4d8266fee77396b2a6. Runtime log confirms Activity TLS terminal state with no fallback/retry, three trusted wrong-SAN refusals and no application request on negative fixture.
- Next dev/activity-history-terminal-fence 2f6e18d includes 5d84192 synthetic ordered history/telemetry callback tests and QA subtest identity privacy. Local 219/219, independent validator and manifest PASS, zero unattributed outcomes. Native CI required; no live concurrent socket cancellation or physical user CA claim.

## Activity history terminal fencing candidate
- Base PR #53 ef0495c, dev/activity-history-terminal-fence. Add androidTest-only deterministic ordered callbacks on actual Activity, two fresh instances, positive history delivery, terminal history vs terminal telemetry with both FutureTask fixtures pending, close/cancel and old-generation refusal after same-access synthetic session. Mandatory runtime PASS marker. No production change or network use by this fixture; no live cancellation latency, physical or user CA claim. Native CI pending integration after PR #53.

## QA outcome identity privacy candidate
- On dev/activity-history-terminal-fence after 5d84192, reproduced skipped subTest synthetic canary in EvidenceResult.rows key. Restrict runtime records to admitted parent and reviewed IDs, preserve strongest nonpassing status, count unadmitted fixture outcomes without synthetic JUnit records, require zero unattributed outcomes in gate/verifier. Four explicit new fixtures; registry 219, AST unchanged. General test stdout/stderr isolation remains open. Hold for integration after #53.

## Verified Activity callback fencing and QA privacy
- PR #54 head e41e4cb938d2f5b170a4d28b0132002811be1fad merged 542eb08fd9c2209e1697188e17dcd1ab6b4ad82b. Windows 45544210874/45544219151, Android 45544210886/45544218728, runtime 45544210785, reproduction 45544218746: all eight jobs PASS.
- Independently downloaded both common reports: verified manifest, exact registry and baseline, 219/219, debt 329, zero unattributed outcomes, checkout cb63bb7ded128dd3e9ad01671b1945134b8e53c8 tree 32e6337839aaa221670d60d846a606a27498db9e. Runtime log confirms ordered history/telemetry callback fencing and terminal TLS/no fallback/no HTTP on negative fixture.
- Next: inspect production REST cancellation, qualify explicit owned request lifecycle without changing trust or transport selection. Physical acceptance and process/uninstall gates remain open.

## Explicit Launcher image candidate
- Base main 64e9d0b, dev/launcher-explicit-image. Pass absolute verified Desktop path as explicit subprocess executable and argv[0]; replace second installed-manifest read with bounded identity-checked read. New manifest growth regression; 11/11 Launcher tests and actual isolated package dry-run PASS. Registry expanded explicitly to 220. Hold locally pending #55; native Windows CI required, no live process created.

## Windows process observation candidate
- On dev/launcher-explicit-image after b3a3a01, add PackageProcessObservation.psm1 and read-only CLI Get-PackageProcessObservation.ps1; system-wide fixed Desktop/Host names, count-only output, exit 0 clear observation/2 blocked/1 unavailable. Fixtures cover empty/matching/private fields/invalid/excessive rows; native CI adds observation during existing owned Host smoke and after cleanup. No process mutation, ownership proof, hard provider deadline or lifetime lock. PowerShell/CIM unavailable locally; native NOT_RUN. Publish independently of Android PR #55 and require fresh CI before merge. Full common registry 220; no new AST debt.

## Verified Launcher and Windows process observation
- PR #56 head 3fe959c60d9f01591ced60f8493abc2bffbdf8ee merged e4fb31f69ee82a792924cd2ee46f487ad248c94a; ten jobs PASS, Windows 45545383687/45545391505, Android 45545383785/45545391484, reproduction 45545391204/45545391272. Independently downloaded Windows QA 220/220, manifest and verifier PASS, tree 343fbca85ddd6da5586bcaefc6f20274e50d521b, debt 329. Windows log confirms BLOCKED during owned Host and CLEAR_OBSERVATION after cleanup.
- PR #55 head d212297 remains open: six jobs PASS, runtime confirms real TLS REST drip deadline; second independent APK build 45544928553 failed dependency acquisition HTTP 429, comparison skipped. Requested one failed-job rerun, no dependency or verification change. Integrate with accepted main and require fresh combined-source CI before merge.
- Next: cooperative Desktop session admission, then process lifetime and maintenance fencing. No production activation, destructive operation or hardware acceptance.

## Cooperative Desktop session admission candidate
- Base main 2780d6f, dev/desktop-session-admission. New shared named mutex Local\VeyPanel.Desktop.Interactive.v1; explicit App startup creates MainWindow only after admission, exits 2 if busy and 1 on startup failure, releases on UI-thread exit. Abandoned mutex ownership is not Host cleanup or recovery proof. Native unique-name thread contention and nonowner release fixture wired into Windows CI. Linux common QA only; no .NET SDK locally, native NOT_RUN. Cross-process, WPF interaction, older versions, other sessions and exclusive maintenance not qualified. Keep separate from PR #55 until its required reproduction and combined-source CI are complete.

## Cross-process Desktop admission candidate
- On dev/desktop-session-admission after 9b2b0ff: add separate smoke child dispatch, unique GUID fixture names only, blocked child exit 2 while owned, admitted after release, abandoned owner exit and reacquisition with non-owning kernel handle retained, recovered owner excludes another child. Bounded wait/cleanup for owned synthetic child only. No production mutex, Host or WPF activation. Native .NET SDK unavailable on development server; common QA and exact evidence only. PR #55 updated independently to 9b89fa8 with all original eight jobs PASS after HTTP 429 rerun and fresh combined CI pending.

## Owned Host cleanup-required candidate
- Base PR #57 a4e3b5e, dev/host-cleanup-required. Audit found Running depended on token; failed Stop clears token before confirming process exit, UI then incorrectly reports Stopped/disables Stop. Add serialized state Stopped/Ready/CleanupRequired, retain owned process on unavailable observation, require explicit Stop before Start, deny dashboard, refresh controls after failed Close, finalize disposed only after successful cleanup. Existing lifecycle smoke simulates token loss on its own real Host, requires no replacement, dashboard refusal and explicit Stop/restart. No real OS stop failure injection, WPF interaction, process lifetime fence or destructive operation. Hold until #57 and #55 integration; native NOT_RUN locally.

## Managed Host owner-exit fixture candidate
- On dev/host-cleanup-required after a98759d: existing managed Host Program.cs requests shutdown after stdin EOF. Add isolated real Host owner process smoke, private pipe reports owned identity and awaits supervisor handshake; supervisor retains observed process handle and checks exact expected image/start time before owner exits without Dispose. Require owner and Host zero exit, bounded waits and subsequent process observation. Never kill observed Host by PID; bounded cleanup only directly started fixture owner. Native Windows CI required. No power-loss, actual WPF or production process test. PR #57 native contention/abandonment PASS (five jobs), held while exact integrated #55 runtime 45546707362 executes.
