using System.Diagnostics;
using System.Runtime.InteropServices;

namespace VeyPanel.Host;

public sealed record PhysicalDiskMetric(string Instance, double? ReadBytesPerSecond,
    double? WriteBytesPerSecond, double? ReadsPerSecond, double? WritesPerSecond);
public sealed record PhysicalDiskSnapshot(string Status, PhysicalDiskMetric[] Disks);

internal sealed class PhysicalDiskSampler : IDisposable
{
    private static readonly string[] Paths = [
        @"\PhysicalDisk(*)\Disk Read Bytes/sec", @"\PhysicalDisk(*)\Disk Write Bytes/sec",
        @"\PhysicalDisk(*)\Disk Reads/sec", @"\PhysicalDisk(*)\Disk Writes/sec"
    ];
    private readonly IntPtr[] counters = new IntPtr[4];
    private IntPtr query;
    private long? lastOpen, lastSample;
    private int samples;

    internal PhysicalDiskSnapshot Capture()
    {
        if (!OperatingSystem.IsWindows() || !GpuEngineSampler.LayoutValid()) return new("unsupported-platform", []);
        var now = Stopwatch.GetTimestamp();
        if (query == IntPtr.Zero && !Open(now)) return new("unavailable", []);
        if (lastSample is long old && Stopwatch.GetElapsedTime(old, now).TotalSeconds < .9)
            return new("warming-up", []);
        if (PdhCollectQueryData(query) != 0) { Reset(); return new("unavailable", []); }
        lastSample = now;
        if (++samples < 2) return new("warming-up", []);
        var result = Merge(counters.Select(c => c == IntPtr.Zero
            ? [] : GpuEngineSampler.ReadArray(c)).ToArray());
        if (result.Status == "unavailable") Reset();
        return result;
    }

    private bool Open(long now)
    {
        if (lastOpen is long old && Stopwatch.GetElapsedTime(old, now).TotalSeconds < 30) return false;
        lastOpen = now;
        if (PdhOpenQueryW(null, UIntPtr.Zero, out query) != 0) { query = IntPtr.Zero; return false; }
        for (var i = 0; i < Paths.Length; i++)
        {
            if (PdhAddEnglishCounterW(query, Paths[i], UIntPtr.Zero, out var translator) != 0) continue;
            var path = GpuEngineSampler.LocalizedPath(translator);
            PdhRemoveCounter(translator);
            if (path is not null && PdhAddCounterW(query, path, UIntPtr.Zero, out var counter) == 0)
                counters[i] = counter;
        }
        if (counters.Any(c => c != IntPtr.Zero)) return true;
        Reset(); return false;
    }

    internal static PhysicalDiskSnapshot Merge((string Name, double? Percent)[][] columns)
    {
        if (columns.Length != 4) return new("unavailable", []);
        var rows = new Dictionary<string, double?[]>(StringComparer.OrdinalIgnoreCase);
        bool partial = false;
        for (var i = 0; i < columns.Length; i++)
        {
            foreach (var group in columns[i].GroupBy(x => x.Name, StringComparer.OrdinalIgnoreCase))
            {
                if (group.Key.Equals("_Total", StringComparison.OrdinalIgnoreCase)) continue;
                if (string.IsNullOrWhiteSpace(group.Key) || group.Key.Length > 128) { partial = true; continue; }
                if (!rows.TryGetValue(group.Key, out var values))
                {
                    if (rows.Count >= 128) { partial = true; continue; }
                    rows[group.Key] = values = new double?[4];
                }
                var value = group.First().Percent;
                values[i] = group.Count() == 1 && value is double v && double.IsFinite(v) && v >= 0 ? v : null;
                if (values[i] is null) partial = true;
            }
        }
        var disks = rows.OrderBy(x => x.Key, StringComparer.OrdinalIgnoreCase)
            .Select(x => new PhysicalDiskMetric(x.Key, x.Value[0], x.Value[1], x.Value[2], x.Value[3])).ToArray();
        partial |= rows.Values.Any(r => r.Any(v => v is null));
        return new(disks.Length == 0 ? "unavailable" : partial ? "partial" : "ok", disks);
    }

    private void Reset()
    {
        if (query != IntPtr.Zero) PdhCloseQuery(query);
        query = IntPtr.Zero; Array.Clear(counters); samples = 0; lastSample = null;
    }
    public void Dispose() => Reset();

    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhOpenQueryW(string? source, UIntPtr data, out IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhAddEnglishCounterW(IntPtr query, string path, UIntPtr data, out IntPtr counter);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhAddCounterW(IntPtr query, string path, UIntPtr data, out IntPtr counter);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhRemoveCounter(IntPtr counter);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCollectQueryData(IntPtr query);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCloseQuery(IntPtr query);
}
