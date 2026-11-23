package com.veypanel.client;

import android.media.MediaCodecInfo;
import android.media.MediaCodecList;
import android.os.Build;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Read-only Android decoder capability survey; never starts a codec or stream. */
final class VideoDecoderSurvey {
    private static final int MAX_DECODERS = 32;

    static final class Entry {
        final String name, mime;
        final Boolean hardware, hd60, fullHd60, tablet60;

        Entry(String name, String mime, Boolean hardware, Boolean hd60,
              Boolean fullHd60, Boolean tablet60) {
            this.name = name;
            this.mime = mime;
            this.hardware = hardware;
            this.hd60 = hd60;
            this.fullHd60 = fullHd60;
            this.tablet60 = tablet60;
        }
    }

    private VideoDecoderSurvey() { }

    static Entry[] collect() {
        List<Entry> entries = new ArrayList<>();
        for (MediaCodecInfo codec : new MediaCodecList(MediaCodecList.REGULAR_CODECS).getCodecInfos()) {
            if (codec.isEncoder()) continue;
            for (String type : codec.getSupportedTypes()) {
                String mime = type.toLowerCase(Locale.ROOT);
                if (!supportedMime(mime)) continue;
                entries.add(describe(codec, type, mime));
                if (entries.size() == MAX_DECODERS) return entries.toArray(new Entry[0]);
            }
        }
        return entries.toArray(new Entry[0]);
    }

    private static boolean supportedMime(String mime) {
        return mime.equals("video/avc") || mime.equals("video/hevc") || mime.equals("video/av01");
    }

    private static Entry describe(MediaCodecInfo codec, String type, String mime) {
        Boolean hardware = Build.VERSION.SDK_INT >= 29 ? codec.isHardwareAccelerated() : null;
        MediaCodecInfo.VideoCapabilities video = null;
        try {
            video = codec.getCapabilitiesForType(type).getVideoCapabilities();
        } catch (RuntimeException ignored) { /* Unsupported capability stays N/A. */ }
        String name = codec.getName();
        if (name.length() > 96) name = name.substring(0, 96);
        return new Entry(name, mime, hardware, supports(video, 1280, 720),
            supports(video, 1920, 1080), supports(video, 2560, 1600));
    }

    private static Boolean supports(MediaCodecInfo.VideoCapabilities caps, int width, int height) {
        if (caps == null) return null;
        try { return caps.areSizeAndRateSupported(width, height, 60); }
        catch (RuntimeException ignored) { return null; }
    }

    static String report(Entry[] entries) {
        StringBuilder text = new StringBuilder("Android video decoder inventory · read-only\n");
        text.append("Declared 60 FPS capabilities, not real decoding or stream acceptance\n");
        if (entries.length == 0) return text.append("No regular AVC / HEVC / AV1 decoder reported.").toString();
        for (Entry entry : entries) {
            text.append(entry.mime).append(" · ").append(entry.name).append("\n")
                .append("Hardware: ").append(label(entry.hardware))
                .append(" · 720p: ").append(label(entry.hd60))
                .append(" · 1080p: ").append(label(entry.fullHd60))
                .append(" · 2560x1600: ").append(label(entry.tablet60)).append("\n");
        }
        if (entries.length == MAX_DECODERS) text.append("Additional codecs may be omitted.\n");
        return text.toString();
    }

    private static String label(Boolean value) {
        return value == null ? "N/A" : value ? "declared yes" : "declared no";
    }
}
