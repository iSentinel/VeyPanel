package com.veypanel.client;

import java.io.IOException;
import java.security.cert.CertificateException;
import javax.net.ssl.SSLHandshakeException;
import javax.net.ssl.SSLPeerUnverifiedException;

/** Test shared failure classification without network, credentials or Android. */
public final class TransportFailureSmoke {
    private TransportFailureSmoke() { }

    /** Exercise direct, wrapped, ordinary, null and cyclic failures. */
    public static void main(String[] args) {
        check(TransportFailure.isTls(new SSLHandshakeException("fixture")), "Direct TLS");
        check(TransportFailure.isTls(new IOException(new SSLPeerUnverifiedException("fixture"))),
            "Wrapped peer identity");
        check(TransportFailure.isTls(new RuntimeException(new CertificateException("fixture"))),
            "Wrapped certificate");
        check(!TransportFailure.isTls(new IOException("SSLException certificate fixture")),
            "Text is not a TLS classification");
        check(!TransportFailure.isTls(null), "Null failure");
        Throwable first = new IOException("first");
        Throwable second = new IOException("second");
        first.initCause(second);
        second.initCause(first);
        check(!TransportFailure.isTls(first), "Cyclic chain bounded");
        Throwable nested = new SSLHandshakeException("fixture");
        for (int i = 0; i < 7; i++) nested = new IOException(nested);
        check(TransportFailure.isTls(nested), "Eighth cause recognized");
        check(!TransportFailure.isTls(new IOException(nested)), "Existing eight-cause bound");
        System.out.println("PASS: shared bounded TLS failure classification");
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new IllegalStateException(label);
    }
}
