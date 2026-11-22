using System.Diagnostics;
using System.Runtime.InteropServices;

namespace VeyPanel.Host;

internal sealed class GpuEngineSampler : IDisposable
{
    private const uint MoreData = 0x800007d2;
    private const uint FormatDouble = 0x200, NoCap100 = 0x8000;
    private const uint MaxBuffer = 4 * 1024 * 1024;
    private IntPtr query, counter;
    private int samples;
    private long? lastOpen, lastSample;

    internal GpuMetric Capture()
    {
        if (!OperatingSystem.IsWindows() || IntPtr.Size != 8)
            return GpuEngineMath.Empty("unsupported-platform");
        var now = Stopwatch.GetTimestamp();
        if (query == IntPtr.Zero && !TryOpen(now)) return GpuEngineMath.Empty("unavailable");
        if (lastSample is long previous && Stopwatch.GetElapsedTime(previous, now).TotalSeconds < 0.9)
            return GpuEngineMath.Empty("warming-up");
        if (PdhCollectQueryData(query) != 0)
        { Reset(); return GpuEngineMath.Empty("unavailable"); }
        lastSample = now;
        if (++samples < 2) return GpuEngineMath.Empty("warming-up");
        var data = ReadArray();
        var metric = GpuEngineMath.Aggregate(data);
        if (metric.Status == "unavailable") Reset();
        return metric;
    }

    private bool TryOpen(long now)
    {
        if (lastOpen is long last && Stopwatch.GetElapsedTime(last, now).TotalSeconds < 30) return false;
        lastOpen = now;
        if (!LayoutValid() || PdhOpenQueryW(null, UIntPtr.Zero, out query) != 0)
        { query = IntPtr.Zero; return false; }
        if (PdhAddEnglishCounterW(query, @"\GPU Engine(*)\Utilization Percentage", UIntPtr.Zero, out var translator) != 0)
        { Reset(); return false; }
        var localized = LocalizedPath(translator);
        PdhRemoveCounter(translator);
        // PdhGetFormattedCounterArray supports localized wildcard paths (including changing instances).
        if (localized is not null && PdhAddCounterW(query, localized, UIntPtr.Zero, out counter) == 0)
            return true;
        Reset();
        return false;
    }

    private static string? LocalizedPath(IntPtr counter)
    {
        uint size = 0;
        if (PdhGetCounterInfoW(counter, false, ref size, IntPtr.Zero) != MoreData || size < 48 || size > MaxBuffer)
            return null;
        var buffer = Marshal.AllocHGlobal((int)size);
        var capacity = size;
        try
        {
            if (PdhGetCounterInfoW(counter, false, ref size, buffer) != 0 || size > capacity || size < 48)
                return null;
            // PDH_COUNTER_INFO_W on x64: six 32-bit fields, two ULONG_PTRs, then szFullPath.
            return ReadBoundedString(buffer, size, Marshal.ReadIntPtr(buffer, 40));
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }

    private (string Name, double? Percent)[] ReadArray()
    {
        for (var attempt = 0; attempt < 2; attempt++)
        {
            uint size = 0;
            var status = PdhGetFormattedCounterArrayW(counter, FormatDouble | NoCap100, ref size, out _, IntPtr.Zero);
            if (status != MoreData || size == 0 || size > MaxBuffer) return [];
            var capacity = size;
            var buffer = Marshal.AllocHGlobal((int)size);
            try
            {
                status = PdhGetFormattedCounterArrayW(counter, FormatDouble | NoCap100, ref size, out var count, buffer);
                if (status == MoreData) continue;
                if (status != 0 || size > capacity || count > size / 24) return [];
                var values = new List<(string, double?)>((int)count);
                for (var i = 0; i < count; i++)
                {
                    var item = Marshal.PtrToStructure<CounterItem>(IntPtr.Add(buffer, checked(i * 24)));
                    var name = ReadBoundedString(buffer, size, item.Name);
                    if (name is not null) values.Add((name, DiskIoSampler.Normalize(item.Status, item.Value)));
                    else values.Add(("", null));
                }
                return values.ToArray();
            }
            finally { Marshal.FreeHGlobal(buffer); }
        }
        return [];
    }

    private static string? ReadBoundedString(IntPtr buffer, uint size, IntPtr text)
    {
        var offset = text.ToInt64() - buffer.ToInt64();
        if (offset < 0 || offset >= size || (offset & 1) != 0) return null;
        var max = Math.Min((size - offset) / 2, 4096);
        for (var i = 0; i < max; i++)
            if (Marshal.ReadInt16(text, i * 2) == 0) return Marshal.PtrToStringUni(text, i);
        return null;
    }

    private void Reset()
    {
        if (query != IntPtr.Zero) PdhCloseQuery(query);
        query = counter = IntPtr.Zero;
        samples = 0;
        lastSample = null;
    }

    public void Dispose() => Reset();

    [StructLayout(LayoutKind.Explicit, Size = 24)]
    private struct CounterItem
    {
        [FieldOffset(0)] public IntPtr Name;
        [FieldOffset(8)] public uint Status;
        [FieldOffset(16)] public double Value;
    }

    internal static bool LayoutValid() => IntPtr.Size == 8 && Marshal.SizeOf<CounterItem>() == 24
        && Marshal.OffsetOf<CounterItem>(nameof(CounterItem.Value)).ToInt32() == 16;

    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhOpenQueryW(string? source, UIntPtr data, out IntPtr query);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhAddEnglishCounterW(IntPtr query, string path, UIntPtr data, out IntPtr counter);
    [DllImport("pdh.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern uint PdhAddCounterW(IntPtr query, string path, UIntPtr data, out IntPtr counter);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhRemoveCounter(IntPtr counter);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhGetCounterInfoW(IntPtr counter, [MarshalAs(UnmanagedType.Bool)] bool explain, ref uint size, IntPtr info);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCollectQueryData(IntPtr query);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhGetFormattedCounterArrayW(IntPtr counter, uint format, ref uint size, out uint count, IntPtr buffer);
    [DllImport("pdh.dll", ExactSpelling = true)]
    private static extern uint PdhCloseQuery(IntPtr query);
}
