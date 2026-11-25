package com.veypanel.client;

import android.app.Activity;
import android.app.Instrumentation;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.TextureView;
import android.content.Intent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ScrollView;
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
            verifyLocalTouch(runner, activity);
            verifyFreshPreview(runner, activity);
            verifyPreviewReset(runner, activity);
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
            revealBottom(root);
        });
        java.util.concurrent.atomic.AtomicBoolean complete = new java.util.concurrent.atomic.AtomicBoolean();
        for (int attempt = 0; attempt < 150 && !complete.get(); attempt++) {
            runner.waitForIdleSync();
            runner.runOnMainSync(() -> {
                View root = activity.getWindow().getDecorView();
                TextView status = find(root, "Local AVC preview: PASS", false);
                TextView button = find(root, "Preview local AVC frame", true);
                complete.set(status != null && button != null && button.isEnabled()
                    && status.getText().toString().contains("TextureView updates"));
            });
            if (!complete.get()) {
                try { Thread.sleep(100); }
                catch (InterruptedException ex) { Thread.currentThread().interrupt(); break; }
            }
        }
        if (!complete.get()) throw new IllegalStateException("Visible AVC preview did not complete");
    }

    private static void verifyLocalTouch(Instrumentation runner, Activity activity) {
        runner.runOnMainSync(() -> {
            View root = activity.getWindow().getDecorView();
            TextureView preview = findTexture(root);
            if (preview == null || !preview.isAvailable()
                || preview.getVisibility() != View.VISIBLE)
                throw new IllegalStateException("Local preview touch target missing");
            long when = SystemClock.uptimeMillis();
            float x = preview.getWidth() / 2f, y = preview.getHeight() / 2f;
            MotionEvent down = MotionEvent.obtain(when, when, MotionEvent.ACTION_DOWN, x, y, 0);
            MotionEvent up = MotionEvent.obtain(when, when + 30, MotionEvent.ACTION_UP, x, y, 0);
            try {
                if (!preview.dispatchTouchEvent(down) || !preview.dispatchTouchEvent(up))
                    throw new IllegalStateException("Local touch rejected");
            } finally { down.recycle(); up.recycle(); }
            TextView status = find(root, "Local preview touch:", false);
            if (status == null || !status.getText().toString().contains("(32, 32)")
                || !status.getText().toString().contains("not sent to Windows"))
                throw new IllegalStateException("Local synthetic touch output missing");
        });
    }

    private static void verifyFreshPreview(Instrumentation runner, Activity activity) {
        java.util.concurrent.atomic.AtomicReference<TextureView> previous =
            new java.util.concurrent.atomic.AtomicReference<>();
        runner.runOnMainSync(() ->
            previous.set(findTexture(activity.getWindow().getDecorView())));
        verifyLocalPreview(runner, activity);
        runner.runOnMainSync(() -> {
            TextureView current = findTexture(activity.getWindow().getDecorView());
            if (current == null || current == previous.get() || !current.isAvailable())
                throw new IllegalStateException("Preview generation reused previous view");
        });
        verifyLocalTouch(runner, activity);
    }

    private static void verifyPreviewReset(Instrumentation runner, Activity activity) {
        runner.runOnMainSync(() -> {
            View root = activity.getWindow().getDecorView();
            TextureView preview = findTexture(root);
            TextView button = find(root, "Inspect video decoders", true);
            if (button == null || !button.performClick() || preview == null
                    || preview.getVisibility() != View.GONE)
                throw new IllegalStateException("Previous preview not cleared");
            TextView status = find(root, "Local preview touch:", false);
            if (status == null || !status.getText().toString().contains("N/A"))
                throw new IllegalStateException("Previous touch state not cleared");
        });
    }

    private static TextureView findTexture(View view) {
        if (view instanceof TextureView) return (TextureView)view;
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)view;
            for (int i = 0; i < group.getChildCount(); i++) {
                TextureView result = findTexture(group.getChildAt(i));
                if (result != null) return result;
            }
        }
        return null;
    }

    private static void revealBottom(View root) {
        if (root instanceof ScrollView) {
            ((ScrollView)root).fullScroll(View.FOCUS_DOWN);
            return;
        }
        if (root instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)root;
            for (int i = 0; i < group.getChildCount(); i++)
                revealBottom(group.getChildAt(i));
        }
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
