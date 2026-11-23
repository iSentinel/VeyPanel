package com.veypanel.client;

import org.json.JSONObject;
import java.time.Instant;

final class TelemetrySample {
    final Instant stamp;
    final Double cpu, ram, gpu, encode, decode, read, write, total, used, readIops, writeIops;
    final String details;

    private TelemetrySample(JSONObject root) throws Exception {
        stamp = SampleRules.timestamp(root.getString("timestampUtc"));
        if (!SampleRules.fresh(stamp, Instant.now())) throw new IllegalArgumentException("Stale sample");
        cpu = SampleRules.percent(root.opt("cpuPercent"));
        ram = SampleRules.percent(root.opt("memoryUsedPercent"));
        JSONObject graphics = root.optJSONObject("gpu");
        gpu = percent(graphics, "busiestEnginePercent");
        encode = percent(graphics, "videoEncodePercent");
        decode = percent(graphics, "videoDecodePercent");
        JSONObject io = root.optJSONObject("diskIo");
        read = rate(io, "readBytesPerSecond");
        write = rate(io, "writeBytesPerSecond");
        readIops = rate(io, "readsPerSecond"); writeIops = rate(io,"writesPerSecond");
        Double capacity = SampleRules.nonnegative(root.opt("memoryTotalBytes"));
        Double available = SampleRules.nonnegative(root.opt("memoryAvailableBytes"));
        total = capacity != null && capacity > 0 && available != null && available <= capacity ? capacity : null;
        used = total == null ? null : total - available;
        details = ResourceDetails.render(root, Instant.now());
    }

    static TelemetrySample parse(String body) throws Exception {
        return new TelemetrySample(new JSONObject(body));
    }
    private static Double percent(JSONObject object, String key) {
        return object == null ? null : SampleRules.percent(object.opt(key));
    }
    private static Double rate(JSONObject object, String key) {
        return object == null ? null : SampleRules.nonnegative(object.opt(key));
    }
}
