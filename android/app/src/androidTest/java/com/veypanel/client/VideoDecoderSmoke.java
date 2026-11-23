package com.veypanel.client;

/** Android emulator capability API integration without codec initialization. */
final class VideoDecoderSmoke {
    private VideoDecoderSmoke() { }

    static void run() {
        VideoDecoderSurvey.Entry[] entries = VideoDecoderSurvey.collect();
        if (entries.length > 32) throw new IllegalStateException("Unbounded decoder survey");
        for (VideoDecoderSurvey.Entry entry : entries) {
            if (entry.name == null || entry.name.length() > 96
                || !(entry.mime.equals("video/avc") || entry.mime.equals("video/hevc")
                || entry.mime.equals("video/av01")))
                throw new IllegalStateException("Invalid video capability entry");
        }
        String report = VideoDecoderSurvey.report(entries);
        if (!report.contains("read-only") || !report.contains("not real decoding"))
            throw new IllegalStateException("Missing hardware acceptance warning");
    }
}
