package com.veypanel.client;

/** Foreground-only counters, no endpoints, credentials, or exception text. */
final class ConnectionDiagnostics {
    enum Event { CONNECTING, WSS, REST, FALLBACK, NETWORK, STALE, TLS, DENIED, PAUSED, IDLE }
    private int attempts, fallback, restErrors, samples;
    private Event event = Event.IDLE;
    private long lastFresh = -1;

    void reset() {
        attempts = fallback = restErrors = samples = 0;
        lastFresh = -1;
        event = Event.IDLE;
    }

    void connecting() { event = Event.CONNECTING; }
    void attempt() { attempts = increment(attempts); event = Event.CONNECTING; }
    void fallback() { fallback = increment(fallback); event = Event.FALLBACK; }
    void networkError() { restErrors = increment(restErrors); event = Event.NETWORK; }

    void fresh(boolean wss, long now) {
        samples = increment(samples);
        lastFresh = now;
        event = wss ? Event.WSS : Event.REST;
    }

    void mark(Event value) { event = value; }

    String describe(long now) {
        String age = lastFresh < 0 || now < lastFresh ? "N/A" : ((now - lastFresh) / 1000) + " s ago";
        return "Connection diagnostics · " + event.name()
            + "\nWSS attempts: " + attempts + " · Fallbacks: " + fallback
            + "\nREST errors: " + restErrors + " · Fresh samples: " + samples
            + "\nLast fresh receipt: " + age + " · RAM only";
    }

    private static int increment(int value) {
        return value == Integer.MAX_VALUE ? value : value + 1;
    }
}
