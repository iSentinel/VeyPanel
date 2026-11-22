using System.Runtime.InteropServices;

namespace VeyPanel.Host;

internal sealed record DisplaySource(string DeviceName, string AdapterName, bool Primary,
    uint? Width, uint? Height, int? X, int? Y, uint? Hz, uint? Orientation, bool ModeAvailable);
internal sealed record DisplaySnapshot(DateTimeOffset TimestampUtc, string Status, DisplaySource[] Sources);

internal static class DisplayInventory
{
    private const uint AttachedToDesktop = 1, PrimaryDevice = 4;
    private const uint Position = 0x20, Orientation = 0x80, Width = 0x80000,
        Height = 0x100000, Frequency = 0x400000;
    private const uint CurrentSettings = 0xFFFFFFFF;

    internal static DisplaySnapshot Capture()
    {
        if (!OperatingSystem.IsWindows()) return new(DateTimeOffset.UtcNow, "unsupported-platform", []);
        var sources = new List<DisplaySource>();
        for (uint i = 0; i < 256; i++)
        {
            var device = new DisplayDevice { Size = (uint)Marshal.SizeOf<DisplayDevice>() };
            if (!EnumDisplayDevices(null, i, ref device, 0))
                return Finish(sources);
            if ((device.StateFlags & AttachedToDesktop) == 0) continue;
            sources.Add(ReadSource(device));
        }
        return new(DateTimeOffset.UtcNow, "enumeration-limit", sources.ToArray());
    }

    private static DisplaySnapshot Finish(List<DisplaySource> sources)
    {
        var status = sources.Count == 0 ? "no-desktop-sources"
            : sources.All(source => source.ModeAvailable) ? "ok" : "partial";
        return new(DateTimeOffset.UtcNow, status, sources.ToArray());
    }

    private static DisplaySource ReadSource(DisplayDevice device)
    {
        var mode = new DevMode { Size = (ushort)Marshal.SizeOf<DevMode>() };
        var ok = EnumDisplaySettingsEx(device.DeviceName, CurrentSettings, ref mode, 0);
        var fields = ok ? mode.Fields : 0;
        return new(device.DeviceName, device.DeviceString, (device.StateFlags & PrimaryDevice) != 0,
            Has(fields, Width) && mode.PelsWidth > 0 ? mode.PelsWidth : null,
            Has(fields, Height) && mode.PelsHeight > 0 ? mode.PelsHeight : null,
            Has(fields, Position) ? mode.PositionX : null,
            Has(fields, Position) ? mode.PositionY : null,
            Has(fields, Frequency) && mode.DisplayFrequency > 1 ? mode.DisplayFrequency : null,
            Has(fields, Orientation) && mode.DisplayOrientation <= 3 ? mode.DisplayOrientation : null,
            ok);
    }

    private static bool Has(uint fields, uint flag) => (fields & flag) != 0;
    internal static bool LayoutIsValid() => Marshal.SizeOf<DisplayDevice>() == 840
        && Marshal.SizeOf<DevMode>() == 220
        && Marshal.OffsetOf<DevMode>(nameof(DevMode.PositionX)).ToInt32() == 76
        && Marshal.OffsetOf<DevMode>(nameof(DevMode.PelsWidth)).ToInt32() == 172;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DisplayDevice
    {
        public uint Size;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceString;
        public uint StateFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceId;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DeviceKey;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DevMode
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string DeviceName;
        public ushort SpecVersion, DriverVersion, Size, DriverExtra;
        public uint Fields;
        public int PositionX, PositionY;
        public uint DisplayOrientation, DisplayFixedOutput;
        public short Color, Duplex, YResolution, TTOption, Collate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FormName;
        public ushort LogPixels;
        public uint BitsPerPel, PelsWidth, PelsHeight, DisplayFlags, DisplayFrequency,
            ICMMethod, ICMIntent, MediaType, DitherType, Reserved1, Reserved2, PanningWidth, PanningHeight;
    }

    [DllImport("user32.dll", EntryPoint = "EnumDisplayDevicesW", CharSet = CharSet.Unicode, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumDisplayDevices(string? device, uint index, ref DisplayDevice output, uint flags);

    [DllImport("user32.dll", EntryPoint = "EnumDisplaySettingsExW", CharSet = CharSet.Unicode, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumDisplaySettingsEx(string device, uint mode, ref DevMode output, uint flags);
}
