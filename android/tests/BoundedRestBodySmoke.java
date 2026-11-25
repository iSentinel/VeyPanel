package com.veypanel.client;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/** Deterministic body limits, EOF and interrupt checks without network I/O. */
public final class BoundedRestBodySmoke {
    private BoundedRestBodySmoke() { }

    /** Cover the exact byte boundary, late EOF, slow reads and cancellation. */
    public static void main(String[] args) throws Exception {
        check(BoundedRestBody.read(new ByteArrayInputStream(new byte[]{65}), () -> 0).equals("A"));
        check(BoundedRestBody.read(new ByteArrayInputStream(new byte[BoundedRestBody.LIMIT]),
            () -> 0).length() == BoundedRestBody.LIMIT);
        refuse(new ByteArrayInputStream(new byte[BoundedRestBody.LIMIT + 1]),
            new AtomicLong(), "REST response size or read limit");
        timedRead(-1);
        timedRead(1);
        cancelled();
        cancelledAtEof();
        refuse(new InputStream() {
            @Override public int read() { return 0; }
            @Override public int read(byte[] target, int offset, int count) { return 0; }
        }, new AtomicLong(), "REST response size or read limit");
        System.out.println("PASS: bounded REST body bytes, deadline at EOF and cancellation");
    }

    private static void timedRead(int outcome) throws Exception {
        AtomicLong clock = new AtomicLong();
        InputStream input = new InputStream() {
            @Override public int read() { throw new IllegalStateException("Unexpected single read"); }
            @Override public int read(byte[] target, int offset, int count) {
                clock.set(TimeUnit.SECONDS.toNanos(5));
                return outcome;
            }
        };
        refuse(input, clock, "REST response deadline");
    }

    private static void refuse(InputStream input, AtomicLong clock, String reason) throws Exception {
        try { BoundedRestBody.read(input, clock::get); }
        catch (IOException expected) { check(reason.equals(expected.getMessage())); return; }
        throw new IllegalStateException("Invalid REST response accepted");
    }

    private static void cancelled() throws Exception {
        Thread.currentThread().interrupt();
        try {
            BoundedRestBody.read(new InputStream() {
                @Override public int read() { throw new IllegalStateException("Cancelled read entered"); }
            }, () -> 0);
            throw new IllegalStateException("Cancelled response accepted");
        } catch (InterruptedIOException expected) {
            check(Thread.currentThread().isInterrupted());
        } finally { Thread.interrupted(); }
    }

    private static void cancelledAtEof() throws Exception {
        try {
            BoundedRestBody.read(new InputStream() {
                @Override public int read() { return -1; }
                @Override public int read(byte[] target, int offset, int count) {
                    Thread.currentThread().interrupt();
                    return -1;
                }
            }, () -> 0);
            throw new IllegalStateException("Cancelled EOF accepted");
        } catch (InterruptedIOException expected) {
            check(Thread.currentThread().isInterrupted());
        } finally { Thread.interrupted(); }
    }

    private static void check(boolean value) {
        if (!value) throw new IllegalStateException("REST body fixture failed");
    }
}
