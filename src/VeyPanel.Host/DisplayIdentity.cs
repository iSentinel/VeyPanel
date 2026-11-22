using System.Runtime.InteropServices;
using N = VeyPanel.Host.DisplayConfigNative;

namespace VeyPanel.Host;

internal sealed record DisplayIdentity(string? GdiName, string? FriendlyName, string? MonitorDevicePath,
    uint? ConnectorInstance, uint? OutputTechnology, ushort? EdidManufacturer, ushort? EdidProduct,
    uint? NameFlags, int SourceError, int TargetError);

internal static class DisplayIdentityReader
{
    [StructLayout(LayoutKind.Sequential)]
    private struct Header { public uint Type, Size; public N.Luid Adapter; public uint Id; }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct SourceName
    {
        public Header Header;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string Name;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct TargetName
    {
        public Header Header;
        public uint Flags, Technology;
        public ushort Manufacturer, Product;
        public uint Connector;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)] public string Name;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string DevicePath;
    }

    [DllImport("user32.dll", EntryPoint = "DisplayConfigGetDeviceInfo", ExactSpelling = true)]
    private static extern int GetSourceName(ref SourceName request);

    [DllImport("user32.dll", EntryPoint = "DisplayConfigGetDeviceInfo", ExactSpelling = true)]
    private static extern int GetTargetName(ref TargetName request);

    internal static bool LayoutValid() => Marshal.SizeOf<Header>() == 20
        && Marshal.SizeOf<SourceName>() == 84 && Marshal.SizeOf<TargetName>() == 420;

    internal static DisplayIdentity Read(N.Path path)
    {
        if (!LayoutValid()) return new(null, null, null, null, null, null, null, null, -1, -1);
        var source = new SourceName {
            Header = new() { Type = 1, Size = (uint)Marshal.SizeOf<SourceName>(),
                Adapter = path.Source.Adapter, Id = path.Source.Id },
            Name = string.Empty
        };
        var target = new TargetName {
            Header = new() { Type = 2, Size = (uint)Marshal.SizeOf<TargetName>(),
                Adapter = path.Target.Adapter, Id = path.Target.Id },
            Name = string.Empty, DevicePath = string.Empty
        };
        var se = GetSourceName(ref source);
        var te = GetTargetName(ref target);
        var edidValid = te == 0 && (target.Flags & 4) != 0;
        return new(se == 0 ? NonEmpty(source.Name) : null,
            te == 0 ? NonEmpty(target.Name) : null, te == 0 ? NonEmpty(target.DevicePath) : null,
            te == 0 ? target.Connector : null, te == 0 ? target.Technology : null,
            edidValid ? target.Manufacturer : null, edidValid ? target.Product : null,
            te == 0 ? target.Flags : null, se, te);
    }

    private static string? NonEmpty(string? value) => string.IsNullOrWhiteSpace(value) ? null : value;
}

internal static class DisplayRecoveryPolicy
{
    // Same-session eligibility only. This does not authorize or perform a display write.
    internal static string[] Check(TopologySnapshot baseline, TopologySnapshot current)
    {
        var issues = new List<string>();
        if (baseline.Status != "ok" || current.Status != "ok"
            || DisplayTopology.Validate(baseline).Length != 0 || DisplayTopology.Validate(current).Length != 0)
            issues.Add("incomplete-topology");
        if (baseline.QueryFlags != current.QueryFlags)
            issues.Add("query-flags-changed");
        var before = Index(baseline, issues);
        var after = Index(current, issues);
        if (before.Count == 0 || before.Count != after.Count) issues.Add("target-set-changed");
        foreach (var (key, path) in before)
        {
            if (!after.TryGetValue(key, out var match))
            { issues.Add("target-missing"); continue; }
            if (match.TargetAdapter != path.TargetAdapter || match.TargetId != path.TargetId
                || match.SourceAdapter != path.SourceAdapter || match.SourceId != path.SourceId
                || match.Identity?.ConnectorInstance != path.Identity?.ConnectorInstance
                || match.Technology != path.Technology)
                issues.Add("session-path-changed");
        }
        return issues.Distinct(StringComparer.Ordinal).ToArray();
    }

    private static Dictionary<string, TopologyPath> Index(TopologySnapshot snapshot, List<string> issues)
    {
        var result = new Dictionary<string, TopologyPath>(StringComparer.OrdinalIgnoreCase);
        foreach (var path in snapshot.Paths)
        {
            var identity = path.Identity;
            if (identity is null || identity.TargetError != 0 || identity.SourceError != 0
                || string.IsNullOrWhiteSpace(identity.GdiName)
                || string.IsNullOrWhiteSpace(identity.MonitorDevicePath))
            { issues.Add("target-identity-unavailable"); continue; }
            if (!result.TryAdd(identity.MonitorDevicePath, path)) issues.Add("ambiguous-target-identity");
        }
        return result;
    }
}
