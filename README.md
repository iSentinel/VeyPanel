# VeyPanel

Extend. Monitor. Control.

Windows-to-Android display streaming and independent system telemetry over a local network.

**Status: 0.1.0-alpha.10 development source, not a validated release.** CPU/RAM telemetry and an adaptive browser dashboard are implemented; streaming, virtual displays, native Android, and installers are not yet implemented. An initial WPF display diagnostic UI and a local Apollo inventory CLI are implemented; actual upstream runtime compatibility remains unverified. No Apollo or driver binary is bundled. See [ROADMAP](ROADMAP.md) and [RESUME](RESUME.md).

## Build and run locally (Windows 11)

Install the .NET 10 SDK from https://dotnet.microsoft.com/download/dotnet/10.0, then run from the repository root:

```powershell
dotnet build src/VeyPanel.Host -c Release
dotnet run --project tests/VeyPanel.Smoke -c Release
dotnet run --project src/VeyPanel.Host -c Release
```

Open the local dashboard URL printed by Host, including the fragment token. The owner token changes when the host restarts; do not share terminal output. The token is removed from the browser URL after loading and is kept only in page memory; refreshing requires opening the original link again. Ctrl+C stops Host. The default binds only 127.0.0.1:47860.

## Experimental LAN mode for Lenovo

Optional: obtain a TLS certificate with the actual host IPv4 address in its SAN, trusted by Android. Do not bypass certificate warnings. Certificate provisioning and QR pairing are not implemented. This alpha accepts only explicitly configured RFC1918 IPv4 addresses (10/8, 172.16/12, 192.168/16). Set the actual address, existing PFX path, and PFX password in the launching PowerShell session; keep the password out of scripts and history.

```powershell
$env:VEYPANEL_LAN_IP = '192.168.1.123' # replace with actual host IP
$env:VEYPANEL_PFX = 'C:\certs\veypanel.pfx' # replace with actual path
# Set VEYPANEL_PFX_PASSWORD securely in this process if required.
dotnet run --project src/VeyPanel.Host -c Release
```

Allow TCP 47861 only on the private local network when needed. Enter the printed HTTPS URL in the tablet browser. Do not enable router port forwarding. In default ephemeral mode the initial LAN link receives a separate 256-bit reader token, valid for 24 hours or until revoked/restart. In protected mode use the local owner dashboard to enroll readers. The loopback owner token never authorizes LAN requests. The browser prefers authenticated WebSocket updates once per second and falls back to REST polling automatically. The dashboard is read-only. Clear the LAN environment variables to return to loopback mode. No firewall or certificate settings are automatically changed.

## Target device

Lenovo TB-J607Z, 2000x1200 at 60 Hz; Intel Core Ultra 5 125H / Intel Arc. HEVC with H.264 fallback is the initial streaming test target, not a verified performance result.

## Streaming plan

Use a separately installed, verified Apollo release and its virtual display driver with Moonlight/Artemis. Review the upstream release's supported API and permissions before integrating. Do not reuse existing display configurations or install drivers automatically without a recovery plan. See docs/architecture.md.

## Inspect Apollo (experimental CLI)

Use a separately installed Apollo v0.4.6 and confirm its TLS certificate SHA-256 fingerprint independently from the host's actual certificate file. Do not trust a fingerprint merely presented by the connection. With the verified fingerprint, run:

```powershell
.\VeyPanel.Host.exe --apollo-inspect YOUR_VERIFIED_64_HEX_SHA256
```

The CLI prompts for credentials without echoing the password; they are not persisted. It connects only to HTTPS loopback port 47990, rejects redirects, pins the entire certificate and checks validity dates. Exact pinning is the trust model for Apollo's self-signed certificate; a changed certificate fails closed. Login replaces the active upstream Web UI session. The only subsequent actions are GET inventory calls, with client count and application names printed locally rather than exposing sensitive upstream config through the LAN dashboard. No pairing or topology changes. Physical validation pending.

## Desktop display inventory (read only)

```powershell
.\VeyPanel.Host.exe --display-inventory
.\VeyPanel.Host.exe --display-inventory | Set-Content -Encoding utf8 display-before.json
```

