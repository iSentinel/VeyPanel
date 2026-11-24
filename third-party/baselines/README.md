# Resolved component baselines

These component lists are copied from passing build jobs for PR #19
(commit 5da1856c2de303e5b2cc6246fb28cde6db10ecf6), not handwritten guesses:

- Android debug runtime: run 45363566720, veypanel-android-monitor-debug;
  10 resolved Maven modules.
- Windows Host win-x64: run 45363566718, veypanel-host-win-x64-alpha;
  2 resolved NuGet packages.

CI compares the exact set of package URLs, including resolved versions, to
these baselines. Additions, removals and version changes fail CI. To update
a baseline, first review the dependency changes and their provenance,
licenses and security implications, then record a new successful build
inventory in an explicit reviewable change. Do not regenerate it silently.

This is a **post-resolution component drift gate**, not a Gradle/NuGet
native lockfile, artifact hash lock, exhaustive SBOM or security approval.
Build tools, runtime packs, SDKs and license conclusions are not included.
