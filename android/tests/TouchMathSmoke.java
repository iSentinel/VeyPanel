package com.veypanel.client;

/** Portable geometry assertions matching Windows TouchMappingTests vectors. */
final class TouchMathSmoke {
    private TouchMathSmoke() { }

    static void run() {
        TouchMath.Viewport full = new TouchMath.Viewport(1920, 1080, 1920, 1080, 0);
        TouchMath.Rect desktop = new TouchMath.Rect(-1920, -100, 0, 980);
        check("negative origin", point(-1920, -100), TouchMath.map(0, 0, full, desktop));
        check("opposite corner", point(-1, 979), TouchMath.map(1920, 1080, full, desktop));
        check("center", point(-960, 440), TouchMath.map(960, 540, full, desktop));
        TouchMath.Viewport bars = new TouchMath.Viewport(200, 100, 100, 100, 0);
        TouchMath.Rect square = new TouchMath.Rect(0, 0, 100, 100);
        check("left bar", null, TouchMath.map(49, 50, bars, square));
        check("right bar", null, TouchMath.map(151, 50, bars, square));
        check("left content", point(0, 50), TouchMath.map(50, 50, bars, square));
        check("right content", point(99, 50), TouchMath.map(150, 50, bars, square));
        check("90 degree rotation", point(0, 99), rotate(0, 0, 90));
        check("180 degree rotation", point(199, 99), rotate(0, 0, 180));
        check("270 degree rotation", point(199, 0), rotate(0, 0, 270));
        check("invalid viewport", null, TouchMath.map(1, 1,
            new TouchMath.Viewport(0, 100, 100, 100, 0), square));
        check("invalid target", null, TouchMath.map(1, 1, full,
            new TouchMath.Rect(5, 4, 3, 2)));
        check("invalid rotation", null, TouchMath.map(1, 1,
            new TouchMath.Viewport(100, 100, 100, 100, 45), square));
        check("NaN", null, TouchMath.map(Double.NaN, 50, bars, square));
        check("infinity", null, TouchMath.map(100, Double.POSITIVE_INFINITY, bars, square));
        check("out of screen", null, TouchMath.map(200, 50,
            new TouchMath.Viewport(100, 100, 100, 100, 0), square));
        check("desktop overflow", null, TouchMath.map(50, 50, full,
            new TouchMath.Rect(Integer.MIN_VALUE, 0, Integer.MAX_VALUE, 100)));
        System.out.println("PASS: Android touch math matches Windows rotation and letterbox fixtures");
    }

    private static TouchMath.Pixel rotate(int x, int y, int degrees) {
        return TouchMath.map(x, y, new TouchMath.Viewport(100, 200, 100, 200, degrees),
            new TouchMath.Rect(0, 0, 200, 100));
    }

    private static TouchMath.Pixel point(int x, int y) { return new TouchMath.Pixel(x, y); }

    private static void check(String name, TouchMath.Pixel expected, TouchMath.Pixel actual) {
        if (expected == null ? actual != null : !expected.equals(actual))
            throw new IllegalStateException("Touch fixture mismatch: " + name);
    }
}
