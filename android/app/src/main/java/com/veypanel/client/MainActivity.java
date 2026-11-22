package com.veypanel.client;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.*;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import javax.net.ssl.SSLException;

public final class MainActivity extends Activity {
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private ReaderSession session;
    private EnrollmentClient.Claim claim;
    private Button approve;
    private boolean enrollmentBusy;
    private EditText input;
    private TextView status, values;
    private Future<?> request;
    private boolean resumed;
    private int generation;
    private final Runnable poll = this::pollOnce;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        buildUi();
        offline("Enter a private reader link from the PC owner.");
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(20 * getResources().getDisplayMetrics().density);
        column.setPadding(pad,pad,pad,pad);
        scroll.setOnApplyWindowInsetsListener((v,insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(column);
        TextView title = new TextView(this);
        title.setText("VeyPanel · Monitor"); title.setTextSize(28);
        column.addView(title);
        input = new EditText(this);
        input.setHint("Paste private reader or invitation link");
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD
            | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setSingleLine(true); input.setSaveEnabled(false);
        input.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO);
        column.addView(input);
        Button connect = new Button(this); connect.setText("Connect");
        connect.setOnClickListener(v -> connect()); column.addView(connect);
        approve = new Button(this); approve.setText("Check owner approval");
        approve.setVisibility(android.view.View.GONE);
        approve.setOnClickListener(v -> finishEnrollment()); column.addView(approve);
        Button disconnect = new Button(this); disconnect.setText("Disconnect");
        disconnect.setOnClickListener(v -> { stopPoll(); session = null; clearClaim(); input.setText(""); offline("Disconnected"); });
        column.addView(disconnect);
        status = new TextView(this); status.setTextSize(16); column.addView(status);
        values = new TextView(this); values.setTextSize(22); values.setPadding(0,pad,0,0);
        column.addView(values);
        setContentView(scroll);
    }

    private void connect() {
        stopPoll(); session = null; clearClaim();
        String link = input.getText().toString();
        input.setText("");
        try {
            session = ReaderSession.parse(link);
            offline("Connecting…"); main.post(poll); return;
        } catch (IllegalArgumentException ignored) { }
        try { startEnrollment(InvitationLink.parse(link)); }
        catch (IllegalArgumentException ex) { offline("Use a private IPv4 HTTPS reader or invitation link on port 47861."); }
    }

    private void clearClaim() {
        claim = null; enrollmentBusy = false;
        approve.setVisibility(android.view.View.GONE); approve.setEnabled(true);
    }

    private void startEnrollment(InvitationLink link) {
        int current = generation;
        enrollmentBusy = true;
        offline("Claiming invitation…");
        request = worker.submit(() -> {
            try {
                EnrollmentClient.Claim result = EnrollmentClient.claim(link);
                main.post(() -> {
                    if (!resumed || current != generation) return;
                    claim = result; enrollmentBusy = false; showClaim();
                });
            } catch (Exception ex) { main.post(() -> enrollmentError(current)); }
        });
    }

    private void showClaim() {
        if (claim == null || !claim.expires.isAfter(java.time.Instant.now())) {
            clearClaim(); offline("Invitation expired. Request a new link."); return;
        }
        offline("Compare code " + claim.code + " with the PC owner. Then check approval.");
        approve.setVisibility(android.view.View.VISIBLE);
        approve.setEnabled(!enrollmentBusy);
    }

    private void finishEnrollment() {
        if (!resumed || enrollmentBusy || claim == null) return;
        if (!claim.expires.isAfter(java.time.Instant.now())) { showClaim(); return; }
        int current = generation;
        EnrollmentClient.Claim chosen = claim;
        enrollmentBusy = true; approve.setEnabled(false);
        request = worker.submit(() -> {
            try {
                ReaderSession result = EnrollmentClient.finish(chosen);
                main.post(() -> {
                    if (!resumed || current != generation) return;
                    enrollmentBusy = false;
                    if (result == null) { showClaim(); return; }
                    clearClaim(); session = result; offline("Enrolled. Connecting…"); main.post(poll);
                });
            } catch (Exception ex) { main.post(() -> enrollmentError(current)); }
        });
    }

    private void enrollmentError(int current) {
        if (!resumed || current != generation) return;
        clearClaim(); offline("Enrollment failed. Verify HTTPS trust and request a new invitation.");
    }

    private void pollOnce() {
        if (!resumed || session == null) return;
        int current = generation;
        ReaderSession chosen = session;
        request = worker.submit(() -> {
            try {
                TelemetrySample sample = TelemetryClient.fetch(chosen);
                main.post(() -> complete(current, sample, null, false));
            } catch (TelemetryClient.Denied ex) {
                main.post(() -> complete(current, null, "Access expired or revoked", true));
            } catch (SSLException ex) {
                main.post(() -> complete(current, null, "TLS trust failed. Verify the PC certificate.", true));
            } catch (Exception ex) {
                main.post(() -> complete(current, null, "Unavailable / stale sample; retrying", false));
            }
        });
    }

    private void complete(int current, TelemetrySample sample, String error, boolean terminal) {
        if (!resumed || current != generation) return;
        if (sample == null || !SampleRules.fresh(sample.stamp, java.time.Instant.now()))
            offline(error == null ? "Stale sample" : error);
        else showSample(sample);
        if (terminal) { session = null; return; }
        main.postDelayed(poll, 1000);
    }

    private void showSample(TelemetrySample s) {
        status.setText("Connected · HTTPS REST · " + s.stamp);
        values.setText("CPU  " + pct(s.cpu) + "\nRAM  " + pct(s.ram) + "\nGPU  " + pct(s.gpu)
            + "\nVideo Encode  " + pct(s.encode) + "\nVideo Decode  " + pct(s.decode)
            + "\nDisk Read  " + rate(s.read) + "\nDisk Write  " + rate(s.write));
        main.removeCallbacks(expire);
        main.postDelayed(expire, 5000);
    }

    private final Runnable expire = () -> offline("No fresh sample");
    private void offline(String message) {
        main.removeCallbacks(expire);
        status.setText(message);
        values.setText("CPU  N/A\nRAM  N/A\nGPU  N/A\nVideo Encode  N/A\nVideo Decode  N/A\nDisk Read  N/A\nDisk Write  N/A");
    }
    private static String pct(Double n) { return n == null ? "N/A" : String.format(Locale.getDefault(), "%.1f%%", n); }
    private static String rate(Double n) { return n == null ? "N/A" : String.format(Locale.getDefault(), "%.2f MiB/s", n / 1048576); }

    private void stopPoll() {
        generation++;
        // A claim/finish interrupted during an in-flight exchange is ambiguous; do not replay it.
        if (enrollmentBusy) clearClaim();
        main.removeCallbacks(poll);
        main.removeCallbacks(expire);
        if (request != null) request.cancel(true);
    }
    @Override protected void onResume() { super.onResume(); resumed = true; if (session != null) main.post(poll); else if (claim != null) showClaim(); }
    @Override protected void onPause() { resumed = false; stopPoll(); offline("Paused"); super.onPause(); }
    @Override protected void onDestroy() { stopPoll(); session = null; clearClaim(); worker.shutdownNow(); super.onDestroy(); }
}
