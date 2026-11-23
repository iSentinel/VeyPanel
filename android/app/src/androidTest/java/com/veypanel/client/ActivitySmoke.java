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
                if (toggle == null || diagnostics == null || history == null
                    || diagnostics.getVisibility() != View.GONE || history.isEnabled() || codecs == null) return;
                toggle.performClick();
                boolean visible = diagnostics.getVisibility() == View.VISIBLE
                    && diagnostics.getText().toString().contains("IDLE");
                toggle.performClick();
                passed.set(visible && diagnostics.getVisibility() == View.GONE);
            });
            if (!passed.get()) throw new IllegalStateException("Activity diagnostics gate");
        } finally {
            runner.runOnMainSync(activity::finish);
            runner.waitForIdleSync();
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
