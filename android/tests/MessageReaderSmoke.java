package com.veypanel.client;

import java.io.ByteArrayInputStream;
import java.io.IOException;

final class MessageReaderSmoke {
    private MessageReaderSmoke() { }

    static void run() {
        try {
            String sample = BoundedMessageReader.readText(input(1,1,'a',0x89,1,'p',0x80,1,'b'),
                (opcode, data) -> {
                    if (opcode != 9 || data.length != 1 || data[0] != 'p')
                        throw new IOException("Control mismatch");
                });
            if (!sample.equals("ab")) throw new IllegalStateException("Fragment join");
            String utf8 = BoundedMessageReader.readText(input(1,1,0xc3,0x80,1,0xa9), (o,d) -> {});
            if (!utf8.equals("\u00e9")) throw new IllegalStateException("Split UTF-8");
            reject(input(0x81,1,0xff));
            reject(input(0x81,2,'a'));
            reject(input(0x88,0));
            reject(input(0x81,127,0,0,0,0,0,16,0,1));
            byte[] frames = new byte[514];
            frames[0] = 1;
            for (int i = 2; i < frames.length; i += 2) frames[i] = 0;
            reject(new ByteArrayInputStream(frames));
            System.out.println("PASS: bounded message assembly, control interleave, strict UTF-8 and frame count");
        } catch (IOException ex) {
            throw new IllegalStateException("Valid message rejected", ex);
        }
    }

    private static ByteArrayInputStream input(int... values) {
        byte[] bytes = new byte[values.length];
        for (int i = 0; i < bytes.length; i++) bytes[i] = (byte)values[i];
        return new ByteArrayInputStream(bytes);
    }

    private static void reject(ByteArrayInputStream input) {
        try { BoundedMessageReader.readText(input, (o,d) -> {}); }
        catch (IOException expected) { return; }
        throw new IllegalStateException("Invalid message accepted");
    }
}
