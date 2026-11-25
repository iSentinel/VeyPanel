package com.veypanel.client;

import java.io.InputStream;
import java.net.Proxy;
import javax.net.ssl.HttpsURLConnection;

final class TelemetryClient {
    static final class Denied extends Exception { }
    static TelemetrySample fetch(ReaderSession session) throws Exception {
        return fetch(session, null);
    }

    // The explicit factory overload is exercised only by the isolated transport fixture.
    static TelemetrySample fetch(ReaderSession session, javax.net.ssl.SSLSocketFactory fixtureTrust) throws Exception {
        return TelemetrySample.parse(fetchJson(session, false, fixtureTrust));
    }

    static MonitorHistory.Point[] fetchHistory(ReaderSession session) throws Exception {
        return fetchHistory(session, null);
    }

    static MonitorHistory.Point[] fetchHistory(ReaderSession session, javax.net.ssl.SSLSocketFactory fixtureTrust) throws Exception {
        return HostHistory.parse(fetchJson(session, true, fixtureTrust), java.time.Instant.now());
    }

    private static String fetchJson(ReaderSession session, boolean history,
                                    javax.net.ssl.SSLSocketFactory fixtureTrust) throws Exception {
        java.net.URI uri = history ? session.endpoint.resolve("/api/v1/history") : session.endpoint;
        HttpsURLConnection c = (HttpsURLConnection)uri.toURL().openConnection(Proxy.NO_PROXY);
        if (fixtureTrust != null) c.setSSLSocketFactory(fixtureTrust);
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
                || c.getContentLengthLong() > BoundedRestBody.LIMIT) throw new IllegalStateException("Invalid response");
            return read(c);
        } finally { c.disconnect(); }
    }

    private static String read(HttpsURLConnection c) throws Exception {
        try (InputStream input = c.getInputStream()) {
            return BoundedRestBody.read(input);
        }
    }
}
