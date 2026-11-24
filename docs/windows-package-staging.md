# Windows package preflight and isolated staging

Status: PR #34 merged; both Windows CI passed, actual dry-run and staging verified 836 files. Requires Python 3.12 and the scripts
from a trusted source checkout. This is not an installer or activation tool.

Obtain the expected SHA-256 from an independently trusted channel. An
unsigned ZIP and checksum downloaded together cannot establish authenticity.
Use a new destination under an existing private directory controlled by
the current user; do not stage in a shared or concurrently modified tree.

    python scripts/stage_windows_package.py VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --destination C:\VeyPanel-test\stage --dry-run
    python scripts/stage_windows_package.py VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --destination C:\VeyPanel-test\stage --apply

Dry-run is the default. It verifies the external digest, canonical archive
layout, required Desktop and Host files, matching source identity, exact
nested Host manifest, every archived file hash and available disk space.
Apply additionally writes exclusive files to a newly created directory
and verifies both extracted manifests. Existing destinations are refused.
A failed extraction attempts to remove only the newly created staging
directory. Abrupt process termination can leave incomplete staging;
nothing is automatically activated or launched. The tool assumes the
destination parent and package are under the maintainer's exclusive control.

The tool does not register services, modify system settings, create shortcuts,
install drivers, stop existing processes or switch active versions. It does
not verify Authenticode or signed provenance. Activation, transaction recovery,
upgrade/rollback and uninstall remain later steps. Never launch an unsigned
package merely because its embedded manifests match.
