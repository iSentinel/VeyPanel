package com.veypanel.client;

import android.os.Bundle;
import android.view.WindowManager;
import com.journeyapps.barcodescanner.CaptureActivity;

/** Internal camera UI only. Never starts enrollment or opens scanned URLs. */
public final class PrivateScanActivity extends CaptureActivity {
    @Override protected void onCreate(Bundle saved) {
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        super.onCreate(saved);
    }
}
