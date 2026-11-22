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
    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        isolated = "true".equals(args.getString("isolated"));
        start();
    }
    @Override public void onStart() {
        Bundle report = new Bundle();
        try {
            if (!isolated) throw new IllegalStateException("Explicit isolated test required");
            runStore();
            runQr();
            report.putString("stream", "\nPASS: AndroidKeyStore actual encryption, reopen, fresh ciphertext, corruption, key removal and Forget\n");
            finish(Activity.RESULT_OK, report);
        } catch (Exception ex) {
            report.putString("stream", "\nFAIL: AndroidKeyStore smoke (" + ex.getClass().getSimpleName() + ")\n");
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
    private static boolean reject(CredentialStore store) {
        try { store.load(); return false; } catch (Exception ex) { return true; }
    }
    private static void check(boolean ok, String label) {
        if (!ok) throw new IllegalStateException(label);
    }
}
