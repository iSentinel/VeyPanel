# VeyPanel

Extend. Monitor. Control.

Windows-to-Android display streaming and independent system telemetry over a local network.

**Status: 0.1.0-alpha.1 source prototype, not a validated release.** CPU/RAM telemetry and an adaptive browser dashboard are implemented; streaming, virtual displays, WPF, native Android, WebSocket, GPU sensors, and installers are not yet implemented. No Apollo or driver binary is bundled. See [ROADMAP](ROADMAP.md) and [RESUME](RESUME.md).

## Build and run locally (Windows 11)

Install the .NET 10 SDK from https://dotnet.microsoft.com/download/dotnet/10.0, then run from the repository root:

```powershell
dotnet build src/VeyPanel.Host -c Release
dotnet run --project tests/VeyPanel.Smoke -c Release
dotnet run --project src/VeyPanel.Host -c Release
```

Open the local dashboard URL printed by Host, including the fragment token. The token changes when the host restarts; do not share terminal output. The token is removed from the browser URL after loading and is kept only in page memory; refreshing requires opening the original link again. Ctrl+C stops Host. The default binds only 127.0.0.1:47860.

## Experimental LAN mode for Lenovo

Optional: obtain a TLS certificate with the actual host IPv4 address in its SAN, trusted by Android. Do not bypass certificate warnings. Certificate provisioning and QR pairing are not implemented. Set the actual address, existing PFX path, and PFX password in the launching PowerShell session; keep the password out of scripts and history.

```powershell
$env:VEYPANEL_LAN_IP = '192.168.1.123' # replace with actual host IP
$env:VEYPANEL_PFX = 'C:\certs\veypanel.pfx' # replace with actual path
# Set VEYPANEL_PFX_PASSWORD securely in this process if required.
dotnet run --project src/VeyPanel.Host -c Release
```

Allow TCP 47861 only on the private local network when needed. Enter the printed HTTPS URL in the tablet browser. Do not enable router port forwarding. The API requires a per-process 256-bit token. This prototype polls once per second; it does not use WebSocket yet. The dashboard is read-only. Clear the LAN environment variables to return to loopback mode. No firewall or certificate settings are automatically changed.

## Target device

Lenovo TB-J607Z, 2000x1200 at 60 Hz; Intel Core Ultra 5 125H / Intel Arc. HEVC with H.264 fallback is the initial streaming test target, not a verified performance result.

## Streaming plan

Use a separately installed, verified Apollo release and its virtual display driver with Moonlight/Artemis. Review the upstream release's supported API and permissions before integrating. Do not reuse existing display configurations or install drivers automatically without a recovery plan. See docs/architecture.md.
