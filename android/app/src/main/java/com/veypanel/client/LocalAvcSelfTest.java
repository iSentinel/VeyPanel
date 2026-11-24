package com.veypanel.client;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.MediaCodec;
import android.media.MediaCodecInfo;
import android.media.MediaCodecList;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.os.Build;
import android.os.SystemClock;
import java.nio.ByteBuffer;
import java.io.IOException;

/** Decode original, local two-frame AVC without a network, renderer or display change. */
final class LocalAvcSelfTest {
    private static final long TIMEOUT_US = 100_000;
    private static final long MAX_MS = 8000;
    private static final String CLIP = "selftest/avc_64x64_2frames.mp4";

    static final class Result {
        final String codec;
        final Boolean hardware;
        final int frames;
        final long elapsedMs;

        Result(String codec, Boolean hardware, int frames, long elapsedMs) {
            this.codec = codec;
            this.hardware = hardware;
            this.frames = frames;
            this.elapsedMs = elapsedMs;
        }

        String report() {
            String kind = hardware == null ? "N/A (Android API)" :
                hardware ? "Reported hardware" : "Reported software";
            return "Local AVC decode: PASS (synthetic 64x64, 2 frames)\n"
                + "Codec: " + codec + "\nHardware: " + kind
                + "\nDecoded buffers: " + frames + " · Duration: " + elapsedMs
                + " ms\nNot a video stream or sustained 60 FPS test.";
        }
    }

    private static final class Progress {
        int submitted, decoded;
        boolean inputEnd, outputEnd;
    }

    private LocalAvcSelfTest() { }

    static Result run(Context context) throws Exception {
        long startedAt = SystemClock.elapsedRealtime();
        try (AssetFileDescriptor clip = context.getAssets().openFd(CLIP)) {
            MediaExtractor extractor = new MediaExtractor();
            MediaCodec decoder = null;
            boolean started = false;
            try {
                extractor.setDataSource(clip.getFileDescriptor(), clip.getStartOffset(), clip.getLength());
                MediaFormat format = extractor.getTrackFormat(0);
                if (!"video/avc".equals(format.getString(MediaFormat.KEY_MIME)))
                    throw new IllegalStateException("Self-test format mismatch");
                extractor.selectTrack(0);
                decoder = selectDecoder();
                String name = decoder.getName();
                Boolean hardware = hardwareClass(name);
                decoder.configure(format, null, null, 0);
                decoder.start(); started = true;
                int frames = decode(decoder, extractor);
                return new Result(name, hardware, frames, SystemClock.elapsedRealtime() - startedAt);
            } finally {
                try { if (decoder != null) { try { if (started) decoder.stop(); }
                      finally { decoder.release(); } } }
                finally { extractor.release(); }
            }
        }
    }

    private static MediaCodec selectDecoder() throws IOException {
        if (Build.VERSION.SDK_INT >= 29) {
            for (MediaCodecInfo codec : new MediaCodecList(MediaCodecList.REGULAR_CODECS).getCodecInfos()) {
                if (codec.isEncoder() || !codec.isHardwareAccelerated()) continue;
                for (String type : codec.getSupportedTypes()) {
                    if (!"video/avc".equalsIgnoreCase(type)) continue;
                    try {
                        if (codec.getCapabilitiesForType(type).getVideoCapabilities()
                            .areSizeAndRateSupported(64, 64, 30)) return MediaCodec.createByCodecName(codec.getName());
                    } catch (RuntimeException ignored) { /* Try the next available decoder. */ }
                }
            }
        }
        return MediaCodec.createDecoderByType("video/avc");
    }

    private static Boolean hardwareClass(String name) {
        if (Build.VERSION.SDK_INT < 29) return null;
        for (MediaCodecInfo codec : new MediaCodecList(MediaCodecList.REGULAR_CODECS).getCodecInfos())
            if (codec.getName().equals(name)) return codec.isHardwareAccelerated();
        return null;
    }

    private static int decode(MediaCodec decoder, MediaExtractor extractor) throws InterruptedException {
        Progress state = new Progress();
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        long deadline = SystemClock.elapsedRealtime() + MAX_MS;
        while (!state.outputEnd && SystemClock.elapsedRealtime() < deadline) {
            if (Thread.currentThread().isInterrupted()) throw new InterruptedException("Decode cancelled");
            if (!state.inputEnd) enqueue(decoder, extractor, state);
            int output = decoder.dequeueOutputBuffer(info, TIMEOUT_US);
            if (output >= 0) {
                if (info.size > 0 && (info.flags & MediaCodec.BUFFER_FLAG_CODEC_CONFIG) == 0)
                    state.decoded++;
                state.outputEnd = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
                decoder.releaseOutputBuffer(output, false);
            }
        }
        if (state.submitted != 2 || state.decoded < 1 || !state.outputEnd)
            throw new IllegalStateException("Self-test decoder produced no complete frames");
        return state.decoded;
    }

    private static void enqueue(MediaCodec decoder, MediaExtractor extractor, Progress state) {
        int slot = decoder.dequeueInputBuffer(TIMEOUT_US);
        if (slot < 0) return;
        ByteBuffer buffer = decoder.getInputBuffer(slot);
        if (buffer == null) throw new IllegalStateException("Decoder input unavailable");
        buffer.clear();
        int size = extractor.readSampleData(buffer, 0);
        if (size < 0) {
            decoder.queueInputBuffer(slot, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM);
            state.inputEnd = true;
        } else {
            decoder.queueInputBuffer(slot, 0, size, extractor.getSampleTime(), 0);
            state.submitted++;
            extractor.advance();
        }
    }
}
