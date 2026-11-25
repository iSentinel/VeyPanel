# Upstream integration checkpoint

PR #72 merged fff1cfa3e7642a875832141ca2e1de94c5d0111e; tree
700712da898744ce7db5c7f290a700fddc63e10e matches independently verified
synthetic 1520e457bb80f160b8d72aca9991aada675ac4c1. Windows 45563461358
and Android 45563461386 QA 286/286, manifests and source-bound verifier PASS;
both push checks PASS. Gateway control API returned error after actual merge;
GitHub state and main tree were reconciled before further mutation.

PR #73 original head 70cf3fa: Windows 45563627439/45563621335 and Android
45563627242/45563621303 all PASS. Both PR reports independently verified
294/294 against synthetic 18dde21ef153de7bea4505a96fc3b9f236e0af90,
tree e58b914f19e8101076f427856c9d986f5d654b33, debt329. After retargeting
onto main, fresh integrated CI is required. No network or release change
in the normalization candidate. Next independent step is the bounded
public HTTPS collector, not dependency adoption.
