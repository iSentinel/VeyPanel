using VeyPanel.Host;

internal static class HistoryTests
{
    internal static int Run()
    {
        var history = new TelemetryHistory();
        var now = DateTimeOffset.UtcNow;
        for (var i = 0; i < 1000; i++)
            history.Add(new Snapshot(now.AddSeconds(i), 25, 100, 50, 50, "ok"));
        var end = now.AddSeconds(999);
        var data = history.Read(end);
        var valid = data.Samples.Length == 900 && data.Samples[0].TimestampUtc == now.AddSeconds(100)
            && data.Samples[^1].CpuPercent == 25;
        history.Add(new Snapshot(end, 100, null, null, null, "partial"));
        valid &= history.Read(end).Samples[^1].CpuPercent == 25;
        history.Add(new Snapshot(end.AddSeconds(1), double.NaN, null, null, -1, "partial"));
        valid &= history.Read(end.AddSeconds(1)).Samples[^1] is { CpuPercent: null, MemoryUsedPercent: null };
        valid &= history.Read(end.AddSeconds(902)).Samples.Length == 0;
        history.Add(new Snapshot(end.AddSeconds(5), 0, null, null, null, "partial"));
        history.Add(new Snapshot(now, 0, null, null, null, "partial"));
        valid &= history.Read(now).Samples.Length == 1 && history.Read(now).Samples[0].CpuPercent == 0;
        Console.WriteLine($"{(valid ? "PASS" : "FAIL")} History bounded capacity, age, duplicate, clock reset and N/A");
        return valid ? 0 : 1;
    }
}
