package com.veypanel.client;

import android.app.Activity;
import android.app.Instrumentation;
import android.os.Bundle;
import java.io.File;
import java.nio.file.Files;
import java.security.KeyStore;
import java.time.Instant;
import java.util.Arrays;

public final class StoreInstrumentation extends Instrumentation {
    private boolean isolated;
    private String fixtureCa;
    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        isolated = "true".equals(args.getString("isolated"));
        fixtureCa = args.getString("fixtureCa");
        start();
    }
    @Override public void onStart() {
        Bundle report = new Bundle();
        String stage = "isolation";
        StringBuilder results = new StringBuilder("\n");
        try {
            if (!isolated) throw new IllegalStateException("Explicit isolated test required");
            stage = "AndroidKeyStore";
            runStore();
            results.append("PASS: AndroidKeyStore actual encryption, reopen, fresh ciphertext, corruption, key removal and Forget\n");
            stage = "QR";
            runQr();
            results.append("PASS: synthetic offline QR decode\n");
            stage = "telemetry";
            runMetrics();
            results.append("PASS: Android extended telemetry fixture\n");
            stage = "history";
            runHistory();
            results.append("PASS: Android bounded history fixture\n");
            stage = "Host history codec";
            HostHistorySmoke.run();
            results.append("PASS: Android Host history codec fixture\n");
            stage = "Activity UI";
            ActivitySmoke.run(this);
            results.append("PASS: Android Activity diagnostics, local AVC decode and visible Surface preview\n");
            stage = "Android video decoder inventory";
            VideoDecoderSmoke.run();
            results.append("PASS: read-only Android video decoder API survey (no hardware guarantee)\n");
            stage = "Synthetic AVC decoding";
            VideoDecodeSmoke.run(getTargetContext());
            results.append("PASS: Android local AVC self-test decodes original clip twice (emulator only)\n");
            stage = "AVC Surface rendering";
            SurfaceDecodeSmoke.run(getTargetContext());
            results.append("PASS: Android MediaCodec delivered original AVC frame to test Surface (emulator only)\n");
            stage = "HTTPS/WSS transport";
            if (fixtureCa != null) {
                TransportSmoke transport = new TransportSmoke(fixtureCa);
                transport.run();
                stage = "Bounded TLS prototype";
                transport.runBounded();
                results.append("PASS: bounded TLS and persistent stream reject unknown CA and oversized frame; ping/pong, two samples, close, cancellation and drip-feed deadline\n");
                results.append("PASS: isolated HTTPS/WSS transport, TLS denial, fallback and revocation\n");
            } else {
                results.append("SKIP: transport fixture not configured\n");
            }
            report.putString("stream", results.toString());
            finish(Activity.RESULT_OK, report);
        } catch (Exception ex) {
            results.append("FAIL: ").append(stage).append(" (")
                .append(ex.getClass().getSimpleName()).append(")\n");
            report.putString("stream", results.toString());
            finish(Activity.RESULT_CANCELED, report);
        }
    }
    private void runStore() throws Exception {
        File file = new File(getTargetContext().getNoBackupFilesDir(), "reader.v1");
        KeyStore keys = KeyStore.getInstance("AndroidKeyStore"); keys.load(null);
        if (file.exists() || new File(file + ".bak").exists() || new File(file + ".new").exists()
            || keys.containsAlias("veypanel.reader.v1"))
            throw new IllegalStateException("Existing credentials; refusing test");
        CredentialStore store = new CredentialStore(getTargetContext());
        String token = new String(new char[64]).replace('\u0000', 'A');
        SavedReader record = new SavedReader(ReaderSession.parse("https://192.168.1.10:47861/#token=" + token), Instant.now());
        try {
            check(store.load() == null, "empty");
            store.save(record);
            byte[] first = Files.readAllBytes(file.toPath());
            check(!new String(first, java.nio.charset.StandardCharsets.UTF_8).contains(token), "ciphertext");
            check(new CredentialStore(getTargetContext()).load().link().equals(record.link()), "reopen");
            store.save(record);
            byte[] second = Files.readAllBytes(file.toPath());
            check(!Arrays.equals(first, second) && !Arrays.equals(Arrays.copyOfRange(first, 2, 14), Arrays.copyOfRange(second, 2, 14)), "fresh IV and ciphertext");
            second[second.length-1] ^= 1;
            Files.write(file.toPath(), second);
            check(reject(store), "corruption rejected");
            check(store.load() == null, "corruption cleared");
            store.save(record);
            keys.deleteEntry("veypanel.reader.v1");
            check(reject(store), "missing key rejected");
            check(store.load() == null, "missing key cleared");
            store.save(record); store.forget();
            check(!file.exists() && store.load() == null, "forget");
        } finally { store.forget(); }
    }
    private static void runQr() throws Exception {
        String text = "https://192.168.1.10:47861/enroll.html#id=11111111-2222-3333-4444-555555555555&secret="
            + new String(new char[64]).replace('\0', 'A');
        com.google.zxing.common.BitMatrix matrix = new com.google.zxing.qrcode.QRCodeWriter()
            .encode(text, com.google.zxing.BarcodeFormat.QR_CODE, 320, 320);
        int[] pixels = new int[320 * 320];
        for (int y = 0; y < 320; y++) for (int x = 0; x < 320; x++)
            pixels[y * 320 + x] = matrix.get(x,y) ? 0xff000000 : 0xffffffff;
        com.google.zxing.RGBLuminanceSource source = new com.google.zxing.RGBLuminanceSource(320, 320, pixels);
        com.google.zxing.BinaryBitmap bitmap = new com.google.zxing.BinaryBitmap(new com.google.zxing.common.HybridBinarizer(source));
        String decoded = new com.google.zxing.qrcode.QRCodeReader().decode(bitmap).getText();
        check(text.equals(decoded) && InvitationLink.parse(decoded).origin.getHost().equals("192.168.1.10"), "Offline QR");
    }
    private static void runMetrics() throws Exception {
        Instant now = Instant.now();
        check(SampleRules.timestamp("2026-11-22T14:00:00.1234567+02:00")
            .equals(Instant.parse("2026-11-22T12:00:00.123456700Z")), "Android offset timestamp");
        org.json.JSONObject root = new org.json.JSONObject().put("timestampUtc",now.toString())
            .put("cpuPercent",0).put("memoryTotalBytes",1024).put("memoryAvailableBytes",512)
            .put("diskIo",new org.json.JSONObject().put("readsPerSecond",5));
        root.put("thermal",new org.json.JSONObject().put("receivedUtc",now.minusSeconds(30).toString())
            .put("sensors",new org.json.JSONArray().put(new org.json.JSONObject().put("sensor","STALE_TEST").put("celsius",99))));
        TelemetrySample sample = TelemetrySample.parse(root.toString());
        check(sample.cpu == 0 && sample.ram == null && sample.used == 512 && sample.readIops == 5
            && sample.writeIops == null && !sample.details.contains("STALE_TEST"), "Extended resource data");
        root.put("memoryAvailableBytes",2048);
        check(TelemetrySample.parse(root.toString()).used == null, "Invalid capacity rejected");
    }
    private static void runHistory() throws Exception {
        MonitorHistory history = new MonitorHistory();
        Instant now = Instant.now();
        TelemetrySample first = TelemetrySample.parse(new org.json.JSONObject().put("timestampUtc",now.toString()).put("cpuPercent",0).toString());
        history.add(first); history.add(first);
        check(history.read(now).length==1 && history.read(now)[0].series(0)==0 && history.read(now)[0].series(1)==null,"History duplicate and null");
        check(history.read(now.plusSeconds(901)).length==0,"History expiry");
        for(int i=0;i<1000;i++) {
            TelemetrySample sample=TelemetrySample.parse(new org.json.JSONObject().put("timestampUtc",now.plusNanos(i*1000L).toString()).toString());
            history.add(sample);
        }
        check(history.read(now).length==900,"History capacity");
        history.add(first); check(history.read(now).length==1,"Clock reset");
        history.clear(); check(history.read(now).length==0,"History clear");
    }
    private static boolean reject(CredentialStore store) {
        try { store.load(); return false; } catch (Exception ex) { return true; }
    }
    private static void check(boolean ok, String label) {
        if (!ok) throw new IllegalStateException(label);
    }
}
