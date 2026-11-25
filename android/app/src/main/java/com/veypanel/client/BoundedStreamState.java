package com.veypanel.client;

import java.io.IOException;
import java.net.Socket;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

/** Serialize socket ownership, single-reader admission and deadline generations. */
final class BoundedStreamState implements AutoCloseable {
    private final ScheduledExecutorService deadlines = Executors.newSingleThreadScheduledExecutor();
    private Socket socket;
    private boolean closed;
    private boolean expired;
    private boolean reading;
    private Deadline active;

    /** One operation's deadline; identity prevents an obsolete timer closing a later read. */
    static final class Deadline {
        private final long until;
        private ScheduledFuture<?> future;

        private Deadline(long until) { this.until = until; }
    }

    synchronized void ensureOpen() throws IOException {
        if (closed || expired) throw new IOException("Stream closed");
    }

    synchronized void beginRead() throws IOException {
        ensureOpen();
        if (reading) throw new IOException("Concurrent stream read");
        reading = true;
    }

    synchronized void endRead() { reading = false; }

    /** Transfer ownership or close the candidate if cancellation already won. */
    synchronized void attach(Socket candidate) throws IOException {
        if (closed || expired || socket != null) {
            candidate.close();
            throw new IOException("Socket registration rejected");
        }
        socket = candidate;
    }

    synchronized Deadline beginDeadline(long millis) throws IOException {
        ensureOpen();
        if (active != null) throw new IOException("Concurrent stream deadline");
        Deadline ticket = new Deadline(System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(millis));
        active = ticket;
        ticket.future = deadlines.schedule(() -> expire(ticket), millis, TimeUnit.MILLISECONDS);
        return ticket;
    }

    /** Reject a completion past its absolute deadline even if the timer ran late. */
    synchronized void finishDeadline(Deadline ticket) {
        if (active != ticket) return;
        if (System.nanoTime() - ticket.until >= 0) expire(ticket);
        active = null;
        ticket.future.cancel(false);
    }

    synchronized void expire(Deadline ticket) {
        if (closed || active != ticket) return;
        expired = true;
        abortSocket();
    }

    private void abortSocket() {
        if (socket != null) {
            try { socket.close(); } catch (IOException ignored) { }
        }
    }

    /** Cancel the owned socket and scheduler exactly once; no new registration can win. */
    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        if (active != null) {
            active.future.cancel(false);
            active = null;
        }
        abortSocket();
        deadlines.shutdownNow();
    }
}
