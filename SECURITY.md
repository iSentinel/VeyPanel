# VeyPanel security boundaries

Alpha, not security-certified. Report vulnerabilities privately through a
maintainer-approved channel; do not post secrets or live exploit evidence
in public issues. No release, lab mutation or external publication approval
is implied by this document.

- Host defaults to HTTP loopback; explicitly configured RFC1918 LAN IPv4
  requires trusted TLS and separate reader authority. Owner administration
  remains loopback-only. Never bypass certificate or platform verification.
- Tokens and invitation links are private user-facing secrets. No query
  string tokens, raw authorization or private endpoints in shared logs.
  Per-device grants are revocable; optional standalone Windows DPAPI store
  and Android Keystore have scoped guarantees, not anti-rollback or
  privileged-adversary guarantees.
- Telemetry is read-only. Missing observations remain null/N/A. Do not
  enable internet exposure, firewall rules, remote input or unreviewed drivers.
  Display topology changes require a prior snapshot and qualified rollback.
- Package verification assumes trusted external hashes, a trusted maintenance
  interpreter and exclusive owner control of private package directories.
  Unsigned portable artifacts and local manifests are not publisher
  authentication. No automatic orphan deletion or lock clearing. Uncertain
  writes require reconciliation; physical durability is not established.
- Routine CI uses synthetic/local fixtures and scoped dependency/advisory
  access; no production credentials or live targets. Live lab, fault,
  destructive and hardware acceptance require separate review and approval.
- Keep third-party licenses and notices, exact locks and scoped advisory
  evidence. No automatic bumps or unreviewed redistribution.
- Open risk register: docs/engineering-adoption-audit.md and ROADMAP.md.
  Native UI, physical tablet/Windows, streaming/input, signing, full
  security audit and crash recovery are not release-qualified.
