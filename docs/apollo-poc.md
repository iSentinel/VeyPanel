# Apollo integration PoC

## Reviewed baseline

- Apollo v0.4.6: https://github.com/ClassicOldSong/Apollo/releases/tag/v0.4.6
- Official release asset Apollo-0.4.6.exe; GitHub asset SHA-256: `42b2aefaacb3474511517a56b96ee9f0517f30ac38b5dd2fda9fd5b478f5021a`.
- GPL-3.0 upstream; no installer, code or drivers redistributed here.
- API source: https://github.com/ClassicOldSong/Apollo/blob/v0.4.6/src/confighttp.cpp
- Documentation: https://github.com/ClassicOldSong/Apollo/blob/v0.4.6/docs/api.md
- README: https://github.com/ClassicOldSong/Apollo/blob/v0.4.6/README.md

Pinned for source review and compatibility experiments, not a security endorsement. Check upstream security notices and installer provenance before installation. Do not disable Secure Boot or signature enforcement.

## API findings

The documentation says Basic authentication, but the tagged source actually implements POST /api/login with JSON username/password, followed by an `auth` cookie (Secure, SameSite=Strict). Authenticated handlers check origin, cookie and expiry. A new login replaces the server-side session cookie; avoid repeated automatic logins that disrupt an operator session.

Candidate endpoints: GET /api/apps, GET /api/clients/list, GET /api/config, POST /api/pin, POST /api/clients/update, POST /api/clients/disconnect. All future writes require a narrowly scoped UI operation and confirmation where disruptive. Do not expose Apollo credentials or its session cookie to the telemetry client. Use loopback TLS with explicit verified certificate trust; never disable TLS validation. Store credentials only with user consent in OS-protected credential storage. Initial client adapter is not implemented yet.

Apollo grants the first paired device full permissions by default; inspect and restrict permissions to the intended streaming/input capabilities. No UPnP or WAN exposure for the VeyPanel use case.

## Read-only preflight

From the source checkout in Windows PowerShell:

```powershell
pwsh -File scripts/Invoke-ApolloPreflight.ps1
pwsh -File scripts/Invoke-ApolloPreflight.ps1 -InstallerPath C:\Downloads\Apollo-0.4.6.exe
```

Optional catalog verification: pass `-DriverCatalogPath` for a separately located catalog. Hash equality and a valid Authenticode signature are preliminary checks, not proof of publisher identity, driver package integrity or compatibility. Inspect publisher and catalog membership independently. The preflight reports GPU names and desktop bounds, not verified Quick Sync capability or actual display modes.

## Hardware acceptance matrix (all pending)

| ID | Procedure | PASS criteria |
|---|---|---|
| VP-01 | Capture existing display layout; record resolution, refresh, primary and coordinates | Baseline retained for rollback |
| VP-02 | Install verified upstream package only after owner approval; inspect Device Manager | No driver warning or physical monitor disruption |
| VP-03 | Pair Moonlight/Artemis via local PIN, H.264 first, SDR | Stable authenticated stream |
| VP-04 | Mirror selected physical monitor | Correct content, no topology changes |
| VP-05 | Launch virtual display at custom 2000x1200, 60 Hz | Windows recognizes extra monitor; window moves to tablet; verify full-area display |
| VP-06 | Switch to HEVC and set initial 20 Mbps | GPU Video Encode active; tablet hardware decoding; measure dropped frames and latency |
| VP-07 | Touch, drag and rotate if supported | Correct coordinates, no events on wrong display |
| VP-08 | Disconnect, reconnect, sleep/wake | Physical display layout restored; no stranded windows or orphan virtual monitors |
| VP-09 | Remove upstream software in test environment | Original topology and primary monitor remain functional |

Do not mark PASS using only GitHub-hosted runners. The actual Intel Core Ultra 5 125H and Lenovo TB-J607Z are required. If native resolution fails, test 1500x900 at 30 Hz as fallback, then isolate host/client limitations.
