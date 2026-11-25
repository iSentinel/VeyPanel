package com.veypanel.client;

import java.io.IOException;
import java.net.Socket;

/** Deterministic state-transition fixtures; no network connection is made. */
public final class BoundedStreamStateSmoke {
    private BoundedStreamStateSmoke() { }

    /** Exercise cancellation, single-reader admission and obsolete timer rejection. */
    public static void main(String[] args) throws IOException {
        rejectLateSocket();
        singleReader();
        staleTimer();
        closeDuringDeadline();
        System.out.println("PASS: bounded WSS socket ownership and deadline generations");
    }

    private static void rejectLateSocket() throws IOException {
        try (BoundedStreamState state = new BoundedStreamState(); Socket socket = new Socket()) {
            state.close();
            reject(() -> state.attach(socket));
            check(socket.isClosed(), "Late socket closed");
            reject(state::beginRead);
        }
    }

    private static void singleReader() throws IOException {
        try (BoundedStreamState state = new BoundedStreamState(); Socket socket = new Socket()) {
            state.attach(socket);
            state.beginRead();
            reject(state::beginRead);
            check(!socket.isClosed(), "Second reader did not cancel first");
            state.endRead();
            state.beginRead();
            state.endRead();
        }
    }

    private static void staleTimer() throws IOException {
        try (BoundedStreamState state = new BoundedStreamState(); Socket socket = new Socket()) {
            state.attach(socket);
            var old = state.beginDeadline(60000);
            state.finishDeadline(old);
            var current = state.beginDeadline(60000);
            state.expire(old);
            state.ensureOpen();
            check(!socket.isClosed(), "Obsolete timer ignored");
            state.expire(current);
            check(socket.isClosed(), "Current timer closes socket");
            reject(state::ensureOpen);
            state.finishDeadline(current);
        }
    }

    private static void closeDuringDeadline() throws IOException {
        try (BoundedStreamState state = new BoundedStreamState(); Socket socket = new Socket()) {
            state.attach(socket);
            var ticket = state.beginDeadline(60000);
            state.close();
            state.finishDeadline(ticket);
            state.expire(ticket);
            check(socket.isClosed(), "Cancellation closed registered socket");
            reject(() -> state.beginDeadline(60000));
        }
    }

    private interface IoAction { void run() throws IOException; }

    private static void reject(IoAction action) throws IOException {
        try {
            action.run();
        } catch (IOException expected) { return; }
        throw new IOException("Invalid state transition accepted");
    }

    private static void check(boolean condition, String reason) {
        if (!condition) throw new IllegalStateException(reason);
    }
}
