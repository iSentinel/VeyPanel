package com.veypanel.client;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;

/** A bounded WSS stream, held separate from MainActivity until acceptance. */
final class BoundedTelemetryStream implements TelemetryFeed {
    private final ReaderSession session;
    private final SSLSocketFactory factory;
    private final SecureRandom random = new SecureRandom();
    private final BoundedStreamState state = new BoundedStreamState();
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
        // A rejected second caller must not cancel the admitted reader.
        state.beginRead();
        try {
            if (input == null) open();
            BoundedStreamState.Deadline deadline = state.beginDeadline(5500);
            TelemetrySample sample;
            try {
                String body = BoundedMessageReader.readText(input, (opcode, bytes) ->
                    WssControl.reply(output, opcode, bytes, random));
                sample = TelemetrySample.parse(body);
            } finally { state.finishDeadline(deadline); }
            state.ensureOpen();
            return sample;
        } catch (Exception ex) {
            close();
            throw ex;
        } finally { state.endRead(); }
    }

    private void open() throws Exception {
        String host = session.endpoint.getHost();
        Socket socket = new Socket(Proxy.NO_PROXY);
        state.attach(socket);
        BoundedStreamState.Deadline timeout = state.beginDeadline(8000);
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
        } finally { state.finishDeadline(timeout); }
        state.ensureOpen();
    }

    private void authorize() throws Exception {
        String key = BoundedUpgrade.key(random);
        output.write(BoundedUpgrade.request(session, key));
        output.flush();
        BoundedUpgrade.verify(input, key);
        byte[] credential = session.token.getBytes(StandardCharsets.US_ASCII);
        try { MaskedClientFrame.write(output, 1, credential, random); }
        finally { Arrays.fill(credential, (byte)0); }
        state.ensureOpen();
    }

    @Override public void close() { state.close(); }
}
