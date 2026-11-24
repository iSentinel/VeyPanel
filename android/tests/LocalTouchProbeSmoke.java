package com.veypanel.client;

/** JVM fixtures never access the Android input injection APIs. */
final class LocalTouchProbeSmoke {
    private LocalTouchProbeSmoke() { }

    static void run() {
        assertContains(LocalTouchProbe.describe(50, 50, 100, 100, 1), "(32, 32)");
        assertContains(LocalTouchProbe.describe(0, 0, 100, 100, 1), "(0, 0)");
        assertContains(LocalTouchProbe.describe(100, 100, 100, 100, 1), "(63, 63)");
        assertContains(LocalTouchProbe.describe(5, 50, 200, 100, 1), "outside frame");
        assertContains(LocalTouchProbe.describe(50, 50, 100, 100, 2), "multi-touch rejected");
        assertContains(LocalTouchProbe.describe(Float.NaN, 1, 100, 100, 1), "outside frame");
        assertContains(LocalTouchProbe.describe(1, 1, 0, 100, 1), "outside frame");
        assertContains(LocalTouchProbe.describe(50, 50, 100, 100, 1), "not sent to Windows");
        System.out.println("PASS: local AVC touch probe is bounded and never forwards input");
    }

    private static void assertContains(String text, String expected) {
        if (!text.contains(expected)) throw new IllegalStateException("Touch fixture mismatch");
    }
}
