package com.veypanel.client;

import java.time.Instant;
import java.util.ArrayDeque;

/** Foreground numeric observations only; no disk writes or device identifiers. */
final class MonitorHistory {
    static final int CAPACITY = 900;
    static final int WINDOW_SECONDS = 900;
    static final class Point {
        final Instant stamp;
        private final Double[] values;
        Point(TelemetrySample s) {
            this(s.stamp, new Double[]{s.cpu,s.ram,s.gpu,s.encode,s.decode,s.read,s.write});
        }
        Point(Instant stamp, Double[] values) {
            if (values.length != 7) throw new IllegalArgumentException("History series count");
            this.stamp = stamp;
            this.values = values.clone();
        }
        Double series(int i) { return values[i]; }
    }
    private final ArrayDeque<Point> points = new ArrayDeque<>();
    private Point[] host = new Point[0];

    void replaceHost(Point[] snapshot) {
        if (snapshot.length > CAPACITY) throw new IllegalArgumentException("Host history capacity");
        host = snapshot.clone();
    }

    boolean hasHost() { return host.length != 0; }
    void add(TelemetrySample sample) {
        if (!points.isEmpty()) {
            int order = sample.stamp.compareTo(points.getLast().stamp);
            if (order == 0) return;
            if (order < 0) clear();
        }
        prune(sample.stamp);
        if (points.size() >= CAPACITY) points.removeFirst();
        points.addLast(new Point(sample));
    }
    Point[] read(Instant now) {
        if (!points.isEmpty() && points.getLast().stamp.isAfter(now.plusSeconds(5))) clear();
        prune(now);
        java.util.TreeMap<Instant, Point> merged = new java.util.TreeMap<>();
        Instant start = now.minusSeconds(WINDOW_SECONDS);
        if (host.length != 0 && !host[host.length-1].stamp.isAfter(start)) host = new Point[0];
        for (Point point : host) {
            if (point.stamp.isAfter(now.plusSeconds(5))) { clear(); return new Point[0]; }
            if (point.stamp.isAfter(start)) merged.put(point.stamp, point);
        }
        for (Point point : points) merged.put(point.stamp, point);
        while (merged.size() > CAPACITY) merged.pollFirstEntry();
        return merged.values().toArray(new Point[0]);
    }
    private void prune(Instant now) {
        Instant start = now.minusSeconds(WINDOW_SECONDS);
        while (!points.isEmpty() && !points.getFirst().stamp.isAfter(start)) points.removeFirst();
    }
    void clear() { points.clear(); host = new Point[0]; }
}
