package com.veypanel.client;

import java.net.Proxy;
import java.util.concurrent.TimeUnit;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;
import okio.ByteString;

/** Single foreground stream; only the newest received sample is retained. */
final class TelemetryStream implements TelemetryFeed {
    private static final int MAX_TEXT = 1024 * 1024;
    private static final OkHttpClient CLIENT = new OkHttpClient.Builder()
        .proxy(Proxy.NO_PROXY).followRedirects(false).followSslRedirects(false)
        .retryOnConnectionFailure(false).connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(3, TimeUnit.SECONDS).writeTimeout(3, TimeUnit.SECONDS)
        .pingInterval(10, TimeUnit.SECONDS).build();

    private final LatestTelemetryMailbox<TelemetrySample> mailbox = new LatestTelemetryMailbox<>();
    private final WebSocket socket;

    TelemetryStream(ReaderSession session) { this(session, CLIENT); }

    // Fixture-specific trust is injected by instrumentation, never by a user setting.
    static TelemetryStream fixture(ReaderSession session, javax.net.ssl.SSLSocketFactory factory,
                                   javax.net.ssl.X509TrustManager manager) {
        return new TelemetryStream(session, CLIENT.newBuilder().sslSocketFactory(factory, manager).build());
    }

    private TelemetryStream(ReaderSession session, OkHttpClient client) {
        Request request = new Request.Builder().url(session.websocketUrl()).build();
        socket = client.newWebSocket(request, new WebSocketListener() {
            @Override public void onOpen(WebSocket ws, Response response) {
                if (mailbox.isClosed() || !ws.send(session.token)) end(ws);
            }
            @Override public void onMessage(WebSocket ws, String text) {
                if (mailbox.isClosed()) return;
                long received = System.nanoTime();
                // OkHttp has already assembled the text; this is a parser limit.
                if (text.length() > MAX_TEXT) { end(ws); return; }
                try {
                    TelemetrySample sample = TelemetrySample.parse(text);
                    mailbox.offer(sample, received);
                } catch (Exception ex) { end(ws); }
            }
            @Override public void onMessage(WebSocket ws, ByteString bytes) { end(ws); }
            @Override public void onClosing(WebSocket ws, int code, String reason) { end(ws); }
            @Override public void onClosed(WebSocket ws, int code, String reason) { mailbox.close(false); }
            @Override public void onFailure(WebSocket ws, Throwable error, Response response) {
                mailbox.close(isTlsError(error));
                if (response != null) response.close();
            }
        });
    }

    @Override public TelemetrySample next() throws Exception {
        return mailbox.take(5500, 5000);
    }

    private void end(WebSocket ws) { mailbox.close(false); ws.cancel(); }

    static boolean isTlsError(Throwable value) {
        return TransportFailure.isTls(value);
    }

    @Override public void close() { end(socket); }
}
