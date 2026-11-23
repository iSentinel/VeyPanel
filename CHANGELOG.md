# Changelog

## Android 0.1.0-alpha.15 (build and emulator runtime PASS; hardware pending)

- Add a read-only, on-demand AVC/HEVC/AV1 decoder survey; never claim hardware decode success from declared capabilities.

## Bounded WebSocket control prototype (CI PASS)

- Validate ping/pong, close codes, sequential samples and read cancellation against isolated TLS fixture. Production Android transport remains OkHttp.

## WSS bounds follow-up (CI PASS)

- Windows Host outbound telemetry cap; Android experimental bounded frame/message parser. Production client integration pending.

## Android 0.1.0-alpha.14 (build, isolated Activity and transport runtime PASS)

- Add foreground connection diagnostic panel with WSS attempts, fallback, REST errors, fresh receipt age and reset on session lifecycle. No endpoints, tokens or exception text are retained.

## Android 0.1.0-alpha.13 (credential and baseline runtime CI PASS; history APK/lint and isolated transport runtime PASS)

- Added isolated Android TLS/WSS transport instrumentation using CI-only certificates and synthetic reader grants. Corrected fixture routing via explicit adb reverse and added host readiness and phase-specific runtime reporting after ConnectException.
- Added Android foreground history and three responsive graphs, explicit Host history refresh, bounded merge and reader authorization fixtures; PR #1 merged.
- Fixed destructive invalid-link handling, scoped saved access invalidation to matching reader, and corrected runtime shell result gate.

## Android 0.1.0-alpha.12 (WSS build CI PASS; responsive UI APK/lint PASS; full CI pending; runtime in progress)

- Added WSS-first foreground telemetry, REST fallback and bounded retry.
- Added responsive monitor cards, collapsible connection controls and resource details.
- Corrected raw instrumentation output gate and added software-emulator fallback when KVM is unavailable; no physical runtime acceptance implied.

## Android 0.1.0-alpha.11 (Keystore build CI PASS; QR CI PASS; runtime in progress)

- Added opt-in AndroidKeyStore protected reader access, local forget and saved reconnect.
- Added local camera QR invitation scanner and isolated Keystore instrumentation source. No automatic background reconnect. Windows version unchanged.

## 0.1.0-alpha.10 (Windows history/CSV CI PASS; Android Monitor APK CI PASS; native invitation CI PASS; hardware acceptance pending)

- Added history range selector, codec/disk charts and authenticated CSV export.
- Added initial native Android Monitor-only app with strict private HTTPS link validation, REST polling and debug APK CI.
- Fixed CI SDK provisioning after initial runner lacked sdkmanager; native JVM fixtures and corrected APK/lint CI passed.
- Added native pasted invitation flow with explicit code comparison and reader-only handoff; camera scanning and protected storage pending.
- Alpha.9 final ACL and reparse fixtures and full CI passed.

## 0.1.0-alpha.9 (protected restart CI PASS; history CI PASS; ACL fixtures PASS; remaining CI in progress; physical acceptance pending)

- Added opt-in persistence groundwork: Windows DPAPI CurrentUser, restrictive directory ACL, exclusive lock, bounded atomic replacement and interrupted transaction refusal. Added opt-in standalone live registry integration, explicit storage status and revoke-all, with registry reopen/failure fixtures. Managed mode remains ephemeral.
- Added isolated published Host restart/revocation/dirty-marker startup integration smoke; fixed explicit InvalidDataException handling in prior fixture and startup.
- Added 15-minute in-memory telemetry history with bounded authorized REST access and dashboard chart; no disk history.
- Added file ACL verification and isolated negative directory/file ACL and symlink fixtures.
- Alpha.8 strict grant codec CI passed.

## 0.1.0-alpha.8 (QR CI verified; grant codec CI in progress; hardware acceptance pending)

- Implemented short-lived one-time invitation API with explicit local owner verification and reader-only redemption.
- Added parallel replay, expiry, cancellation and capacity tests. Added local owner controls, separate tablet enrollment page and HTTPS integration scenario. Added local QR PNG generation with pinned MIT encoder and packaged license. Added strict bounded codec and corruption/expiry/privacy fixtures for the future grant store. Protected disk persistence and live integration not implemented.

## 0.1.0-alpha.7 (thermal CI verified; device API and owner UI CI verified after route fix; hardware acceptance pending)

- Optional local LibreHardwareMonitor read-only thermal adapter with explicit Celsius schema, bounded polling and dashboard.
- Added scoped ephemeral per-device tokens, local-only owner API, expiry/revocation and active WebSocket checks.
- Added local owner dashboard controls for creating, listing and revoking reader access; no QR or persistence yet.
- Documented local-only QR invitation and durable grant trust model; not implemented.
- Alpha.6 storage worker CI passed (provider partial, two rows).

