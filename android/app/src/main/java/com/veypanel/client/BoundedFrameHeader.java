package com.veypanel.client;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;

/** Experimental uncompressed server-frame header gate. Does not read payload bytes. */
final class BoundedFrameHeader {
    static final int MAX_MESSAGE = 1024 * 1024;
    final int opcode, length;
    final boolean fin;

    private BoundedFrameHeader(int opcode, int length, boolean fin) {
        this.opcode = opcode;
        this.length = length;
        this.fin = fin;
    }

    static BoundedFrameHeader read(InputStream in, boolean fragmented, int remaining) throws IOException {
        if (remaining < 0 || remaining > MAX_MESSAGE) throw new IOException("Invalid message budget");
        int first = octet(in), second = octet(in);
        boolean fin = (first & 0x80) != 0;
        int opcode = first & 15;
        if ((first & 0x70) != 0 || (second & 0x80) != 0) throw new IOException("Unsupported frame flags");
        boolean control = opcode == 8 || opcode == 9 || opcode == 10;
        if (!control && (fragmented ? opcode != 0 : opcode != 1))
            throw new IOException("Unsupported data opcode");
        int indicator = second & 127;
        if (control && (!fin || indicator > 125)) throw new IOException("Invalid control frame");
        long length = length(in, indicator);
        if (opcode == 8 && length == 1) throw new IOException("Invalid close length");
        if (length > (control ? 125 : remaining)) throw new IOException("Frame exceeds remaining budget");
        return new BoundedFrameHeader(opcode, (int)length, fin);
    }

    private static long length(InputStream in, int indicator) throws IOException {
        if (indicator < 126) return indicator;
        int count = indicator == 126 ? 2 : 8;
        long value = 0;
        for (int i = 0; i < count; i++) {
            int next = octet(in);
            if (i == 0 && count == 8 && (next & 128) != 0) throw new IOException("Invalid 64-bit length");
            value = (value << 8) | next;
        }
        if (value < (count == 2 ? 126 : 65536)) throw new IOException("Noncanonical frame length");
        return value;
    }

    private static int octet(InputStream in) throws IOException {
        int b = in.read();
        if (b < 0) throw new EOFException("Incomplete frame header");
        return b;
    }
}
