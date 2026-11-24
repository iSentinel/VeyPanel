package com.veypanel.client;

/** Pure touch-to-desktop geometry; never injects input or opens network access. */
final class TouchMath {
    static final class Viewport {
        final int width, height, frameWidth, frameHeight, clockwise;

        Viewport(int width, int height, int frameWidth, int frameHeight, int clockwise) {
            this.width = width; this.height = height;
            this.frameWidth = frameWidth; this.frameHeight = frameHeight;
            this.clockwise = clockwise;
        }
    }

    static final class Rect {
        final int left, top, right, bottom;

        Rect(int left, int top, int right, int bottom) {
            this.left = left; this.top = top;
            this.right = right; this.bottom = bottom;
        }
    }

    static final class Pixel {
        final int x, y;

        Pixel(int x, int y) { this.x = x; this.y = y; }

        @Override public boolean equals(Object other) {
            return other instanceof Pixel && x == ((Pixel)other).x && y == ((Pixel)other).y;
        }

        @Override public int hashCode() { return 31 * x + y; }
    }

    private TouchMath() { }

    static Pixel map(double x, double y, Viewport view, Rect desktop) {
        if (!valid(view, desktop) || !Double.isFinite(x) || !Double.isFinite(y)) return null;
        double scale = Math.min((double)view.width / view.frameWidth,
            (double)view.height / view.frameHeight);
        double shownWidth = view.frameWidth * scale;
        double shownHeight = view.frameHeight * scale;
        double u = (x - (view.width - shownWidth) / 2) / shownWidth;
        double v = (y - (view.height - shownHeight) / 2) / shownHeight;
        if (u < 0 || u > 1 || v < 0 || v > 1) return null;
        double dx = horizontal(u, v, view.clockwise);
        double dy = vertical(u, v, view.clockwise);
        long width = (long)desktop.right - desktop.left;
        long height = (long)desktop.bottom - desktop.top;
        long px = desktop.left + Math.round(dx * (width - 1));
        long py = desktop.top + Math.round(dy * (height - 1));
        if (px < Integer.MIN_VALUE || px > Integer.MAX_VALUE
            || py < Integer.MIN_VALUE || py > Integer.MAX_VALUE) return null;
        return new Pixel((int)px, (int)py);
    }

    private static double horizontal(double u, double v, int angle) {
        if (angle == 90) return v;
        if (angle == 180) return 1 - u;
        if (angle == 270) return 1 - v;
        return u;
    }

    private static double vertical(double u, double v, int angle) {
        if (angle == 90) return 1 - u;
        if (angle == 180) return 1 - v;
        if (angle == 270) return u;
        return v;
    }

    private static boolean valid(Viewport v, Rect d) {
        long width = (long)d.right - d.left;
        long height = (long)d.bottom - d.top;
        return inRange(v.width) && inRange(v.height) && inRange(v.frameWidth)
            && inRange(v.frameHeight)
            && (v.clockwise == 0 || v.clockwise == 90
                || v.clockwise == 180 || v.clockwise == 270)
            && width > 0 && width <= 32768 && height > 0 && height <= 32768;
    }

    private static boolean inRange(int value) { return value > 0 && value <= 32768; }
}
