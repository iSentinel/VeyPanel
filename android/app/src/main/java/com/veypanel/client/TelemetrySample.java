package com.veypanel.client;

import org.json.JSONObject;
import java.time.Instant;

final class TelemetrySample {
    final Instant stamp;
    final Double cpu, ram, gpu, encode, decode, read, write;

    private TelemetrySample(JSONObject root) throws Exception {
        stamp = Instant.parse(root.getString("timestampUtc"));
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
