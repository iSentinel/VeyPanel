# Upstream review-only baseline

Observed 2026-11-25 06:07–06:09 UTC via authenticated GitHub metadata API.
This is the first recorded watch baseline, status REVIEW for every row.
Repository and release identity are observations, not an endorsement,
dependency pin, redistribution permission or release approval.

| Repository | Role | Default branch HEAD | Latest published release / ID | Release commit | Reported license |
|---|---|---|---|---|---|
| ClassicOldSong/Apollo | External streaming host / virtual display | master adc5c5a0bd80831ce495434bb16aee2cd4175fb8 | v0.4.6 / 232074361 | 0cd32abaaa141d262477d039ac447b38fe99c394 | GPL-3.0 |
| moonlight-stream/moonlight-android | External Android client reference | master b48494cb96bff23d8886c4775cc4f39a1075495d | v12.2 / 387680237 | b48494cb96bff23d8886c4775cc4f39a1075495d | GPL-3.0 |
| itkawa/screen-spawner | Display lifecycle reference | main 5951f8090858c226e70ab22c3d615ff91db0f619 | v0.3.2 / 454820983 | 5951f8090858c226e70ab22c3d615ff91db0f619 | GPL-3.0 |
| LibreHardwareMonitor/LibreHardwareMonitor | External thermal provider reference | master 9e2d677cefff5c614ecc38da88fbc447eb478e2a | v0.9.6 / 286366766 | 3d331e3370efb858411f19511373eff65a218701 | MPL-2.0 |

All four repository metadata queries succeeded and reported nonarchived
repositories. The release tag refs were direct commit objects; the commits
endpoint corroborated each exact SHA. Apollo and LibreHardwareMonitor HEAD
differ from their documented release tags; no code delta review is implied.
Latest published release is not necessarily the newest tag or prerelease.
No independent signature, binary, asset, license-text or provenance audit
was performed during this observation. Artemis is named as a possible
external client in README but no exact upstream repository was identified
in the canonical architecture references; its watch entry remains unresolved.

## Candidate follow-up

Screen Spawner v0.3.2 (2026-11-22T23:14:11Z) release notes describe a
GNOME mirror-mode reconnection fix. Add a Windows-specific reconnect
and restore test design before any display topology changes. The upstream
test report is not a VeyPanel hardware result. No code or binary adoption.

## Repeat observation

Use GitHub repository metadata, default branch commit, latest release
metadata and exact tag target:

    gh api repos/OWNER/REPO
    gh api repos/OWNER/REPO/commits/DEFAULT_BRANCH
    gh api repos/OWNER/REPO/releases/latest
    gh api repos/OWNER/REPO/git/ref/tags/TAG
    gh api repos/OWNER/REPO/commits/TAG

For an annotated tag, resolve its object to the commit and corroborate.
Review HEAD, release ID/tag and exact release commit against this baseline.
Use REVIEW for changes, UNCHANGED only when all required observations match,
ERROR for incomplete or failed required queries. Missing latest release
does not prove absence of tags. Do not automatically update pins, adopt
code/assets or install packages. Automated periodic watch and structured
report validation are separate unfinished work.
