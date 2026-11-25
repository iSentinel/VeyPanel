package com.veypanel.client;

/** Deterministic ownership interleavings without Android or a live decoder. */
public final class LocalPreviewLeaseSmoke {
    private LocalPreviewLeaseSmoke() { }

    /** Verify exclusive release responsibility in each ordered interleaving. */
    public static void main(String[] args) {
        LocalPreviewLease queued = new LocalPreviewLease();
        check(queued.destroy(), "Framework releases queued texture");
        check(!queued.acquire() && !queued.finish(), "Late worker refused");

        LocalPreviewLease active = new LocalPreviewLease();
        check(active.acquire() && active.started(), "Worker admitted");
        check(!active.acquire(), "Second worker rejected");
        check(!active.destroy(), "Framework defers active texture");
        check(active.finish(), "Worker releases detached texture");
        check(!active.finish() && !active.destroy(), "No duplicate release");

        LocalPreviewLease completed = new LocalPreviewLease();
        check(completed.acquire(), "Worker admitted before completion");
        check(!completed.finish(), "Attached texture stays with framework");
        check(completed.destroy(), "Framework releases completed texture");
        check(!completed.acquire() && !completed.finish(), "Completed lease cannot reopen");

        LocalPreviewLease untouched = new LocalPreviewLease();
        check(!untouched.started() && !untouched.finish(), "No phantom worker");
        check(untouched.destroy(), "Framework owns unused texture");
        System.out.println("PASS: local preview exclusive texture release ownership");
    }

    private static void check(boolean value, String message) {
        if (!value) throw new IllegalStateException(message);
    }
}
