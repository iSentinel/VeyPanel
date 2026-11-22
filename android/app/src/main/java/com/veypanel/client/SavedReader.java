package com.veypanel.client;

import java.time.Instant;

final class SavedReader {
    final ReaderSession session;
    final Instant saved;
    SavedReader(ReaderSession session, Instant saved) {
        this.session = session;
        this.saved = saved;
    }

    boolean validAt(Instant now) {
        return !now.isBefore(saved) && now.isBefore(saved.plusSeconds(86400));
    }

    String link() {
        return session.endpoint.resolve("/").toString() + "#token=" + session.token;
    }

    String encode() { return saved.toString() + "\n" + link(); }

    static SavedReader decode(String text, Instant now) {
        if (text == null || text.length() > 256) throw new IllegalArgumentException();
        String[] parts = text.split("\n", -1);
        if (parts.length != 2) throw new IllegalArgumentException();
        SavedReader record = new SavedReader(ReaderSession.parse(parts[1]), Instant.parse(parts[0]));
        if (!record.validAt(now)) throw new IllegalArgumentException("Saved access expired");
        return record;
    }
}
