using VeyPanel.Host;

internal static class TouchMappingTests
{
    internal static int Run()
    {
        var failures = 0;
        foreach (var (label, expected, actual) in Cases())
        {
            var pass = actual == expected;
            Console.WriteLine($"{(pass ? "PASS" : "FAIL")} touch mapping: {label}");
            if (!pass) failures++;
        }
        return failures;
    }

    private static IEnumerable<(string, DesktopTouchPoint?, DesktopTouchPoint?)> Cases()
    {
        var full = new TouchViewport(1920, 1080, 1920, 1080, 0);
        var desktop = new DisplayRect(-1920, -100, 0, 980);
        yield return ("top left negative origin", new(-1920, -100), TouchMapping.Map(0, 0, full, desktop));
        yield return ("bottom right", new(-1, 979), TouchMapping.Map(1920, 1080, full, desktop));
        yield return ("center negative origin", new(-960, 440), TouchMapping.Map(960, 540, full, desktop));
        var bars = new TouchViewport(200, 100, 100, 100, 0);
        var square = new DisplayRect(0, 0, 100, 100);
        yield return ("left black bar rejected", null, TouchMapping.Map(49, 50, bars, square));
        yield return ("right black bar rejected", null, TouchMapping.Map(151, 50, bars, square));
        yield return ("content left edge", new(0, 50), TouchMapping.Map(50, 50, bars, square));
        yield return ("content right edge", new(99, 50), TouchMapping.Map(150, 50, bars, square));
        yield return ("90 degrees clockwise inverse", new(0, 99), Rotate(0, 0, 90));
        yield return ("180 degrees clockwise inverse", new(199, 99), Rotate(0, 0, 180));
        yield return ("270 degrees clockwise inverse", new(199, 0), Rotate(0, 0, 270));
        yield return ("invalid view", null, TouchMapping.Map(1, 1, new(0, 100, 100, 100, 0), square));
        yield return ("invalid destination", null, TouchMapping.Map(1, 1, full, new(5, 4, 3, 2)));
        yield return ("unsupported rotation", null, TouchMapping.Map(1, 1, new(100, 100, 100, 100, 45), square));
        yield return ("NaN rejected", null, TouchMapping.Map(double.NaN, 50, bars, square));
        yield return ("infinity rejected", null, TouchMapping.Map(100, double.PositiveInfinity, bars, square));
        yield return ("touch outside screen", null, TouchMapping.Map(200, 50, new(100, 100, 100, 100, 0), square));
        yield return ("desktop overflow rejected", null,
            TouchMapping.Map(50, 50, full, new(int.MinValue, 0, int.MaxValue, 100)));
    }

    private static DesktopTouchPoint? Rotate(double x, double y, int degrees) =>
        TouchMapping.Map(x, y, new(100, 200, 100, 200, degrees), new(0, 0, 200, 100));
}
