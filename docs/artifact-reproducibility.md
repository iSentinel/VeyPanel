# Artifact file manifest and reproducibility preflight

Status: candidate. Ten offline fixtures pass; CI publication not yet accepted.

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
