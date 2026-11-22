using N = VeyPanel.Host.DisplayConfigNative;

namespace VeyPanel.Host;

internal sealed record AdapterKey(uint Low, int High);
internal sealed record DisplayRate(uint Numerator, uint Denominator);
internal sealed record DisplayRect(int Left, int Top, int Right, int Bottom);
internal sealed record SourceGeometry(uint Width, uint Height, uint PixelFormat, int X, int Y);
internal sealed record TargetTiming(ulong PixelRate, DisplayRate Horizontal, DisplayRate Vertical,
    uint ActiveWidth, uint ActiveHeight, uint TotalWidth, uint TotalHeight, uint Standard, uint Scanline);
internal sealed record DesktopGeometry(int SourceWidth, int SourceHeight, DisplayRect Region, DisplayRect Clip);
internal sealed record TopologyMode(uint Type, AdapterKey Adapter, uint Id,
    SourceGeometry? Source, TargetTiming? Target, DesktopGeometry? Desktop);
internal sealed record TopologyPath(AdapterKey SourceAdapter, uint SourceId, uint? SourceMode,
    uint? CloneGroup, uint SourceStatus, AdapterKey TargetAdapter, uint TargetId,
    uint? TargetMode, uint? DesktopMode, uint Technology, uint Rotation, uint Scaling,
    DisplayRate Refresh, uint Scanline, bool Available, uint TargetStatus, uint Flags)
{
    public DisplayIdentity? Identity { get; init; }
}
internal sealed record TopologySnapshot(int SchemaVersion, DateTimeOffset TimestampUtc, uint QueryFlags,
    string Status, int? NativeError, TopologyPath[] Paths, TopologyMode[] Modes, string[] Issues);

internal static class DisplayTopology
{
    internal static TopologySnapshot Capture() => Capture(out _, out _);

    internal static TopologySnapshot Capture(out N.Path[] nativePaths, out N.Mode[] nativeModes)
    {
        nativePaths = [];
        nativeModes = [];
        const uint flags = N.ActivePaths | N.VirtualModeAware | N.VirtualRefreshAware;
        if (!OperatingSystem.IsWindows()) return Failure(flags, "unsupported-platform");
        if (!N.LayoutValid()) return Failure(flags, "invalid-interop-layout");

        for (var attempt = 0; attempt < 5; attempt++)
        {
            var result = N.GetDisplayConfigBufferSizes(flags, out var pathCount, out var modeCount);
            if (result == N.InsufficientBuffer) continue;
            if (result != 0) return Failure(flags, "native-error", result);
            if (pathCount == 0) return Failure(flags, "no-active-paths");
            if (pathCount > 4096 || modeCount > 8192) return Failure(flags, "capacity-limit");
            var paths = new N.Path[pathCount];
            var modes = new N.Mode[Math.Max(modeCount, 1u)];
            result = N.QueryDisplayConfig(flags, ref pathCount, paths, ref modeCount, modes, IntPtr.Zero);
            if (result == N.InsufficientBuffer) continue;
            if (result != 0) return Failure(flags, "native-error", result);
            if (pathCount > paths.Length || modeCount > modes.Length) return Failure(flags, "invalid-native-counts");
            nativePaths = paths.Take((int)pathCount).ToArray();
            nativeModes = modes.Take((int)modeCount).ToArray();
            var snapshot = new TopologySnapshot(1, DateTimeOffset.UtcNow, flags, "ok", null,
                nativePaths.Select(path => ConvertPath(path) with { Identity = DisplayIdentityReader.Read(path) }).ToArray(),
                nativeModes.Select(ConvertMode).ToArray(), []);
            var issues = Validate(snapshot);
            return snapshot with { Status = issues.Length == 0 ? "ok" : "partial", Issues = issues };
        }
        return Failure(flags, "topology-race", N.InsufficientBuffer);
    }

