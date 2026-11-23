package com.veypanel.client;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;

/** A bounded WSS stream, held separate from MainActivity until acceptance. */
final class BoundedTelemetryStream implements TelemetryFeed {
    private final ReaderSession session;
    private final SSLSocketFactory factory;
    private final SecureRandom random = new SecureRandom();
    private final ScheduledExecutorService deadlines = Executors.newSingleThreadScheduledExecutor();
    private volatile Socket raw;
    private volatile boolean closed;
    private BufferedInputStream input;
    private BufferedOutputStream output;

    BoundedTelemetryStream(ReaderSession session) {
        this(session, (SSLSocketFactory)SSLSocketFactory.getDefault());
    }

    // Fixture trust injection is only reachable from instrumentation.
    static BoundedTelemetryStream fixture(ReaderSession session, SSLSocketFactory trust) {
        return new BoundedTelemetryStream(session, trust);
    }

    private BoundedTelemetryStream(ReaderSession session, SSLSocketFactory trust) {
        this.session = session;
        this.factory = trust;
    }

    @Override public TelemetrySample next() throws Exception {
        if (closed) throw new IOException("Stream closed");
        try {
            if (input == null) open();
            ScheduledFuture<?> deadline = deadlines.schedule(this::abortSocket, 5500, TimeUnit.MILLISECONDS);
            try {
                String body = BoundedMessageReader.readText(input, (opcode, bytes) ->
                    WssControl.reply(output, opcode, bytes, random));
                return TelemetrySample.parse(body);
            } finally { deadline.cancel(false); }
        } catch (Exception ex) {
            close();
            throw ex;
        }
    }

    private void open() throws Exception {
        String host = session.endpoint.getHost();
        Socket socket = new Socket(Proxy.NO_PROXY);
        raw = socket;
        if (closed) throw new IOException("Stream closed");
        ScheduledFuture<?> timeout = deadlines.schedule(this::abortSocket, 8000, TimeUnit.MILLISECONDS);
        try {
            socket.connect(new InetSocketAddress(host, 47861), 3000);
            SSLSocket tls = (SSLSocket)factory.createSocket(socket, host, 47861, true);
            tls.setSoTimeout(3000);
            SSLParameters parameters = tls.getSSLParameters();
            parameters.setEndpointIdentificationAlgorithm("HTTPS");
            tls.setSSLParameters(parameters);
            tls.startHandshake();
            input = new BufferedInputStream(tls.getInputStream(), 4096);
            output = new BufferedOutputStream(tls.getOutputStream(), 4096);
            authorize();
        } finally { timeout.cancel(false); }
    }

    private void authorize() throws Exception {
        String key = BoundedUpgrade.key(random);
        output.write(BoundedUpgrade.request(session, key));
        output.flush();
        BoundedUpgrade.verify(input, key);
        byte[] credential = session.token.getBytes(StandardCharsets.US_ASCII);
        try { MaskedClientFrame.write(output, 1, credential, random); }
        finally { Arrays.fill(credential, (byte)0); }
        if (closed) throw new IOException("Stream closed");
    }

    private void abortSocket() {
        Socket socket = raw;
        if (socket != null) {
            try { socket.close(); } catch (IOException ignored) { }
        }
    }

    @Override public void close() {
        closed = true;
        abortSocket();
        deadlines.shutdownNow();
    }
}
