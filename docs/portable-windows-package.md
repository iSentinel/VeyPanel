# Unsigned portable Windows package

Status: PR #33 merged; Windows CI and independent ZIP reproduction PASS.

The portable ZIP includes the exact verified Desktop publication and nested
Host. It has sorted file names, fixed DOS timestamps, regular-file metadata
and stored (uncompressed) entries, avoiding compression-library-dependent
output. Every entry is checked against the embedded root SHA-256 manifest;
nested Host integrity is verified separately in Windows CI after extraction.
The archive refuses overwrite, unsafe Windows device names, case collisions,
unlisted files and mismatched hashes.

Local examples (Python 3.12):

    python scripts/portable_zip.py write publish-desktop VeyPanel-win-x64-portable.zip
    python scripts/portable_zip.py verify VeyPanel-win-x64-portable.zip

The ZIP is unsigned and is not an installer. Do not run it unless the source
and expected digest are trusted. The embedded manifest and adjacent digest
are integrity evidence, not independent authentication. No administrator
rights, service registration, registry changes, firewall changes, drivers,
or display topology mutations are performed by packaging.

The independent CI experiment compares exact archive SHA-256 for the same
checkout's experimental Desktop bundle. Ordinary CI also publishes a
portable ZIP including its actual evidence reports, whose contents may
differ across runner environments. Installation, upgrade, uninstall,
production signing, interactive WPF and physical device acceptance remain
separate.

Actual ordinary package artifact 14931435132 independently verified (836 files). Experimental same-checkout ZIP hashes match in run 45412991876. Ordinary package SHA-256: 58ea65c2093f2af20924c77250e619d17d464a1f3108da21f83732019d3ef2ce.
