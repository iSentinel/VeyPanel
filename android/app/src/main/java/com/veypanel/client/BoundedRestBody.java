package com.veypanel.client;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import java.util.function.LongSupplier;

/** Bound REST response bytes and check monotonic budget around every read. */
final class BoundedRestBody {
    static final int LIMIT = 1024 * 1024;
    private static final long BUDGET = TimeUnit.SECONDS.toNanos(5);

    private BoundedRestBody() { }

    static String read(InputStream input) throws IOException {
        return read(input, System::nanoTime);
    }

    /** Clock injection is used only for deterministic offline fixtures. */
    static String read(InputStream input, LongSupplier clock) throws IOException {
        long start = clock.getAsLong();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        while (true) {
            check(start, clock);
            int count = input.read(buffer, 0, Math.min(buffer.length, LIMIT - out.size() + 1));
            check(start, clock);
            if (count == -1) break;
            if (count <= 0 || count > LIMIT - out.size())
                throw new IOException("REST response size or read limit");
            out.write(buffer, 0, count);
        }
        return new String(out.toByteArray(), StandardCharsets.UTF_8);
    }

    private static void check(long start, LongSupplier clock) throws IOException {
        if (Thread.currentThread().isInterrupted())
            throw new InterruptedIOException("REST response cancelled");
        if (clock.getAsLong() - start >= BUDGET)
            throw new IOException("REST response deadline");
    }
}