Reports active GDI desktop sources with primary flag, current resolution, coordinates, orientation and refresh when supplied by Windows. Missing fields are null. No active desktop sources returns an explicit non-success status, which is possible in non-interactive sessions.

This is a diagnostic baseline, not a full DisplayConfig topology backup or an automatic rollback file. Cloned outputs may share a source. Do not infer physical monitor count or virtual identity from adapter names. No display settings are changed.

## Active DisplayConfig topology (read only)

```powershell
.\VeyPanel.Host.exe --display-topology
.\VeyPanel.Host.exe --display-topology | Set-Content -Encoding utf8 topology-before.json
```

Captures active paths and mode tables with Windows 11 virtual-mode and virtual-refresh awareness. Supports split mode indices and clone groups. Reports source geometry, target timing, desktop-image region and path flags. Nonzero exit indicates the snapshot is not complete. Adapter LUIDs are session-local, not persistent monitor identities. Source names, monitor paths and connector metadata are included when available; redact hardware identifiers before sharing JSON. Missing identity blocks the internal candidate eligibility policy. A separate validate-only command is available; no topology application or rollback writes are implemented. See [recovery design](docs/display-recovery.md).

## Explicit local Apollo pairing (experimental)

Start the pairing flow on Moonlight or Artemis on a device you physically control. Verify the host certificate fingerprint independently, then run:

```powershell
.\VeyPanel.Host.exe --apollo-pair YOUR_VERIFIED_64_HEX_SHA256
```

Type PAIR, enter Apollo credentials, the device name and the four-digit PIN shown on the tablet. The password and PIN are hidden and not saved; the command makes one pairing request, without automatic retry or permission changes. A successful API response means Apollo accepted the PIN, not that the complete device pairing or streaming works. Verify the device in Apollo and review its permissions (especially the first device). Do not pair untrusted devices. Live acceptance pending; CI uses mock endpoints only.

## Validate the current topology without applying

```powershell
.\VeyPanel.Host.exe --display-validate
```

The command captures two live snapshots, rejects incomplete, ambiguous or changing topology, then asks Windows to validate the current native paths/modes with SDC_VALIDATE only. It checks topology again afterwards. It accepts no imported JSON or caller-provided flags. No SDC_APPLY, persistence or permissive mode changes are implemented. A validated result is not a recovery guarantee. Native validation on the target PC remains untested.

## Windows desktop diagnostic UI

Open VeyPanel.Desktop.exe from the separate desktop CI artifact, or run:

```powershell
dotnet run --project src/VeyPanel.Desktop -c Release
```

The alpha GUI lists desktop sources and active display paths, calls the same guarded validate-only diagnostic, and supports minimize-to-tray. The bundled Desktop package starts/stops its own loopback-only telemetry Host and opens the local browser dashboard. Keep the host subfolder alongside the Desktop executable. It does not install drivers, change displays or provide streaming control yet. Closing Desktop stops its owned Host; an unmanaged existing Host is never terminated. LAN mode remains explicit via standalone Host. It links the same diagnostic source files rather than duplicating the implementation. Compilation/publish and interactive GUI acceptance are separate gates.

## Apollo in Desktop

The Apollo tab provides local inventory and explicit PIN pairing with the same certificate-pinned adapter as the CLI. Credentials/PIN are cleared from inputs and are not persisted. A separate confirmation is required before either login or pairing. Verify device permissions after pairing. No stream start/stop, automatic driver installation or real device acceptance yet.

## Extended monitoring

The dashboard also shows per-active-interface RX/TX byte rates (no IP/MAC or adapter IDs exposed) and fixed local volume capacity/free space. Rates are calculated using monotonic counter deltas; first sample, resets and unavailable counters are N/A. Volume data refreshes every five seconds. These are logical volume capacity metrics, not SSD/NVMe SMART, physical disk I/O or temperatures. The disk I/O panel uses native Windows PDH English counters for system-wide PhysicalDisk(_Total) read/write bytes/sec and read/write operations/sec. Counters require warm-up; unavailable values are N/A, not zero. This is not per-SSD throughput, latency, SMART or NVMe health. Experimental GPU engine telemetry uses Windows PDH, resolves the localized wildcard path, samples current process instances and aggregates each observed adapter/engine across processes. Reports the busiest observed engine across adapters and busiest observed Video Encode / Video Decode engines; absent/invalid samples are N/A. This is not a named Intel Arc metric, not streaming encoder verification, and not GPU temperature or VRAM. Real WDDM GPU validation remains pending.

