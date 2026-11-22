package com.veypanel.client;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.time.Instant;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

final class CredentialStore {
    private static final String ALIAS = "veypanel.reader.v1";
    private static final byte[] AAD = "VeyPanel/Android/reader/v1".getBytes(StandardCharsets.UTF_8);
    private static final int MAX = 1024;
    private static final Object LOCK = new Object();
    private final AtomicFile file;

    CredentialStore(Context context) {
        file = new AtomicFile(new File(context.getNoBackupFilesDir(), "reader.v1"));
    }

    SavedReader load() throws Exception {
        synchronized (LOCK) {
            if (!file.getBaseFile().exists() && !new File(file.getBaseFile() + ".bak").exists()) return null;
            try {
                byte[] bytes;
                try (java.io.FileInputStream input = file.openRead()) {
                    bytes = new byte[MAX + 1];
                    int used = 0, n;
                    while (used < bytes.length && (n = input.read(bytes, used, bytes.length-used)) != -1) used += n;
                    if (used > MAX || used < 30) throw new IllegalArgumentException("Invalid envelope");
                    bytes = Arrays.copyOf(bytes, used);
                }
                ByteBuffer envelope = ByteBuffer.wrap(bytes);
                if (envelope.get() != 1 || envelope.get() != 12) throw new IllegalArgumentException("Invalid envelope");
                byte[] iv = new byte[12]; envelope.get(iv);
                byte[] encrypted = new byte[envelope.remaining()]; envelope.get(encrypted);
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, existingKey(), new GCMParameterSpec(128, iv));
                cipher.updateAAD(AAD);
                byte[] plain = cipher.doFinal(encrypted);
                try { return SavedReader.decode(new String(plain, StandardCharsets.UTF_8), Instant.now()); }
                finally { Arrays.fill(plain, (byte)0); }
            } catch (Exception ex) {
                forgetLocked();
                throw ex;
            }
        }
    }

    void save(SavedReader record) throws Exception {
        synchronized (LOCK) {
            // Replace, never resurrect the prior credential after a failed write.
            forgetLocked();
            if (!record.validAt(Instant.now())) throw new IllegalArgumentException("Expired");
            byte[] plain = record.encode().getBytes(StandardCharsets.UTF_8);
            FileOutputStream output = null;
            try {
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.ENCRYPT_MODE, newKey());
                cipher.updateAAD(AAD);
                byte[] iv = cipher.getIV(), encrypted = cipher.doFinal(plain);
                if (iv.length != 12 || encrypted.length + 14 > MAX) throw new IllegalStateException("Envelope bounds");
                byte[] envelope = ByteBuffer.allocate(14 + encrypted.length)
                    .put((byte)1).put((byte)12).put(iv).put(encrypted).array();
                output = file.startWrite();
                output.write(envelope);
                file.finishWrite(output);
                output = null;
                // AtomicFile can report a failed rename only through Android system logs.
                // Verify that the expected ciphertext actually became authoritative.
                if (!Arrays.equals(envelope, file.readFully())) throw new IllegalStateException("Commit failed");
            } catch (Exception ex) {
                if (output != null) file.failWrite(output);
                forgetLocked();
                throw ex;
            } finally { Arrays.fill(plain, (byte)0); }
        }
    }

    void forget() throws Exception { synchronized (LOCK) { forgetLocked(); } }

    private void forgetLocked() throws Exception {
        // Key deletion first makes any surviving encrypted copy unreadable.
        KeyStore ks = keyStore();
        ks.deleteEntry(ALIAS);
        if (ks.containsAlias(ALIAS)) throw new IllegalStateException("Key deletion failed");
        file.delete();
        for (String suffix : new String[] {"", ".bak", ".new"})
            if (new File(file.getBaseFile() + suffix).exists()) throw new IllegalStateException("File deletion failed");
    }

    private static KeyStore keyStore() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null); return ks;
    }

    private static SecretKey existingKey() throws Exception {
        java.security.Key key = keyStore().getKey(ALIAS, null);
        if (!(key instanceof SecretKey)) throw new IllegalStateException("Key unavailable");
        return (SecretKey)key;
    }

    private static SecretKey newKey() throws Exception {
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
            KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true).build());
        return generator.generateKey();
    }
}
