package com.veypanel.client;

import java.net.URI;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class InvitationLink {
    private static final Pattern LINK = Pattern.compile(
        "^https://([0-9]{1,3}(?:\\.[0-9]{1,3}){3}):47861/enroll\\.html#id=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})&secret=([A-F0-9]{64})$");
    final URI origin;
    final String id, secret;

    private InvitationLink(URI origin, String id, String secret) {
        this.origin = origin; this.id = id; this.secret = secret;
    }

    static InvitationLink parse(String input) {
        if (input == null || input.length() > 256) throw new IllegalArgumentException();
        Matcher m = LINK.matcher(input.trim());
        if (!m.matches() || !ReaderSession.privateIp(m.group(1))) throw new IllegalArgumentException();
        return new InvitationLink(URI.create("https://" + m.group(1) + ":47861/"), m.group(2), m.group(3));
    }

    URI endpoint(boolean finish) {
        return origin.resolve(finish ? "/api/v1/enroll/finish" : "/api/v1/enroll/claim");
    }

    ReaderSession reader(String token) {
        return ReaderSession.parse(origin.toString() + "#token=" + token);
    }
}
