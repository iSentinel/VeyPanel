package com.veypanel.client;

import java.time.Instant;

final class SampleRules {
    private SampleRules() { }
    // Windows DateTimeOffset JSON uses an explicit offset and up to seven fractional digits.
    static Instant timestamp(String value) {
        return java.time.OffsetDateTime.parse(value, java.time.format.DateTimeFormatter.ISO_OFFSET_DATE_TIME).toInstant();
    }

    static boolean fresh(Instant timestamp, Instant now) {
        return !timestamp.isBefore(now.minusSeconds(5)) && !timestamp.isAfter(now.plusSeconds(5));
    }

    static Double percent(Object value) {
        if (!(value instanceof Number)) return null;
        double n = ((Number)value).doubleValue();
        return Double.isFinite(n) && n >= 0 && n <= 100 ? n : null;
    }

    static Double nonnegative(Object value) {
        if (!(value instanceof Number)) return null;
        double n = ((Number)value).doubleValue();
        return Double.isFinite(n) && n >= 0 ? n : null;
    }
}
