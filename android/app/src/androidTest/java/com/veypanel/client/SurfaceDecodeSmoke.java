package com.veypanel.client;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.graphics.SurfaceTexture;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.Surface;
import java.nio.ByteBuffer;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/** Render the original AVC clip into a detached test Surface, never a remote display. */
final class SurfaceDecodeSmoke {
    private static final long BUFFER_TIMEOUT_US = 100_000;
    private static final long MAX_DECODE_MS = 8000;

    private SurfaceDecodeSmoke() { }

    static void run(Context context) throws Exception {
        // API 26 detached mode avoids requiring a current OpenGL texture/context.
        SurfaceTexture texture = new SurfaceTexture(false);
        CountDownLatch available = new CountDownLatch(1);
        texture.setDefaultBufferSize(64, 64);
        texture.setOnFrameAvailableListener(t -> available.countDown(),
            new Handler(Looper.getMainLooper()));
        Surface surface = new Surface(texture);
        try (AssetFileDescriptor asset = context.getAssets().openFd(
                "selftest/avc_64x64_2frames.mp4")) {
            MediaExtractor extractor = new MediaExtractor();
            try {
                extractor.setDataSource(asset.getFileDescriptor(),
                    asset.getStartOffset(), asset.getLength());
                MediaFormat format = extractor.getTrackFormat(0);
                if (!"video/avc".equals(format.getString(MediaFormat.KEY_MIME)))
                    throw new IllegalStateException("Not original AVC");
                extractor.selectTrack(0);
                decode(extractor, format, surface);
                if (!available.await(2, TimeUnit.SECONDS))
                    throw new IllegalStateException("Surface frame not delivered");
            } finally { extractor.release(); }
        } finally {
            surface.release();
            texture.release();
        }
    }

    private static void decode(MediaExtractor extractor, MediaFormat format, Surface surface)
            throws Exception {
        MediaCodec decoder = MediaCodec.createDecoderByType("video/avc");
        boolean started = false;
        try {
            decoder.configure(format, surface, null, 0);
            decoder.start(); started = true;
            checkOutput(decoder, extractor);
        } finally {
            try { if (started) decoder.stop(); }
            finally { decoder.release(); }
        }
    }

    private static void checkOutput(MediaCodec decoder, MediaExtractor extractor)
            throws InterruptedException {
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        boolean inputEnd = false, outputEnd = false;
        int submitted = 0, rendered = 0;
        long deadline = SystemClock.elapsedRealtime() + MAX_DECODE_MS;
        while (!outputEnd && SystemClock.elapsedRealtime() < deadline) {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException();
            if (!inputEnd) {
                int slot = decoder.dequeueInputBuffer(BUFFER_TIMEOUT_US);
                if (slot >= 0) {
                    int bytes = feed(decoder, extractor, slot);
                    if (bytes < 0) inputEnd = true;
                    else submitted++;
                }
            }
            int slot = decoder.dequeueOutputBuffer(info, BUFFER_TIMEOUT_US);
            if (slot >= 0) {
                boolean frame = info.size > 0
                    && (info.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) == 0;
                decoder.releaseOutputBuffer(slot, frame);
                if (frame) rendered++;
                outputEnd = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
            }
        }
        if (submitted != 2 || rendered < 1 || !outputEnd)
            throw new IllegalStateException("AVC Surface output incomplete");
    }

    private static int feed(MediaCodec decoder, MediaExtractor extractor, int slot) {
        ByteBuffer input = decoder.getInputBuffer(slot);
        if (input == null) throw new IllegalStateException("Missing AVC input");
        input.clear();
        int bytes = extractor.readSampleData(input, 0);
        if (bytes < 0) {
            decoder.queueInputBuffer(slot, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM);
        } else {
            decoder.queueInputBuffer(slot, 0, bytes, extractor.getSampleTime(), 0);
            extractor.advance();
        }
        return bytes;
    }
}
