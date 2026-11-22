package com.veypanel.client;

import android.os.SystemClock;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.Proxy;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import javax.net.ssl.HttpsURLConnection;

final class EnrollmentClient {
    static final class Claim {
        final InvitationLink link;
        final String secret, code;
        final Instant expires;
        Claim(InvitationLink link, String secret, String code, Instant expires) {
            this.link = link; this.secret = secret; this.code = code; this.expires = expires;
        }
    }

    static Claim claim(InvitationLink link) throws Exception {
        JSONObject body = post(link.endpoint(false), link.id, link.secret, 200);
        String secret = body.getString("secret"), code = body.getString("code");
        Instant expires = Instant.parse(body.getString("expiresUtc")), now = Instant.now();
        if (!link.id.equals(body.getString("id")) || !secret.matches("[A-F0-9]{64}")
            || secret.equals(link.secret) || !code.matches("[0-9]{6}") || !expires.isAfter(now)
            || expires.isAfter(now.plusSeconds(125))) throw new IllegalStateException("Invalid claim");
        return new Claim(link, secret, code, expires);
    }

    static ReaderSession finish(Claim claim) throws Exception {
        if (!claim.expires.isAfter(Instant.now())) throw new IllegalStateException("Expired");
        JSONObject body = post(claim.link.endpoint(true), claim.link.id, claim.secret, 201);
        if (body == null) return null; // 202 pending: no token issued
        return claim.link.reader(body.getString("token"));
    }

    private static JSONObject post(URI endpoint, String id, String secret, int expected) throws Exception {
        HttpsURLConnection c = (HttpsURLConnection)endpoint.toURL().openConnection(Proxy.NO_PROXY);
        c.setInstanceFollowRedirects(false);
        c.setConnectTimeout(3000);
        c.setReadTimeout(3000);
        c.setUseCaches(false);
        c.setDoOutput(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("Content-Type", "application/json");
        c.setRequestProperty("Accept", "application/json");
        byte[] bytes = new JSONObject().put("id", id).put("secret", secret).toString().getBytes(StandardCharsets.UTF_8);
        c.setFixedLengthStreamingMode(bytes.length);
        try {
            try (java.io.OutputStream output = c.getOutputStream()) { output.write(bytes); }
            int status = c.getResponseCode();
            if (expected == 201 && status == 202) return null;
            if (status != expected || c.getContentType() == null
                || !c.getContentType().startsWith("application/json") || c.getContentLengthLong() > 65536)
                throw new IllegalStateException("Enrollment unavailable");
            return new JSONObject(read(c));
        } finally { java.util.Arrays.fill(bytes, (byte)0); c.disconnect(); }
    }

    private static String read(HttpsURLConnection c) throws Exception {
        long end = SystemClock.elapsedRealtime() + 5000;
        try (InputStream input = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int n;
            while ((n = input.read(buffer)) != -1) {
                if (SystemClock.elapsedRealtime() > end || out.size() + n > 65536
                    || Thread.currentThread().isInterrupted()) throw new IllegalStateException("Response limit");
                out.write(buffer, 0, n);
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }
}
