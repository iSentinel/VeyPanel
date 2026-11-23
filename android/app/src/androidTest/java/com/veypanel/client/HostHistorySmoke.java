package com.veypanel.client;

import java.time.Instant;
import org.json.JSONArray;
import org.json.JSONObject;

final class HostHistorySmoke {
    private HostHistorySmoke() { }

    static void run() throws Exception {
        Instant now = Instant.parse("2026-11-23T00:00:00Z");
        JSONObject first = new JSONObject().put("timestampUtc", now.minusSeconds(1).toString())
            .put("cpuPercent", 0).put("memoryUsedPercent", JSONObject.NULL).put("diskReadBytesPerSecond", 1024);
        JSONObject next = new JSONObject().put("timestampUtc", now.toString()).put("gpuPercent", 100);
        JSONObject root = snapshot(now, new JSONArray().put(first).put(next));
        MonitorHistory.Point[] points = HostHistory.parse(root.toString(), now);
        check(points.length == 2 && points[0].series(0) == 0 && points[0].series(1) == null
            && points[0].series(5) == 1024 && points[1].series(2) == 100);
        check(HostHistory.parse(snapshot(now, new JSONArray()).toString(), now).length == 0);
        reject(snapshot(now, new JSONArray().put(next).put(first)), now);
        reject(snapshot(now, new JSONArray().put(first).put(first)), now);
        reject(snapshot(now, new JSONArray().put(new JSONObject().put("timestampUtc", now.minusSeconds(900).toString()))), now);
        reject(snapshot(now, new JSONArray().put(new JSONObject().put("timestampUtc", now.plusSeconds(1).toString()))), now);
        reject(snapshot(now.minusSeconds(6), new JSONArray()), now);
        reject(snapshot(now.plusSeconds(6), new JSONArray()), now);
        reject(snapshot(now, new JSONArray()).put("windowSeconds", "900"), now);
        reject(snapshot(now, new JSONArray()).put("windowSeconds", 899), now);
        JSONArray large = new JSONArray();
        for (int i = 0; i < 901; i++) large.put(first);
        reject(snapshot(now, large), now);
        reject(snapshot(now, new JSONArray().put(first.put("cpuPercent", 101))), now);
        reject(snapshot(now, new JSONArray().put(first.put("cpuPercent", "42"))), now);
        reject(snapshot(now, new JSONArray().put(first.put("cpuPercent", 0).put("diskReadBytesPerSecond", -1))), now);
    }

    private static JSONObject snapshot(Instant stamp, JSONArray points) throws Exception {
        return new JSONObject().put("timestampUtc", stamp.toString()).put("windowSeconds", 900).put("samples", points);
    }

    private static void reject(JSONObject root, Instant now) throws Exception {
        try { HostHistory.parse(root.toString(), now); }
        catch (IllegalArgumentException ex) { return; }
        throw new IllegalStateException("Invalid Host history accepted");
    }

    private static void check(boolean valid) {
        if (!valid) throw new IllegalStateException("Host history fixture mismatch");
    }
}
