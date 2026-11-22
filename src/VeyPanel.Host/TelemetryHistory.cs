namespace VeyPanel.Host;

public sealed record HistoryPoint(DateTimeOffset TimestampUtc, double? CpuPercent, double? MemoryUsedPercent,
    double? GpuPercent, double? VideoEncodePercent, double? VideoDecodePercent,
    double? DiskReadBytesPerSecond, double? DiskWriteBytesPerSecond);
public sealed record HistorySnapshot(DateTimeOffset TimestampUtc, int WindowSeconds, HistoryPoint[] Samples);

internal sealed class TelemetryHistory
{
    internal const int WindowSeconds = 900;
    private const int Capacity = 900;
    private readonly Queue<HistoryPoint> points = new(Capacity);
    private readonly object gate = new();
    private DateTimeOffset? last;

    internal void Add(Snapshot sample)
    {
        var stamp = sample.TimestampUtc;
        lock (gate)
        {
            if (last is DateTimeOffset prior)
            {
                if (stamp == prior) return;
                if (stamp < prior) points.Clear();
            }
            last = stamp;
            Prune(stamp);
            if (points.Count >= Capacity) points.Dequeue();
            points.Enqueue(new(stamp, Percent(sample.CpuPercent), Percent(sample.MemoryUsedPercent),
                Percent(sample.Gpu?.BusiestEnginePercent), Percent(sample.Gpu?.VideoEncodePercent),
                Percent(sample.Gpu?.VideoDecodePercent), Rate(sample.DiskIo?.ReadBytesPerSecond),
                Rate(sample.DiskIo?.WriteBytesPerSecond)));
        }
    }

    internal HistorySnapshot Read(DateTimeOffset now)
    {
        lock (gate)
        {
            if (last is DateTimeOffset prior && prior > now) { points.Clear(); last = null; }
            Prune(now);
            return new(now, WindowSeconds, points.ToArray());
        }
    }

    private void Prune(DateTimeOffset now)
    {
        var start = now.AddSeconds(-WindowSeconds);
        while (points.TryPeek(out var head) && head.TimestampUtc <= start) points.Dequeue();
    }

    private static double? Percent(double? value) =>
        value is double v && double.IsFinite(v) && v is >= 0 and <= 100 ? v : null;
    private static double? Rate(double? value) =>
        value is double v && double.IsFinite(v) && v >= 0 ? v : null;
}
