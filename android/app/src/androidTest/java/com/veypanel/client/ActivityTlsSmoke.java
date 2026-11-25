package com.veypanel.client;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;

/** Exercise foreground terminal behavior with the isolated untrusted TLS fixture. */
final class ActivityTlsSmoke {
    private ActivityTlsSmoke() { }

    /** Use the real production transport; only the test supplies a loopback session. */
    static void run(Instrumentation runner) {
        Activity activity = runner.startActivitySync(new Intent(
            runner.getTargetContext(), MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try {
            runner.runOnMainSync(() -> begin(activity));
            awaitTerminal(runner, activity);
            // Exceed several normal one-second poll intervals. No automatic retry.
            SystemClock.sleep(3500);
            runner.runOnMainSync(() -> {
                if (!terminal(activity)) throw new IllegalStateException("TLS session resumed");
            });
        } finally {
            runner.runOnMainSync(activity::finish);
            runner.waitForIdleSync();
        }
    }

    private static void begin(Activity activity) {
        if (field(activity, "session") != null || !Boolean.TRUE.equals(field(activity, "resumed")))
            throw new IllegalStateException("Unexpected initial Activity state");
        try {
            Field session = MainActivity.class.getDeclaredField("session");
            session.setAccessible(true);
            session.set(activity, ReaderSession.fixture('A'));
            Method poll = MainActivity.class.getDeclaredMethod("pollOnce");
            poll.setAccessible(true);
            poll.invoke(activity);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Fixture session admission failed");
        }
    }

    private static Object field(Activity activity, String name) {
        try {
            Field field = MainActivity.class.getDeclaredField(name);
            field.setAccessible(true);
            return field.get(activity);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Fixture Activity inspection failed");
        }
    }

    private static void awaitTerminal(Instrumentation runner, Activity activity) {
        AtomicBoolean done = new AtomicBoolean();
        long deadline = SystemClock.elapsedRealtime() + 15000;
        while (!done.get() && SystemClock.elapsedRealtime() < deadline) {
            runner.runOnMainSync(() -> done.set(terminal(activity)));
            if (!done.get()) SystemClock.sleep(100);
        }
        if (!done.get()) throw new IllegalStateException("Terminal TLS Activity state missing");
    }

    private static boolean terminal(Activity activity) {
        View root = activity.getWindow().getDecorView();
        TextView diagnostics = find(root, "Connection diagnostics");
        TextView status = find(root, "TLS trust failed.");
        TextView history = find(root, "Refresh Host history");
        if (diagnostics == null || status == null || history == null) return false;
        String text = diagnostics.getText().toString();
        return text.startsWith("Connection diagnostics · TLS")
            && text.contains("WSS attempts: 1 · Fallbacks: 0")
            && text.contains("REST errors: 0 · Fresh samples: 0")
            && !history.isEnabled() && field(activity, "session") == null
            && field(activity, "stream") == null;
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
}
