# Dependency and redistribution preflight

Status: Android CI 45334220672 PASS for license packaging; not full dependency or
license acceptance for a production release.

## Reviewed direct dependencies

Android Gradle direct dependencies use strict versions:
- ZXing Android Embedded 4.3.0 (Android app QR capture).
- ZXing Core 3.5.3 (QR data decoding).
- OkHttp 4.12.1 (established HTTPS/WSS transport).

The app source includes the license/notice assets for all three families and
an explanatory third-party README. A published alpha.18 debug APK was
inspected; all five files survived packaging, along with the OkHttp
public-suffix NOTICE. The offline APK verifier now explicitly requires the
five app-supplied documents, so packaging regressions fail CI.

Windows Host (net10.0) has exact PackageReference versions:
- System.Security.Cryptography.ProtectedData 10.0.15.
- Net.Codecrete.QrCodeGenerator 3.2.1; MIT license bundled with Host publish.

Host uses NuGetAudit=true, NuGetAuditMode=all, and treats NU1903 and NU1904
as build errors. These are existing safeguards, not a substitute for a
complete release dependency audit.

## Remaining blockers

- No Gradle dependency lockfile or fully resolved SBOM is committed.
- No NuGet packages.lock.json or complete transitive SBOM is committed.
- Review actual transitive component licenses/notices and vulnerability
  advisory snapshots for the target release.
- Establish reproducible production dependency resolution and independently
  owner-approved signing/release provenance.
- Validate installed artifacts on owned Windows and Lenovo TB-J607Z hardware.

No library version, device setting, driver or runtime permission changes were
made by this preflight.

## Scoped resolved component inventories (CI PASS)

Android CI records the selected debugRuntimeClasspath modules. Windows CI
reads the restored win-x64 Host package target after publish. Both produce
runtime-components.cdx.json (CycloneDX 1.5), sorted by package URL, beside
their application artifacts. This is an inventory, not an exhaustive release
SBOM: build plugins, Android SDK, .NET runtime packs, dependency edges,
file hashes, license conclusions and advisory results are out of scope.
Use the recorded versions as inputs to subsequent lockfile and review gates.
