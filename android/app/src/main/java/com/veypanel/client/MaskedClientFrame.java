package com.veypanel.client;

import java.io.IOException;
import java.io.OutputStream;
import java.security.SecureRandom;

/** Experimental client authentication and control frame encoder. */
final class MaskedClientFrame {
    private MaskedClientFrame() { }

    static void write(OutputStream out, int opcode, byte[] payload, SecureRandom random) throws IOException {
        boolean auth = opcode == 1 && payload.length == 64;
        boolean control = (opcode == 8 || opcode == 9 || opcode == 10) && payload.length <= 125
            && (opcode != 8 || payload.length != 1);
        if (!auth && !control) throw new IOException("Unsupported client frame");
        byte[] mask = new byte[4];
        random.nextBytes(mask);
        out.write(0x80 | opcode);
        out.write(0x80 | payload.length);
        out.write(mask);
        for (int i = 0; i < payload.length; i++) out.write(payload[i] ^ mask[i & 3]);
        out.flush();
    }
}
