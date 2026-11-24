package com.veypanel.client;

import android.content.Context;

/** Exercise the exact same decoder path that the owner can run on the tablet. */
final class VideoDecodeSmoke {
    private VideoDecodeSmoke() { }

    static void run(Context context) throws Exception {
        LocalAvcSelfTest.Result first = LocalAvcSelfTest.run(context);
        if (first.frames < 1 || first.codec.isEmpty() || first.elapsedMs > 8000
            || !first.report().contains("Not a video stream"))
            throw new IllegalStateException("AVC self-test output mismatch");
        LocalAvcSelfTest.Result second = LocalAvcSelfTest.run(context);
        if (second.frames < 1 || second.codec.isEmpty())
            throw new IllegalStateException("Decoder cannot reopen cleanly");
    }
}
