using System.Diagnostics;
using System.Text.Json;

namespace VeyPanel.Host;

public sealed record StorageHealthDisk(string? Name, string? Model, string? MediaType, string? BusType,
    ulong? SizeBytes, string? ProviderHealth, string CounterStatus, ulong? TemperatureC,
    ulong? WearPercent, ulong? PowerOnHours, ulong? ReadErrorsTotal, ulong? WriteErrorsTotal);
public sealed record StorageHealthSnapshot(string Status, DateTimeOffset? TimestampUtc, StorageHealthDisk[] Disks);

public sealed class StorageHealthWorker : BackgroundService
{
    private StorageHealthSnapshot latest = new("warming-up", null, []);
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);
    internal StorageHealthSnapshot Latest => Fresh(Volatile.Read(ref latest), DateTimeOffset.UtcNow);

    internal static StorageHealthSnapshot Fresh(StorageHealthSnapshot sample, DateTimeOffset now) =>
        sample.TimestampUtc is DateTimeOffset stamp && (now - stamp).TotalSeconds is < -5 or > 150
            ? new("stale", stamp, []) : sample;

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (!OperatingSystem.IsWindows())
        {
            Volatile.Write(ref latest, new("unsupported-platform", null, [])); return;
        }
        do
        {
            var result = await CollectAsync(stoppingToken);
            Volatile.Write(ref latest, result);
            await Task.Delay(TimeSpan.FromSeconds(60), stoppingToken);
        } while (!stoppingToken.IsCancellationRequested);
    }

    private static async Task<StorageHealthSnapshot> CollectAsync(CancellationToken stop)
    {
        var script = Path.Combine(AppContext.BaseDirectory, "diagnostics", "Get-StorageHealth.ps1");
        var executable = Path.Combine(Environment.SystemDirectory, "WindowsPowerShell", "v1.0", "powershell.exe");
        if (!File.Exists(script) || !File.Exists(executable)) return Empty("unavailable");
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(stop);
        deadline.CancelAfter(TimeSpan.FromSeconds(20));
        using var child = new Process { StartInfo = new ProcessStartInfo(executable) {
            UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true,
            RedirectStandardError = true, WorkingDirectory = Path.GetDirectoryName(script)!
        }};
        foreach (var argument in new[] { "-NoLogo", "-NoProfile", "-NonInteractive", "-File", script, "-AsJson" })
            child.StartInfo.ArgumentList.Add(argument);
        bool started = false;
        try
        {
            started = child.Start();
            if (!started) return Empty("unavailable");
            var output = ReadBoundedAsync(child.StandardOutput, 256 * 1024, deadline.Token);
            var errors = ReadBoundedAsync(child.StandardError, 32 * 1024, deadline.Token);
            await child.WaitForExitAsync(deadline.Token);
            await errors;
            var report = await output;
            if (child.ExitCode is not (0 or 1)) return Empty("unavailable");
            return Parse(report, DateTimeOffset.UtcNow);
        }
        catch (OperationCanceledException) { return Empty(stop.IsCancellationRequested ? "unavailable" : "timeout"); }
        catch (Exception ex) when (ex is IOException or InvalidOperationException or System.ComponentModel.Win32Exception or JsonException)
        { return Empty("unavailable"); }
        finally
        {
            if (started && !child.HasExited)
            {
                try { child.Kill(entireProcessTree: true); await child.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(2)); }
                catch (Exception ex) when (ex is InvalidOperationException or System.ComponentModel.Win32Exception or TimeoutException) { }
            }
        }
    }

    private static async Task<string> ReadBoundedAsync(StreamReader reader, int limit, CancellationToken ct)
    {
        var result = new System.Text.StringBuilder();
        var buffer = new char[4096];
        int count;
        while ((count = await reader.ReadAsync(buffer.AsMemory(), ct)) != 0)
        {
            if (result.Length + count > limit) throw new InvalidDataException("Provider output limit");
            result.Append(buffer, 0, count);
        }
        return result.ToString();
    }

    internal static StorageHealthSnapshot Parse(string text, DateTimeOffset now)
    {
        try
        {
            using var document = JsonDocument.Parse(text);
            var root = document.RootElement;
            if (root.GetProperty("schemaVersion").GetInt32() != 1
                || root.GetProperty("source").GetString() != "Windows Storage Provider")
                return Empty("unavailable");
            var stamp = root.GetProperty("timestampUtc").GetDateTimeOffset();
            if (Math.Abs((now - stamp).TotalSeconds) > 30) return Empty("stale");
            var status = root.GetProperty("status").GetString();
            if (status is not ("ok" or "partial" or "unavailable")) return Empty("unavailable");
            var rows = root.GetProperty("disks");
            if (rows.ValueKind != JsonValueKind.Array || rows.GetArrayLength() > 128) return Empty("unavailable");
            var result = rows.Deserialize<StorageHealthDisk[]>(Json);
            if (result is null || result.Any(d => d is null || !Valid(d))) return Empty("unavailable");
            if (status == "unavailable" || result.Length == 0) return new("unavailable", stamp, []);
            return new(status, stamp, result);
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException or KeyNotFoundException or FormatException)
        { return Empty("unavailable"); }
    }

    private static bool Valid(StorageHealthDisk disk) =>
        disk.CounterStatus is "unavailable" or "partial" or "provider-reported"
        && disk.TemperatureC is null or (>= 1 and <= 150)
        && disk.WearPercent is null or <= 100
        && new[] { disk.Name, disk.Model, disk.MediaType, disk.BusType, disk.ProviderHealth }.All(s => s is null || s.Length <= 256)
        && (disk.CounterStatus != "unavailable" || (disk.TemperatureC is null && disk.WearPercent is null
            && disk.PowerOnHours is null && disk.ReadErrorsTotal is null && disk.WriteErrorsTotal is null));

    private static StorageHealthSnapshot Empty(string status) => new(status, DateTimeOffset.UtcNow, []);
}
