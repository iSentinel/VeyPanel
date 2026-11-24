using VeyPanel.Host;

internal static class TouchBindingTests
{
    internal static int Run()
    {
        var now = DateTimeOffset.UtcNow;
        var snapshot = Fixture(now);
        var key = new AdapterKey(7, 0);
        var screen = new TouchViewport(2000, 1200, 2000, 1200, 0);
        var failures = 0;
        foreach (var (name, valid) in Checks(snapshot, now, key, screen))
        {
            Console.WriteLine($"{(valid ? "PASS" : "FAIL")} touch identity gate: {name}");
            if (!valid) failures++;
        }
        return failures;
    }

    private static IEnumerable<(string, bool)> Checks(TopologySnapshot s, DateTimeOffset now,
        AdapterKey adapter, TouchViewport viewport)
    {
        DesktopTouchPoint? Map(TopologySnapshot before, TopologySnapshot current,
            long beforeGeneration = 7, long activeGeneration = 7, double x = 1000) =>
            TouchBindingGuard.TryMap(x, 600, viewport, before, current, adapter, 2,
                beforeGeneration, activeGeneration, now);
        yield return ("validated center", Map(s, s) == new DesktopTouchPoint(-1000, 600));
        yield return ("wrong adapter rejected", TouchBindingGuard.TryMap(1000, 600, viewport,
            s, s, new AdapterKey(99, 0), 2, 7, 7, now) is null);
        yield return ("expired binding rejected", Map(s with { TimestampUtc = now.AddSeconds(-11) }, s) is null);
        yield return ("future snapshot rejected", Map(s, s with { TimestampUtc = now.AddSeconds(1) }) is null);
        yield return ("generation mismatch rejected", Map(s, s, 7, 8) is null);
        yield return ("zero generation rejected", Map(s, s, 0, 0) is null);
        yield return ("topology status rejected", Map(s, s with { Status = "partial" }) is null);
        yield return ("target identity rejected", Map(s, s with {
            Paths = [s.Paths[0] with { Identity = s.Paths[0].Identity! with {
                MonitorDevicePath = "different-target" } }]
        }) is null);
        yield return ("source moved rejected", Map(s, s with {
            Modes = [s.Modes[0] with { Source = s.Modes[0].Source! with { X = -1900 } }, s.Modes[1]]
        }) is null);
        yield return ("duplicate target rejected", Map(s with { Paths = [s.Paths[0], s.Paths[0]] }, s) is null);
        yield return ("missing identity rejected", Map(s with {
            Paths = [s.Paths[0] with { Identity = null }]
        }, s) is null);
        yield return ("invalid huge frame rejected", Map(s with {
            Modes = [s.Modes[0] with { Source = s.Modes[0].Source! with { Width = 65536 } }, s.Modes[1]]
        }, s with {
            Modes = [s.Modes[0] with { Source = s.Modes[0].Source! with { Width = 65536 } }, s.Modes[1]]
        }) is null);
        var bars = new TouchViewport(2400, 1200, 2000, 1200, 0);
        yield return ("letterbox rejected", TouchBindingGuard.TryMap(100, 600, bars,
            s, s, adapter, 2, 7, 7, now) is null);
    }

    private static TopologySnapshot Fixture(DateTimeOffset now)
    {
        var key = new AdapterKey(7, 0);
        var identity = new DisplayIdentity("DISPLAY1", "Mock panel", "mock-device-path",
            1, 5, null, null, 0, 0, 0);
        var path = new TopologyPath(key, 1, 0, null, 0, key, 2, 1, null, 5, 0, 0,
            new DisplayRate(60, 1), 0, true, 0, DisplayConfigNative.PathActive)
        {
            Identity = identity
        };
        var source = new TopologyMode(1, key, 1,
            new SourceGeometry(2000, 1200, 4, -2000, 0), null, null);
        var target = new TopologyMode(2, key, 2, null,
            new TargetTiming(100, new DisplayRate(1, 1), new DisplayRate(60, 1),
                2000, 1200, 2100, 1300, 0, 1), null);
        return new TopologySnapshot(1, now, 82, "ok", null, [path], [source, target], []);
    }
}
