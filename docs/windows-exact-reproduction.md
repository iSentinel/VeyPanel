# Windows Host exact-checkout reproduction experiment

Status: candidate, not normal publication policy.

PR #25 comparisons found four different Host files but compared PR and
push jobs, whose actual Git checkout IDs were not equal. The static endpoint
JSON differed only in 50 Last-Modified values, corresponding to source and
compressed file timestamps. Replacing those values with the same explicit
epoch in diagnostic copies produced byte-identical JSON.

The separate Windows reproduction workflow publishes the Host twice on
independent Windows runners with identical explicit checkout commit/tree,
pinned SDK, locked NuGet packages and ContinuousIntegrationBuild enabled.
It saves raw file inventories and original static endpoint JSON before any
normalization. For the experimental normalized output only, existing
Last-Modified headers are set to the actual source commit timestamp. Routes,
asset paths, ETags, integrity, lengths, encodings and all other values remain
unchanged. Both publications are smoke tested. The comparison publishes raw
differences, and requires every normalized file hash and path to match.
It never silently excludes binaries or raw differences from evidence.

The existing ordinary Windows publication workflow is unchanged. Adoption
of the normalization policy requires a successful experiment and review of
cache semantics, installer behavior and release provenance. Desktop binaries,
Authenticode and complete reproducible release packaging remain separate.

    python3 -m unittest discover -s scripts -p test_normalize_static_endpoints.py -v
    python3 scripts/normalize_static_endpoints.py PATH_TO_EXPERIMENTAL_MANIFEST --epoch SOURCE_COMMIT_EPOCH
