using System.Runtime.InteropServices;

namespace VeyPanel.Host;

internal static class DisplayConfigNative
{
    internal const uint ActivePaths = 2, VirtualModeAware = 0x10, VirtualRefreshAware = 0x40;
    internal const uint PathActive = 1, PathVirtual = 8;
    internal const int InsufficientBuffer = 122;

    [StructLayout(LayoutKind.Sequential)]
    internal struct Luid { public uint Low; public int High; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Point { public int X, Y; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Rect { public int Left, Top, Right, Bottom; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Size { public uint Width, Height; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Rational { public uint Numerator, Denominator; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Source { public Luid Adapter; public uint Id, ModeIndex, Status; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Target
    {
        public Luid Adapter;
        public uint Id, ModeIndex, Technology, Rotation, Scaling;
        public Rational Refresh;
        public uint Scanline;
        public int Available;
        public uint Status;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Path { public Source Source; public Target Target; public uint Flags; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct SourceMode
    {
        public uint Width, Height, PixelFormat;
        public Point Position;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct Signal
    {
        public ulong PixelRate;
        public Rational Horizontal, Vertical;
        public Size Active, Total;
        public uint Standard, Scanline;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct DesktopMode { public Point SourceSize; public Rect Region, Clip; }

    [StructLayout(LayoutKind.Explicit, Size = 64)]
    internal struct Mode
    {
        [FieldOffset(0)] public uint Type;
        [FieldOffset(4)] public uint Id;
        [FieldOffset(8)] public Luid Adapter;
        [FieldOffset(16)] public SourceMode Source;
        [FieldOffset(16)] public Signal Target;
        [FieldOffset(16)] public DesktopMode Desktop;
    }

    [DllImport("user32.dll", ExactSpelling = true)]
    internal static extern int GetDisplayConfigBufferSizes(uint flags, out uint paths, out uint modes);

    [DllImport("user32.dll", ExactSpelling = true)]
    internal static extern int QueryDisplayConfig(uint flags, ref uint pathCount, [Out] Path[] paths,
        ref uint modeCount, [Out] Mode[] modes, IntPtr topology);

    internal static bool LayoutValid() => Marshal.SizeOf<Path>() == 72
        && Marshal.SizeOf<Source>() == 20 && Marshal.SizeOf<Target>() == 48
        && Marshal.SizeOf<Mode>() == 64 && Marshal.SizeOf<Signal>() == 48
        && Marshal.SizeOf<DesktopMode>() == 40
        && Marshal.OffsetOf<Path>(nameof(Path.Target)).ToInt32() == 20
        && Marshal.OffsetOf<Target>(nameof(Target.Refresh)).ToInt32() == 28;
}
