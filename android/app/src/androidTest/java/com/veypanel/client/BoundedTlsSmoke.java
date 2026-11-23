package com.veypanel.client;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLException;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;

/** Isolated TLS exchange, intentionally not a production transport. */
final class BoundedTlsSmoke {
    private BoundedTlsSmoke() { }

    static void run(SSLSocketFactory factory) throws Exception {
        try {
            exchange((SSLSocketFactory)SSLSocketFactory.getDefault(), 'A');
            throw new IllegalStateException("Unknown CA accepted");
        } catch (SSLException expected) { }
        if (TelemetrySample.parse(exchange(factory, 'A')).cpu != 42)
            throw new IllegalStateException("Bounded TLS sample mismatch");
        if (TelemetrySample.parse(exchange(factory, 'F')).cpu != 42)
            throw new IllegalStateException("Ping and stream fixture mismatch");
        try {
            exchange(factory, 'G');
            throw new IllegalStateException("Invalid close accepted");
        } catch (IOException expected) {
            if (!"Invalid close status".equals(expected.getMessage())) throw expected;
        }
        try {
            exchange(factory, 'E');
            throw new IllegalStateException("Oversized frame accepted");
        } catch (IOException expected) {
            if (!"Frame exceeds remaining budget".equals(expected.getMessage())) throw expected;
        }
    }

    private static String exchange(SSLSocketFactory factory, char token) throws Exception {
        ReaderSession session = ReaderSession.fixture(token);
        ScheduledExecutorService timeout = Executors.newSingleThreadScheduledExecutor();
        try (Socket raw = new Socket(Proxy.NO_PROXY)) {
            // Closing the underlying socket also bounds a drip-fed TLS handshake or read.
            timeout.schedule(() -> closeQuietly(raw), 8, TimeUnit.SECONDS);
            raw.connect(new InetSocketAddress(session.endpoint.getHost(), 47861), 3000);
            try (SSLSocket tls = (SSLSocket)factory.createSocket(raw, session.endpoint.getHost(), 47861, true)) {
                tls.setSoTimeout(3000);
                SSLParameters parameters = tls.getSSLParameters();
                parameters.setEndpointIdentificationAlgorithm("HTTPS");
                tls.setSSLParameters(parameters);
                tls.startHandshake();
                return message(tls, session);
            }
        } finally { timeout.shutdownNow(); }
    }

    private static String message(SSLSocket tls, ReaderSession session) throws Exception {
        SecureRandom random = new SecureRandom();
        String key = BoundedUpgrade.key(random);
        BufferedInputStream input = new BufferedInputStream(tls.getInputStream(), 4096);
        BufferedOutputStream output = new BufferedOutputStream(tls.getOutputStream(), 4096);
        output.write(BoundedUpgrade.request(session, key)); output.flush();
        BoundedUpgrade.verify(input, key);
        byte[] token = session.token.getBytes(StandardCharsets.US_ASCII);
        try { MaskedClientFrame.write(output, 1, token, random); }
        finally { java.util.Arrays.fill(token, (byte)0); }
        BoundedMessageReader.Control control = (opcode, payload) ->
            WssControl.reply(output, opcode, payload, random);
        String first = BoundedMessageReader.readText(input, control);
        if (!session.token.startsWith("F")) return first;
        if (TelemetrySample.parse(BoundedMessageReader.readText(input, control)).cpu != 42)
            throw new IOException("Second sample mismatch");
        try {
            BoundedMessageReader.readText(input, control);
            throw new IllegalStateException("Close did not end stream");
        } catch (java.io.EOFException expected) {
            if (!"Peer closed".equals(expected.getMessage())) throw expected;
        }
        return first;
    }

    private static void closeQuietly(Socket socket) {
        try { socket.close(); } catch (IOException ignored) { }
    }
}
