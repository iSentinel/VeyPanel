package com.veypanel.client;

import android.os.SystemClock;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.Proxy;
import java.nio.charset.StandardCharsets;
import javax.net.ssl.HttpsURLConnection;

final class TelemetryClient {
    static final class Denied extends Exception { }
    private static final int LIMIT = 1024 * 1024;
    static TelemetrySample fetch(ReaderSession session) throws Exception {
        HttpsURLConnection c = (HttpsURLConnection)session.endpoint.toURL().openConnection(Proxy.NO_PROXY);
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(3000);
        c.setReadTimeout(3000);
        c.setUseCaches(false);
        c.setRequestMethod("GET");
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Authorization", "Bearer " + session.token);
        try {
            int status = c.getResponseCode();
            if (status == 401 || status == 403) throw new Denied();
            String type = c.getContentType();
            if (status != 200 || type == null || !type.startsWith("application/json")
                || c.getContentLengthLong() > LIMIT) throw new IllegalStateException("Invalid response");
            return TelemetrySample.parse(read(c));
        } finally { c.disconnect(); }
    }

    private static String read(HttpsURLConnection c) throws Exception {
        long end = SystemClock.elapsedRealtime() + 5000;
        try (InputStream input = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int n;
            while ((n = input.read(buffer)) != -1) {
                if (SystemClock.elapsedRealtime() > end || out.size() + n > LIMIT
                    || Thread.currentThread().isInterrupted()) throw new IllegalStateException("Response limit");
                out.write(buffer, 0, n);
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }
}
