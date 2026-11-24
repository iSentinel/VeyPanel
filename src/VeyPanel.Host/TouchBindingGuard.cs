namespace VeyPanel.Host;

// Read-only precondition for a future owner-approved input session; no injection.
internal static class TouchBindingGuard
{
    internal static DesktopTouchPoint? TryMap(double x, double y, TouchViewport viewport,
        TopologySnapshot bound, TopologySnapshot current, AdapterKey adapter, uint targetId,
        long expectedGeneration, long activeGeneration, DateTimeOffset nowUtc)
    {
        if (expectedGeneration <= 0 || expectedGeneration != activeGeneration
            || !Fresh(bound.TimestampUtc, nowUtc) || !Fresh(current.TimestampUtc, nowUtc)
            || !DisplayValidation.Equivalent(bound, current)
            || DisplayRecoveryPolicy.Check(bound, current).Length != 0)
            return null;
        var matches = bound.Paths.Where(p => p.TargetAdapter == adapter && p.TargetId == targetId)
            .Take(2).ToArray();
        if (matches.Length != 1 || matches[0].SourceMode is not uint index
            || index >= bound.Modes.Length)
            return null;
        var mode = bound.Modes[(int)index];
        if (mode.Source is not SourceGeometry source || mode.Type != 1)
            return null;
        var right = (long)source.X + source.Width;
        var bottom = (long)source.Y + source.Height;
        if (right is < int.MinValue or > int.MaxValue
            || bottom is < int.MinValue or > int.MaxValue)
            return null;
        return TouchMapping.Map(x, y, viewport,
            new DisplayRect(source.X, source.Y, (int)right, (int)bottom));
    }

    private static bool Fresh(DateTimeOffset captured, DateTimeOffset now) =>
        captured <= now && now - captured <= TimeSpan.FromSeconds(10);
}
