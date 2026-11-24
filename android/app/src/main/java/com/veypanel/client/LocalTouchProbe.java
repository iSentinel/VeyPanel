package com.veypanel.client;

/** Convert touches on the synthetic square video to local pixel coordinates only. */
final class LocalTouchProbe {
    private static final int CLIP_WIDTH = 64;
    private static final int CLIP_HEIGHT = 64;

    private LocalTouchProbe() { }

    static String describe(float x, float y, int width, int height, int pointers) {
        if (pointers != 1) return "Local preview touch: multi-touch rejected · not sent to Windows";
        TouchMath.Pixel pixel = TouchMath.map(x, y,
            new TouchMath.Viewport(width, height, CLIP_WIDTH, CLIP_HEIGHT, 0),
            new TouchMath.Rect(0, 0, CLIP_WIDTH, CLIP_HEIGHT));
        if (pixel == null) return "Local preview touch: outside frame · not sent to Windows";
        return "Local preview touch: (" + pixel.x + ", " + pixel.y
            + ") / 64×64 · not sent to Windows";
    }
}