## Telemetry WebSocket

Connect to `/api/v1/telemetry/ws` on the same listener (ws loopback, wss for LAN). Send the 64-character uppercase token as the first complete text message within five seconds. No query-string tokens. Subsequent messages are read-only server snapshots in the same JSON schema as REST; extra client messages close the connection. Browser origins must match the explicit listener; native clients may omit Origin. Eight total concurrent sockets including pending authentication; excess connections return 503. Browser reconnects with REST fallback. This alpha supports individually revocable in-memory reader grants and a separate loopback owner token. No durable enrollment yet.

CI covers loopback WS and private-interface WSS with a temporary pinned certificate, negative trust tests, origin and query rejection and connection capacity. Browser trust on Android must use a valid trusted certificate; the CI pinning callback is test-only.

## Named graphics adapters

DXGI 1.1 inventory is refreshed every ten seconds, including adapter description, PCI vendor/device IDs, reported dedicated/shared capacity and software flag. PDH observations are grouped by normalized session LUID and matched to DXGI adapters; unmatched observations remain unnamed, idle/unobserved engines are N/A, not fake zero. Capacity is not current memory usage. LUID format and matching on Intel Arc require physical validation. API reference: https://learn.microsoft.com/en-us/windows/win32/api/dxgi/ns-dxgi-dxgi_adapter_desc1 .

## Local storage reliability diagnostic

From a repository checkout on Windows, run `powershell.exe -NoProfile -File scripts/Get-StorageHealth.ps1 -AsJson` (or omit `-AsJson` for a table). It reads provider-visible disks and reliability counters without mutating settings or elevating privileges. Missing/invalid readings are null; zero temperature is conservatively treated as unavailable, while other zeros may be valid provider values. Provider health and wear are reported as supplied and are not an independent SMART/NVMe log-page verdict. No serial or unique identifiers are exported. Unsupported devices or permission failures are explicit. The same diagnostic is bundled with Host and sampled independently by its storage worker; no installer yet. Reference: https://learn.microsoft.com/en-us/powershell/module/storage/get-storagereliabilitycounter .

## Physical disk instance I/O

The additional panel reports Windows PhysicalDisk wildcard instances (excluding _Total), up to 128 rows. Rates and IOPS are joined by exact case-insensitive provider instance name; missing/duplicate values remain N/A. Instance labels may change and may represent virtual or aggregated devices, not stable SSD identifiers. No correlation with reliability counters is inferred. Hosted CI and actual physical storage acceptance are separate.

## Storage health dashboard

The Host invokes the bundled Windows PowerShell diagnostic without elevation or execution-policy bypass, separately from one-second sampling. Each invocation is limited to 20 seconds with bounded output and is repeated 60 seconds after completion. A timestamp older than 150 seconds is stale. Driver/provider or permission failures may leave data unavailable. No serial/unique identifiers or raw command output are included in the API. The health rows are not automatically joined to PDH disk instances.

## Optional CPU/GPU temperatures (experimental)

The default is disabled. If you already run a separately installed, trusted LibreHardwareMonitor v0.9.6-compatible provider, with an existing loopback-only HTTP listener on port 8085 and read access permitted, set `VEYPANEL_LHM_LOCAL=1` before launching Host. The adapter uses only GET http://127.0.0.1:8085/data.json, no redirects/proxy, no credential guessing or configuration changes. Do not enable a LAN listener or disable existing provider authentication to use this alpha; authenticated providers are not supported yet. No provider version handshake is available. The adapter accepts the reviewed v0.9.6 Celsius string shape only, rejects other units and numeric schema, and keeps sensor labels separate. Receipt age is checked, but upstream sample age cannot be verified. No driver or LHM binary bundled. Real sensor acceptance pending.

## Local device enrollment API (experimental)

