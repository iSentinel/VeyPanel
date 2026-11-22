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
        String token = "A".repeat(64);
        SavedReader record = new SavedReader(ReaderSession.parse("https://192.168.1.10:47861/#token=" + token), Instant.now());
        try {
            check(store.load() == null, "empty");
            store.save(record);
            byte[] first = Files.readAllBytes(file.toPath());
            check(!new String(first, java.nio.charset.StandardCharsets.UTF_8).contains(token), "ciphertext");
            check(new CredentialStore(getTargetContext()).load().link().equals(record.link()), "reopen");
            store.save(record);
            byte[] second = Files.readAllBytes(file.toPath());
            check(!Arrays.equals(first, second), "fresh ciphertext");
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
    private static boolean reject(CredentialStore store) {
        try { store.load(); return false; } catch (Exception ex) { return true; }
    }
    private static void check(boolean ok, String label) {
        if (!ok) throw new IllegalStateException(label);
    }
}
