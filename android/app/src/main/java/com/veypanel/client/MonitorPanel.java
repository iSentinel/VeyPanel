package com.veypanel.client;

import android.content.Context;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.Locale;

/** Responsive metric cards, no inferred readings. */
final class MonitorPanel extends LinearLayout {
    private static final String[] LABELS = {"CPU", "RAM", "GPU", "Video encode", "Video decode",
        "Memory used / total", "Disk read", "Disk write", "Read IOPS", "Write IOPS"};
    private final TextView[] fields = new TextView[LABELS.length];
    private final LinearLayout grid;
    private final TextView details;
    private int columns = 1;
    private TelemetrySample latest;

    MonitorPanel(Context context) {
        super(context);
        setOrientation(VERTICAL);
        grid = new LinearLayout(context); grid.setOrientation(VERTICAL); addView(grid);
        details = new TextView(context);
        details.setTextSize(16); details.setPadding(dp(8),dp(12),dp(8),dp(12)); addView(details);
        rebuild();
    }

    @Override protected void onSizeChanged(int w, int h, int ow, int oh) {
        super.onSizeChanged(w,h,ow,oh);
        int desired = w >= dp(800) ? 3 : w >= dp(440) ? 2 : 1;
        if (desired != columns) {
            columns = desired;
            post(this::rebuild);
        }
    }

    private void rebuild() {
        grid.removeAllViews();
        LinearLayout row = null;
        for (int i = 0; i < LABELS.length; i++) {
            if (i % columns == 0) {
                row = new LinearLayout(getContext()); row.setOrientation(HORIZONTAL);
                grid.addView(row, new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT));
            }
            LinearLayout card = new LinearLayout(getContext()); card.setOrientation(VERTICAL);
            card.setPadding(dp(12),dp(10),dp(12),dp(10));
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(0xff1b293b); bg.setCornerRadius(dp(10));
            bg.setStroke(dp(1),0xff35465b); card.setBackground(bg);
            LayoutParams params = new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1);
            params.setMargins(dp(4),dp(4),dp(4),dp(4)); row.addView(card, params);
            TextView label = new TextView(getContext()); label.setText(LABELS[i]);
            label.setTextColor(0xffb8cee6); label.setTextSize(14); card.addView(label);
            fields[i] = new TextView(getContext()); fields[i].setTextColor(Color.WHITE);
            fields[i].setTextSize(24); fields[i].setContentDescription(LABELS[i] + " N/A"); card.addView(fields[i]);
        }
        if (row != null) for (int i = LABELS.length % columns; i > 0 && i < columns; i++)
            row.addView(new android.view.View(getContext()), new LayoutParams(0, 1, 1));
        render(latest);
    }

    void render(TelemetrySample sample) {
        latest = sample;
        if (sample == null) {
            for (int i=0;i<fields.length;i++) metric(i,"N/A");
            details.setText("Network interfaces · N/A\nVolumes · N/A\nCPU / GPU sensors · N/A\nStorage health · N/A");
            return;
        }
        metric(0,format(sample.cpu,"%")); metric(1,format(sample.ram,"%")); metric(2,format(sample.gpu,"%"));
        metric(3,format(sample.encode,"%")); metric(4,format(sample.decode,"%"));
        metric(5,sample.used == null || sample.total == null ? "N/A"
            : format(sample.used/1073741824,"") + " / " + format(sample.total/1073741824," GiB"));
        metric(6,rate(sample.read)); metric(7,rate(sample.write));
        metric(8,format(sample.readIops,"")); metric(9,format(sample.writeIops,""));
        details.setText(sample.details);
    }

    private void metric(int i, String text) {
        fields[i].setText(text); fields[i].setContentDescription(LABELS[i] + " " + text);
    }
    private int dp(int n) { return Math.round(n*getResources().getDisplayMetrics().density); }
    private static String format(Double n, String unit) {
        return n == null ? "N/A" : String.format(Locale.getDefault(),"%.1f%s",n,unit);
    }
    private static String rate(Double n) { return n == null ? "N/A" : format(n/1048576," MiB/s"); }
}
