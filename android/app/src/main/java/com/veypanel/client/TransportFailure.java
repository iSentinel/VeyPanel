package com.veypanel.client;

import java.security.cert.CertificateException;
import javax.net.ssl.SSLException;

/** Shared bounded classification; never inspect or expose exception messages. */
final class TransportFailure {
    private TransportFailure() { }

    /** Recognize direct or wrapped TLS and certificate exceptions. */
    static boolean isTls(Throwable failure) {
        for (int depth = 0; failure != null && depth < 8; depth++, failure = failure.getCause()) {
            if (failure instanceof SSLException || failure instanceof CertificateException) return true;
        }
        return false;
    }
}
