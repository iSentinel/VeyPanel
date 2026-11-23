package com.veypanel.client;

import java.time.Instant;
import org.json.JSONArray;
import org.json.JSONObject;

/** Strict decoder for the bounded, numeric-only Windows Host history response. */
final class HostHistory {
    private static final int MAX_TEXT = 1024 * 1024;
    private static final String[] FIELDS = {"cpuPercent", "memoryUsedPercent", "gpuPercent",
        "videoEncodePercent", "videoDecodePercent", "diskReadBytesPerSecond", "diskWriteBytesPerSecond"};

    private HostHistory() { }

    static MonitorHistory.Point[] parse(String body, Instant now) throws Exception {
        if (body == null || body.length() > MAX_TEXT) throw new IllegalArgumentException("History size");
        JSONObject root = new JSONObject(body);
        Object window = root.opt("windowSeconds");
        if (!(window instanceof Number) || ((Number)window).doubleValue() != MonitorHistory.WINDOW_SECONDS)
            throw new IllegalArgumentException("History window");
        Instant snapshot = SampleRules.timestamp(root.getString("timestampUtc"));
        if (!SampleRules.fresh(snapshot, now)) throw new IllegalArgumentException("Stale history");
        JSONArray samples = root.getJSONArray("samples");
        if (samples.length() > MonitorHistory.CAPACITY) throw new IllegalArgumentException("History capacity");
        MonitorHistory.Point[] data = new MonitorHistory.Point[samples.length()];
        Instant previous = snapshot.minusSeconds(MonitorHistory.WINDOW_SECONDS);
        for (int i = 0; i < data.length; i++) {
            JSONObject record = samples.getJSONObject(i);
            Instant stamp = SampleRules.timestamp(record.getString("timestampUtc"));
            if (!stamp.isAfter(previous) || stamp.isAfter(snapshot))
                throw new IllegalArgumentException("History timestamp order/window");
            data[i] = new MonitorHistory.Point(stamp, decodeValues(record));
            previous = stamp;
        }
        return data;
    }

    private static Double[] decodeValues(JSONObject record) {
        Double[] values = new Double[FIELDS.length];
        for (int i = 0; i < values.length; i++) {
            Object raw = record.opt(FIELDS[i]);
            values[i] = i < 5 ? SampleRules.percent(raw) : SampleRules.nonnegative(raw);
            if (raw != null && raw != JSONObject.NULL && values[i] == null)
                throw new IllegalArgumentException("Invalid history metric");
        }
        return values;
    }
}
