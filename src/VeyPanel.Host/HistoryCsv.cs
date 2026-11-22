using System.Globalization;
using System.Text;

namespace VeyPanel.Host;

internal static class HistoryCsv
{
    internal const string Header = "timestamp_utc,cpu_percent,ram_percent,gpu_percent,video_encode_percent,video_decode_percent,disk_read_bytes_per_second,disk_write_bytes_per_second";
    internal static string Format(HistorySnapshot history)
    {
        var csv = new StringBuilder().Append(Header).Append("\r\n");
        foreach (var p in history.Samples)
        {
            csv.Append(p.TimestampUtc.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture));
            foreach (var value in new[] { p.CpuPercent, p.MemoryUsedPercent, p.GpuPercent,
                p.VideoEncodePercent, p.VideoDecodePercent, p.DiskReadBytesPerSecond, p.DiskWriteBytesPerSecond })
            {
                csv.Append(',');
                if (value is double n && double.IsFinite(n) && n >= 0)
                    csv.Append(n.ToString("G17", CultureInfo.InvariantCulture));
            }
            csv.Append("\r\n");
        }
        return csv.ToString();
    }
}
