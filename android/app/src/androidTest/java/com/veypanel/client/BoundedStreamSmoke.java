package com.veypanel.client;

import java.io.IOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLException;
import javax.net.ssl.SSLSocketFactory;

/** Real WSS transport fixture with several messages, TLS failure and cancellation. */
final class BoundedStreamSmoke {
    private BoundedStreamSmoke() { }

    static void run(SSLSocketFactory fixtureTrust) throws Exception {
        try (BoundedTelemetryStream untrusted = new BoundedTelemetryStream(ReaderSession.fixture('A'))) {
            try {
                untrusted.next();
                throw new IllegalStateException("Unknown CA accepted");
            } catch (SSLException expected) { }
        }
        try (BoundedTelemetryStream valid = open('F', fixtureTrust)) {
            check(valid.next().cpu == 42, "First sample");
            check(valid.next().cpu == 42, "Second sample");
            try {
                valid.next();
                throw new IllegalStateException("Missing close");
            } catch (java.io.EOFException expected) { }
        }
        rejectFrame('E', fixtureTrust, "Frame exceeds remaining budget");
        rejectFrame('G', fixtureTrust, "Invalid close status");
        cancellation(fixtureTrust);
        absoluteDeadline(fixtureTrust);
    }

    private static BoundedTelemetryStream open(char token, SSLSocketFactory factory) {
        return BoundedTelemetryStream.fixture(ReaderSession.fixture(token), factory);
    }

    private static void rejectFrame(char token, SSLSocketFactory factory, String reason) throws Exception {
        try (BoundedTelemetryStream stream = open(token, factory)) {
            try {
                stream.next();
                throw new IllegalStateException("Invalid frame accepted");
            } catch (IOException expected) {
                check(reason.equals(expected.getMessage()), "Frame rejection");
            }
        }
    }

    private static void cancellation(SSLSocketFactory factory) throws Exception {
        try (BoundedTelemetryStream stream = open('H', factory)) {
            check(stream.next().cpu == 42, "Sample before cancellation");
            var worker = Executors.newSingleThreadExecutor();
            try {
                Future<Boolean> blocked = worker.submit(() -> {
                    try { stream.next(); return false; }
                    catch (IOException expected) { return true; }
                });
                Thread.sleep(400);
                long start = android.os.SystemClock.elapsedRealtime();
                stream.close();
                check(blocked.get(2, TimeUnit.SECONDS), "Blocked read cancel");
                check(android.os.SystemClock.elapsedRealtime() - start < 2000, "Cancel deadline");
            } catch (ExecutionException ex) {
                throw new IllegalStateException("Cancel task failed", ex);
            } finally { worker.shutdownNow(); }
        }
    }

    private static void absoluteDeadline(SSLSocketFactory factory) throws Exception {
        try (BoundedTelemetryStream stream = open('I', factory)) {
            long start = android.os.SystemClock.elapsedRealtime();
            try {
                stream.next();
                throw new IllegalStateException("Drip-fed message accepted");
            } catch (IOException expected) {
                long elapsed = android.os.SystemClock.elapsedRealtime() - start;
                check(elapsed >= 4800 && elapsed < 8500, "Absolute message deadline");
                check(!(expected instanceof java.net.SocketTimeoutException), "Socket idle timeout, not deadline");
            }
        }
    }

    private static void check(boolean value, String reason) {
        if (!value) throw new IllegalStateException(reason);
    }
}