## 0.1.0-alpha.6 (per-disk and worker CI verified; hardening runtime smoke passed; hardware acceptance pending)

- Added per-instance PhysicalDisk PDH throughput and IOPS, bounded merge and dashboard UI.
- Added independent periodic Storage Provider worker, bounded subprocess and schema validation, freshness and health dashboard.
- Explicit UTF-8 provider output and bounded runtime completion probe.
- Reviewed version-specific LibreHardwareMonitor thermal interface; no dependency bundled or thermal adapter implemented.
- Alpha.5 storage diagnostic fixture CI completed successfully.

## 0.1.0-alpha.5 (WS/WSS and DXGI CI verified; storage fixtures passed; hardware acceptance pending)

- Added authenticated local WebSocket telemetry with bounded sessions and browser REST fallback.
- Added loopback and private-NIC WSS integration tests, origin/query rejection, connection capacity and test certificate trust checks.
- Added native DXGI adapter inventory and per-adapter GPU/codec metrics matched by session LUID; unmatched and unavailable values remain explicit.
- Added local Windows Storage Provider reliability probe with sanitized JSON/table output and conversion fixtures; not yet in dashboard.
- GPU alpha.4 CI passed; real Intel Arc monitoring remains unverified.

## 0.1.0-alpha.4 (CI verified; hardware acceptance pending)

- Bundle telemetry Host with the Desktop package; start, stop and open local dashboard.
- Managed child uses loopback only, ephemeral tokens, authenticated readiness and stdin EOF shutdown; lifecycle smoke tests cover restart and collision.
- No external Host termination, automatic driver installation or display changes.
- Added Apollo WPF inventory and explicit PIN pairing controls using the shared certificate-pinned adapter.
- Added per-interface network throughput and fixed-volume capacity monitoring with explicit unavailable values and dashboard cards.
- Added native PDH system-total disk read/write throughput and IOPS; unavailable counters remain N/A.
- Added experimental PDH GPU busiest-engine and Video Encode/Decode monitoring with strict grouping and unavailable semantics.
- Managed lifecycle, Apollo WPF build, network/volume and native PDH disk smoke passed in CI runs 45050593038, 45050643363, 45050707013 and 45050803404. Native disk capability was `ok`. GPU CI: run 45050942800.

## 0.1.0-alpha.3 (Host and desktop CI verified; physical acceptance pending)

- Added read-only Windows 11 CCD topology capture with virtual mode/refresh awareness.
- Added structural validation, JSON export, twelve CCD tests and staged recovery design. No topology changes.
- Added monitor/source identity queries and conservative same-session eligibility policy; no restore writes.
- Added explicit local PIN pairing CLI and five additional Apollo tests; live device validation pending.
- Added fixed-flag SDC_VALIDATE-only CLI and pre/post stability checks; no topology apply or persistence.
- Added initial WPF diagnostic desktop and system tray, with separate self-contained CI publish.
- Host CI run 45049793209 passed 8/8 CPU math, 14/14 Apollo mock and 12/12 CCD tests, published host and HTTPS LAN smoke. Hosted CCD capture was partial. No physical hardware acceptance.

## 0.1.0-alpha.2 (Windows CI verified; hardware acceptance pending)

- Added local Apollo v0.4.6 cookie-authenticated inventory CLI, strict SHA-256 certificate pinning and date validation.
- No redirects, proxy, credential persistence, upstream config writes or LAN admin API.
- Added nine mock protocol and certificate checks; real upstream compatibility remains pending.
- Added read-only desktop source inventory CLI and Windows interop layout/runtime smoke checks.
- Restricted LAN bind to private RFC1918 IPv4 and added automated HTTPS LAN integration and negative TLS tests.
- CI: build and publish PASS; CPU 8/8, Apollo 9/9, Win32 inventory, local host and private-interface HTTPS integration PASS ([run 45047071449](https://github.com/iSentinel/VeyPanel/actions/runs/45047071449)).

## 0.1.0-alpha.1 (source checkpoint; unreleased)

- Proposed VeyPanel architecture and hardware target.
- Implemented Windows CPU and physical RAM sampling with null values on unavailable data.
- Added token-protected REST endpoint, local responsive dashboard, 60-sample history and optional TLS LAN configuration.
- Added CPU math smoke test project and Windows build/publish CI definition.
- Compilation, runtime, security acceptance and physical device tests pending.



- Confirmed full corrected Android runtime smoke and fixed graph selector resource IDs after lint found invalid literal IDs.
