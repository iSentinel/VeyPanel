# Artifact file manifest and reproducibility preflight

Status: PR #27 merged, both Android and Windows CI pairs passed. Downloaded artifacts independently verified (8 Android, 360 Host, 834 Desktop files).

Android debug, Windows Host and Windows Desktop artifacts will carry
artifact-files.sha256.json: relative file names, byte sizes and SHA-256
hashes of every published regular file, excluding only the root manifest
itself. Android stages the existing eight named files before hashing.
The verifier refuses links, hidden files (which GitHub artifact upload may
omit), ambiguous paths, malformed hashes and mismatched file sets.

    python3 -m unittest discover -s scripts -p test_artifact_manifest.py -v
    python3 scripts/artifact_manifest.py verify downloaded-artifact
    python3 scripts/artifact_manifest.py compare first/artifact-files.sha256.json second/artifact-files.sha256.json

A manifest distributed with the artifact is an integrity inventory, not an
independent trust anchor, signature or proof of source-to-binary provenance.
Comparing complete artifacts may expose legitimate build evidence differences.
Never silently exclude differing files to report a reproducibility PASS.

## Initial actual same-commit comparison

Source commit 8ddb734e87a3bffcc49e2a71750e4068674a7828 (PR #25):

- Android CI 45377626137 and 45377614152: full debug APK SHA-256 differs.
  All 25 ZIP file entries have identical decompressed content hashes,
  no additions or removals. Examined ZIP entry metadata and central directory
  offsets also matched. The signing block and other raw archive bytes have
  not been conclusively isolated; no exact APK reproducibility claim.
- Windows CI 45377626247 and 45377613953: 360 files in each Host artifact;
  356 identical, four changed (VeyPanel.Host.dll, .exe, .pdb and
  .staticwebassets.endpoints.json). No additions or removals. The static
  web asset JSON is not semantically identical. Root causes remain open.

Machine-readable observations are in docs/evidence/pr25-*-repro-comparison.json.
No production signing keys, device installation or display mutation are used.

## Follow-up scope correction

The original PR #25 comparison used matching GitHub workflow headSha values,
not verified checkout SHAs. The PR Windows job 45377626247 actually checked
out synthetic merge abd2c66. Push and PR jobs may therefore compile different
source revision IDs even when trees match. Do not interpret those samples
as a strict same-checkout experiment.

Further inspection found 1027 different APK bytes, all within the identical
4096-byte APK signing blocks at offsets [1782490,1786586). Bytes outside
the blocks matched exactly. Signature validity is a separate apksigner gate.
Windows static asset endpoint differences include Last-Modified timestamps.

## Exact-checkout Android experiment (CI PASS)

The dedicated Android reproduction workflow builds two clean debug APKs on
separate runners, with Gradle build/cache reuse disabled and strict dependency
verification. Both jobs check out the exact workflow SHA, record the actual
commit and tree, and require Android SDK apksigner verification. The comparison
checks those checkout records and then requires exact bytes outside the
validated APK v2 signing blocks, including ZIP headers and central directory.
The signing block boundaries must be equal. It reports full APK equality
separately and does not claim that the comparison validates a signature.

    python3 scripts/compare_apk_payload.py first/app-debug.apk second/app-debug.apk

Six synthetic structural fixtures and the actual PR #25 pair pass locally.
A reproducible debug payload is not a reproducible signed release APK.

### Verified result

Run 45403501445: both builds and comparison PASS. Actual checkout
0c70d781e4dea4e547b2de5ea728ec50800c536e, tree
03b1d9eebedd65606ed081fcea124938c08bf966 matched. The complete APK hashes
were different, while bytes outside the validated signing blocks at
[1782490,1786586) matched exactly. Both APK v2 signatures independently
passed apksigner. Comparison artifact 14924837063.
