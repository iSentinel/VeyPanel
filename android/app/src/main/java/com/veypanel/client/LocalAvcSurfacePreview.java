package com.veypanel.client;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.os.SystemClock;
import android.view.Surface;
import java.nio.ByteBuffer;

/** Decode the original local AVC clip to a caller-owned Surface without networking. */
final class LocalAvcSurfacePreview {
    private static final long BUFFER_TIMEOUT_US = 100_000;
    private static final long MAX_DECODE_MS = 8000;
    private static final String CLIP = "selftest/avc_64x64_2frames.mp4";

    private LocalAvcSurfacePreview() { }

    static int run(Context context, Surface surface) throws Exception {
        if (surface == null || !surface.isValid()) throw new IllegalArgumentException("Surface unavailable");
        try (AssetFileDescriptor asset = context.getAssets().openFd(CLIP)) {
            MediaExtractor extractor = new MediaExtractor();
            try {
                extractor.setDataSource(asset.getFileDescriptor(),
                    asset.getStartOffset(), asset.getLength());
                MediaFormat format = extractor.getTrackFormat(0);
                if (!"video/avc".equals(format.getString(MediaFormat.KEY_MIME)))
                    throw new IllegalStateException("Unexpected AVC fixture");
                extractor.selectTrack(0);
                return decode(extractor, format, surface);
            } finally { extractor.release(); }
        }
    }

    private static int decode(MediaExtractor extractor, MediaFormat format, Surface surface)
            throws Exception {
        MediaCodec codec = MediaCodec.createDecoderByType("video/avc");
        boolean started = false;
        try {
            codec.configure(format, surface, null, 0);
            codec.start(); started = true;
            return render(codec, extractor);
        } finally {
            try { if (started) codec.stop(); }
            finally { codec.release(); }
        }
    }

    private static int render(MediaCodec codec, MediaExtractor extractor) throws Exception {
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        boolean inputEnd = false, outputEnd = false;
        int submitted = 0, rendered = 0;
        long deadline = SystemClock.elapsedRealtime() + MAX_DECODE_MS;
        while (!outputEnd && SystemClock.elapsedRealtime() < deadline) {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException("Preview cancelled");
            if (!inputEnd) {
                int slot = codec.dequeueInputBuffer(BUFFER_TIMEOUT_US);
                if (slot >= 0) {
                    int bytes = enqueue(codec, extractor, slot);
                    if (bytes < 0) inputEnd = true;
                    else submitted++;
                }
            }
            int slot = codec.dequeueOutputBuffer(info, BUFFER_TIMEOUT_US);
            if (slot >= 0) {
                boolean frame = info.size > 0
                    && (info.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) == 0;
                codec.releaseOutputBuffer(slot, frame);
                if (frame) rendered++;
                outputEnd = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
            }
        }
        if (submitted != 2 || rendered < 1 || !outputEnd)
            throw new IllegalStateException("AVC Surface preview incomplete");
        return rendered;
    }

    private static int enqueue(MediaCodec codec, MediaExtractor extractor, int slot) {
        ByteBuffer buffer = codec.getInputBuffer(slot);
        if (buffer == null) throw new IllegalStateException("Missing codec input");
        buffer.clear();
        int bytes = extractor.readSampleData(buffer, 0);
        if (bytes < 0) {
            codec.queueInputBuffer(slot, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM);
        } else {
            codec.queueInputBuffer(slot, 0, bytes, extractor.getSampleTime(), 0);
            extractor.advance();
        }
        return bytes;
    }
}
