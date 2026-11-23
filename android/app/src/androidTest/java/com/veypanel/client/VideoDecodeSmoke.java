package com.veypanel.client;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.os.SystemClock;
import java.nio.ByteBuffer;

/** Decode original, low-resolution AVC fixture; never launches a video stream. */
final class VideoDecodeSmoke {
    private static final long TIMEOUT_US = 100_000;
    private static final long TOTAL_MS = 8000;

    private static final class Progress {
        int submitted;
        int decoded;
        boolean inputEnd;
        boolean outputEnd;
    }

    private VideoDecodeSmoke() { }

    static void run(Context context) throws Exception {
        try (AssetFileDescriptor asset = context.getAssets().openFd("avc_64x64_2frames.mp4")) {
            MediaExtractor extractor = new MediaExtractor();
            MediaCodec decoder = null;
            boolean started = false;
            try {
                extractor.setDataSource(asset.getFileDescriptor(), asset.getStartOffset(), asset.getLength());
                MediaFormat format = extractor.getTrackFormat(0);
                if (!"video/avc".equals(format.getString(MediaFormat.KEY_MIME)))
                    throw new IllegalStateException("Unexpected video type");
                extractor.selectTrack(0);
                decoder = MediaCodec.createDecoderByType("video/avc");
                decoder.configure(format, null, null, 0);
                decoder.start(); started = true;
                decode(decoder, extractor);
            } finally {
                if (decoder != null) {
                    if (started) decoder.stop();
                    decoder.release();
                }
                extractor.release();
            }
        }
    }

    private static void decode(MediaCodec decoder, MediaExtractor extractor) {
        Progress state = new Progress();
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        long deadline = SystemClock.elapsedRealtime() + TOTAL_MS;
        while (!state.outputEnd && SystemClock.elapsedRealtime() < deadline) {
            if (!state.inputEnd) enqueue(decoder, extractor, state);
            int output = decoder.dequeueOutputBuffer(info, TIMEOUT_US);
            if (output >= 0) {
                if (info.size > 0) state.decoded++;
                state.outputEnd = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
                decoder.releaseOutputBuffer(output, false);
            }
        }
        if (state.submitted != 2 || state.decoded < 1 || !state.outputEnd)
            throw new IllegalStateException("AVC decode output missing");
    }

    private static void enqueue(MediaCodec decoder, MediaExtractor extractor, Progress state) {
        int index = decoder.dequeueInputBuffer(TIMEOUT_US);
        if (index < 0) return;
        ByteBuffer input = decoder.getInputBuffer(index);
        if (input == null) throw new IllegalStateException("No decoder input buffer");
        input.clear();
        int count = extractor.readSampleData(input, 0);
        if (count < 0) {
            decoder.queueInputBuffer(index, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM);
            state.inputEnd = true;
        } else {
            decoder.queueInputBuffer(index, 0, count, extractor.getSampleTime(), 0);
            state.submitted++;
            extractor.advance();
        }
    }
}
