# Fail-closed release verification

Status: PR #36 merged; all 14 CI jobs passed, including mandatory negative verification and fresh reproduction experiments.

Implicit GitHub Actions Linux shell invocations used bash -e without
pipefail. A failing verifier followed by tee could therefore return
success. Explicit bash shell selection enables -e -o pipefail on Android
build, runtime, APK reproduction and the Linux Windows/Desktop comparison
steps. Ordinary Windows PowerShell steps retain their existing policy.

The Android build includes an intentionally failing pipeline with
continue-on-error solely for that controlled negative fixture. Its following
step requires the actual step outcome to be failure. Real archive, identity
and signature verification commands must first accept the genuine build and
then reject deliberately invalid fixtures with output captured through tee.
All ordinary gates remain mandatory.

The APK identity policy requires exactly two unconditional permission
declarations: CAMERA and INTERNET. Unknown permission declaration formats,
duplicates, missing declarations and extra permissions fail closed.
APK ZIP paths reject colons and repeated trailing separators.

Prior successful CI outcomes alone do not establish that piped verification
failures propagated. Previously downloaded exact-checkout Android APK
comparison and normalized Host manifest evidence were independently
rechecked. This is not a complete release security audit or signature
provenance claim. The APK ZIP check does not establish redistribution
compliance or physical device acceptance.
