using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace VeyPanel.Host;

public sealed record ThermalReading(string Category, string Hardware, string Sensor, double? Celsius);
public sealed record ThermalSnapshot(string Status, DateTimeOffset? ReceivedUtc, ThermalReading[] Sensors);

internal static partial class ThermalProvider
{
    [GeneratedRegex(@"^(-?[0-9]{1,3}[.,][0-9]) °C$", RegexOptions.CultureInvariant)]
    private static partial Regex TemperaturePattern();

    internal static double? ParseCelsius(JsonElement raw)
    {
        if (raw.ValueKind != JsonValueKind.String) return null;
        var match = TemperaturePattern().Match(raw.GetString() ?? "");
        if (!match.Success || !double.TryParse(match.Groups[1].Value.Replace(',', '.'),
            NumberStyles.AllowLeadingSign | NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var n))
            return null;
        return double.IsFinite(n) && n is >= -50 and <= 150 ? n : null;
    }

    internal static ThermalSnapshot Parse(string data, DateTimeOffset received)
    {
        try
        {
            using var json = JsonDocument.Parse(data, new JsonDocumentOptions { MaxDepth = 24 });
            var root = json.RootElement;
            if (Text(root, "Text") != "Sensor" || !root.TryGetProperty("Children", out var children)
                || children.ValueKind != JsonValueKind.Array)
                return new("invalid-schema", received, []);
            var readings = new List<ThermalReading>();
            int nodes = 0;
            Walk(root, null, null, null, readings, ref nodes);
            var status = readings.Count == 0 ? "unavailable"
                : readings.Any(r => r.Celsius is null) ? "partial" : "provider-reported";
            if (readings.All(r => r.Celsius is null)) status = "unavailable";
            return new(status, received, readings.ToArray());
        }
        catch (Exception ex) when (ex is JsonException or InvalidDataException)
        { return new("invalid-schema", received, []); }
    }

    private static void Walk(JsonElement node, string? category, string? hardware, string? hardwareId,
        List<ThermalReading> rows, ref int nodes)
    {
        if (++nodes > 8192 || node.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("Thermal tree limit or node shape");
        if (node.TryGetProperty("HardwareId", out _))
        {
            hardwareId = Text(node, "HardwareId");
            category = Category(hardwareId);
            hardware = Label(Text(node, "Text"));
        }
        if (category is not null && hardware is not null && hardwareId is not null
            && Text(node, "Type") == "Temperature" && Text(node, "SensorId") is string id
            && id.StartsWith(hardwareId + "/temperature/", StringComparison.OrdinalIgnoreCase))
        {
            if (rows.Count >= 256) throw new InvalidDataException("Thermal row limit");
            var sensor = Label(Text(node, "Text"));
            if (sensor is not null)
                rows.Add(new(category, hardware, sensor,
                    node.TryGetProperty("RawValue", out var raw) ? ParseCelsius(raw) : null));
        }
        if (!node.TryGetProperty("Children", out var children)) return;
        if (children.ValueKind != JsonValueKind.Array) throw new InvalidDataException("Thermal children");
        foreach (var child in children.EnumerateArray()) Walk(child, category, hardware, hardwareId, rows, ref nodes);
    }

    private static string? Category(string? id)
    {
        var prefix = id?.Split('/', StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();
        return prefix switch
        {
            "intelcpu" or "amdcpu" or "genericcpu" => "CPU",
            "gpu-intel-integrated" or "gpu-amd" or "gpu-nvidia" => "GPU",
            _ => null
        };
    }
    private static string? Text(JsonElement node, string key) =>
        node.ValueKind == JsonValueKind.Object && node.TryGetProperty(key, out var value)
        && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
    private static string? Label(string? value) =>
        !string.IsNullOrWhiteSpace(value) && value.Length <= 128 && !value.Any(char.IsControl) ? value : null;
}

public sealed class ThermalWorker : BackgroundService
{
    private ThermalSnapshot latest = new("disabled", null, []);
    internal ThermalSnapshot Latest => Fresh(Volatile.Read(ref latest), DateTimeOffset.UtcNow);

    internal static ThermalSnapshot Fresh(ThermalSnapshot sample, DateTimeOffset now) =>
        sample.ReceivedUtc is DateTimeOffset stamp && (now - stamp).TotalSeconds is < -5 or > 20
            ? new("stale", stamp, []) : sample;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (Environment.GetEnvironmentVariable("VEYPANEL_LHM_LOCAL") != "1") return;
        using var client = new HttpClient(new HttpClientHandler {
            UseProxy = false, AllowAutoRedirect = false, UseCookies = false
        }) { Timeout = TimeSpan.FromSeconds(3), MaxResponseContentBufferSize = 512 * 1024 };
        do
        {
            Volatile.Write(ref latest, await CollectAsync(client, stoppingToken));
            await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
        } while (!stoppingToken.IsCancellationRequested);
    }

    internal static async Task<ThermalSnapshot> CollectAsync(HttpClient client, CancellationToken ct)
    {
        try
        {
            using var result = await client.GetAsync("http://127.0.0.1:8085/data.json", ct);
            if (!result.IsSuccessStatusCode) return new("unavailable", DateTimeOffset.UtcNow, []);
            return ThermalProvider.Parse(await result.Content.ReadAsStringAsync(ct), DateTimeOffset.UtcNow);
        }
        catch (OperationCanceledException) { return new("unavailable", DateTimeOffset.UtcNow, []); }
        catch (Exception ex) when (ex is HttpRequestException or IOException or InvalidOperationException)
        { return new("unavailable", DateTimeOffset.UtcNow, []); }
    }
}
