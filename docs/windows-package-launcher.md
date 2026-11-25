# Verified-package Desktop launcher

Status: candidate. Python 3.12 and a trusted source checkout are required.
Keep the original portable ZIP, its independently trusted digest, and the
selected version tree in private directories under exclusive owner control.

    python scripts/launch_windows_package.py --root C:\VeyPanel-test --package VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --dry-run
    python scripts/launch_windows_package.py --root C:\VeyPanel-test --package VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --apply

The read-only default resolves the selected version and verifies the full
tree, original archive digest, nested Host identity and equality of the
selected manifest with the archive. This prevents a rewritten selection
record and manifest alone from establishing trust. Apply repeats verification
under the cooperating selection lock, requires native Windows, and starts only
the fixed Desktop executable with the version directory as its working
directory and no shell. The lock is released after process creation; it is
not a lifetime lock. The launcher does not implement single-instance
enforcement, process shutdown, readiness, migration or restart.

Use only independently trusted archives. The portable Alpha ZIP is unsigned;
digest equality is not publisher authentication. Do not bypass platform
security checks or run untrusted binaries. Exclusive owner control is assumed;
a hostile concurrent writer, modified interpreter or malicious environment
is outside the protection boundary. No registry, shortcut, service, driver,
display topology or firewall changes are performed by the launcher itself.

Tests mock the process boundary and verify refusal of corrupt or replaced
payloads. CI runs only a real package dry-run, not interactive WPF activation.
An actual process creation report is not proof of application readiness.
Physical acceptance, process coordination and interrupted-state recovery
remain open.

## Engineering policy integration

Public Python APIs and fixtures comply with the new exact source audit.
CLI failure diagnostics use fixed reason codes instead of raw exception
text. The launch plan contains local paths for the private operator; do not
share that output or capture it in production evidence. CI uses a synthetic
isolated root. Exit code 1 continues to denote validation or execution
failure. Actual interactive activation is not qualified by this change.
