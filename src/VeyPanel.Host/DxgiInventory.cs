using System.Diagnostics;
using System.Runtime.InteropServices;

namespace VeyPanel.Host;

internal sealed record AdapterDescription(string Luid, string Name, uint VendorId, uint DeviceId,
    ulong DedicatedVideoBytes, ulong SharedSystemBytes, bool Software);

internal static class DxgiInventory
{
    private const int NotFound = unchecked((int)0x887A0002);
    private static readonly Guid FactoryId = new("770aae78-f26f-4dba-a829-253c83d1b387");

    internal static (string Status, AdapterDescription[] Adapters) Capture()
    {
        if (!OperatingSystem.IsWindows() || !LayoutValid()) return ("unsupported-platform", []);
        var iid = FactoryId;
        if (CreateDXGIFactory1(ref iid, out var factory) < 0 || factory == IntPtr.Zero)
            return ("unavailable", []);
        var adapters = new List<AdapterDescription>();
        try
        {
            var enumerate = Method<EnumAdapter>(factory, 12);
            for (uint i = 0; i < 64; i++)
            {
                var hr = enumerate(factory, i, out var adapter);
                if (hr == NotFound) return (adapters.Count == 0 ? "unavailable" : "ok", adapters.ToArray());
                if (hr < 0 || adapter == IntPtr.Zero) return ("partial", adapters.ToArray());
                try
                {
                    if (Method<GetDescription>(adapter, 10)(adapter, out var d) < 0)
                        return ("partial", adapters.ToArray());
                    adapters.Add(new(Key(d.High, d.Low), d.DescriptionText ?? "Unknown adapter", d.VendorId,
                        d.DeviceId, d.DedicatedVideoMemory.ToUInt64(), d.SharedSystemMemory.ToUInt64(),
                        (d.Flags & 2) != 0));
                }
                finally { Marshal.Release(adapter); }
            }
            return ("partial", adapters.ToArray());
        }
        finally { Marshal.Release(factory); }
    }

    internal static string Key(int high, uint low) => $"{unchecked((uint)high):x8}:{low:x8}";

    private static T Method<T>(IntPtr instance, int slot) where T : Delegate =>
        Marshal.GetDelegateForFunctionPointer<T>(Marshal.ReadIntPtr(Marshal.ReadIntPtr(instance), slot * IntPtr.Size));

    internal static bool LayoutValid() => IntPtr.Size == 8 && Marshal.SizeOf<Description>() == 312
        && Marshal.OffsetOf<Description>(nameof(Description.Low)).ToInt32() == 296
        && Marshal.OffsetOf<Description>(nameof(Description.Flags)).ToInt32() == 304;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct Description
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DescriptionText;
        public uint VendorId, DeviceId, SubSysId, Revision;
        public UIntPtr DedicatedVideoMemory, DedicatedSystemMemory, SharedSystemMemory;
        public uint Low;
        public int High;
        public uint Flags;
    }

    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    private delegate int EnumAdapter(IntPtr self, uint index, out IntPtr adapter);
    [UnmanagedFunctionPointer(CallingConvention.StdCall)]
    private delegate int GetDescription(IntPtr self, out Description description);
    [DllImport("dxgi.dll", ExactSpelling = true)]
    private static extern int CreateDXGIFactory1(ref Guid iid, out IntPtr factory);
}

public sealed record GpuAdapterMetric(string Name, uint? VendorId, uint? DeviceId, bool? Software,
    ulong? DedicatedVideoBytes, ulong? SharedSystemBytes, double? BusiestEnginePercent,
    double? VideoEncodePercent, double? VideoDecodePercent);

internal sealed class GpuAdapterInventory
{
    private AdapterDescription[] descriptions = [];
    private string status = "unavailable";
    private long? last;

    internal GpuMetric Attach(GpuMetric metric)
    {
        var now = Stopwatch.GetTimestamp();
        if (last is null || Stopwatch.GetElapsedTime(last.Value, now).TotalSeconds >= 10)
        {
            (status, descriptions) = DxgiInventory.Capture();
            last = now;
        }
        return Map(metric, status, descriptions);
    }

    internal static GpuMetric Map(GpuMetric metric, string status, AdapterDescription[] descriptions)
    {
        var observed = metric.Observed.ToDictionary(x => x.Luid, StringComparer.Ordinal);
        var items = new List<GpuAdapterMetric>();
        foreach (var group in descriptions.GroupBy(d => d.Luid))
        {
            var d = group.First();
            if (group.Count() != 1) { status = "partial"; continue; }
            observed.Remove(d.Luid, out var m);
            items.Add(new(d.Name, d.VendorId, d.DeviceId, d.Software, d.DedicatedVideoBytes,
                d.SharedSystemBytes, m?.Busiest, m?.Encode, m?.Decode));
        }
        foreach (var m in observed.Values)
            items.Add(new("Unmatched GPU adapter", null, null, null, null, null, m.Busiest, m.Encode, m.Decode));
        return metric with { InventoryStatus = status, Adapters = items.ToArray() };
    }
}
