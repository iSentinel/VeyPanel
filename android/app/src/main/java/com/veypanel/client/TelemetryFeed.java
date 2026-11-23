package com.veypanel.client;

/** One foreground, cancelable telemetry source; no ownership of saved grants. */
interface TelemetryFeed extends AutoCloseable {
    TelemetrySample next() throws Exception;
    @Override void close();
}
