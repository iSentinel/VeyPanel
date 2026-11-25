# Collector integration checkpoint

PR #73 merged ae45f88e555b3776f6cc5e4562db3ca61c2b640b after all four
integrated Windows/Android jobs PASS. Downloaded Windows 45564483722
and Android 45564483839 reports independently verified 294/294, exact
synthetic 8368c2c262fc3009c96dd614a63d1c89287772bb tree
584435bdcac8bbac1eb76cdf6dfc26739d999694. The merged main tree is identical.

PR #74 original stacked source dbefce1: Windows 45564542907/45564535410
and Android 45564542878/45564535299 all PASS. Both PR QA reports independently
verified 302/302 against synthetic 56c2ba7872b3f4bf79ee8bcb62eef7880aa949a1,
tree 1c5ba8df7794bacdf1659a4e2a5415a91d94330a, debt329. Retargeted to main;
fresh integrated CI is mandatory. No dependency or release changes.
