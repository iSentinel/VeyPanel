package com.veypanel.client;

import android.content.Context;
import android.graphics.SurfaceTexture;
import android.os.Handler;
import android.os.Looper;
import android.view.Surface;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Exercise the production local preview decoder on a detached headless Surface. */
final class SurfaceDecodeSmoke {
    private SurfaceDecodeSmoke() { }

    static void run(Context context) throws Exception {
        SurfaceTexture texture = new SurfaceTexture(false);
        CountDownLatch available = new CountDownLatch(1);
        texture.setDefaultBufferSize(64, 64);
        texture.setOnFrameAvailableListener(t -> available.countDown(),
            new Handler(Looper.getMainLooper()));
        Surface surface = new Surface(texture);
        try {
            int frames = LocalAvcSurfacePreview.run(context, surface);
            if (frames < 1 || !available.await(2, TimeUnit.SECONDS))
                throw new IllegalStateException("Local Surface frame missing");
        } finally {
            surface.release();
            texture.release();
        }
    }
}
