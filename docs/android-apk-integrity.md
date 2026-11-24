# Android APK artifact integrity preflight

Status: Android CI 45332888028 PASS; Windows CI 45332888086 PASS. The APK remains a **debug-signed**
development artifact, not a production release or an authorized device install.

Each Android CI build must:
1. Pass offline verifier policy tests (success and malformed archive fixtures).
2. Build the debug and instrumentation APKs and pass Android lint.
3. Validate the debug APK's ZIP metadata, entry names, duplicate policy,
   bounded size, essential manifest/DEX/resources files and CRCs.
4. Record SHA-256 of the exact APK file.
5. Require Android SDK apksigner verify --verbose to return success.
6. Publish app-debug.apk, apk-integrity.txt and apk-signing.txt together.

ZIP integrity alone **does not** prove that the signer is trusted or the app
is safe. The debug certificate is generated for development and is not the
production identity. A stable release must have separately owner-approved
signing keys, reproducible metadata, release-channel provenance and upgrade /
uninstall acceptance. No key material should be logged or committed.

## Examples

Run tests and inspect a locally downloaded debug APK:

    python3 -m unittest discover -s scripts -p test_verify_android_apk.py -v
    python3 scripts/verify_android_apk.py veypanel-alpha18/app-debug.apk
    "$ANDROID_HOME/build-tools/35.0.0/apksigner" verify --verbose veypanel-alpha18/app-debug.apk

Download an artifact from the exact GitHub CI run before installation.
Always check the expected package and origin manually, and install only on an
owned Android device. Do not infer hardware capability or app store readiness
from a passing archive/signature check.


Verified debug artifact example: GitHub Actions run 45332888028,
artifact 14893015165. It contains the APK and two text verification reports.
The signature report demonstrates APK Signature Scheme v2 with one signer,
which remains a development/debug signer.

## Packaged identity and permission gate (pending CI)

Android CI additionally records the output of Android Build Tools aapt dump
badging and checks package ID, version code/name, minSdk, targetSdk against the
reviewed app build.gradle. The permissions are explicitly limited to the
reviewed INTERNET and CAMERA permissions only (confirmed in the actual
alpha.18 merged manifest).
Any unexpected merged-manifest permission rejects the build pending human
review. APK badging and identity reports accompany the existing ZIP/SHA256
and signature reports. This does not request device privileges, enable input
injection, grant network exposure or establish trusted release signing.
