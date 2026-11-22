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
