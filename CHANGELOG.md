# Changelog

## 0.1.0-alpha.4 (development; CI pending)

- Bundle telemetry Host with the Desktop package; start, stop and open local dashboard.
- Managed child uses loopback only, ephemeral tokens, authenticated readiness and stdin EOF shutdown; lifecycle smoke tests cover restart and collision.
- No external Host termination, automatic driver installation or display changes.
- Added Apollo WPF inventory and explicit PIN pairing controls using the shared certificate-pinned adapter.
- Added per-interface network throughput and fixed-volume capacity monitoring with explicit unavailable values and dashboard cards.
- Added native PDH system-total disk read/write throughput and IOPS; unavailable counters remain N/A.
- Added experimental PDH GPU busiest-engine and Video Encode/Decode monitoring with strict grouping and unavailable semantics.

## 0.1.0-alpha.3 (Host CI verified; desktop CI in progress)

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
