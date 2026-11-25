package com.veypanel.client;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import javax.net.ssl.SSLException;

/** Exercise the production mailbox without network access or device secrets. */
public final class LatestTelemetryMailboxSmoke {
    private LatestTelemetryMailboxSmoke() { }

    /** Check replacement, local age, terminal cause, cancellation and reader admission. */
    public static void main(String[] args) throws Exception {
        latestAndAge();
        terminalCause();
        waitingReader();
        System.out.println("PASS: production WSS latest mailbox lifecycle and freshness");
    }

    private static void latestAndAge() throws Exception {
        LatestTelemetryMailbox<String> mailbox = new LatestTelemetryMailbox<>();
        mailbox.offer("old", System.nanoTime());
        mailbox.offer("new", System.nanoTime());
        check("new".equals(mailbox.take(100, 5000)), "Latest value");
        mailbox.offer("stale", System.nanoTime() - TimeUnit.SECONDS.toNanos(10));
        expectIo(mailbox, false);
        mailbox.offer("fresh", System.nanoTime());
        check("fresh".equals(mailbox.take(100, 5000)), "Fresh after stale");
        mailbox.close(false);
        mailbox.offer("late", System.nanoTime());
        expectIo(mailbox, false);
    }

    private static void terminalCause() throws Exception {
        LatestTelemetryMailbox<String> tls = new LatestTelemetryMailbox<>();
        tls.close(true);
        tls.close(false);
        expectIo(tls, true);
        LatestTelemetryMailbox<String> cancelled = new LatestTelemetryMailbox<>();
        cancelled.close(false);
        cancelled.close(true);
        expectIo(cancelled, false);
    }

    private static void waitingReader() throws Exception {
        LatestTelemetryMailbox<String> mailbox = new LatestTelemetryMailbox<>();
        AtomicReference<Throwable> result = new AtomicReference<>();
        Thread reader = new Thread(() -> {
            try {
                mailbox.take(5000, 5000);
                result.set(new AssertionError("Closed reader returned sample"));
            } catch (Throwable failure) { result.set(failure); }
        });
        reader.setDaemon(true);
        reader.start();
        try {
            long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
            while (reader.getState() != Thread.State.TIMED_WAITING && System.nanoTime() < until)
                Thread.sleep(1);
            check(reader.getState() == Thread.State.TIMED_WAITING, "Reader waiting");
            expectIo(mailbox, false);
            check(reader.isAlive(), "Second read did not cancel first");
            mailbox.close(false);
            reader.join(1000);
            check(!reader.isAlive() && result.get() instanceof IOException, "Close woke reader");
        } finally {
            mailbox.close(false);
            reader.interrupt();
            reader.join(1000);
        }
    }

    private static void expectIo(LatestTelemetryMailbox<String> mailbox, boolean tls) throws Exception {
        try { mailbox.take(20, 5000); }
        catch (SSLException expected) { check(tls, "Unexpected TLS error"); return; }
        catch (IOException expected) { check(!tls, "Missing TLS error"); return; }
        throw new IllegalStateException("Expected mailbox refusal");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new IllegalStateException(label);
    }
}
