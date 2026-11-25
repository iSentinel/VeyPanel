package com.veypanel.client;

/** Coordinate framework texture release and a single decoder worker. */
final class LocalPreviewLease {
    private boolean acquired;
    private boolean active;
    private boolean destroyed;

    /** A queued worker must not acquire a texture that was already destroyed. */
    synchronized boolean acquire() {
        if (destroyed || acquired) return false;
        acquired = true;
        active = true;
        return true;
    }

    /** True only when the decoder has actually entered the worker. */
    synchronized boolean started() { return acquired; }

    /** True delegates release to TextureView; false transfers it to the worker. */
    synchronized boolean destroy() {
        if (destroyed) return false;
        destroyed = true;
        return !active;
    }

    /** True means the worker must release the detached texture exactly once. */
    synchronized boolean finish() {
        if (!active) return false;
        active = false;
        return destroyed;
    }
}
