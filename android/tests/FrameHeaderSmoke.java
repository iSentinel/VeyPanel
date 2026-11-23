package com.veypanel.client;

import java.io.ByteArrayInputStream;
import java.io.IOException;

final class FrameHeaderSmoke {
    private FrameHeaderSmoke() { }

    static void run() {
        try {
            check(read(false, 1, 0x81, 1).length == 1);
            check(read(false, 126, 0x01, 126, 0, 126).length == 126);
            check(read(true, 5, 0x80, 5).fin);
            check(read(true, 0, 0x89, 125).length == 125);
            check(read(false, BoundedFrameHeader.MAX_MESSAGE, 0x81, 127, 0,0,0,0,0,16,0,0).length
                == BoundedFrameHeader.MAX_MESSAGE);
            reject(false, BoundedFrameHeader.MAX_MESSAGE, 0x81, 127, 0,0,0,0,0,16,0,1);
            reject(true, 2, 0x80, 3);
            reject(false, 10, 0x80, 1);
            reject(true, 10, 0x81, 1);
            reject(false, 10, 0x82, 1);
            reject(false, 10, 0xc1, 1);
            reject(false, 10, 0x81, 0x81);
            reject(false, 100, 0x09, 1);
            reject(false, 100, 0x88, 1);
            reject(false, 100, 0x89, 126, 0,126);
            reject(false, 100, 0x81, 126, 0,1);
            reject(false, 100, 0x81, 127, 128,0,0,0,0,0,0,0);
            reject(false, 100, 0x81, 126, 0);
            System.out.println("PASS: pre-payload frame header and aggregate budget fixtures");
        } catch (IOException ex) {
            throw new IllegalStateException("Valid frame rejected", ex);
        }
    }

    private static BoundedFrameHeader read(boolean fragmented, int remaining, int... bytes) throws IOException {
        byte[] data = new byte[bytes.length];
        for (int i = 0; i < bytes.length; i++) data[i] = (byte)bytes[i];
        ByteArrayInputStream input = new ByteArrayInputStream(data);
        BoundedFrameHeader header = BoundedFrameHeader.read(input, fragmented, remaining);
        check(input.available() == 0);
        return header;
    }

    private static void reject(boolean fragmented, int remaining, int... bytes) {
        try { read(fragmented, remaining, bytes); }
        catch (IOException expected) { return; }
        throw new IllegalStateException("Invalid frame accepted");
    }

    private static void check(boolean valid) {
        if (!valid) throw new IllegalStateException("Frame header mismatch");
    }
}
