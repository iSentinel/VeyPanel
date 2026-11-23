package com.veypanel.client;

import java.io.ByteArrayOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Experimental uncompressed message reader, not wired to production transport. */
final class BoundedMessageReader {
    private static final int MAX_FRAMES = 256;

    interface Control {
        void accept(int opcode, byte[] bytes) throws IOException;
    }

    private BoundedMessageReader() { }

    static String readText(InputStream in, Control control) throws IOException {
        ByteArrayOutputStream message = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        boolean fragmented = false;
        for (int i = 0; i < MAX_FRAMES; i++) {
            BoundedFrameHeader frame = BoundedFrameHeader.read(in, fragmented,
                BoundedFrameHeader.MAX_MESSAGE - message.size());
            if (frame.opcode >= 8) {
                byte[] payload = new byte[frame.length];
                readFully(in, payload, payload.length);
                if (frame.opcode == 8) WssControl.validateClose(payload);
                control.accept(frame.opcode, payload);
                if (frame.opcode == 8) throw new EOFException("Peer closed");
                continue;
            }
            int remaining = frame.length;
            while (remaining > 0) {
                int count = Math.min(remaining, buffer.length);
                readFully(in, buffer, count);
                message.write(buffer, 0, count);
                remaining -= count;
            }
            if (frame.fin) return StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(message.toByteArray())).toString();
            fragmented = true;
        }
        throw new IOException("Message frame count limit");
    }

    private static void readFully(InputStream in, byte[] bytes, int count) throws IOException {
        int offset = 0;
        while (offset < count) {
            int n = in.read(bytes, offset, count - offset);
            if (n <= 0) throw new EOFException("Incomplete frame payload");
            offset += n;
        }
    }
}
