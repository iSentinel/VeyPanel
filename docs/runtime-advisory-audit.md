# Runtime package advisory audit

Status: candidate; first live API snapshot and six offline fixtures passed.
This is a narrowly scoped inventory query, not security approval.

The script queries the public OSV batch API for exact versions in the
reviewed Android and Windows Host component baselines. Only public package
names, ecosystems and versions are sent. No host credentials, device data,
source code or application telemetry are included. The runtime applications
do not call OSV. This is a CI/maintainer operation only.

    python3 -m unittest discover -s scripts -p test_audit_runtime_advisories.py -v
    python3 scripts/audit_runtime_advisories.py \
      third-party/baselines/android-debug.cdx.json \
      third-party/baselines/host-win-x64.cdx.json \
      --output runtime-advisories.json

The JSON report includes UTC collection time and advisory IDs with modified
timestamps for each package. The collector rejects incomplete response
cardinality, unexpected per-item schemas, repeated pagination tokens and
excessive response sizes. Network failures are audit failures, never
interpreted as zero advisories. Successful collection does not mean zero
findings: any returned ID requires separate triage before release.

The initial live snapshot on 2026-11-24 returned zero advisory matches for
12 exact package coordinates (10 Maven and 2 NuGet). That result is
time-dependent and not proof of safety. Build plugins, SDKs, runtime packs,
native binaries, driver components, application vulnerabilities, withdrawn
records and advisory source coverage require separate review. The workflow
runs on relevant changes or manual dispatch, not as an application service.

API reference: https://google.github.io/osv.dev/post-v1-querybatch/
