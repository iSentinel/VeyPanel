# Changelog

## 0.1.0-alpha.3 (development; CI pending)

- Added read-only Windows 11 CCD topology capture with virtual mode/refresh awareness.
- Added structural validation, JSON export, twelve CCD tests and staged recovery design. No topology changes.
- Added monitor/source identity queries and conservative same-session eligibility policy; no restore writes.
- Added explicit local PIN pairing CLI and five additional Apollo tests; live device validation pending.
- Added fixed-flag SDC_VALIDATE-only CLI and pre/post stability checks; no topology apply or persistence.
- Added initial WPF diagnostic desktop and system tray, with separate self-contained CI publish.

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
