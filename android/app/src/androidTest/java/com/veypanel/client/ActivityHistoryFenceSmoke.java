package com.veypanel.client;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.time.Instant;
import java.util.concurrent.FutureTask;

/** Exercise ordered foreground callback interleavings without network or real grants. */
final class ActivityHistoryFenceSmoke {
    private static final String TLS = "TLS trust failed. Verify the PC certificate.";
    private ActivityHistoryFenceSmoke() { }

    /** Test both terminal callback orders on separate Activity instances. */
    static void run(Instrumentation runner) {
        exercise(runner, false);
        exercise(runner, true);
    }

    private static void exercise(Instrumentation runner, boolean historyFirst) {
        Activity activity = runner.startActivitySync(new Intent(
            runner.getTargetContext(), MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try {
            runner.runOnMainSync(() -> {
                try { checkOrder(activity, historyFirst); }
                catch (Exception failure) { throw new IllegalStateException("History fence fixture failed", failure); }
            });
        } finally {
            runner.runOnMainSync(activity::finish);
            runner.waitForIdleSync();
        }
    }

    private static void checkOrder(Activity activity, boolean historyFirst) throws Exception {
        ReaderSession session = ReaderSession.fixture('A');
        TelemetrySample sample = TelemetrySample.parse(new org.json.JSONObject()
            .put("timestampUtc", Instant.now().toString()).put("cpuPercent", 12).toString());
        MonitorHistory.Point[] points = {new MonitorHistory.Point(sample)};
        int generation = (Integer) get(activity, "generation");
        FakeFeed feed = new FakeFeed();
        FutureTask<Void> live = new FutureTask<>(() -> null);
        FutureTask<Void> history = new FutureTask<>(() -> null);
        set(activity, "session", session);
        set(activity, "stream", feed);
        call(activity, "showSample", new Class<?>[]{TelemetrySample.class}, sample);
        historyCallback(activity, generation, session, points, null, false);
        require(text(activity, "Host snapshot refreshed") != null, "Positive history control");
        set(activity, "request", live);
        set(activity, "historyRequest", history);
        set(activity, "historyBusy", true);
        if (historyFirst) historyCallback(activity, generation, session, null, TLS, true);
        else liveCallback(activity, generation, null, TLS, true);
        require(live.isCancelled() && history.isCancelled() && feed.closed == 1, "Both requests cancelled");
        require((Integer) get(activity, "generation") != generation, "Generation invalidated");
        requireTerminal(activity);
        // Simulate workers that had posted results before cancellation completed.
        liveCallback(activity, generation, sample, null, false);
        historyCallback(activity, generation, session, points, null, false);
        historyCallback(activity, generation, session, null, "Access expired or revoked", true);
        requireTerminal(activity);
        require(feed.closed == 1, "No duplicate feed close");
        verifySameAccessReconnect(activity, generation, session, sample, points);
    }

    private static void verifySameAccessReconnect(Activity activity, int old, ReaderSession session,
                                                   TelemetrySample sample, MonitorHistory.Point[] points)
            throws Exception {
        // A subsequent explicit reconnect may use the same access identity.
        set(activity, "session", session);
        call(activity, "showSample", new Class<?>[]{TelemetrySample.class}, sample);
        historyCallback(activity, old, session, points, null, false);
        liveCallback(activity, old, null, TLS, true);
        require(get(activity, "session") == session && text(activity, "Connected ·") != null,
            "Old terminal callback rejected after reconnect");
        require(text(activity, "Host snapshot refreshed") == null, "Old history rejected after reconnect");
    }

    private static void requireTerminal(Activity activity) throws Exception {
        require(get(activity, "session") == null && get(activity, "stream") == null
            && get(activity, "lastLive") == null && Boolean.FALSE.equals(get(activity, "historyBusy")),
            "Terminal session state");
        TextView history = text(activity, "Refresh Host history");
        require(history != null && !history.isEnabled() && text(activity, TLS) != null
            && text(activity, "Host snapshot refreshed") == null
            && text(activity, "Host + foreground history") == null, "Terminal UI and history state");
    }

    private static void liveCallback(Activity activity, int current, TelemetrySample sample,
                                     String error, boolean terminal) throws Exception {
        call(activity, "complete", new Class<?>[]{int.class, TelemetrySample.class, String.class, boolean.class},
            current, sample, error, terminal);
    }

    private static void historyCallback(Activity activity, int current, ReaderSession session,
                                        MonitorHistory.Point[] points, String error, boolean terminal)
            throws Exception {
        call(activity, "finishHistory", new Class<?>[]{int.class, ReaderSession.class,
            MonitorHistory.Point[].class, String.class, boolean.class}, current, session, points, error, terminal);
    }

    private static Object get(Activity activity, String name) throws Exception {
        Field field = MainActivity.class.getDeclaredField(name);
        field.setAccessible(true);
        return field.get(activity);
    }

    private static void set(Activity activity, String name, Object value) throws Exception {
        Field field = MainActivity.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(activity, value);
    }

    private static void call(Activity activity, String name, Class<?>[] types, Object... args)
            throws Exception {
        Method method = MainActivity.class.getDeclaredMethod(name, types);
        method.setAccessible(true);
        method.invoke(activity, args);
    }

    private static TextView text(Activity activity, String prefix) {
        return find(activity.getWindow().getDecorView(), prefix);
    }

    private static TextView find(View view, String prefix) {
        if (view instanceof TextView && ((TextView)view).getText().toString().startsWith(prefix))
            return (TextView)view;
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)view;
            for (int i = 0; i < group.getChildCount(); i++) {
                TextView found = find(group.getChildAt(i), prefix);
                if (found != null) return found;
            }
        }
        return null;
    }

    private static void require(boolean condition, String label) {
        if (!condition) throw new IllegalStateException(label);
    }

    private static final class FakeFeed implements TelemetryFeed {
        int closed;
        @Override public TelemetrySample next() { throw new IllegalStateException("Unexpected network read"); }
        @Override public void close() { closed++; }
    }
}
