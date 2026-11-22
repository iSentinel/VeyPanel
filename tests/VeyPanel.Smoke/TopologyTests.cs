using System.Text.Json;
using VeyPanel.Host;
using N = VeyPanel.Host.DisplayConfigNative;

internal static class TopologyTests
{
    internal static int Run()
    {
        var failures = 0;
        var tests = new (string Name, Func<bool> Check)[] {
            ("CCD native ABI layouts", N.LayoutValid),
            ("CCD legacy indices", Legacy),
            ("CCD virtual indices and clone group", Virtual),
            ("CCD invalid index sentinels", Invalid),
            ("CCD source/target mode matching", Matching),
            ("CCD duplicate target rejected", Duplicate),
            ("CCD snapshot JSON round trip", RoundTrip),
            ("CCD identity ABI", DisplayIdentityReader.LayoutValid),
            ("CCD recovery identity policy", Recovery),
            ("CCD validate-only flags", ValidationFlags),
            ("CCD snapshot stability policy", Stability),
            ("CCD live capture", Live)
        };
        foreach (var test in tests)
        {
            bool pass;
            try { pass = test.Check(); } catch { pass = false; }
            Console.WriteLine($"{(pass ? "PASS" : "FAIL")} {test.Name}");
            if (!pass) failures++;
        }
        Console.WriteLine($"{tests.Length - failures}/{tests.Length} CCD tests passed");
        return failures;
    }

    private static N.Path Native(bool aware, uint sourceIndex, uint targetIndex) => new()
    {
        Source = new N.Source { Adapter = new N.Luid { Low = 7 }, Id = 1, ModeIndex = sourceIndex },
        Target = new N.Target { Adapter = new N.Luid { Low = 7 }, Id = 2, ModeIndex = targetIndex, Available = 1 },
        Flags = N.PathActive | (aware ? N.PathVirtual : 0)
    };

    private static bool Legacy()
    {
        var p = DisplayTopology.ConvertPath(Native(false, 0, 1));
        return p.SourceMode == 0 && p.TargetMode == 1 && p.CloneGroup is null && p.DesktopMode is null;
    }

    private static bool Virtual()
    {
        var p = DisplayTopology.ConvertPath(Native(true, 0x00020009, 0x00030004));
        return p.SourceMode == 2 && p.CloneGroup == 9 && p.TargetMode == 3 && p.DesktopMode == 4;
    }

    private static bool Invalid()
    {
        var p = DisplayTopology.ConvertPath(Native(true, uint.MaxValue, uint.MaxValue));
        var q = DisplayTopology.ConvertPath(Native(false, uint.MaxValue, uint.MaxValue));
        return p.SourceMode is null && p.TargetMode is null && p.CloneGroup is null
            && p.DesktopMode is null && q.SourceMode is null && q.TargetMode is null;
    }

    private static TopologySnapshot Fixture()
    {
        var p = DisplayTopology.ConvertPath(Native(false, 0, 1));
        var key = new AdapterKey(7, 0);
        var source = new TopologyMode(1, key, 1, new SourceGeometry(2000, 1200, 4, -2000, 0), null, null);
        var target = new TopologyMode(2, key, 2, null,
            new TargetTiming(100, new DisplayRate(1, 1), new DisplayRate(60, 1), 2000, 1200, 2100, 1300, 0, 1), null);
        return new TopologySnapshot(1, DateTimeOffset.UtcNow, 82, "ok", null, [p], [source, target], []);
    }

    private static bool Matching()
    {
        var s = Fixture();
        var p = s.Paths[0];
        return DisplayTopology.Validate(s).Length == 0
            && DisplayTopology.Validate(s with { Paths = [p with { TargetMode = 20 }] }).Length > 0
            && DisplayTopology.Validate(s with { Paths = [p with { SourceMode = 1 }] }).Length > 0
            && DisplayTopology.Validate(s with { Paths = [p with { SourceId = 77 }] }).Length > 0;
    }

    private static bool Duplicate()
    {
        var s = Fixture();
        return DisplayTopology.Validate(s with { Paths = [s.Paths[0], s.Paths[0]] })
            .Any(i => i.EndsWith(":duplicate-target", StringComparison.Ordinal));
    }

    private static bool RoundTrip()
    {
        var s = Fixture();
        var json = JsonSerializer.Serialize(s);
        var read = JsonSerializer.Deserialize<TopologySnapshot>(json);
        return read is not null && read.Modes[0].Source?.X == -2000
            && DisplayTopology.Validate(read).Length == 0;
    }

    private static bool Recovery()
    {
        var fixture = Fixture();
        var path = fixture.Paths[0] with {
            Identity = new DisplayIdentity("DISPLAY1", "Panel", "mock-monitor-path", 1, 5, null, null, 0, 0, 0)
        };
        var baseline = fixture with { Paths = [path] };
        var missing = fixture with { Paths = [path with { Identity = null }] };
        var changed = fixture with { Paths = [path with {
            Identity = path.Identity! with { MonitorDevicePath = "other-monitor" }
        }] };
        return DisplayRecoveryPolicy.Check(baseline, baseline).Length == 0
            && DisplayRecoveryPolicy.Check(baseline, missing).Contains("target-identity-unavailable")
            && DisplayRecoveryPolicy.Check(baseline, changed).Contains("target-missing")
            && DisplayRecoveryPolicy.Check(baseline, baseline with { Status = "partial" }).Contains("incomplete-topology");
    }

    private static bool ValidationFlags() =>
        N.ValidationFlags == 0x28060 && (N.ValidationFlags & (0x80 | 0x200 | 0x400)) == 0;

    private static bool Stability()
    {
        var s = Fixture();
        return DisplayValidation.Equivalent(s, s with { TimestampUtc = s.TimestampUtc.AddSeconds(1) })
            && !DisplayValidation.Equivalent(s, s with { Status = "partial" })
            && !DisplayValidation.Equivalent(s, s with {
                Paths = [s.Paths[0] with { Rotation = 2 }]
            });
    }

    private static bool Live()
    {
        var s = DisplayTopology.Capture();
        Console.WriteLine($"CCD status={s.Status}, paths={s.Paths.Length}, modes={s.Modes.Length}, nativeError={s.NativeError}");
        if (!OperatingSystem.IsWindows()) return s.Status == "unsupported-platform";
        if (s.Status == "native-error" && s.NativeError is 5 or 50)
        {
            Console.WriteLine("SKIP: CCD inaccessible in this desktop session");
            return true;
        }
        if (s.Status == "no-active-paths")
        {
            Console.WriteLine("SKIP: runner has no active display paths");
            return true;
        }
        return s.Status is "ok" or "partial" && s.Paths.Length > 0;
    }
}