    internal static string[] Validate(TopologySnapshot snapshot)
    {
        var issues = new List<string>();
        if (snapshot.SchemaVersion != 1) issues.Add("unsupported-schema");
        if (snapshot.Paths.Length == 0) issues.Add("no-active-paths");
        var targets = new HashSet<(AdapterKey, uint)>();
        foreach (var path in snapshot.Paths)
        {
            var label = $"target:{path.TargetAdapter.High:X8}:{path.TargetAdapter.Low:X8}:{path.TargetId}";
            if ((path.Flags & N.PathActive) == 0) issues.Add(label + ":inactive");
            if (!path.Available) issues.Add(label + ":unavailable");
            if (!targets.Add((path.TargetAdapter, path.TargetId))) issues.Add(label + ":duplicate-target");
            if (!ValidMode(snapshot.Modes, path.SourceMode, 1, path.SourceAdapter, path.SourceId))
                issues.Add(label + ":source-mode");
            if (!ValidMode(snapshot.Modes, path.TargetMode, 2, path.TargetAdapter, path.TargetId))
                issues.Add(label + ":target-mode");
            if (path.DesktopMode is uint index &&
                (index >= snapshot.Modes.Length || snapshot.Modes[index].Type != 3
                    || snapshot.Modes[index].Desktop is null))
                issues.Add(label + ":desktop-mode");
        }
        if (snapshot.Modes.Any(m => m.Type is < 1 or > 3)) issues.Add("unknown-mode-type");
        return issues.ToArray();
    }

    private static bool ValidMode(TopologyMode[] modes, uint? index, uint type, AdapterKey adapter, uint id)
    {
        if (index is not uint i || i >= modes.Length) return false;
        var m = modes[i];
        if (m.Type != type || m.Adapter != adapter || m.Id != id) return false;
        return type == 1 ? m.Source is { Width: > 0, Height: > 0 } : m.Target is not null;
    }

    internal static TopologyPath ConvertPath(N.Path path)
    {
        var s = path.Source;
        var t = path.Target;
        var aware = (path.Flags & N.PathVirtual) != 0;
        return new(Key(s.Adapter), s.Id, Index(s.ModeIndex, aware),
            aware ? SmallIndex(s.ModeIndex & 0xffff) : null, s.Status,
            Key(t.Adapter), t.Id, Index(t.ModeIndex, aware),
            aware ? SmallIndex(t.ModeIndex & 0xffff) : null,
            t.Technology, t.Rotation, t.Scaling, Rate(t.Refresh), t.Scanline,
            t.Available != 0, t.Status, path.Flags);
    }

    internal static TopologyMode ConvertMode(N.Mode mode)
    {
        var s = mode.Source;
        var t = mode.Target;
        var d = mode.Desktop;
        return new(mode.Type, Key(mode.Adapter), mode.Id,
            mode.Type == 1 ? new(s.Width, s.Height, s.PixelFormat, s.Position.X, s.Position.Y) : null,
            mode.Type == 2 ? new(t.PixelRate, Rate(t.Horizontal), Rate(t.Vertical),
                t.Active.Width, t.Active.Height, t.Total.Width, t.Total.Height, t.Standard, t.Scanline) : null,
            mode.Type == 3 ? new(d.SourceSize.X, d.SourceSize.Y, Rect(d.Region), Rect(d.Clip)) : null);
    }

    private static uint? Index(uint value, bool aware) => aware ? SmallIndex(value >> 16)
        : value == uint.MaxValue ? null : value;
    private static uint? SmallIndex(uint value) => value == 0xffff ? null : value;
    private static AdapterKey Key(N.Luid id) => new(id.Low, id.High);
    private static DisplayRate Rate(N.Rational value) => new(value.Numerator, value.Denominator);
    private static DisplayRect Rect(N.Rect value) => new(value.Left, value.Top, value.Right, value.Bottom);
    private static TopologySnapshot Failure(uint flags, string status, int? error = null) =>
        new(1, DateTimeOffset.UtcNow, flags, status, error, [], [], [status]);
}