Only the loopback owner link can administer devices using the owner token as Bearer authorization. On http://127.0.0.1:47860, GET /api/v1/devices lists metadata, POST /api/v1/devices with a JSON body containing name (1–64 characters, Content-Length at most 1024) issues a reader token once, DELETE /api/v1/devices/{id} revokes it. If LAN HTTPS is enabled, issue returns a separate dashboard URL; send it privately to the intended tablet. No secret is returned by list. Up to 32 active grants, fixed 24-hour expiry. By default grants are lost on restart; optional protected Windows storage retains unexpired reader hashes. Reader tokens cannot administer; owner token cannot authenticate via LAN. Active sockets revalidate before each sample; an in-flight sample can still complete. Two-step QR enrollment is available when LAN HTTPS is enabled; optional protected grant persistence is available on standalone Windows Host. Open the local owner Dashboard for reader creation, list and revocation; the panel is hidden unless the local owner API authorizes it. A newly issued secret is displayed temporarily; copy it privately, then clear it. Reader/remote clients cannot use the panel. Treat both URL and token as secrets.

## Two-step reader invitation (alpha.8)

With LAN HTTPS enabled on standalone Host, open its local owner dashboard. Enter a device name, create a two-minute invitation, and scan the locally rendered QR on the intended tablet or share its link privately. On the tablet, open the trusted HTTPS link, accept, and compare the shown code with the PC operator; the operator types that code after Refresh invitations and Compare and approve. On the tablet select Check approval. This issues a reader-only token once. No browser persistence, certificate installation or automatic firewall changes. QR rendering is fully local; see third-party/Codecrete-QrCodeGenerator-LICENSE.txt. Camera scanning is not yet verified. Both invitation and final token expire; restarting Host always invalidates invitations and invalidates readers in default ephemeral mode only. Interactive acceptance pending.

## Optional protected grant persistence (alpha.9)

Windows standalone Host only: `$env:VEYPANEL_PERSIST_GRANTS = '1'; .\\VeyPanel.Host.exe`. The fixed current-user store is `%LOCALAPPDATA%\\VeyPanel-GrantStore-v1`; only encrypted hashes and minimal reader metadata are stored, not owner tokens or invitations. Reader expiry remains 24 hours. With persistence enabled, no automatic initial LAN grant is generated; enroll using the local owner dashboard. Restart keeps unexpired grants. Revoke-all removes all issued readers (outstanding invitations must be cancelled separately). The browser still keeps credentials only in memory; reopening requires a private link or native client. A corrupt/interrupted store prevents Host startup; runtime save failure disables readers and rejects the mutation. Do not restore old store backups. Failed revocation is not acknowledged and if the marker could not be written, previous state may remain on disk; stop using that store until explicitly reset offline. No guarantees against privileged or same-account rollback or sudden power-loss metadata loss. Physical crash/power-loss testing pending.

## Host history

Authenticated GET `/api/v1/history` returns a compact in-memory ring of at most 900 samples from the previous 15 minutes, with CPU/RAM, GPU/codec and aggregate disk rates. No query parameters, no disk persistence, no raw device identifiers. Missing readings remain null. Dashboard Refresh history loads a historical snapshot and plots CPU/RAM/GPU with gaps for missing or delayed samples. Reader revocation applies to this endpoint. History resets on Host restart or detected backward clock jump. Browser interaction remains pending.

History charts support 1/5/15-minute view of the fetched snapshot, including video codecs and disk throughput. Explicit Export full CSV downloads the current bounded Host history, not only the selected chart range. Authenticated GET /api/v1/history.csv, fixed numeric-only schema, UTC, invariant decimals, empty missing readings. No tokens or hardware identifiers exported; export is user initiated and may contain private usage data. CI pending.

## Android Monitor preview

See [android/README.md](android/README.md). Initial native read-only monitor accepts an existing private HTTPS reader link. Latest source also supports pasted two-step invitation links; camera QR scanning, protected credential storage, WSS and video remain pending. Build/debug APK CI is separate from Windows. Do not install unknown certificate authorities or bypass TLS verification.

First verified debug APK: https://github.com/iSentinel/VeyPanel/actions/runs/45067558759/artifacts/14771743918 (development signing key only; no device runtime acceptance).