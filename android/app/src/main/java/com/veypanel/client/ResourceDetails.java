package com.veypanel.client;

import org.json.JSONArray;
import org.json.JSONObject;
import java.time.Instant;
import java.util.Locale;

final class ResourceDetails {
    private ResourceDetails() { }

    static String render(JSONObject root, Instant now) {
        StringBuilder text = new StringBuilder();
        JSONObject resources = root.optJSONObject("resources");
        section(text, "Network interfaces", resources, "network", 32, false, now);
        section(text, "Volumes", resources, "volumes", 32, true, now);
        section(text, "CPU / GPU sensors", root.optJSONObject("thermal"), "sensors", 64, true, now);
        section(text, "Storage health", root.optJSONObject("storageHealth"), "disks", 32, true, now);
        return text.toString().trim();
    }

    private static void section(StringBuilder out, String title, JSONObject source, String key,
                                int cap, boolean timed, Instant now) {
        out.append(title).append('\n');
        JSONArray items = source == null ? null : source.optJSONArray(key);
        if (timed && !fresh(source, key, now)) items = null;
        if (items == null || items.length() == 0) { out.append("N/A\n\n"); return; }
        for (int i = 0; i < Math.min(cap, items.length()); i++) {
            JSONObject row = items.optJSONObject(i);
            if (row != null) out.append(line(key, row)).append('\n');
        }
        if (items.length() > cap) out.append("Additional entries omitted\n");
        out.append('\n');
    }

    private static boolean fresh(JSONObject source, String key, Instant now) {
        if (source == null) return false;
        String field = key.equals("sensors") ? "receivedUtc" : key.equals("volumes") ? "storageTimestampUtc" : "timestampUtc";
        long limit = key.equals("sensors") ? 20 : key.equals("volumes") ? 12 : 150;
        try {
            Instant stamp = SampleRules.timestamp(source.getString(field));
            return !stamp.isBefore(now.minusSeconds(limit)) && !stamp.isAfter(now.plusSeconds(5));
        } catch (Exception ex) { return false; }
    }

    private static String line(String key, JSONObject row) {
        if (key.equals("network")) return label(row,"name") + " · RX " + rate(row,"receiveBytesPerSecond")
            + " · TX " + rate(row,"transmitBytesPerSecond");
        if (key.equals("volumes")) {
            Double free = number(row,"freeBytes"), total = number(row,"totalBytes");
            return label(row,"name") + " · " + (free != null && total != null && free <= total
                ? format(free/1073741824, " GiB") + " / " + format(total/1073741824, " GiB") + " free" : "N/A");
        }
        if (key.equals("sensors")) {
            Double value = row.opt("celsius") instanceof Number ? ((Number)row.opt("celsius")).doubleValue() : null;
            return label(row,"category") + " · " + label(row,"hardware") + " · " + label(row,"sensor")
                + " · " + (value != null && Double.isFinite(value) && value >= -50 && value <= 150 ? format(value," °C") : "N/A");
        }
        Double wear = SampleRules.percent(row.opt("wearPercent"));
        Double temp = number(row,"temperatureC");
        return label(row,"model") + " · " + label(row,"providerHealth") + " · "
            + (temp != null && temp >= 1 && temp <= 150 ? format(temp," °C") : "N/A")
            + " · Wear " + format(wear,"%");
    }

    private static String label(JSONObject row, String key) {
        Object value = row.opt(key);
        if (!(value instanceof String)) return "N/A";
        String s = (String)value;
        if (s.isEmpty() || s.length() > 128) return "N/A";
        for (int i = 0; i < s.length(); i++) if (Character.isISOControl(s.charAt(i))) return "N/A";
        return s;
    }
    private static Double number(JSONObject row, String key) { return SampleRules.nonnegative(row.opt(key)); }
    private static String rate(JSONObject row, String key) {
        Double n = number(row,key); return n == null ? "N/A" : format(n/1048576," MiB/s");
    }
    private static String format(Double n, String unit) {
        return n == null ? "N/A" : String.format(Locale.getDefault(), "%.1f%s", n, unit);
    }
}
