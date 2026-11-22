using VeyPanel.Host;

internal static class GpuTests
{
    internal static int Run()
    {
        var tests = new (string Name, Func<bool> Test)[] {
            ("GPU counter layout", GpuEngineSampler.LayoutValid),
            ("GPU grouping across processes", Group),
            ("GPU missing encode is N/A", Missing),
            ("GPU explicit zero is valid", Zero),
            ("GPU malformed/duplicate samples", Malformed),
            ("GPU impossible group rejected", Impossible),
        };
        var failures = 0;
        foreach (var test in tests)
        {
            bool passed;
            try { passed = test.Test(); } catch { passed = false; }
            Console.WriteLine($"{(passed ? "PASS" : "FAIL")} {test.Name}");
            if (!passed) failures++;
        }
        Console.WriteLine($"{tests.Length - failures}/{tests.Length} GPU tests passed");
        return failures;
    }
    private static string Name(int pid, int engine, string type, int adapter = 1) =>
        $"pid_{pid}_luid_0x0_0x{adapter:x}_phys_0_eng_{engine}_engtype_{type}";

    private static bool Group()
    {
        var g = GpuEngineMath.Aggregate([(Name(1, 0, "3D"), 20), (Name(2, 0, "3D"), 35),
            (Name(3, 1, "VideoEncode"), 44), (Name(4, 0, "3D", 2), 50)]);
        return g.Status == "ok" && g.AdapterCount == 2 && g.BusiestEnginePercent == 55
            && g.VideoEncodePercent == 44 && g.VideoDecodePercent is null;
    }
    private static bool Missing() => GpuEngineMath.Aggregate([(Name(1, 0, "3D"), 40)]).VideoEncodePercent is null;
    private static bool Zero() => GpuEngineMath.Aggregate([(Name(1, 1, "VideoEncode"), 0)]).VideoEncodePercent == 0;
    private static bool Malformed()
    {
        var g = GpuEngineMath.Aggregate([(Name(1, 0, "3D"), 30), (Name(1, 0, "3D") + "#1", 30), ("unknown", 99)]);
        return g.Status == "partial" && g.BusiestEnginePercent == 30;
    }
    private static bool Impossible()
    {
        var g = GpuEngineMath.Aggregate([(Name(1, 1, "VideoEncode"), 80), (Name(2, 1, "VideoEncode"), 80)]);
        return g.Status == "unavailable" && g.VideoEncodePercent is null && g.BusiestEnginePercent is null;
    }
}
