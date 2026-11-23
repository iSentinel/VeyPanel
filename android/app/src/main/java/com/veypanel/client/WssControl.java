package com.veypanel.client;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;

/** Control-frame validation and replies for the experimental uncompressed transport. */
final class WssControl {
    private WssControl() { }

    static void validateClose(byte[] payload) throws IOException {
        if (payload.length == 0) return;
        if (payload.length < 2 || payload.length > 125) throw new IOException("Invalid close length");
        int status = ((payload[0] & 255) << 8) | (payload[1] & 255);
        if (!validCode(status)) throw new IOException("Invalid close status");
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(payload, 2, payload.length - 2));
    }

    private static boolean validCode(int code) {
        return (code >= 1000 && code <= 1014 && code != 1004 && code != 1005 && code != 1006)
            || (code >= 3000 && code <= 4999);
    }

    static void reply(OutputStream out, int opcode, byte[] payload, SecureRandom random) throws IOException {
        if (opcode == 8) {
            validateClose(payload);
            MaskedClientFrame.write(out, 8, payload, random);
        } else if (opcode == 9) {
            MaskedClientFrame.write(out, 10, payload, random);
        } else if (opcode != 10) throw new IOException("Invalid control opcode");
    }
}
