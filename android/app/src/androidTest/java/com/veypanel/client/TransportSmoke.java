package com.veypanel.client;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;
import javax.net.ssl.SSLException;

final class TransportSmoke {
    private final SSLContext context;
    private final X509TrustManager manager;

    TransportSmoke(String encodedCa) throws Exception {
        byte[] der = android.util.Base64.decode(encodedCa,android.util.Base64.DEFAULT);
        if (der.length > 8192) throw new IllegalArgumentException("Fixture CA size");
        java.security.cert.Certificate ca = CertificateFactory.getInstance("X.509")
            .generateCertificate(new ByteArrayInputStream(der));
        KeyStore keys = KeyStore.getInstance(KeyStore.getDefaultType()); keys.load(null);
        keys.setCertificateEntry("fixture",ca);
        TrustManagerFactory tm = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        tm.init(keys);
        manager = (X509TrustManager)tm.getTrustManagers()[0];
        context = SSLContext.getInstance("TLS");
        context.init(null,new javax.net.ssl.TrustManager[]{manager},null);
    }

    void runBounded() throws Exception {
        BoundedTlsSmoke.run(context.getSocketFactory());
        BoundedStreamSmoke.run(context.getSocketFactory());
    }

    void run() throws Exception {
        ReaderSession valid = ReaderSession.fixture('A'), denied = ReaderSession.fixture('B'), fallback = ReaderSession.fixture('C'), revoke = ReaderSession.fixture('D');
        expectTls(valid);
        check(TelemetryClient.fetch(valid,context.getSocketFactory()).cpu == 42,"Trusted HTTPS");
        try (TelemetryStream stream = open(valid)) {
            check(stream.next().cpu == 42,"Trusted WSS");
        }
        expectDenied(denied);
        MonitorHistory.Point[] history = TelemetryClient.fetchHistory(valid,context.getSocketFactory());
        check(history.length == 1 && history[0].series(0) == 42, "Trusted HTTPS history");
        expectHistoryDenied(denied);
        try (TelemetryStream stream = open(fallback)) { expectEnded(stream); }
        check(TelemetryClient.fetch(fallback,context.getSocketFactory()).cpu == 42,"REST after WSS refusal");
        try (TelemetryStream stream = open(revoke)) {
            check(stream.next().cpu == 42,"Before revocation");
            expectEnded(stream);
        }
        expectDenied(revoke);
        expectHistoryDenied(revoke);
        // The test fixture accepts only known artificial credentials.
    }

    private void expectTls(ReaderSession s) throws Exception {
        boolean denied=false;
        try { TelemetryClient.fetch(s); }
        catch (SSLException ex) { denied = true; }
        check(denied,"Default HTTPS rejects unknown CA");
        try (TelemetryStream stream = new TelemetryStream(s)) {
            denied=false;
            try { stream.next(); }
            catch (SSLException ex) { denied=true; }
            check(denied,"Default WSS rejects unknown CA");
        }
    }
    private TelemetryStream open(ReaderSession s) {
        return TelemetryStream.fixture(s,context.getSocketFactory(),manager);
    }
    private void expectDenied(ReaderSession s) throws Exception {
        try { TelemetryClient.fetch(s,context.getSocketFactory()); }
        catch (TelemetryClient.Denied ex) { return; }
        throw new IllegalStateException("Reader access not denied");
    }
    private void expectHistoryDenied(ReaderSession s) throws Exception {
        try { TelemetryClient.fetchHistory(s,context.getSocketFactory()); }
        catch (TelemetryClient.Denied ex) { return; }
        throw new IllegalStateException("History access not denied");
    }

    private static void expectEnded(TelemetryStream stream) throws Exception {
        try { stream.next(); }
        catch (SSLException ex) { throw ex; }
        catch (IOException ex) { return; }
        throw new IllegalStateException("Expected stream end");
    }
    private static void check(boolean condition,String message) {
        if (!condition) throw new IllegalStateException(message);
    }
}
