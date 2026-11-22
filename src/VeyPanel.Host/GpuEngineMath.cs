using System.Text.RegularExpressions;
using System.Globalization;
using System.Text.Json.Serialization;

namespace VeyPanel.Host;

public sealed record GpuMetric(string Status, int AdapterCount, double? BusiestEnginePercent,
    double? VideoEncodePercent, double? VideoDecodePercent)
{
    public string InventoryStatus { get; init; } = "unavailable";
    public GpuAdapterMetric[] Adapters { get; init; } = [];
    [JsonIgnore] internal ObservedGpu[] Observed { get; init; } = [];
}

internal sealed record ObservedGpu(string Luid, double Busiest, double? Encode, double? Decode);

internal static partial class GpuEngineMath
{
    [GeneratedRegex(@"^pid_(?<pid>\d+)_luid_(?<high>0x[0-9a-f]+)_(?<low>0x[0-9a-f]+)_phys_(?<phys>\d+)_eng_(?<eng>\d+)_engtype_(?<type>[^#]+)(?:#\d+)?$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant)]
    private static partial Regex InstancePattern();

    internal static GpuMetric Aggregate(IEnumerable<(string Name, double? Percent)> samples)
    {
        var engines = new Dictionary<string, (string Adapter, string Type, double Percent)>(StringComparer.OrdinalIgnoreCase);
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        bool partial = false;
        foreach (var (name, percent) in samples)
        {
            var match = InstancePattern().Match(name);
            if (!match.Success || percent is not double value || !double.IsFinite(value) || value < 0 || value > 100)
            { partial = true; continue; }
            if (!uint.TryParse(match.Groups["high"].Value.AsSpan(2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var high)
                || !uint.TryParse(match.Groups["low"].Value.AsSpan(2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var low))
            { partial = true; continue; }
            var adapter = $"{DxgiInventory.Key(unchecked((int)high), low)}:{match.Groups["phys"].Value}";
            var type = match.Groups["type"].Value;
            var engine = $"{adapter}:{match.Groups["eng"].Value}:{type}";
            if (!seen.Add($"{engine}:{match.Groups["pid"].Value}"))
            { partial = true; continue; }
            var prior = engines.TryGetValue(engine, out var existing) ? existing.Percent : 0;
            engines[engine] = (adapter, type, prior + value);
        }
        var valid = engines.Values.Where(e => e.Percent <= 100.01)
            .Select(e => (e.Adapter, e.Type, Percent: Math.Min(100, e.Percent))).ToArray();
        partial |= valid.Length != engines.Count;
        if (valid.Length == 0) return Empty("unavailable");
        double? Peak(string type) => valid.Where(e => e.Type.Equals(type, StringComparison.OrdinalIgnoreCase))
            .Select(e => (double?)e.Percent).Max();
        return new(partial ? "partial" : "ok", valid.Select(e => e.Adapter).Distinct(StringComparer.OrdinalIgnoreCase).Count(),
            valid.Max(e => e.Percent), Peak("VideoEncode"), Peak("VideoDecode"))
        {
            Observed = valid.GroupBy(e => e.Adapter[..17], StringComparer.Ordinal)
                .Select(g => new ObservedGpu(g.Key, g.Max(e => e.Percent),
                    g.Where(e => e.Type.Equals("VideoEncode", StringComparison.OrdinalIgnoreCase)).Select(e => (double?)e.Percent).Max(),
                    g.Where(e => e.Type.Equals("VideoDecode", StringComparison.OrdinalIgnoreCase)).Select(e => (double?)e.Percent).Max())).ToArray()
        };
    }

    internal static GpuMetric Empty(string status) => new(status, 0, null, null, null);
}
