# Desktop bundle exact-checkout reproduction

Status: PR #32 merged, exact-checkout reproduction and Windows CI PASS.

The independent Desktop reproduction workflow uses the same actual checkout
commit/tree and pinned .NET SDK on two Windows runners. It publishes the
Host in locked mode with deterministic CI settings and normalizes only
the generated endpoint Last-Modified headers to the source commit epoch.
It runs the Host integration smoke and verifies the Host file manifest.

Desktop is published with ContinuousIntegrationBuild enabled. The complete
verified Host is embedded, the nested Host manifest is rechecked, and the
Desktop bundle's complete file membership, sizes and SHA-256 values are
compared. The source evidence is included. No binary or differing file is
excluded. Runner-specific toolchain and license reports are not generated in
this experimental build, so this is not equality of ordinary CI artifacts.

Interactive WPF launch, physical display topology, tablet input, installer
and Authenticode acceptance remain separate. The workflow does not alter
display topology or launch the Desktop UI on an unattended runner.

Run 45412111245 verified identical checkout 65f5cfc1082bc2deb4c6ef083806ec59c45ab625 and tree e0df7e6d91729adcb6abea6b6aef958a8a33b2b2. All 832 experimental files match. Comparison artifact 14928461490.
