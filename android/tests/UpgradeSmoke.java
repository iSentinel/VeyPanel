package com.veypanel.client;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;

final class UpgradeSmoke {
    private static final String KEY = "dGhlIHNhbXBsZSBub25jZQ==";
    private static final String GOOD = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
        + "Connection: keep-alive, Upgrade\r\nSec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n";

    static void run() {
        try {
            ByteArrayInputStream in = input(GOOD + "\r\nZ");
            BoundedUpgrade.verify(in, KEY);
            if (in.read() != 'Z') throw new IOException("Upgrade consumed frame");
            if (!BoundedUpgrade.accept(KEY).equals("s3pPLMBiTxaQ9kYGzzhZRbK+xOo="))
                throw new IOException("RFC accept mismatch");
            ReaderSession session = ReaderSession.fixture('A');
            String request = new String(BoundedUpgrade.request(session, KEY), StandardCharsets.US_ASCII);
            if (request.contains(session.token) || request.contains("extensions") || !request.endsWith("\r\n\r\n"))
                throw new IOException("Request mismatch");
            reject(GOOD.replace("101", "302") + "\r\n");
            reject(GOOD.replace("s3pPL", "wrong") + "\r\n");
            reject(GOOD + "Sec-WebSocket-Extensions: permessage-deflate\r\n\r\n");
            reject(GOOD + "Upgrade: websocket\r\n\r\n");
            reject(GOOD + "Content-Length: 0\r\n\r\n");
            reject(GOOD + "X-Large: " + "a".repeat(8192) + "\r\n\r\n");
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] token = session.token.getBytes(StandardCharsets.US_ASCII);
            MaskedClientFrame.write(out, 1, token, new SecureRandom());
            byte[] frame = out.toByteArray();
            if (frame.length != 70 || (frame[0] & 255) != 129 || (frame[1] & 255) != 192)
                throw new IOException("Client frame header");
            for (int i = 0; i < token.length; i++)
                if ((byte)(frame[6+i] ^ frame[2+(i&3)]) != token[i]) throw new IOException("Client mask mismatch");
            System.out.println("PASS: bounded upgrade, RFC accept, no extensions and client masking");
        } catch (IOException ex) { throw new IllegalStateException("Upgrade fixture failed", ex); }
    }

    private static ByteArrayInputStream input(String text) {
        return new ByteArrayInputStream(text.getBytes(StandardCharsets.US_ASCII));
    }

    private static void reject(String text) {
        try { BoundedUpgrade.verify(input(text), KEY); }
        catch (IOException expected) { return; }
        throw new IllegalStateException("Invalid upgrade accepted");
    }
}
