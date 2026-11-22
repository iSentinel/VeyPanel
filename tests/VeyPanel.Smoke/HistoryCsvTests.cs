using System.Globalization;
using VeyPanel.Host;

internal static class HistoryCsvTests
{
    internal static int Run()
    {
        var old = CultureInfo.CurrentCulture;
        try
        {
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("uk-UA");
            var now = new DateTimeOffset(2026, 11, 22, 12, 0, 0, TimeSpan.Zero);
            var csv = HistoryCsv.Format(new HistorySnapshot(now, 900, [
                new HistoryPoint(now, 12.5, null, 0, null, 22.5, 1024, null)
            ]));
            var rows = csv.Split("\r\n", StringSplitOptions.RemoveEmptyEntries);
            var ok = rows.Length == 2 && rows[0] == HistoryCsv.Header
                && rows[1] == "2026-11-22T12:00:00.0000000+00:00,12.5,,0,,22.5,1024,"
                && HistoryCsv.Format(new HistorySnapshot(now, 900, [])) == HistoryCsv.Header + "\r\n";
            Console.WriteLine($"{(ok ? "PASS" : "FAIL")} CSV invariant numeric values, UTC, empty and N/A");
            return ok ? 0 : 1;
        }
        finally { CultureInfo.CurrentCulture = old; }
    }
}
