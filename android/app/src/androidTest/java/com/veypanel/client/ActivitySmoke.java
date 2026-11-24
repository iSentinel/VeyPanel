package com.veypanel.client;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import java.util.concurrent.atomic.AtomicBoolean;

/** Isolated no-credential Activity startup and diagnostic visibility smoke. */
final class ActivitySmoke {
    private ActivitySmoke() { }

    static void run(Instrumentation runner) {
        Intent intent = new Intent(runner.getTargetContext(), MainActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Activity activity = runner.startActivitySync(intent);
        try {
            AtomicBoolean passed = new AtomicBoolean(false);
            runner.runOnMainSync(() -> {
                View root = activity.getWindow().getDecorView();
                TextView toggle = find(root, "Show / hide diagnostics", true);
                TextView diagnostics = find(root, "Connection diagnostics", false);
                TextView history = find(root, "Refresh Host history", true);
                TextView codecs = find(root, "Inspect video decoders", true);
                TextView local = find(root, "Run local AVC decode test", true);
                if (toggle == null || diagnostics == null || history == null
                    || diagnostics.getVisibility() != View.GONE || history.isEnabled() || codecs == null || local == null) return;
                toggle.performClick();
                boolean visible = diagnostics.getVisibility() == View.VISIBLE
                    && diagnostics.getText().toString().contains("IDLE");
                toggle.performClick();
                passed.set(visible && diagnostics.getVisibility() == View.GONE);
            });
            if (!passed.get()) throw new IllegalStateException("Activity diagnostics gate");
            verifyLocalDecoderButton(runner, activity);
            verifyLocalPreview(runner, activity);
        } finally {
            runner.runOnMainSync(activity::finish);
            runner.waitForIdleSync();
        }
    }

    private static void verifyLocalDecoderButton(Instrumentation runner, Activity activity) {
        runner.runOnMainSync(() -> {
            TextView button = find(activity.getWindow().getDecorView(),
                "Run local AVC decode test", true);
            if (button == null || !button.performClick())
                throw new IllegalStateException("Local decode action unavailable");
        });
        java.util.concurrent.atomic.AtomicBoolean complete = new java.util.concurrent.atomic.AtomicBoolean();
        for (int attempt = 0; attempt < 120 && !complete.get(); attempt++) {
            runner.waitForIdleSync();
            runner.runOnMainSync(() -> {
                TextView status = find(activity.getWindow().getDecorView(), "Local AVC decode: PASS", false);
                TextView button = find(activity.getWindow().getDecorView(), "Run local AVC decode test", true);
                complete.set(status != null && button != null && button.isEnabled()
                    && status.getText().toString().contains("Decoded buffers:"));
            });
            if (!complete.get()) {
                try { Thread.sleep(100); }
                catch (InterruptedException ex) { Thread.currentThread().interrupt(); break; }
            }
        }
        if (!complete.get()) throw new IllegalStateException("Activity local AVC decode result missing");
    }

    private static void verifyLocalPreview(Instrumentation runner, Activity activity) {
        runner.runOnMainSync(() -> {
            View root = activity.getWindow().getDecorView();
            TextView button = find(root, "Preview local AVC frame", true);
            if (button == null || !button.performClick())
                throw new IllegalStateException("Preview action unavailable");
        });
        java.util.concurrent.atomic.AtomicBoolean complete = new java.util.concurrent.atomic.AtomicBoolean();
        for (int attempt = 0; attempt < 150 && !complete.get(); attempt++) {
            runner.waitForIdleSync();
            runner.runOnMainSync(() -> {
                View root = activity.getWindow().getDecorView();
                TextView status = find(root, "Local AVC preview: PASS", false);
                TextView button = find(root, "Preview local AVC frame", true);
                complete.set(status != null && button != null && button.isEnabled()
                    && status.getText().toString().contains("Not a Windows video stream"));
            });
            if (!complete.get()) {
                try { Thread.sleep(100); }
                catch (InterruptedException ex) { Thread.currentThread().interrupt(); break; }
            }
        }
        if (!complete.get()) throw new IllegalStateException("Visible AVC preview did not complete");
    }

    private static TextView find(View view, String text, boolean button) {
        if (view instanceof TextView && (view instanceof Button) == button
            && ((TextView)view).getText().toString().startsWith(text)) return (TextView)view;
        if (view instanceof ViewGroup) {
            ViewGroup parent = (ViewGroup)view;
            for (int i = 0; i < parent.getChildCount(); i++) {
                TextView found = find(parent.getChildAt(i), text, button);
                if (found != null) return found;
            }
        }
        return null;
    }
}
