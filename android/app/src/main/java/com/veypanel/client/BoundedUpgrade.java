package com.veypanel.client;

import java.io.ByteArrayOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Experimental RFC 6455 upgrade codec for the fixed telemetry endpoint. */
final class BoundedUpgrade {
    private static final int MAX_HEADERS = 8192;
    private static final String GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

    private BoundedUpgrade() { }

    static String key(SecureRandom random) {
        byte[] nonce = new byte[16];
        random.nextBytes(nonce);
        return Base64.getEncoder().encodeToString(nonce);
    }

    static byte[] request(ReaderSession session, String key) {
        String host = session.endpoint.getHost();
        if (!ReaderSession.privateIp(host) && !"127.0.0.1".equals(host))
            throw new IllegalArgumentException("Invalid endpoint");
        if (!key.matches("[A-Za-z0-9+/]{22}==")) throw new IllegalArgumentException("Invalid nonce");
        return ("GET /api/v1/telemetry/ws HTTP/1.1\r\nHost: " + host
            + ":47861\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
            + "Sec-WebSocket-Version: 13\r\nSec-WebSocket-Key: " + key + "\r\n\r\n")
            .getBytes(StandardCharsets.US_ASCII);
    }

    static void verify(InputStream in, String key) throws IOException {
        String[] lines = readHeaders(in).split("\\r\\n", -1);
        if (lines.length < 2 || !lines[0].matches("HTTP/1\\.1 101(?: [ -~]*)?"))
            throw new IOException("Upgrade status rejected");
        Map<String, String> headers = new HashMap<>();
        for (int i = 1; i < lines.length; i++) {
            String line = lines[i];
            int colon = line.indexOf(':');
            if (colon < 1 || !line.substring(0, colon).matches("[A-Za-z0-9!#$%&'*+.^_`|~-]+"))
                throw new IOException("Invalid upgrade header");
            String name = line.substring(0, colon).toLowerCase(Locale.ROOT);
            String value = line.substring(colon + 1).trim();
            if (headers.putIfAbsent(name, value) != null) throw new IOException("Duplicate upgrade header");
        }
        if (!"websocket".equalsIgnoreCase(headers.get("upgrade"))
            || !containsUpgrade(headers.get("connection"))
            || !accept(key).equals(headers.get("sec-websocket-accept"))
            || headers.containsKey("sec-websocket-extensions")
            || headers.containsKey("sec-websocket-protocol")
            || headers.containsKey("transfer-encoding")
            || headers.containsKey("content-length"))
            throw new IOException("Upgrade contract rejected");
    }

    private static boolean containsUpgrade(String value) {
        if (value == null) return false;
        for (String part : value.split(",")) if ("upgrade".equalsIgnoreCase(part.trim())) return true;
        return false;
    }

    private static String readHeaders(InputStream in) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        int tail = 0;
        for (int i = 0; i < MAX_HEADERS; i++) {
            int b = in.read();
            if (b < 0) throw new EOFException("Incomplete upgrade");
            if (b != 13 && b != 10 && (b < 32 || b > 126)) throw new IOException("Invalid header byte");
            bytes.write(b);
            tail = (tail << 8) | b;
            if (tail == 0x0d0a0d0a) {
                byte[] raw = bytes.toByteArray();
                return new String(raw, 0, raw.length - 4, StandardCharsets.US_ASCII);
            }
        }
        throw new IOException("Upgrade header limit");
    }

    static String accept(String key) {
        try {
            return Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1")
                .digest((key + GUID).getBytes(StandardCharsets.US_ASCII)));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("WebSocket digest unavailable", ex);
        }
    }
}
