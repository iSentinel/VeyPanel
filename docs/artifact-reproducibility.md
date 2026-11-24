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
