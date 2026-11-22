using System.Diagnostics;
using System.Runtime.InteropServices;

namespace VeyPanel.Host;

public sealed record DiskIoMetric(string Status, double? ReadBytesPerSecond, double? WriteBytesPerSecond,
    double? ReadsPerSecond, double? WritesPerSecond);

internal sealed class DiskIoSampler : IDisposable
{
    private IntPtr query;
    private readonly IntPtr[] counters = new IntPtr[4];
    private long? lastAttempt, previousSample;
    private int samples;

    private static readonly string[] Names = [
        @"\PhysicalDisk(_Total)\Disk Read Bytes/sec",
        @"\PhysicalDisk(_Total)\Disk Write Bytes/sec",
        @"\PhysicalDisk(_Total)\Disk Reads/sec",
        @"\PhysicalDisk(_Total)\Disk Writes/sec"
    ];

    internal DiskIoMetric Capture()
    {
        if (!OperatingSystem.IsWindows()) return Empty("unsupported-platform");
        var now = Stopwatch.GetTimestamp();
        if (query == IntPtr.Zero && !TryOpen(now)) return Empty("unavailable");
        if (previousSample is long previous && Stopwatch.GetElapsedTime(previous, now).TotalSeconds < 0.9)
            return Empty("warming-up");
        if (PdhCollectQueryData(query) != 0)
        {
            Reset();
            return Empty("unavailable");
        }
        previousSample = now;
        if (++samples < 2) return Empty("warming-up");
        var values = counters.Select(Read).ToArray();
        var count = values.Count(v => v.HasValue);
        if (count == 0)
        {
            Reset();
            return Empty("unavailable");
        }
        return new(count == values.Length ? "ok" : "partial", values[0], values[1], values[2], values[3]);
    }

    private bool TryOpen(long now)
    {
        if (lastAttempt is long last && Stopwatch.GetElapsedTime(last, now).TotalSeconds < 30) return false;
        lastAttempt = now;
        if (!LayoutValid() || PdhOpenQueryW(null, UIntPtr.Zero, out query) != 0)
        {
            query = IntPtr.Zero;
            return false;
        }
        for (var i = 0; i < Names.Length; i++)
        {
            if (PdhAddEnglishCounterW(query, Names[i], UIntPtr.Zero, out var counter) == 0)
                counters[i] = counter;
        }
        if (counters.Any(c => c != IntPtr.Zero)) return true;
        Reset();
        return false;
    }

    private static double? Read(IntPtr counter)
    {
        if (counter == IntPtr.Zero || PdhGetFormattedCounterValue(counter, 0x8200, IntPtr.Zero, out var result) != 0)
            return null;
        return Normalize(result.Status, result.Value);
    }

    internal static double? Normalize(uint status, double value) =>
        status is 0 or 1 && double.IsFinite(value) && value >= 0 ? value : null;

    private static DiskIoMetric Empty(string status) => new(status, null, null, null, null);

    private void Reset()
    {
        if (query != IntPtr.Zero) PdhCloseQuery(query);
        query = IntPtr.Zero;
        Array.Clear(counters);
        previousSample = null;
        samples = 0;
    }

    public void Dispose() => Reset();

    [StructLayout(LayoutKind.Explicit, Size = 16)]
    private struct FormattedValue
    {
        [FieldOffset(0)] public uint Status;
        [FieldOffset(8)] public double Value;
    }

    internal static bool LayoutValid() => Marshal.SizeOf<FormattedValue>() == 16
        && Marshal.OffsetOf<FormattedValue>(nameof(FormattedValue.Value)).ToInt32() == 8;

    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhOpenQueryW(string? source, UIntPtr userData, out IntPtr query);

    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhAddEnglishCounterW(IntPtr query, string path, UIntPtr userData, out IntPtr counter);

    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCollectQueryData(IntPtr query);

    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhGetFormattedCounterValue(IntPtr counter, uint format, IntPtr type, out FormattedValue value);

    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCloseQuery(IntPtr query);
}
