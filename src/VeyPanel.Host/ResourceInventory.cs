using System.Diagnostics;
using System.Net.NetworkInformation;

namespace VeyPanel.Host;

public sealed record NetworkMetric(string Name, double? ReceiveBytesPerSecond, double? TransmitBytesPerSecond);
public sealed record VolumeMetric(string Name, long? TotalBytes, long? FreeBytes);
public sealed record ResourceSnapshot(string NetworkStatus, NetworkMetric[] Network,
    string StorageStatus, VolumeMetric[] Volumes, DateTimeOffset? StorageTimestampUtc);

internal static class RateMath
{
    internal static double? Calculate(long? previous, long current, double seconds) =>
        previous is long old && old >= 0 && current >= old && double.IsFinite(seconds) && seconds > 0
            ? (current - old) / seconds : null;
}

internal sealed class ResourceInventory
{
    private Dictionary<string, (long Rx, long Tx, long Tick)> previous = new();
    private VolumeMetric[] volumes = [];
    private string storageStatus = "warming-up";
    private long? storageTick;
    private DateTimeOffset? storageTime;

    internal ResourceSnapshot Capture()
    {
        var (networkStatus, network) = ReadNetwork();
        var now = Stopwatch.GetTimestamp();
        if (storageTick is null || Stopwatch.GetElapsedTime(storageTick.Value, now).TotalSeconds >= 5)
        {
            (storageStatus, volumes) = ReadVolumes();
            storageTick = Stopwatch.GetTimestamp();
            storageTime = DateTimeOffset.UtcNow;
        }
        return new(networkStatus, network, storageStatus, volumes, storageTime);
    }

    private (string, NetworkMetric[]) ReadNetwork()
    {
        var next = new Dictionary<string, (long Rx, long Tx, long Tick)>();
        var results = new List<NetworkMetric>();
        bool partial = false;
        try
        {
            foreach (var nic in NetworkInterface.GetAllNetworkInterfaces())
            {
                if (nic.OperationalStatus != OperationalStatus.Up || nic.NetworkInterfaceType == NetworkInterfaceType.Loopback)
                    continue;
                try
                {
                    var counters = nic.GetIPStatistics();
                    var current = (Rx: counters.BytesReceived, Tx: counters.BytesSent, Tick: Stopwatch.GetTimestamp());
                    double? rx = null, tx = null;
                    if (previous.TryGetValue(nic.Id, out var old))
                    {
                        var seconds = Stopwatch.GetElapsedTime(old.Tick, current.Tick).TotalSeconds;
                        rx = RateMath.Calculate(old.Rx, current.Rx, seconds);
                        tx = RateMath.Calculate(old.Tx, current.Tx, seconds);
                    }
                    next[nic.Id] = current;
                    results.Add(new(nic.Name, rx, tx));
                }
                catch (Exception ex) when (ex is NetworkInformationException or InvalidOperationException or PlatformNotSupportedException)
                { partial = true; results.Add(new(nic.Name, null, null)); }
            }
        }
        catch (NetworkInformationException) { partial = true; }
        previous = next;
        var status = partial ? "partial" : results.Count == 0 ? "unavailable"
            : results.Any(n => n.ReceiveBytesPerSecond is null || n.TransmitBytesPerSecond is null) ? "warming-up" : "ok";
        return (status, results.ToArray());
    }

    private static (string, VolumeMetric[]) ReadVolumes()
    {
        var results = new List<VolumeMetric>();
        bool partial = false;
        try
        {
            foreach (var drive in DriveInfo.GetDrives())
            {
                try
                {
                    if (drive.DriveType != DriveType.Fixed) continue;
                    if (!drive.IsReady) { partial = true; results.Add(new(drive.Name, null, null)); continue; }
                    var total = drive.TotalSize;
                    var free = drive.TotalFreeSpace;
                    if (total <= 0 || free < 0 || free > total)
                    { partial = true; results.Add(new(drive.Name, null, null)); continue; }
                    results.Add(new(drive.Name, total, free));
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
                { partial = true; results.Add(new(drive.Name, null, null)); }
            }
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException) { partial = true; }
        return (partial ? "partial" : results.Count == 0 ? "unavailable" : "ok", results.ToArray());
    }
}
