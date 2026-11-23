package com.veypanel.client;

import java.io.IOException;
import java.net.Proxy;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.net.ssl.SSLException;
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

    private final ArrayBlockingQueue<TelemetrySample> latest = new ArrayBlockingQueue<>(1);
    private final AtomicBoolean ended = new AtomicBoolean();
    private volatile boolean tlsFailed;
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
                if (ended.get() || !ws.send(session.token)) { ended.set(true); ws.cancel(); }
            }
            @Override public void onMessage(WebSocket ws, String text) {
                if (ended.get()) return;
                if (text.length() > MAX_TEXT) { end(ws); return; }
                try {
                    TelemetrySample sample = TelemetrySample.parse(text);
                    latest.poll(); latest.offer(sample);
                } catch (Exception ex) { end(ws); }
            }
            @Override public void onMessage(WebSocket ws, ByteString bytes) { end(ws); }
            @Override public void onClosing(WebSocket ws, int code, String reason) { end(ws); }
            @Override public void onClosed(WebSocket ws, int code, String reason) { ended.set(true); latest.clear(); }
            @Override public void onFailure(WebSocket ws, Throwable error, Response response) {
                tlsFailed = isTlsError(error);
                ended.set(true); latest.clear();
                if (response != null) response.close();
            }
        });
    }

    @Override public TelemetrySample next() throws Exception {
        long until = android.os.SystemClock.elapsedRealtime() + 5500;
        while (!ended.get() && android.os.SystemClock.elapsedRealtime() < until) {
            TelemetrySample sample = latest.poll(250, TimeUnit.MILLISECONDS);
            if (sample != null && !ended.get()) return sample;
        }
        if (tlsFailed) throw new SSLException("WSS TLS rejected");
        throw new IOException("WSS unavailable");
    }

    private void end(WebSocket ws) { ended.set(true); latest.clear(); ws.cancel(); }

    static boolean isTlsError(Throwable value) {
        for (int i = 0; value != null && i < 8; i++, value = value.getCause())
            if (value instanceof SSLException || value instanceof java.security.cert.CertificateException) return true;
        return false;
    }

    @Override public void close() { end(socket); }
}
