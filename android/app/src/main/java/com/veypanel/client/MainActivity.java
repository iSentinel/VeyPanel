package com.veypanel.client;

import android.app.Activity;
import android.content.Intent;
import com.google.zxing.integration.android.IntentIntegrator;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import javax.net.ssl.SSLException;

public final class MainActivity extends Activity {
    private static final int SCAN_REQUEST = 4091;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private ReaderSession session;
    private TelemetryFeed stream;
    private long nextStreamAttempt;
    private CredentialStore credentials;
    private SavedReader savedReader;
    private CheckBox remember;
    private Button reconnect;
    private TextView credentialStatus;
    private boolean savePending;
    private boolean changingRemember;
    private boolean storageBusy;
    private int storageRevision;
    private boolean storageFault;
    private static final ExecutorService STORAGE = Executors.newSingleThreadExecutor();
    private EnrollmentClient.Claim claim;
    private Button approve;
    private boolean enrollmentBusy;
    private EditText input;
    private TextView status;
    private TextView diagnosticStatus;
    private final ConnectionDiagnostics diagnostics = new ConnectionDiagnostics();
    private MonitorPanel monitor;
    private LinearLayout controls;
    private boolean hideOnSample = true;
    private Future<?> request;
    private final ExecutorService historyWorker = Executors.newSingleThreadExecutor();
    private final ExecutorService videoWorker = Executors.newSingleThreadExecutor();
    private Future<?> videoRequest;
    private Button videoButton;
    private Button videoDecodeButton;
    private int videoRevision;
    private TextView videoStatus;
    private boolean videoBusy;
    private Future<?> historyRequest;
    private boolean historyBusy;
    private java.time.Instant lastLive;
    private boolean resumed;
    private int generation;
    private final Runnable poll = this::pollOnce;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        credentials = new CredentialStore(getApplicationContext());
        buildUi();
        restoreCredential();
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
        status = new TextView(this); status.setTextSize(16); column.addView(status);
        diagnosticStatus = new TextView(this); diagnosticStatus.setTextSize(13);
        diagnosticStatus.setVisibility(android.view.View.GONE);
        Button diagnosticToggle = new Button(this);
        diagnosticToggle.setText("Show / hide diagnostics");
        diagnosticToggle.setOnClickListener(v -> {
            diagnosticStatus.setVisibility(diagnosticStatus.getVisibility() == android.view.View.VISIBLE
                ? android.view.View.GONE : android.view.View.VISIBLE);
            renderDiagnostics();
        });
        column.addView(diagnosticToggle); column.addView(diagnosticStatus);
        Button toggle = new Button(this); toggle.setText("Show / hide connection controls");
        column.addView(toggle);
        controls = new LinearLayout(this); controls.setOrientation(LinearLayout.VERTICAL); column.addView(controls);
        toggle.setOnClickListener(v -> controls.setVisibility(controls.getVisibility() == android.view.View.VISIBLE ? android.view.View.GONE : android.view.View.VISIBLE));
        input = new EditText(this);
        input.setHint("Paste private reader or invitation link");
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD
            | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setSingleLine(true); input.setSaveEnabled(false);
        input.setImportantForAutofill(android.view.View.IMPORTANT_FOR_AUTOFILL_NO);
        controls.addView(input);
        Button scan = new Button(this); scan.setText("Scan invitation QR");
        scan.setOnClickListener(v -> scanInvitation()); controls.addView(scan);
        remember = new CheckBox(this); remember.setText("Remember access on this tablet");
        remember.setSaveEnabled(false); controls.addView(remember);
        credentialStatus = new TextView(this); controls.addView(credentialStatus);
        reconnect = new Button(this); reconnect.setText("Connect saved access"); reconnect.setEnabled(false);
        reconnect.setOnClickListener(v -> reconnectSaved()); controls.addView(reconnect);
        Button forget = new Button(this); forget.setText("Forget saved access on tablet");
        forget.setOnClickListener(v -> forgetAccess()); controls.addView(forget);
        remember.setOnCheckedChangeListener((v, checked) -> {
            if (changingRemember) return;
            if (!checked) { savePending = false; deleteCredential(); }
            else if (session != null && !session.sameAccess(savedReader == null ? null : savedReader.session)) savePending = true;
        });
        Button connect = new Button(this); connect.setText("Connect");
        connect.setOnClickListener(v -> connect()); controls.addView(connect);
        approve = new Button(this); approve.setText("Check owner approval");
        approve.setVisibility(android.view.View.GONE);
        approve.setOnClickListener(v -> finishEnrollment()); controls.addView(approve);
        Button disconnect = new Button(this); disconnect.setText("Disconnect");
        disconnect.setOnClickListener(v -> { stopPoll(); session = null; clearClaim(); savePending = false; input.setText(""); offline("Disconnected"); });
        controls.addView(disconnect);
        monitor = new MonitorPanel(this); monitor.onHistoryRefresh(this::refreshHostHistory); column.addView(monitor);
        videoButton = new Button(this);
        videoButton.setText("Inspect video decoders");
        videoButton.setOnClickListener(v -> inspectVideoDecoders());
        column.addView(videoButton);
        videoDecodeButton = new Button(this);
        videoDecodeButton.setText("Run local AVC decode test");
        videoDecodeButton.setOnClickListener(v -> runLocalVideoTest());
        column.addView(videoDecodeButton);
        videoStatus = new TextView(this); videoStatus.setText("No decoder inspection run");
        videoStatus.setTextSize(13); column.addView(videoStatus);
        setContentView(scroll);
    }

    private void inspectVideoDecoders() {
        runVideoJob(false);
    }

    private void runLocalVideoTest() {
        runVideoJob(true);
    }

    private void runVideoJob(boolean decode) {
        if (!resumed || videoBusy) return;
        videoBusy = true; videoButton.setEnabled(false); videoDecodeButton.setEnabled(false);
        videoStatus.setText(decode ? "Decoding bundled synthetic AVC clip…" : "Inspecting decoders…");
        int revision = ++videoRevision;
        videoRequest = videoWorker.submit(() -> {
            String report;
            try {
                report = decode ? LocalAvcSelfTest.run(getApplicationContext()).report()
                    : VideoDecoderSurvey.report(VideoDecoderSurvey.collect());
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                return;
            } catch (Exception ex) {
                report = decode ? "Local AVC test FAILED or decoder unavailable."
                    : "Decoder inventory unavailable.";
            }
            String message = report;
            main.post(() -> finishVideoJob(revision, message));
        });
    }

    private void finishVideoJob(int revision, String report) {
        if (!resumed || revision != videoRevision) return;
        videoBusy = false;
        videoButton.setEnabled(true); videoDecodeButton.setEnabled(true);
        videoStatus.setText(report);
    }

    private void scanInvitation() {
        if (storageBusy || enrollmentBusy || storageFault) {
            credentialStatus.setText("Finish credential or enrollment operation first."); return;
        }
        input.setText("");
        IntentIntegrator scanner = new IntentIntegrator(this);
        scanner.setCaptureActivity(PrivateScanActivity.class);
        scanner.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE);
        scanner.setOrientationLocked(false);
        scanner.setBeepEnabled(false);
        scanner.setBarcodeImageEnabled(false);
        scanner.setPrompt("Scan this PC's VeyPanel invitation QR");
        try { startActivityForResult(scanner.createScanIntent(), SCAN_REQUEST); }
        catch (android.content.ActivityNotFoundException ex) { credentialStatus.setText("QR scanner unavailable."); }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != SCAN_REQUEST) return;
        input.setText("");
        if (resultCode != RESULT_OK || data == null) {
            credentialStatus.setText("Scan canceled or camera unavailable."); return;
        }
        String value = IntentIntegrator.parseActivityResult(resultCode, data).getContents();
        try {
            InvitationLink.parse(value);
            input.setText(value);
            credentialStatus.setText("Valid invitation format. Press Connect to claim over HTTPS.");
        } catch (IllegalArgumentException ex) {
            credentialStatus.setText("QR is not a VeyPanel invitation.");
        }
    }

    private void connect() {
        if (storageBusy || storageFault) { credentialStatus.setText("Complete credential operation or Forget before connecting."); return; }
        String link = input.getText().toString();
        input.setText("");
        ReaderSession reader = null;
        InvitationLink invitation = null;
        try { reader = ReaderSession.parse(link); }
        catch (IllegalArgumentException ignored) {
            try { invitation = InvitationLink.parse(link); }
            catch (IllegalArgumentException ex) {
                credentialStatus.setText("Invalid link. Existing session and saved access unchanged.");
                return;
            }
        }
        stopPoll(); session = null; clearClaim(); savePending = false;
        hideOnSample = true;
        if (reader != null) {
            session = reader; savePending = remember.isChecked() && !reader.sameAccess(savedReader == null ? null : savedReader.session);
            offline("Connecting…"); main.post(poll);
        } else startEnrollment(invitation);
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
                    clearClaim(); session = result; savePending = remember.isChecked(); offline("Enrolled. Connecting…"); main.post(poll);
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
        if (stream == null && android.os.SystemClock.elapsedRealtime() >= nextStreamAttempt) {
            diagnostics.attempt(); renderDiagnostics();
            try { stream = new TelemetryStream(chosen); }
            catch (RuntimeException ex) {
                diagnostics.fallback(); renderDiagnostics();
                nextStreamAttempt = android.os.SystemClock.elapsedRealtime() + 15000;
            }
        }
        TelemetryFeed active = stream;
        if (active != null) {
            request = worker.submit(() -> readStream(current, active));
            return;
        }
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

    private void readStream(int current, TelemetryFeed active) {
        try {
            TelemetrySample sample = active.next();
            main.post(() -> complete(current, sample, null, false));
        } catch (Exception ex) {
            boolean tls = TelemetryStream.isTlsError(ex);
            main.post(() -> streamFailed(current, active, tls));
        }
    }

    private void streamFailed(int current, TelemetryFeed active, boolean tls) {
        active.close();
        if (!resumed || current != generation || stream != active) return;
        stream = null;
        if (tls) {
            complete(current, null, "TLS trust failed. Verify the PC certificate.", true);
            return;
        }
        diagnostics.fallback(); renderDiagnostics();
        nextStreamAttempt = android.os.SystemClock.elapsedRealtime() + 15000;
        offline("WSS unavailable · checking HTTPS REST");
        main.post(poll);
    }

    private void complete(int current, TelemetrySample sample, String error, boolean terminal) {
        if (!resumed || current != generation) return;
        if (sample == null || !SampleRules.fresh(sample.stamp, java.time.Instant.now())) {
            if (terminal) diagnostics.mark("Access expired or revoked".equals(error)
                ? ConnectionDiagnostics.Event.DENIED : ConnectionDiagnostics.Event.TLS);
            else if (sample == null) diagnostics.networkError();
            else diagnostics.mark(ConnectionDiagnostics.Event.STALE);
            offline(error == null ? "Stale sample" : error);
        }
        else {
            showSample(sample);
            if (savePending && remember.isChecked() && !storageBusy && !storageFault) persistCurrent();
        }
        if (terminal) {
            if ("Access expired or revoked".equals(error) && session != null
                && savedReader != null && session.sameAccess(savedReader.session)) deleteCredential();
            stopPoll(false); session = null; savePending = false;
            diagnostics.mark("Access expired or revoked".equals(error)
                ? ConnectionDiagnostics.Event.DENIED : ConnectionDiagnostics.Event.TLS);
            renderDiagnostics(); return;
        }
        main.postDelayed(poll, 1000);
    }

    private void restoreCredential() {
        storageBusy = true;
        int revision = ++storageRevision;
        remember.setEnabled(false);
        STORAGE.submit(() -> {
            SavedReader result = null;
            boolean failed = false;
            try { result = credentials.load(); } catch (Exception ex) { failed = true; }
            SavedReader loaded = result;
            boolean error = failed;
            main.post(() -> {
                if (isDestroyed() || revision != storageRevision) return;
                storageBusy = false; storageFault = error; savedReader = loaded;
                remember.setEnabled(true);
                changingRemember = true; remember.setChecked(loaded != null); changingRemember = false;
                reconnect.setEnabled(loaded != null);
                credentialStatus.setText(error ? "Saved access unreadable; verify or forget it."
                    : loaded == null ? "No saved access" : "Saved access available · Connect saved access");
            });
        });
    }

    private void reconnectSaved() {
        if (storageBusy || storageFault || savedReader == null) return;
        stopPoll(); clearClaim(); savePending = false; session = null;
        if (!savedReader.validAt(java.time.Instant.now())) {
            deleteCredential(); offline("Saved access expired"); return;
        }
        session = savedReader.session; hideOnSample = true;
        offline("Connecting saved access…"); main.post(poll);
    }

    private void persistCurrent() {
        if (session == null) return;
        savePending = false; storageBusy = true;
        SavedReader record = new SavedReader(session, java.time.Instant.now());
        int revision = ++storageRevision;
        STORAGE.submit(() -> {
            boolean success = false;
            try { credentials.save(record); success = true; } catch (Exception ignored) { }
            boolean ok = success;
            main.post(() -> {
                // The save was accepted after an authorized sample. Pause/rotation
                // does not undo it; a later explicit Forget is queued after it.
                if (isDestroyed() || revision != storageRevision) return;
                storageBusy = false; storageFault = !ok; savedReader = ok ? record : null;
                reconnect.setEnabled(ok);
                credentialStatus.setText(ok ? "Encrypted reader access saved" : "Save failed; access is memory-only");
            });
        });
    }

    private void deleteCredential() {
        savedReader = null; reconnect.setEnabled(false);
        storageBusy = true;
        int revision = ++storageRevision;
        STORAGE.submit(() -> {
            boolean success = false;
            try { credentials.forget(); success = true; } catch (Exception ignored) { }
            boolean ok = success;
            main.post(() -> {
                if (isDestroyed() || revision != storageRevision) return;
                storageBusy = false; storageFault = !ok;
                remember.setEnabled(true);
                credentialStatus.setText(ok ? "No saved access" : "Forget failed; clear app data before reuse.");
            });
        });
    }

    private void forgetAccess() {
        stopPoll(); session = null; clearClaim(); savePending = false;
        changingRemember = true; remember.setChecked(false); changingRemember = false;
        deleteCredential(); offline("Disconnected. Forget requested; revoke on PC to invalidate the token there.");
    }

    private void refreshHostHistory() {
        if (!resumed || session == null || historyBusy || lastLive == null
            || !SampleRules.fresh(lastLive, java.time.Instant.now())) return;
        int current = generation;
        ReaderSession chosen = session;
        historyBusy = true;
        monitor.historyEnabled(false);
        monitor.historyFeedback("Refreshing Host history…");
        historyRequest = historyWorker.submit(() -> {
            try {
                MonitorHistory.Point[] points = TelemetryClient.fetchHistory(chosen);
                main.post(() -> finishHistory(current, chosen, points, null, false));
            } catch (TelemetryClient.Denied ex) {
                main.post(() -> finishHistory(current, chosen, null, "Access expired or revoked", true));
            } catch (SSLException ex) {
                main.post(() -> finishHistory(current, chosen, null, "TLS trust failed. Verify the PC certificate.", true));
            } catch (Exception ex) {
                main.post(() -> finishHistory(current, chosen, null, "Host history unavailable; local data retained", false));
            }
        });
    }

    private void finishHistory(int current, ReaderSession chosen, MonitorHistory.Point[] points,
                               String error, boolean terminal) {
        if (!resumed || current != generation || !chosen.sameAccess(session)) return;
        historyBusy = false;
        if (terminal) { complete(current, null, error, true); return; }
        if (points != null) monitor.hostHistory(points);
        else monitor.historyFeedback(error);
        monitor.historyEnabled(lastLive != null && SampleRules.fresh(lastLive, java.time.Instant.now()));
    }

    private void renderDiagnostics() {
        diagnosticStatus.setText(diagnostics.describe(android.os.SystemClock.elapsedRealtime()));
    }

    private void showSample(TelemetrySample s) {
        diagnostics.fresh(stream != null, android.os.SystemClock.elapsedRealtime());
        renderDiagnostics();
        lastLive = s.stamp;
        monitor.historyEnabled(!historyBusy);
        status.setText("Connected · " + (stream == null ? "HTTPS REST" : "WSS") + " · " + s.stamp);
        monitor.render(s); monitor.observe(s);
        if (hideOnSample) { controls.setVisibility(android.view.View.GONE); hideOnSample = false; }
        main.removeCallbacks(expire);
        main.postDelayed(expire, 5000);
    }

    private final Runnable expire = () -> {
        diagnostics.mark(ConnectionDiagnostics.Event.STALE);
        offline("No fresh sample");
    };
    private void offline(String message) {
        main.removeCallbacks(expire);
        status.setText(message); renderDiagnostics();
        lastLive = null; monitor.historyEnabled(false);
        monitor.render(null);
        controls.setVisibility(android.view.View.VISIBLE);
    }

    private void stopPoll() { stopPoll(true); }

    private void stopPoll(boolean resetDiagnostics) {
        generation++;
        if (resetDiagnostics) diagnostics.reset();
        renderDiagnostics();
        lastLive = null; historyBusy = false;
        if (historyRequest != null) historyRequest.cancel(true);
        monitor.historyEnabled(false);
        monitor.clearHistory();
        if (stream != null) { stream.close(); stream = null; }
        nextStreamAttempt = 0;
        // A claim/finish interrupted during an in-flight exchange is ambiguous; do not replay it.
        if (enrollmentBusy) clearClaim();
        main.removeCallbacks(poll);
        main.removeCallbacks(expire);
        if (request != null) request.cancel(true);
    }
    @Override protected void onResume() { super.onResume(); resumed = true; if (session != null) main.post(poll); else if (claim != null) showClaim(); }
    @Override protected void onPause() {
        if (videoRequest != null) videoRequest.cancel(true);
        videoRevision++;
        videoBusy = false; videoButton.setEnabled(true); videoDecodeButton.setEnabled(true);
        resumed = false; stopPoll(); diagnostics.mark(ConnectionDiagnostics.Event.PAUSED); offline("Paused"); super.onPause(); }
    @Override protected void onDestroy() { stopPoll(); session = null; clearClaim(); worker.shutdownNow(); historyWorker.shutdownNow(); videoWorker.shutdownNow(); super.onDestroy(); }
}
