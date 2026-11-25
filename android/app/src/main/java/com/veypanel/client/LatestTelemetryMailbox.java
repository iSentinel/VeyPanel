package com.veypanel.client;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLException;

/** One latest sample with atomic terminal state and monotonic freshness. */
final class LatestTelemetryMailbox<T> {
    private T latest;
    private long received;
    private boolean closed;
    private boolean tlsFailed;
    private boolean reading;

    /** Publish only while open; replace rather than queue older samples. */
    synchronized void offer(T sample, long receivedNanos) {
        if (closed) return;
        if (sample == null) throw new IllegalArgumentException("Missing sample");
        latest = sample;
        received = receivedNanos;
        notifyAll();
    }

    synchronized boolean isClosed() { return closed; }

    /** Preserve the first terminal cause and wake an admitted reader. */
    synchronized void close(boolean tls) {
        if (closed) return;
        closed = true;
        tlsFailed = tls;
        latest = null;
        notifyAll();
    }

    /** Wait within a bounded budget; reject stale samples and concurrent readers. */
    synchronized T take(long waitMillis, long maxAgeMillis)
            throws IOException, InterruptedException {
        if (waitMillis <= 0 || waitMillis > 60000 || maxAgeMillis <= 0 || maxAgeMillis > 60000)
            throw new IllegalArgumentException("Invalid mailbox budget");
        if (reading) throw new IOException("Concurrent stream read");
        reading = true;
        try {
            return awaitSample(TimeUnit.MILLISECONDS.toNanos(waitMillis),
                TimeUnit.MILLISECONDS.toNanos(maxAgeMillis));
        } finally { reading = false; }
    }

    private T awaitSample(long budget, long maxAge) throws IOException, InterruptedException {
        long start = System.nanoTime();
        while (!closed) {
            if (Thread.interrupted()) throw new InterruptedException();
            long now = System.nanoTime();
            long remaining = budget - (now - start);
            if (remaining <= 0) break;
            if (latest != null) {
                T sample = latest;
                latest = null;
                long age = now - received;
                if (age >= 0 && age <= maxAge) return sample;
            }
            TimeUnit.NANOSECONDS.timedWait(this, remaining);
        }
        if (tlsFailed) throw new SSLException("WSS TLS rejected");
        throw new IOException("WSS unavailable");
    }
}
