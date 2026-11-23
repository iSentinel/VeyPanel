package com.veypanel.client;

import java.net.URI;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class ReaderSession {
    private static final Pattern LINK = Pattern.compile(
        "^https://([0-9]{1,3}(?:\\.[0-9]{1,3}){3}):47861/#token=([A-F0-9]{64})$");
    final URI endpoint;
    final String token;

    private ReaderSession(URI endpoint, String token) {
        this.endpoint = endpoint;
        this.token = token;
    }

    static ReaderSession parse(String input) {
        if (input == null || input.length() > 160) throw new IllegalArgumentException();
        Matcher m = LINK.matcher(input.trim());
        if (!m.matches() || !privateIp(m.group(1))) throw new IllegalArgumentException();
        return new ReaderSession(URI.create("https://" + m.group(1) + ":47861/api/v1/telemetry"), m.group(2));
    }

    // Fixed loopback endpoint and artificial tokens for isolated instrumentation only.
    // User-facing parsing continues to reject all loopback links.
    static ReaderSession fixture(char token) {
        if (token < 'A' || token > 'E') throw new IllegalArgumentException();
        return new ReaderSession(URI.create("https://127.0.0.1:47861/api/v1/telemetry"),
            new String(new char[64]).replace('\0', token));
    }

    boolean sameAccess(ReaderSession other) {
        return other != null && endpoint.equals(other.endpoint) && token.equals(other.token);
    }

    String websocketUrl() {
        return "wss://" + endpoint.getHost() + ":47861/api/v1/telemetry/ws";
    }

    static boolean privateIp(String address) {
        String[] parts = address.split("\\.", -1);
        if (parts.length != 4) return false;
        int[] n = new int[4];
        for (int i = 0; i < 4; i++) {
            if (!parts[i].matches("0|[1-9][0-9]{0,2}")) return false;
            n[i] = Integer.parseInt(parts[i]);
            if (n[i] > 255) return false;
        }
        return n[0] == 10 || (n[0] == 172 && n[1] >= 16 && n[1] <= 31)
            || (n[0] == 192 && n[1] == 168);
    }
}
