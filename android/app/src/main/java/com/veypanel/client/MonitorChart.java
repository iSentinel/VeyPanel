package com.veypanel.client;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import java.time.Instant;
import java.util.Locale;

/** Observed values only; missing or delayed data breaks the line. */
final class MonitorChart extends View {
    private static final int[] COLORS = {0xff69baff,0xffb9a5ff,0xff66d9aa,0xfff3b86e,0xff6ed8d8};
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private MonitorHistory.Point[] points = new MonitorHistory.Point[0];
    private Instant end = Instant.now();
    private int seconds = 900;
    private final int first, count;
    MonitorChart(Context c, int first, int count, String description) {
        super(c); this.first = first; this.count = count;
        setContentDescription(description);
        setBackgroundColor(0xff172335);
    }
    void update(MonitorHistory.Point[] values, Instant now, int range) {
        points = values; end = now; seconds = range; invalidate();
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float d = getResources().getDisplayMetrics().density, left = 58*d, right = getWidth()-12*d;
        float top = 12*d, bottom = getHeight()-24*d;
        if (right <= left || bottom <= top) return;
        long stop = end.toEpochMilli(), start = stop - seconds*1000L;
        double max = peak(start,stop);
        paint.setStrokeWidth(d); paint.setTextSize(11*d);
        for (int i=0;i<=4;i++) {
            float y=top+(bottom-top)*i/4;
            paint.setColor(0xff35465b); canvas.drawLine(left,y,right,y,paint);
        }
        paint.setColor(0xffb8cee6);
        canvas.drawText(first >= 5 ? String.format(Locale.getDefault(),"%.1f M",max/1048576) : "100%",4*d,top+8*d,paint);
        canvas.drawText("0",4*d,bottom,paint);
        canvas.drawText("-"+seconds/60+" min",left,getHeight()-5*d,paint);
        canvas.drawText("now",right-25*d,getHeight()-5*d,paint);
        for (int i=first;i<first+count;i++) drawSeries(canvas,i,start,stop,max,left,right,top,bottom);
    }
    private double peak(long start,long stop) {
        if (first < 5) return 100;
        double max=1048576;
        for (MonitorHistory.Point p:points) {
            long time=p.stamp.toEpochMilli();
            if(time<start || time>stop) continue;
            for(int i=first;i<first+count;i++) if(p.series(i)!=null) max=Math.max(max,p.series(i));
        }
        return max;
    }
    private void drawSeries(Canvas c,int i,long start,long stop,double max,float left,float right,float top,float bottom) {
        paint.setColor(COLORS[i % COLORS.length]); paint.setStrokeWidth(2*getResources().getDisplayMetrics().density);
        long prev = Long.MIN_VALUE; float px=0,py=0;
        for (MonitorHistory.Point p:points) {
            long stamp=p.stamp.toEpochMilli(); Double value=p.series(i);
            if (stamp<start || stamp>stop || value==null) { prev=Long.MIN_VALUE; continue; }
            float x=left+(float)((stamp-start)/(double)(stop-start))*(right-left);
            float y=bottom-(float)(value/max)*(bottom-top);
            if(prev!=Long.MIN_VALUE && stamp>prev && stamp-prev<=2500) c.drawLine(px,py,x,y,paint);
            else c.drawCircle(x,y,paint.getStrokeWidth(),paint);
            prev=stamp; px=x; py=y;
        }
    }
}
