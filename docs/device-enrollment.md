# Device enrollment and trust model

## Current alpha.7
The Host owner token is loopback-only. Per-device reader tokens are random 256-bit secrets; only SHA-256 digests and minimal metadata are retained in RAM. Grants expire after 24 hours, maximum 32; restart invalidates all. Initial LAN access is a separate reader grant, not the owner token. A local owner dashboard can issue, list and revoke grants. REST verifies every request; WS validates the grant before sending each sample (one in-flight frame may complete). A device identity is a label and bearer credential, not proof of physical hardware identity.

## Next: QR enrollment (design only)
- The QR is generated locally on the owner PC without remote services, URLs to third-party QR generators, analytics or external fonts. Review the license, provenance and dependency before bundling an encoder.
- Prefer a short-lived single-use high-entropy invitation over putting a 24-hour reader credential into a QR. Bind it to the specific configured HTTPS origin, maximum lifetime two minutes, cap outstanding invitations, permit explicit cancellation. Generate and view only from authenticated loopback owner UI. Never encode the owner token, Apollo credentials or PFX password.
- The tablet must establish trust in the HTTPS certificate before presenting the secret; no trust-warning bypass. Browser invitation data should be in a URL fragment that is removed from history and submitted over HTTPS in a bounded POST body. Native Android may use a dedicated scanner and an independently verified certificate trust flow.
- Perform atomic one-time redemption with expiry, bounded attempts and no replay, including concurrent requests. Only issue telemetry reader grants. Do not automatically grant input, Apollo, administrative or Windows control privileges. A scanner that sees the invitation first may redeem it, so display an explicit owner pairing confirmation design before enabling enrollment on shared networks.
- Do not log secrets or store raw invitation/reader tokens on the server. Test expiry, concurrent redemption, revocation, foreign origin, wrong host, capacity, invalid certificate and disconnect/reconnect.
- Avoid persistent browser bearer storage. Android should use OS-protected credential storage after explicit enrollment. On the Host, design a versioned minimal hashed-grant store with restrictive ACLs, atomic replacement, bounds, expiry, corruption handling and explicit revoke-all. Do not persist owner credentials or accept arbitrary file paths from the network. Until rollback and recovery tests pass, retain the RAM-only model.

## Acceptance gates
No automatic TLS CA installation, firewall changes, LAN exposure of administrative APIs or hardware configuration changes. QR flow, durable grants and Android credential storage remain unimplemented. Actual Lenovo certificate trust and enrollment must be validated on target hardware.
